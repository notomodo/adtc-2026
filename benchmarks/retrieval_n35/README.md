# Retrieval re-run + reranker reopen, n=35

The locked retriever (BM25 + `bge-small-en-v1.5`, RRF k=60, unchanged — DECISION-002) was
re-run against the **expanded 35-question set** (`data/questions/questions_sme_v3.json`:
the original 19 `auto_v2` questions + 16 new `claude_v3` questions), then a cross-encoder
reranker was layered on top of that same locked retriever as an **evidence-only** study
reopening DECISION-003. **No ship/no-ship decision was made in either run** — see
[`docs/DECISION-005-reranker-reopen.md`](../../docs/DECISION-005-reranker-reopen.md) for
the decision status.

Read `REPORT.md` first (retrieval re-run), then `REPORT_reranker.md` (reranker reopen).

## Retrieval re-run (`REPORT.md`)

Same corpus (47 chunks, Kibuga), same locked hybrid config, same metric definitions as the
n=19 study (DECISION-002) — only the question set grew.

| | n=19 (DECISION-002) | n=35 (this bundle) |
|---|---|---|
| R@1 / R@3 / R@5 / R@10 | 58% / 84% / 89% / 95% | 60% / 80% / 83% / 91% |
| MRR | 0.703 | 0.704 |
| prose R@5 | 75% | **62%** |
| latency | ~40 ms/query | ~50-85 ms/query |

The drop comes entirely from the 16 new questions (4 deep prose misses: Q27, Q29, Q32,
Q35 — hand-verified against the source chunks; genuine retrieval misses, not mislabels).
`k=3` vs `k=5` costs exactly one question (Q17, prose, rank 4 — an *original* question, not
a new one). Consistency check: the 19 shared questions reproduce the original n=19 log's
ranks exactly.

## Reranker reopen (`REPORT_reranker.md`)

Cross-encoder `cross-encoder/ms-marco-MiniLM-L6-v2` layered on the (unmodified) locked
hybrid's top-N candidates, N swept over {10, 15, 20}. Best config N=10:

| Metric | baseline | + rerank top-10 |
|---|---|---|
| R@3 | 80% | 86% |
| R@5 | 83% | 89% |
| MRR | 0.704 | 0.783 |
| prose R@5 | 62% | 75% |
| multi_chunk R@5 | 80% | 100% |

Costs: **~1.3-2.7 s/query added CPU latency**; **two regressions** — Q31 (near_miss)
rank 1→4 (falls out of the `k=3` context window entirely), Q27 (paraphrase) rank 8→10.
Widening N past 10 recovers nothing further and adds more regressions — the deep prose
misses (Q19, Q29, Q35) are unreachable by reranking at any N tested; the cross-encoder
scores those gold chunks *lower*, not higher.

The source report makes no ship/no-ship call; see DECISION-005 for the recorded evidence
and open status.

## Reproduce

```bash
# from the repo root
python src/eval_sme_v3.py \
  --dump benchmarks/chunks_sme.txt \
  --questions data/questions/questions_sme_v3.json \
  --out benchmarks/retrieval_n35/eval_sme_v3_output.log

python src/eval_reranker.py \
  --dump benchmarks/chunks_sme.txt \
  --questions data/questions/questions_sme_v3.json \
  --out benchmarks/retrieval_n35/eval_reranker_output.log
```

Both harnesses import `retriever.HybridRetriever` / `SentenceTransformerEncoder` and
`eval_retriever.load_chunks` directly (same convention as `src/eval_retriever.py` — no
reimplementation). The corpus fingerprint gate (`c7f23f29b738b08d`) is checked against
both `benchmarks/chunks_sme.txt` and `data/questions/questions_sme_v3.json`, which now
carry it natively — no separate `.fp` copies are needed or committed.

`eval_reranker.py`'s only additional dependency is `sentence_transformers.CrossEncoder`,
already present via `requirements-bench.txt` (same benchmark-only class of dependency as
the embedding models — not on the offline shipping path). It needs
`cross-encoder/ms-marco-MiniLM-L6-v2` in the local HF cache.

## Provenance note (byte-identity check)

The original evidence bundle (dated 2026-07-16) claimed its `retriever.py` and
`eval_retriever.py` copies were byte-identical to committed `src/`. Re-verified this
session: **they are not**, quite — both were snapshotted from a repo tarball export that
predated three small same-day fixes (`fe3cfc6`, `2634bc8`, `2798ecd`, all 2026-07-15).
The diffs are confined to `OnnxEncoder`'s tokenizer loading (the shipping-only path; this
benchmark uses `SentenceTransformerEncoder`, which is untouched) and the multi-model
verdict-selection/gating logic in `eval_retriever.py`'s `main()` (irrelevant to this
single-locked-config re-run, which only reuses `load_chunks`). BM25, RRF fusion,
`HybridRetriever`, and `load_chunks` itself are unchanged between the two versions. The
numbers in this bundle reflect the same retrieval algorithm as what's committed today.

## Limitations

- **n = 35 is still thin.** One question ≈ 2.9pp.
- The 16 new (`claude_v3`) gold labels are single-annotator, unverified against the source
  PDFs (see `_meta.WARNING` in `questions_sme_v3.json`).
- Reranker latency (~1.3-2.7 s/query) was measured on the same i5-4300U dev floor as
  retrieval (~50-85 ms/query) — no measurements yet on the deployment reference machine.
- The reranker sweep tested one model at one N-range; it is not a search over reranker
  architectures or thresholds.
