# ADTC 2026 — Locked-Retriever Evaluation on the v3 (35-question) SME Set

**Date:** 2026-07-16
**Author:** Claude Code (automated run)
**Status:** complete — results reproduced twice, identical; both reproducibility gates pass.

This is a hand-off reference. It states exactly what was run, every assumption made,
every package/version used, the findings, and open observations. It is safe to pass
to Claude chat as context.

---

## 1. One-paragraph summary

The **locked retrieval config** — *BM25 + bge-small-en-v1.5 fused by Reciprocal Rank
Fusion (RRF, k=60)* — was run, unmodified, against the expanded **35-question v3 set**
(`questions_sme_v3.json`, 19 original `auto_v2` + 16 new `claude_v3`) over the **47-chunk
Kibuga corpus** (`chunks_sme.txt`). Headline: **R@1 60% · R@3 80% · R@5 83% · R@10 91% ·
MRR 0.704 · ~50–85 ms/q (CPU)**. Choosing **k=3 over k=5 costs exactly one question (Q17,
prose, rank 4)** — and it is an *original* question, not one of the new ones. Six questions
miss even at k=5; they cost k=3 nothing extra. No gold label was found provably wrong.

---

## 2. What was tested (scope)

- **One config only:** the locked `HYBRID: BM25+bge-small-en-v1.5` (RRF k=60). This was
  **not** a re-run of the v2 bake-off — the other dense models (e5, gte, MiniLM) and
  BM25-only were deliberately **not** run. The architecture is LOCKED; this run measures
  it as-is on the bigger question set.
- **Corpus:** 47 chunks, 5 Kibuga PDFs, `chunks_sme.txt`. Chunk indices are the same
  0-based positional indices the v2 eval used; `gold_chunks` reference them directly.
- **Questions:** all 35 in `questions_sme_v3.json`.
- **Metric definition (matches v2 for comparability):**
  - *rank* = 1-based position of the **first** gold chunk in the retriever's **full**
    ranking (all 47 chunks ranked; never truncated at 5, so a rank-12 item is reported
    as 12, not MISS).
  - *Recall@k* = fraction of questions whose first gold rank ≤ k.
  - *MRR* = mean of 1/rank (0 if MISS).
  - For multi_chunk questions the primary rank is the first (best) gold; a secondary
    `g@5` column reports **how many** of the gold chunks landed in the top-5.
  - Percentages are integer-rounded with Python `:.0%` — the **same** formatting the v2
    harness used.

## 3. What was NOT done (guard-rails honored)

- Did **not** reimplement the retriever — imported the committed `retriever.py`
  (`HybridRetriever`, `SentenceTransformerEncoder`) and `eval_retriever.load_chunks`.
- Did **not** tune, add a reranker, or change chunking.
- Did **not** modify `questions_sme_v3.json` (the fingerprint was added to a **copy** —
  see §7).
- Did **not** commit anything.
- Did **not** reach the network for the model — bge loaded offline from the local HF
  cache (`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`).

---

## 4. Results

### 4.1 Recall curve (locked config, n=35)

| Config | R@1 | R@3 | R@5 | R@10 | MRR | ms/q |
|---|---|---|---|---|---|---|
| HYBRID: BM25+bge-small-en-v1.5 | 60% | 80% | 83% | 91% | 0.704 | ~50–85 (CPU) |

### 4.2 Per-stratum recall

| Stratum (n) | R@3 | R@5 |
|---|---|---|
| exact_fact (10) | 100% | 100% |
| near_miss (4)   | 100% | 100% |
| multi_chunk (5) | 80%  | 80%  |
| paraphrase (8)  | 75%  | 75%  |
| **prose (8)**   | **50%** | **62%** |

**prose is the weak stratum** — same story as v2. Legal/narrative phrasing (e.g. account
suspension, jurisdiction) is where the retriever loses gold below rank 5.

### 4.3 k=3 vs k=5 stress test (the k-decision cost)

- **Lost by choosing k=3 (gold at rank 4–5): 1 question**
  - `Q17` [prose] rank 4 — origin **auto_v2** (an *original* question, not new).
- **No `claude_v3` question is in the k=3 loss set.**
- **Already MISS at k=5 (k=3 costs nothing extra on these): 6**
  - `Q19` [prose] r12, `Q22` [multi_chunk] r10, `Q27` [paraphrase] r8,
    `Q29` [paraphrase] r20, `Q32` [prose] r8, `Q35` [prose] r13.

**Reading:** dropping from k=5 to k=3 is nearly free here — it forfeits exactly one
already-known original prose question (Q17). The real recall ceiling is set by the six
deep misses, which k has no effect on.

### 4.4 Full 35-question rank vector

See `eval_sme_v3_output.log` §"FULL RANK VECTOR" for the complete `id [stratum] rank
origin g@5 question` table. Notable rows: all 10 exact_fact = rank 1 (except none miss);
the three new multi_chunk questions Q36/Q37/Q38 landed at rank 2/1/1 with good gold
coverage (2/2, 1/2, 3/3 in top-5).

---

## 5. Consistency check against the v2 run (why you can trust these numbers)

The 19 questions shared with the v2 eval reproduce the v2 log **exactly** for this same
config, which confirms this is the identical, deterministic pipeline:

| Question | v2 log (BM25+bge) | v3 run | Match |
|---|---|---|---|
| Q19 | rank miss (not in top-10) | rank 12 | ✓ (>10 = "miss" at v2's top-10 view) |
| Q22 | rank 10 | rank 10 | ✓ exact |
| Q17 | not a failure (≤5) | rank 4 | ✓ (in top-5) |
| Recall@5 over those 19 | 89% (17/19) | 89% (17/19) | ✓ |

The drop from v2's 89% to v3's 83% R@5 comes **entirely** from the 16 new `claude_v3`
questions (which add four deep misses: Q27, Q29, Q32, Q35). The original 19 are unchanged.

---

## 6. Environment, packages, and the model

### 6.1 Interpreter / packages actually used

Run with the virtualenv **`/home/omodo/ml/.venv`** (the same environment the v2 benchmark
used — confirmed by the identical "Loading weights: 199" trace and identical overlapping
ranks):

| Package | Version used | Repo pin (`requirements*.txt`) | Note |
|---|---|---|---|
| python | 3.13.5 | 3.13.5 (v2 log) | match |
| numpy | 2.5.1 | 2.2.1 | newer; BM25/RRF are exact integer/float ops, unaffected |
| sentence-transformers | 5.6.0 | 3.3.1 (bench-only pin) | newer; loads same weights, same mean-pool+L2 math |
| torch | 2.13.0+cu130 | (transitive) | CPU used (`CUDA_VISIBLE_DEVICES=""`); CUDA not available anyway |
| tokenizers | 0.22.2 | 0.21.0 | not on the ranking path for this run (ST tokenizes internally) |
| transformers | 5.13.1 | — | ST dependency |

**Assumption / caveat:** the pinned benchmark stack (`sentence-transformers==3.3.1`) is
**not installed anywhere on this machine**, so the newer 5.6.0 in `ml/.venv` was used. The
**bge model weights and the embedding math (mean-pool over attention mask → L2 normalize)
are identical across these versions**, so the ranking is unaffected. This is the only
environmental deviation from the repo pins and is stamped in the log header
(`config stamp:` line). If byte-identical reproduction of the pinned stack is required,
create a venv from `requirements-bench.txt` and re-run — the ranks will be identical.

### 6.2 Model (offline)

- **Model:** `BAAI/bge-small-en-v1.5` (384-dim), query prefix
  `"Represent this sentence for searching relevant passages: "`, passage prefix `""`
  (as encoded in `retriever._PREFIXES`).
- **Source:** local HF cache `~/.cache/huggingface/hub/models--BAAI--bge-small-en-v1.5`
  (present since 2026-07-13). Loaded with `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1` — **no
  network access**; the run console shows no Hub warning (unlike the v2 log, which ran
  online and emitted the "unauthenticated requests to the HF Hub" warning).
- **Device:** CPU. Determinism: BM25 + RRF are exact; bge on CPU is deterministic for a
  fixed input. No nondeterminism observed (two runs → identical ranks).

---

## 7. Corpus fingerprint / reproducibility gate

### 7.1 The finding

The repo *designs* a SHA-256 corpus fingerprint gate (`ingest_sme.py` computes it;
`eval_retriever.py` and `scripts/verify_reproducibility.py` check it), **but the shipped
artifacts never carried the value**:

- `chunks_sme.txt` has **no** `# corpus_fingerprint:` line (the committed dump predates
  the ingest feature — the fingerprint-writing `ingest_sme.py` is a later version than the
  one that produced the dump).
- Neither `questions_sme_auto.json` (v2) nor `questions_sme_v3.json` stores
  `_meta.corpus_fingerprint`.
- Consequently `verify_reproducibility.py` on the as-shipped artifacts prints
  **`FAIL: missing fingerprint`**, and `eval_retriever.py`'s inline gate only warns.

**So the gate existed but was inert.** The invariant it protects (the corpus the labels
index into == the corpus being ranked) was verified for this run by a strictly stronger
check: **byte-identity** of the working `chunks_sme.txt` to the committed source-of-truth
dump in `adtc-retrieval.tar.gz` (`benchmarks/chunks_sme.txt`) — SHA-256
`ed13ca69…09370`, identical.

### 7.2 The fix delivered (as requested)

Fingerprint added to **copies** (originals untouched), in `inputs/`:

- `inputs/chunks_sme.fp.txt` — the dump + one inserted header line
  `# corpus_fingerprint: 592a602f845dce20`. Chunk bodies byte-identical to the original
  (`load_chunks` ignores `#` lines; re-parse yields identical texts — asserted).
- `inputs/questions_sme_v3.fp.json` — `questions_sme_v3.json` + `_meta.corpus_fingerprint
  = "592a602f845dce20"` and a `_meta.fingerprint_note`. All questions/labels unchanged.

**The fingerprint value `592a602f845dce20`** is the canonical definition from
`ingest_sme.py`: `sha256("\n".join(f"{i}\x00{text}"))[:16]` over the parsed `(position,
chunk-text)` pairs of all 47 chunks.

> **Caveat on the value:** it is computed over the *parsed* chunk texts (what the retriever
> actually consumes), which is the operationally meaningful corpus. Because the original
> dump lacks the ingest-time line, this is **not** guaranteed byte-identical to what a fresh
> `make ingest` would emit (raw vs parsed whitespace could differ). If the corpus is ever
> re-ingested, **regenerate the fingerprint from `ingest_sme.py`'s own output** and
> propagate it to both the dump and the question set. This caveat is recorded in the copy's
> `_meta.fingerprint_note`.

### 7.3 Proof both gates now pass

- The harness (`eval_sme_v3.py`) ran against the `.fp` copies and its gate reported:
  `drift gate [fingerprint]: PASSED — labels 592a602f845dce20 == dump-embedded
  592a602f845dce20 == recomputed 592a602f845dce20`.
- The **unmodified** shipped `scripts/verify_reproducibility.py`, pointed at the
  fingerprinted artifacts, prints:
  `OK: corpus fingerprint 592a602f845dce20 matches the question set.`

---

## 8. Label review (auto-adjudication)

`LABEL_REVIEW` in the log is **empty** — no gold label is provably wrong by the two
conservative checks run:
1. **auto_v2:** each question's claimed VERBATIM/ANCHOR `_evidence.matched` span must
   appear (normalized) in its gold chunk. All passed.
2. **claude_v3:** the gold chunk must carry at least one *distinctive* term from the answer
   (length ≥4, present in ≤30% of chunks). Flag only if gold carries **zero** while some
   other chunk carries ≥2. None flagged.

Additionally, the four **deepest misses** were hand-checked against the chunk text and the
labels are **correct** (genuine retrieval misses, not mislabels):

- `Q29`→chunk 33 = "…accessing, correcting, or **erasing** your personal data…" ✓
- `Q35`→chunk 20 = "Law and jurisdiction … **exclusive jurisdiction of the courts**…" ✓
- `Q27`→chunk 31 = "Data Retention … as long as necessary … **delete or anonymize**…" ✓
- `Q19`→chunk 2 = registration/account clause containing the suspension wording ✓

**Note for the human annotator:** the `claude_v3` labels remain
`single_annotator_unverified` by design. The checks above are lexical, not semantic — they
catch "points at the wrong chunk," not "is this the *best* chunk." Spot-check the
multi_chunk labels (Q36/Q37/Q38) in particular before treating them as gold.

---

## 9. Observations / recommendations

1. **prose recall (50% @3, 62% @5) is the ceiling.** If the eval budget allows one lever,
   it is the prose stratum, not k. But the architecture is LOCKED, so this is a note for a
   future DECISION, not this run. (`DECISION-003-reranker.md` exists in `newfiles/` and may
   be the intended venue.)
2. **k=3 is defensible.** It forfeits exactly one original prose question (Q17) that k=5
   would catch. If answer completeness on multi_chunk matters, note Q37 only gets 1/2 gold
   chunks in the top-5 regardless of k.
3. **Re-embed the fingerprint at ingest time.** The gate is only as good as the stored
   value. Regenerate `chunks_sme.txt` via `make ingest` (which now writes the line) and
   back-fill `_meta.corpus_fingerprint` into the committed question sets, so
   `verify_reproducibility.py` passes out of the box instead of `FAIL: missing fingerprint`.
4. **Pin the benchmark venv.** The v2 numbers and these were produced on
   `sentence-transformers 5.6.0`, not the repo-pinned 3.3.1. Ranks are unaffected, but for
   an auditable "the pinned stack produces X" claim, build the venv from
   `requirements-bench.txt`.

---

## 10. Exact reproduction

```bash
# from the v3_eval/ bundle directory, with retriever.py + eval_retriever.py importable
# (copies of the committed, byte-identical modules are expected on PYTHONPATH)
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 CUDA_VISIBLE_DEVICES="" \
/home/omodo/ml/.venv/bin/python eval_sme_v3.py \
  --dump inputs/chunks_sme.fp.txt \
  --questions inputs/questions_sme_v3.fp.json \
  --out eval_sme_v3_output.log
```

Legacy (no-fingerprint) inputs still work via the byte-identity fallback:

```bash
... eval_sme_v3.py --dump /home/omodo/Desktop/newfiles/chunks_sme.txt \
  --questions /home/omodo/Desktop/newfiles/questions_sme_v3.json \
  --reference-dump <committed benchmarks/chunks_sme.txt> --out out.log
```

See `RUN_LOG.md` for the full command history of this session and `README.md` for the
bundle layout and checksums.
