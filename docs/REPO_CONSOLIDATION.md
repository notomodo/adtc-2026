# Repository Consolidation — ADTC 2026

**Status:** Reproducibility from the GitHub repository is a **hard competition
requirement**. Judges reproduce from the repo, not from chat history.

**Current risk:** artifacts have been delivered as per-session chat downloads across four
sessions, with in-session patches. Versions in circulation: `extract.py` (v1) →
`extract_v2.py` → `verify_extraction.py` (v2.0 → v2.1 → v3 → v3.1) → `extract_v3.py`.
**There is a live risk that no single repository currently contains the truth.**

This document is the fix. Work through it once; then the repo — not the chat — is
authoritative.

---

## 1. Target structure

```
adtc-2026/
├── README.md                      # what it is, how to run it, in <2 min
├── LICENSE                        # MIT or Apache-2.0 (see §5)
├── DECISIONS.md                   # decision records — the panel will read this
├── CHANGELOG.md
├── requirements.txt
├── .gitignore
│
├── src/
│   ├── ingestion/
│   │   ├── extract.py             # <- extract_v3.py, RENAMED. No version suffix.
│   │   ├── chunk.py
│   │   └── __init__.py
│   ├── retrieval/                 # (embedding + index — next phase)
│   ├── llm/
│   └── app/
│
├── tests/
│   ├── test_extraction.py         # wraps verify_extraction.py gates
│   ├── fixtures/
│   │   ├── ruled_table.pdf
│   │   ├── unruled_table.pdf
│   │   ├── multirow_header.pdf
│   │   └── CORRUPTED_v1_output.txt   # <- NEGATIVE CONTROL. Gates MUST fail on it.
│   └── conftest.py
│
├── benchmarks/
│   ├── benchmark_retrieval.py
│   ├── questions_interim_v1.json
│   └── results/                   # dated, environment-stamped outputs
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ENVIRONMENT_NOTES.md       # incl. the PDF-conversion finding (§4)
│   └── reports/
│       └── 2026-07-12_extraction_rework.md
│
└── .github/workflows/ci.yml
```

### Naming rule (adopt permanently)

**No version suffixes in filenames.** `extract.py`, not `extract_v3.py`. Git *is* the
version history. `extract_v2.py` sitting next to `extract_v3.py` in a repo is how a judge
ends up running the broken one.

Version suffixes were useful for chat delivery. They are a liability in a repository.

---

## 2. Consolidation checklist

- [ ] `git init` (or confirm the existing repo is the canonical one).
- [ ] Copy `extract_v3.py` → `src/ingestion/extract.py`. **Delete v1 and v2 entirely.**
      Do not keep them "just in case" — git has them.
- [ ] Copy `verify_extraction.py` → `tests/` and wrap its gates as pytest cases.
- [ ] Copy `benchmark_retrieval.py` + `questions_interim_v1.json` → `benchmarks/`.
- [ ] Commit the four test fixtures, **including the corrupted negative control**.
- [ ] Write `DECISIONS.md` (§3). This is the highest-value document in the repo.
- [ ] Write `docs/ENVIRONMENT_NOTES.md` (§4).
- [ ] Wire CI (§6).
- [ ] `pip install -r requirements.txt && pytest` on a **clean clone**. If that fails, a
      judge's reproduction fails.

---

## 3. DECISIONS.md — the panel will read this

Each record: what was decided, why, what was rejected, and **what would reverse it**.

Records to write up (all already made):

| # | Decision | Status |
|---|---|---|
| D1 | Domain: Entrepreneurship / SME productivity | Locked, 6 Jul |
| D2 | RAG over fine-tuning | Locked, 6 Jul |
| D3 | African-language bonus declined | Locked, 6 Jul |
| D4 | LLM: Qwen2.5-3B-Instruct (fallback: 1.5B) | Locked, 7 Jul |
| D5 | `num_thread=2` on 2-physical-core CPU | Measured, 7 Jul |
| D6 | Extraction contract + chunking strategy | Locked 8 Jul, **REVERSED 11 Jul**, re-locked 13 Jul |
| D7 | Runtime: benchmark on sentence-transformers, ship on ONNX | Locked, 11 Jul |
| D8 | Grade retrieval in isolation (Recall@k, MRR), not end-to-end | Locked, 11 Jul |
| D9 | English-only for v1; Swahili → v2 | Locked, 11 Jul |
| D10 | Reranker decision **deferred** pending embedder Recall@5 | Open |
| D11 | Chunk-size cap **deferred** pending embedder max input length | Open |
| D12 | Rotated-text/infographic extraction **out of scope for v1** | Locked, 13 Jul |

### D6 deserves its own section — write it as a strength

> The ingestion pipeline was locked on 8 July and found **semantically broken** on
> 11 July. Root cause: **fixture selection bias** — v1 was validated against a
> prose-heavy LaTeX report while the target workload is table-dense financial
> documents. The hardest content class was absent from the validation corpus at lock
> time. The lock was reversed, the extractor rebuilt table-first, and semantic quality
> gates added.

**"We locked it, found a semantic defect, reversed the lock, rebuilt, and re-verified"
is a stronger engineering story than "it worked first time."** It demonstrates a real
phase gate with real teeth. Do not hide it.

---

## 4. ENVIRONMENT_NOTES.md — record this so nobody rediscovers it

> **Claude project containers silently convert uploaded PDFs.** Files mounted into the
> container as `.pdf` are derivatives: one arrived as a plain-text dump, four as ZIP
> archives of page JPEGs. `pdfplumber` cannot read any of them.
>
> **Consequence: no Claude session can run extraction against the real PDF bytes.** All
> extraction verification must run locally. Chunk dumps must be returned to the session
> as `.txt` / `.json`, which survive conversion.
>
> This is structural, not a fixable upload mistake.

Also record: **HuggingFace is network-blocked** inside the container, so no embedding
model can be loaded there. The dense bake-off runs locally.

---

## 5. Licence

**Recommend MIT.** Short, permissive, universally understood, and imposes no obligations
on judges or downstream users. Apache-2.0 is the alternative — it adds an explicit patent
grant, which matters for a commercial spinout but adds friction for a hackathon judge.

Given the stated goal of a portfolio-quality open-source deliverable, **MIT** is the
cleaner default. Check whether ADTC mandates a specific licence before committing.

Verify the transitive licences of dependencies (`pdfplumber` → MIT;
`sentence-transformers` → Apache-2.0; model weights carry their **own** licences —
**Qwen2.5 and the BGE/GTE/E5 families each have separate terms, and these are NOT the same
as the library licence**). Model licences are a common and avoidable audit failure.

---

## 6. CI — make the gates unskippable

```yaml
# .github/workflows/ci.yml
name: ci
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: pip install pytest
      - run: pytest -v
```

`tests/test_extraction.py` must assert **both directions**:

```python
def test_gates_fire_on_known_bad():
    """NEGATIVE CONTROL. A gate that has never failed is untested."""
    corrupted = FIXTURES / "CORRUPTED_v1_output.txt"
    assert is_orphan_number_block(corrupted.read_text())

def test_gates_silent_on_known_good():
    """POSITIVE CONTROL. v2.0's gate over-fired on a table of contents
    precisely because this test did not exist."""
    assert not is_orphan_number_block(
        "Total revenue | H1 2024: 1,522,676 | H1 2023: 1,267,089"
    )
```

**Keep `CORRUPTED_v1_output.txt` in the repo forever.** It is the regression test for the
project's defining bug.

---

## 7. README — judges spend 2 minutes here

Structure, in order:

1. **What it does** — one sentence. "Offline document Q&A for SMEs. No cloud, no API keys."
2. **Why it exists** — the SME problem, in two sentences.
3. **Quick start** — clone, install, run. Must work on a clean machine.
4. **Architecture** — one diagram.
5. **Benchmarks** — the numbers, with the hardware they were measured on.
6. **Known limitations** — honest. Include the rotated-text limitation.
7. **Licence.**

Put a **measured number** above the fold. Not "fast and efficient" — the actual tokens/sec
and the actual RAM, with the actual CPU they were measured on.

---

## 8. Why this is urgent, not housekeeping

Reproducibility is **scored**. The failure mode is silent: everything works on your
machine, and a judge's clean clone breaks on a missing file, a stale `extract_v2.py`, or an
uncommitted fixture. You will not find out until it is too late to fix.

**The test is one command on a clean clone:**

```bash
git clone <repo> && cd adtc-2026 && pip install -r requirements.txt && pytest
```

If that does not pass, the repo is not reproducible — regardless of how well the code runs
where you wrote it.
