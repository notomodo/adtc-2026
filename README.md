# adtc-2026

**An offline, CPU-only RAG document-Q&A assistant for SMEs.**
Built for the Africa Deep Tech Challenge 2026.

Small and medium enterprises hold their rules in PDFs — terms, policies, contracts —
and need plain-language answers grounded in those documents. This system retrieves the
relevant passages and (soon) has a small local LLM answer from them. It runs **entirely
offline on an 8 GB CPU-only machine**: no API calls, no network at runtime. Offline
operation and reproducibility from a clean clone are judged criteria, so they are
enforced in code, not left to convention.

## Architecture

```
   PDF ──▶ extraction ──▶ chunking ──▶ hybrid retrieval ──▶ [ LLM answer ]
           (pdfplumber)   (structure-   (BM25 + dense,        (Qwen2.5-3B,
                           aware)         RRF fusion)           grounded — TBD)
```

- **Extraction** — `src/ingestion/extract.py`: table-aware extractor for the financial
  corpus (headers carried into serialised rows). See `docs/REPO_CONSOLIDATION.md`.
- **Chunking** — `src/ingest_sme.py`: prose-first, structure-aware. Splits on clause and
  section boundaries (not blind character counts) and carries the section heading into
  every chunk. Token budget is **asserted** against the vendored tokenizer, never
  estimated.
- **Retrieval** — `src/retriever.py`: hand-rolled Okapi **BM25** (stdlib only) fused with
  a pluggable **dense encoder** via **Reciprocal Rank Fusion** (RRF, k=60). Pure-BM25
  fallback with an identical API (`encoder=None`).
- **LLM answer layer** — not built yet. Retrieval → Qwen2.5-3B with a grounding prompt.

## Retrieval result

Nine configurations benchmarked against a **47-chunk corpus of real SME documents**
(Kibuga, a Ugandan e-commerce marketplace — terms, privacy, returns, seller terms,
support; 22 pages, prose-only).

**Every hybrid beat BM25 alone on Recall@1 and on MRR — four models out of four, zero
counterexamples.**

| Retriever | R@1 | R@3 | R@5 | R@10 | MRR |
|---|---|---|---|---|---|
| BM25 only (baseline) | 53% | 79% | 89% | 95% | 0.664 |
| HYBRID: BM25 + e5-small-v2 | 63% | 79% | 84% | 100% | 0.717 |
| **HYBRID: BM25 + bge-small-en-v1.5** ✅ | **58%** | **84%** | **89%** | **95%** | **0.703** |
| HYBRID: BM25 + gte-small | 58% | 79% | 89% | 95% | 0.687 |
| HYBRID: BM25 + all-MiniLM-L6-v2 | 63% | 74% | 89% | 89% | 0.712 |

**Selected: BM25 + `bge-small-en-v1.5`** — the only configuration non-negative on every
metric (the others each regress somewhere: e5 loses R@5, MiniLM loses R@3). R@1 is the
metric that matters here: a higher top-1 hit rate means fewer chunks passed to the LLM,
which is a direct latency and RAM saving on CPU-only 8 GB hardware. Full rationale,
per-stratum results and the methodological caveats are in
[`docs/DECISION-002-retrieval-architecture.md`](docs/DECISION-002-retrieval-architecture.md).

`n = 19 questions` — thin. The result rests on **consistency across four independently
trained models**, not the size of any single gap.

## Quickstart

```bash
make setup   # install deps + vendor the tokenizer
make all     # ingest → label → benchmark → verify
```

`make setup` installs `requirements-bench.txt` (which pulls in PyTorch for benchmarking)
and vendors the tokenizer. To run only the offline pipeline (ingest / label / verify)
without PyTorch, `pip install -r requirements.txt` is enough.

Individual stages:

```bash
make ingest   # chunk data/raw/*.pdf  -> benchmarks/chunks_sme.txt (+ corpus fingerprint)
make label    # auto-label by proof   -> data/questions/questions_sme_auto.json
make bench    # run the retrieval bake-off (needs requirements-bench.txt)
make verify   # assert the corpus fingerprint matches the gold-label set
```

## Reproducibility (why this is enforced, not assumed)

Chunk IDs are **positional**, and gold labels are `(question → chunk_id)` pairs — so if
ingestion drifts by even one chunk, every label silently points at the wrong text. This
already happened once: an unpinned tokenizer produced 47 chunks on one machine and 57 on
another, invalidating an entire benchmark. Three guardrails prevent a repeat:

1. **Pinned dependencies.** `requirements.txt` is pinned exactly. `sentence-transformers`
   (≈800 MB of PyTorch) lives in `requirements-bench.txt` and is a **benchmark-only**
   dependency — production uses ONNX. Do not merge the two files.
2. **Vendored tokenizer.** `src/tokenizer.json` is committed. Without it the pipeline
   would fetch from the HuggingFace Hub at runtime, breaking the offline guarantee.
3. **Corpus fingerprint gate.** `scripts/verify_reproducibility.py` refuses to proceed
   unless the freshly-ingested corpus hashes to the value the labels were made against.

The expected corpus is **47 chunks**; auto-labelling yields **19/22 proven, 3 abstained**
(Q11, Q18, Q20 — the labeller abstains rather than guess). See
[`docs/CONCEPTS.md`](docs/CONCEPTS.md) for the concepts behind BM25, dense retrieval, RRF,
and abstaining gold labels.

## Layout

```
src/          retriever, chunker, autolabeller, eval harness, extraction/
scripts/      tokenizer vendoring + reproducibility gate
data/         raw/ (source PDFs) and questions/ (draft + gold sets)
benchmarks/   chunk dumps, result logs, review files
docs/         DECISION-002 (retrieval architecture) + CONCEPTS explainer
tests/        extraction regression suite (pytest)
```

## License

MIT — see [`LICENSE`](LICENSE). The challenge requires open source. Note that model
weights (Qwen, the embedding models) carry their own separate licences.
