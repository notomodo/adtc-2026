# RUN LOG — v3 locked-retriever eval (2026-07-16)

Chronological record of what was run this session, with the key outputs. Machine-level
console of the final canonical run is in `run_console.txt`. Reproduction recipe at the end.

All paths under `~/Desktop` unless absolute.

---

## Phase 1 — locate & verify the real pipeline (no code run yet)

1. Enumerated `~/Desktop`, `lastest_files/`, `newfiles/`, and the sibling dirs `all/`,
   `files/`, `others/` with full mtimes to pick the latest of each similarly-named file.
   - `questions_sme_v3.json` → only in `newfiles/` (edited 2026-07-16 14:32). Unique.
   - `chunks_sme.txt` → only in `newfiles/`. Byte-identical to the committed dump (below).
   - `retriever.py` → identical (md5 `a3b8c05`) in `lastest_files/`, `newfiles/`, and the
     repo tarball `src/`. This is the locked retriever.
   - `eval_retriever.py` → `lastest_files/` == tarball `src/` (md5 `ba1fc9a`); `newfiles/`
     copy differs but its `load_chunks` is byte-identical. Used the canonical one.
2. Extracted `lastest_files/adtc-retrieval.tar.gz` → the committed repo. Confirmed
   `benchmarks/chunks_sme.txt` is **byte-identical** to `newfiles/chunks_sme.txt`
   (`sha256 ed13ca69…09370`).
3. Read: `retriever.py`, `eval_retriever.py`, `ingest_sme.py` (fingerprint code),
   `scripts/verify_reproducibility.py`, `scripts/vendor_tokenizer.py`, `Makefile`,
   `eval_sme_output.log` (v2, for format), `questions_sme_v3.json`,
   `questions_sme_auto.json` `_meta`.

**Key discovery:** neither the dump nor any question set stores a `corpus_fingerprint`,
so the shipped gate is inert (`verify_reproducibility.py` would say `FAIL: missing
fingerprint`). See REPORT §7.

## Phase 2 — environment feasibility

4. Base `python3`: only `numpy`; `sentence_transformers` / `torch` / `tokenizers` /
   `onnxruntime` **absent**. bge weights present in `~/.cache/huggingface/hub/
   models--BAAI--bge-small-en-v1.5`.
5. Found venv `/home/omodo/ml/.venv` with the full stack (the env the v2 bench used).
   Verified it loads bge **offline** from cache and encodes 384-dim vectors.
   `torch.cuda.is_available() == False` → CPU, deterministic.

## Phase 3 — build & run (first pass, byte-identity gate)

6. Wrote `eval_sme_v3.py` (imports `retriever.HybridRetriever` +
   `SentenceTransformerEncoder` + `eval_retriever.load_chunks`; ranks full corpus).
7. Ran offline against the **original** `newfiles/chunks_sme.txt` +
   `questions_sme_v3.json`, `--reference-dump` = committed dump. Exit 0.
   **Result: R@1 60 · R@3 80 · R@5 83 · R@10 91 · MRR 0.704 · 48.7 ms/q.**
   k=3 loses 1 (Q17 r4); MISS@5 = {Q19,Q22,Q27,Q29,Q32,Q35}; LABEL_REVIEW = 0.
8. Cross-checks: overlapping-19 ranks reproduce the v2 log exactly (Q19 miss, Q22 r10,
   Q17 in top-5; R@5 over those 19 = 89% = v2). Hand-verified gold chunks 33/20/2/31 for
   the deepest misses — labels correct.

## Phase 4 — fingerprint + gate proof (this hand-off)

9. Upgraded `eval_sme_v3.py` gate: auto-select **fingerprint** mode when a fingerprint is
   stored (dump line and/or `_meta`), else **byte-identity** fallback. `--reference-dump`
   now optional.
10. Computed canonical fingerprint `592a602f845dce20` and wrote **copies** (originals
    untouched): `inputs/chunks_sme.fp.txt` (+ `# corpus_fingerprint:` line) and
    `inputs/questions_sme_v3.fp.json` (+ `_meta.corpus_fingerprint` + note). Asserted the
    fp-dump re-parses to identical chunk texts.
11. Re-ran against the `.fp` copies (console → `run_console.txt`). **Identical metrics.**
    Gate header now: `drift gate [fingerprint]: PASSED — labels == dump-embedded ==
    recomputed = 592a602f845dce20`.
12. Ran the **unmodified** shipped `scripts/verify_reproducibility.py` against the
    fingerprinted artifacts → `OK: corpus fingerprint 592a602f845dce20 matches the
    question set.`

---

## Canonical command (final, fingerprint-gated, offline, CPU)

```bash
cd <this bundle>            # eval_sme_v3.py here; retriever.py + eval_retriever.py importable
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 CUDA_VISIBLE_DEVICES="" \
/home/omodo/ml/.venv/bin/python eval_sme_v3.py \
  --dump inputs/chunks_sme.fp.txt \
  --questions inputs/questions_sme_v3.fp.json \
  --out eval_sme_v3_output.log
```

Environment used: python 3.13.5 · numpy 2.5.1 · sentence-transformers 5.6.0 ·
torch 2.13.0+cu130 (CPU) · tokenizers 0.22.2 · transformers 5.13.1. Model:
`BAAI/bge-small-en-v1.5` from local HF cache. No network.

> Note: `retriever.py` and `eval_retriever.py` in this bundle are the **byte-identical
> committed modules** (`retriever.py` md5 `a3b8c05`; `eval_retriever.py` md5 `ba1fc9a` ==
> tarball `src/`). The bundle is self-contained — the command above runs from here with
> no external PYTHONPATH. A self-test confirmed identical metrics.
