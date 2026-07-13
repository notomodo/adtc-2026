# Offline Document Q&A for SMEs

**Ask questions about your business documents. No internet. No API keys. No data leaves the
machine.**

Built for the Africa Deep Tech Challenge 2026.

---

## The problem

Small businesses hold their institutional knowledge in documents nobody has time to read —
contracts, financial statements, handbooks, policy files. The obvious answer is a cloud AI
assistant. In Uganda that answer breaks down: connectivity is unreliable and metered, and the
documents are commercially sensitive.

This runs entirely on an ordinary laptop. Point it at a folder of documents and ask questions
in plain English. It answers **from the documents**, citing what it found — and it is built so
that when it cannot find an answer, it says so instead of inventing one.

---

## Status

> **Under active development.** Extraction and the retrieval evaluation harness are complete and
> tested. Embedding model selection is **in progress**. The application layer is not yet built.
>
> This README documents what is **measured**, not what is planned. Numbers below are real.

---

## Measured performance

| | |
|---|---|
| **LLM** | Qwen2.5-3B-Instruct, ~2.1 GB resident |
| **Inference** | CPU-only. `num_thread=2` measured **faster** than 4 on a 2-physical-core CPU |
| **Extraction** | 5 tables / 126 rows recovered from a financial results release that the first pipeline **destroyed** |
| **Retrieval baseline** | BM25: R@5 **67%**, MRR **0.527** (18 questions, hand-labelled) |

**Measured on:** Intel i5-4300U (2 cores, Haswell), 7.66 GiB RAM, HDD, Debian 13.
This is a deliberately **pessimistic** floor — well below the 8 GB target spec.

> **Honesty note.** Every number above was measured on the hardware named. None are estimates.
> Where a claim is an inference rather than a measurement, it is labelled as such — in this
> README and in [`DECISIONS.md`](DECISIONS.md).

---

## Quick start

```bash
git clone https://github.com/<you>/adtc-2026.git
cd adtc-2026
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -v                                    # 20 tests, all should pass
```

Extract and verify a document:

```bash
python tools/dump_chunks.py your_document.pdf > chunks.txt
python tests/verify_extraction.py your_document.pdf
```

Benchmark retrieval:

```bash
python benchmarks/benchmark_retrieval.py \
    --dump chunks.txt \
    --questions benchmarks/questions_interim_v1.json
```

---

## Architecture

```
PDF ──► extract ──► chunk ──► embed ──► index
                                           │
                            question ──► retrieve ──► top-k chunks
                                                           │
                                              grounded prompt ──► Qwen2.5-3B ──► answer
```

Everything runs locally. No network calls at any stage.

### The one design decision worth knowing about

Financial documents are **tables**, and tables are where naive extraction quietly fails.
`pdfplumber.extract_text()` flattens a table into lines of text, which separates the header row
from its data. The result:

```
Total revenue    1,522,676   1,267,089   20.2%   772,184   639,161   20.8%
```

Six numbers, **no column headers**. Which is H1 2024? Unanswerable. No embedding model can
retrieve what is not semantically present, and the LLM will *hallucinate* the column mapping —
because the grounding context genuinely does not contain it.

**This pipeline serialises every table row to carry its own headers:**

```
Total revenue | H1 2024: 1,522,676 | H1 2023: 1,267,089 | YoY: 20.2% | Q2 2024: 772,184
```

Every number now travels with **both** its row name and its column name, in the same chunk. The
embedding encodes the association. The model **reads** the mapping instead of inventing it.

This sounds like a detail. It is the difference between a system that answers financial
questions and one that fabricates them.

---

## Engineering record

**We locked the ingestion pipeline. Three days later we found it was semantically destroying
financial documents. We reversed the lock, rebuilt it, and added gates that would have caught
it.**

That story is written up in full in [`DECISIONS.md`](DECISIONS.md) — including the root cause
(**fixture selection bias**: the pipeline was validated on a prose-heavy report while the target
workload is table-dense financial documents), and the two standing rules adopted to prevent a
recurrence.

The lesson, which recurred at four separate layers of this system:

> **Structural checks cannot detect semantic corruption.**

The chunker reported `chunk count: 49`, `no tiny chunks`, all green — on a corpus that was
destroyed. It even reported **zero tables detected in a financial annual report** and called it
a pass.

Every quality gate in this repository therefore ships with **both** a known-bad fixture (it must
fire) **and** a known-good fixture (it must stay silent), and the harness **aborts** if either
control fails. `tests/fixtures/CORRUPTED_v1_output.txt` is a permanent negative control. It
stays forever.

*A gate that has never failed is untested.*

---

## Known limitations

Stated plainly, because a system whose boundaries you cannot name is a system you do not
understand.

- **Scanned documents are not supported.** No OCR in v1. Scanned files are **detected and
  rejected**, not silently mangled.
- **Heavily designed marketing layouts** (infographic panels with rotated or curved text) extract
  with character-level garbling. These are **detected and flagged** by GATE 3, not passed
  silently. Out of scope for v1 — see [D12](DECISIONS.md).
- **English only.** Swahili and Ugandan languages are deferred to v2 — not for lack of interest,
  but because low-resource language quality would be genuinely poor, and shipping a broken
  feature is worse than not shipping it. See [D3](DECISIONS.md).
- **Retrieves stated facts; does not compute across them.** "What was service revenue?" is in
  scope. "What was the average margin over three years?" is not.

---

## Repository layout

```
src/ingestion/     extraction and chunking
src/retrieval/     embedding and index          (in progress)
src/llm/           local inference              (in progress)
src/app/           user interface               (planned)
tests/             semantic quality gates + bidirectional controls
benchmarks/        retrieval evaluation harness + labelled question set
docs/              architecture, decisions, session reports
```

---

## Licence

MIT. See [`LICENSE`](LICENSE).

Model weights carry **their own, separate licences** — Qwen2.5 and the embedding models each
have distinct terms. See [`DECISIONS.md`](DECISIONS.md) (R4).
