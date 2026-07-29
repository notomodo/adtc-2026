# Session Report — 2026-07-23

**Repo:** `adtc-2026` (github.com/notomodo/adtc-2026)
**Author:** Claude Code (automated), on the `main` branch
**Purpose:** hand-off reference for Claude chat. Every commit made today is listed with
what it changed and *why*. Self-contained — no repo access needed to follow it.

---

## 0. TL;DR

Today's work fell into three tasks, in order:

1. **R5 hand-validation closed out** (3 commits). The human filled in the Layer A
   validation packet; the result was tabulated (9/10 sampled PASSes genuinely correct,
   1 confirmed ungrounded), risk R5 was recorded as *hand-validated but kept Open*, and
   the "71.4%" figure was disambiguated everywhere it appears in the repo.
2. **New persistent index layer built** (3 commits). `src/core/index.py` — an
   append-only chunk index with stable string IDs, atomic writes, crash recovery, and a
   positional→stable ID migration tool. First real storage contract for the CLI app.
3. **Performance benchmark + a bug it surfaced** (3 commits). Benchmarked the new index;
   found and fixed a broken memory metric; added a report and a missing recovery test.

**Net:** 9 commits, all pushed to `origin/main`. Test suite **61 passing** with the full
dependency set. No existing code was modified in the index work — everything is additive
except the R5 doc edits and the index's own follow-up fix.

**Two uncommitted files remain** (deliberately): the migration mapping outputs — see §5.

---

## 1. Commit-by-commit (chronological)

| # | Hash | Type | Summary |
|---|------|------|---------|
| — | `1bd48e2` | (human) | Update human verdicts in R5 review packet *(the user's own commit — filling the packet)* |
| 1 | `33416f3` | test(eval) | R5 packet integrity tests + CI wiring |
| 2 | `1591c04` | docs(eval) | R5 hand-validation result and risk closure |
| 3 | `fac4ccc` | docs | propagate hand-validated accuracy figure |
| 4 | `7902ad8` | feat(core) | persistent append-only chunk index with stable IDs |
| 5 | `1c73b33` | test(core) | index invariants, crash recovery, mismatch detection |
| 6 | `b4d5d1b` | tools | positional-to-stable chunk ID migration mapping |
| 7 | `bcaa2ff` | fix(core) | measure bm25 load memory with tracemalloc, not process RSS |
| 8 | `88d3438` | docs(bench) | core_index performance benchmark report |
| 9 | `8f5b2da` | test(core) | cover crash recovery on the first-ever append |

*(Predecessor context, committed 2026-07-22, not today: `c9d86ca` recorded DECISION-005
"reranker not shipped in v1", and `992f5c1` added the R5 review packet + `r5_tabulate.py`.
Today's R5 work builds directly on those.)*

---

## 2. Task A — R5 hand-validation (commits 1–3)

**Background.** Risk **R5** in `DECISIONS.md` says: *Layer A (the deterministic
token-overlap grader that produces the v3 generation pass rate) is a heuristic, not a
truth oracle; the 71.4% v3 pass rate has not been hand-validated against the actual
answer text.* It was **Blocking** before 71.4% could be quoted as "accuracy" anywhere. A
13-item adversarial review packet (`benchmarks/generation/R5_review_packet.md`) had been
prepared and a tabulator (`src/r5_tabulate.py`) written, but no human verdicts existed
yet. Today the human filled the packet in (`1bd48e2`) and this task adjudicated the
result. **An LLM was explicitly not allowed to judge correctness** — an earlier LLM judge
(Qwen grading Qwen) agreed with Layer A only 46% of the time, so only a human reading the
text can adjudicate.

### Commit 1 — `33416f3` test(eval): R5 packet integrity tests + CI wiring

**What:** new `tests/test_r5_packet.py`. Asserts the packet's structural integrity:
code-fences balanced, every `### Qnn — stratum` header sits *outside* any fenced block,
every block has exactly 4 verdict checkboxes with exactly one checked, the question-ID
set matches the documented 13-item sample, and the checkbox mark style is one the
tabulator's regex actually recognises.

**Why:** the packet is human-edited Markdown parsed by regex, and it had **already
failed once** — a previous edit dropped two closing ```` ``` ```` fences, and because
Markdown fences toggle open/closed in raw sequence, that silently shifted every block
from Q36 through Q07 into the wrong render state. `r5_tabulate.py`'s own parser could not
catch that class of corruption (it only counts boxes *between* headers; it never checks
that the headers themselves survived). These tests pin exactly that failure mode so it
cannot silently recur. No CI file change was needed — the existing `pytest -v` step
already discovers `tests/`.

### Commit 2 — `1591c04` docs(eval): R5 hand-validation result and risk closure

**What:** ran `src/r5_tabulate.py` over the human-completed packet; wrote
`benchmarks/generation/R5_validation_result.md`; updated risk R5 in `DECISIONS.md`.

**Result:** of the **10 sampled Layer A PASSes**, the human confirmed **9 CORRECT and 1
UNGROUNDED** — that one being **Q19**, where the model answered from a non-gold chunk and
Layer A scored it PASS purely on vocabulary overlap. All 3 sampled WEAK items were also
confirmed CORRECT. **Implied precision 9/10 (90%)**, explicitly a *lower bound* because
the sample was deliberately adversarial (weighted toward `prose`/`multi_chunk`, the
strata where token overlap is least reliable).

**Why R5 stays Open, not Closed:** the governing rule was that *any* confirmed
UNGROUNDED/WRONG verdict keeps the risk open regardless of the aggregate number — because
Q19 is exactly the failure mode R5 exists to warn about, now confirmed **real rather than
hypothetical**. A strong 90% does not erase a confirmed instance of the thing being
guarded against. R5's status is now *"Open — hand-validated, not closed."*

### Commit 3 — `fac4ccc` docs: propagate hand-validated accuracy figure

**What:** updated every location that quotes 71.4% to distinguish two now-separate
quantities, and to stop calling the validation "outstanding":
- **71.4% (25/35)** = Layer A's *automated pass rate* (unchanged).
- **90% (9/10)** = *hand-validated precision* of that pass rate on an adversarial sample (new).

Files touched: `README.md`, `docs/DECISION-004-grounding-prompt.md` (limitations bullet +
follow-up item), `benchmarks/generation/README.md`, `docs/SESSION_REPORT_generation.html`
(a *dated* report — the update was date-stamped rather than rewritten silently), and
`DECISIONS.md` D13's "would reverse this" line (which no longer points at an open question).

**Why:** these were being conflated by omission — every place that quoted 71.4% also said
the hand-read validation was still pending. They are different numbers and must not
overwrite one another. 71.4% must never be quoted as "accuracy" without the caveat.

---

## 3. Task B — persistent chunk index (commits 4–6)

**Background & the core problem.** `ingest_sme.py` assigns chunk IDs by `enumerate()`
over the whole corpus, and the corpus fingerprint hashes `(position, text)` pairs — the
ID scheme and the reproducibility gate are the *same mechanism*. That is fine for a
one-shot batch dump, but it means **appending a document renumbers every chunk after it**,
which would silently invalidate every existing gold label and every citation ever shown
to a user. The CLI app needs a real storage layer that can grow without that hazard.

### Commit 4 — `7902ad8` feat(core): persistent append-only chunk index with stable IDs

**What:** new module `src/core/index.py` (+ empty `src/core/__init__.py`). Public API:
`Index.open()`, `.append_document()`, `.search()`, `.stats()`, `.has_document()`. Storage
layout under an index dir (default `~/.adtc/index`):

- `manifest.json` — schema version, embedder identity, and a `documents` map keyed by
  `doc_sha256` (filename, pages, n_chunks, chunk_id_range, ingested_at).
- `chunks.jsonl` — one JSON record per chunk (id, doc_sha256, filename, page,
  char_start, char_end, text, n_tokens).
- `embeddings.npy` — `(N, 384)` float32, **L2-normalised at write time**, row *i* ⇔ line
  *i* of chunks.jsonl.
- `bm25.json` — the inverted index + doc lengths + avgdl + IDF.

**Key design decisions and their reasons:**

- **Stable string IDs `f"{doc_sha256[:8]}:{ordinal}"`** (per-document, zero-based), not
  positional integers. Appending a document can only ever *add* new IDs, never touch an
  existing one. A `sha256[:8]` prefix collision between two different documents is
  detected and refused (it would make two documents' IDs collide).
- **Reuses `retriever.BM25` and `retriever.rrf_fuse` directly**, *not* `HybridRetriever`.
  `HybridRetriever`'s constructor unconditionally re-embeds the entire corpus and holds
  the matrix resident — incompatible with incremental append and mmapped search. At
  search time a `BM25` instance is **reconstructed by bypassing `__init__`** (`BM25.__new__`,
  attributes populated from `bm25.json`) and its real, unmodified `.scores()` method is
  called. This is *exact reuse, not reimplementation* — DECISION-002 locked that scoring on
  measured evidence, so it must not be re-derived. *(Verified empirically this session: the
  reconstructed BM25 reproduces a from-scratch `BM25`'s scores to `atol 1e-6`.)*
- **`bm25.json` is fully rebuilt on every append**, not patched. IDF is a corpus-global
  statistic — adding one document changes the document frequency, and therefore the IDF,
  of every term. There is no correct incremental IDF update that isn't a hand-rederivation
  of the formula, which is exactly the reimplementation being avoided. (This is the source
  of the append/search cost curve in Task C — a deliberate, documented tradeoff.)
- **Atomic writes, manifest last.** Each of the four files is written to a temp file,
  `fsync`'d, then `os.replace`'d (atomic on POSIX), so no single file is ever seen
  half-written. `manifest.json` is written **last** — it is the commit point and the
  source of truth for "what is indexed." A crash before it leaves the other three files
  one document ahead of the manifest; `Index.open()` reconciles this on every open
  (truncate chunks/embeddings back to the manifest's declared count; rebuild bm25.json if
  its count no longer matches). This makes the crash window self-healing with no separate
  repair tool.
- **Fatal encoder-identity check.** The manifest records `embedder_id` and
  `tokenizer_sha256`; appending or searching with a mismatched encoder **raises** rather
  than silently re-embedding into a mixed vector space (which would make every dense score
  meaningless). Since `retriever.Encoder` doesn't track identity, a small
  `IdentifiedEncoder` protocol + `EncoderHandle` adapter were added *here* rather than
  modifying `retriever.py`.
- **Search uses mmap** (`np.load(..., mmap_mode="r")`) so it never holds the full
  embeddings matrix resident; dense scoring is a plain dot product (both sides
  normalised, so the dot product *is* cosine — no per-query normalisation pass).
  `SearchResult` carries `hits`, `considered` (the next 5 below the cut, for abstention
  to show near-misses), and per-stage `timings`.

### Commit 5 — `1c73b33` test(core): index invariants, crash recovery, mismatch detection

**What:** new `tests/test_index.py`, using a deterministic seeded `FakeEncoder` (no model,
no network — mirrors `test_retriever.py`'s `StubEncoder`). Covers: stable IDs across two
appends; re-append is a no-op with no duplicates; **crash simulated between the embeddings
write and the manifest write** (a monkeypatched writer raises only on `manifest.json`) with
both the crashed instance and a fresh `Index.open()` seeing only pre-crash state;
**embedder mismatch RAISES** (known-bad control, on both append and search); search shape;
unit-norm invariant on the persisted matrix; and a known-good control.

**Why (and a real bug it caught):** writing the crash test surfaced a genuine defect —
`append_document` was mutating `self.manifest` in memory *before* the durable write, so a
caught exception left the in-memory object claiming the new document was indexed even
though the write never landed. Fixed by building a *new* manifest dict and only swapping
it into `self.manifest` after the write succeeds. `has_document()` must never lie.

### Commit 6 — `b4d5d1b` tools: positional-to-stable chunk ID migration mapping

**What:** new `scripts/migrate_chunk_ids.py`. Builds a fresh index from `data/raw/*.pdf`
(reusing `ingest_sme.py`'s extraction/chunking unmodified) and emits
`{old_positional_id: new_stable_id}` against the current `benchmarks/chunks_sme.txt`. It
**verifies chunk text is byte-identical** between the old dump and the new `chunks.jsonl`
before writing anything, and **refuses** (writes only a failure report, non-zero exit) if
any chunk differs. **Question sets are not rewritten** — this only reports what *would*
change, for human review first.

**Notable findings/decisions:**
- `char_start`/`char_end` are derived by locating each chunk's body text in a per-document
  reconstruction of `ingest_sme.py`'s internal stream (that chunker tracks only a page
  number, not offsets, and this task did not modify it). Verified: every chunk locates
  cleanly.
- **A pre-existing wart was found and reported, not silently fixed:**
  `eval_retriever.load_chunks` `.strip()`s every chunk it parses, which drops a *real*
  trailing space present in the on-disk dump for 2 of 47 chunks. That is a latent
  discrepancy between the dump file (what every gold label and the fingerprint are computed
  against) and what the benchmark harness actually feeds to the retriever. The migration
  script reads the dump directly to avoid inheriting it.
- **No `.onnx` model file exists anywhere in this repo** (DECISION-002 §9 lists the ONNX
  export as still-outstanding). `--onnx-path` is required by default; `--stub-embedder` is
  an explicit, loudly-labelled dry-run escape hatch for verifying the ID mapping and
  text-identity check without a real encoder — mirroring `ingest_sme.py`'s own
  `--allow-estimate` precedent.

---

## 4. Task C — performance benchmark and the bug it found (commits 7–9)

### Commit 7 — `bcaa2ff` fix(core): measure bm25 load memory with tracemalloc, not process RSS

**What:** rewrote how `Index.stats()` measures `bm25_load_rss_delta_bytes`.

**Why (the bug):** benchmarking showed the metric read **exactly 0 at every corpus size**,
for two compounding reasons:
1. `resource.getrusage().ru_maxrss` is a monotonic high-water mark that never falls within
   a process. `Index.open()` itself already reads the *entire* `chunks.jsonl` during
   `_recover()`'s consistency check, which peaks RSS higher than loading `bm25.json` ever
   does — and there is no way to obtain an `Index` without paying that cost first, so the
   watermark can structurally never isolate the bm25 load.
2. Switching to `/proc/self/status`'s current-usage `VmRSS` didn't help either:
   Python/glibc's allocator can satisfy the bm25.json load entirely out of memory that
   `_recover()` *just freed*, so genuinely real allocation still reads as ~0 net RSS
   growth. Confirmed empirically — identical input varied 0×–4× run to run.

**Fix:** switched to `tracemalloc` (stdlib, **no new dependency**), which tracks
Python-level allocations directly and is immune to both problems. Verified deterministic
across repeated runs. A regression test pins the failure mode.

### Commit 8 — `88d3438` docs(bench): core_index performance benchmark report

**What:** new `benchmarks/core_index/REPORT.md` — real 47-chunk baseline plus a synthetic
scaling curve at 50/500/2000/10000 chunks (the real corpus is too small to show scaling).

**Headline result:** BM25 dominates both append and search cost and scales roughly
linearly with corpus size — exactly as the module's docstring predicts (IDF is
corpus-global, so `bm25.json` is fully rebuilt on every append). At 10,000 chunks a single
append is **~5.4 s** and a single search **~816 ms**, almost entirely BM25; dense scoring
barely moves (0.8 ms → 6.5 ms) because it's a vectorised mmapped dot product.

| n_chunks | append_ms | bm25_ms | dense_ms | total_ms | bm25.json |
|---:|---:|---:|---:|---:|---:|
| 50 | 19 | 2.2 | 0.8 | 3.8 | 24 KB |
| 500 | 177 | 32.2 | 1.5 | 40.6 | 245 KB |
| 2000 | 891 | 143.1 | 4.7 | 185.9 | 1.0 MB |
| 10000 | 5443 | 656.8 | 6.5 | 815.6 | 5.3 MB |

**Caveat baked into the report:** a deterministic stub encoder was used (no `.onnx` model
exists), so `dense_ms` reflects the index's own dot-product/argsort overhead, **not** real
inference latency. Real encode cost is a separate, already-measured number (the
`retriever.py` bake-off, ~36–70 ms/batch).

**Interpretation for whoever picks this up:** if this index is ever pointed at a corpus in
the thousands, **BM25 rebuild-per-append is what to address first** — not the storage
layer's mmap/atomicity design. The current 47-chunk Kibuga corpus is nowhere near that
regime; this is forward-looking information.

### Commit 9 — `8f5b2da` test(core): cover crash recovery on the first-ever append

**What:** added a test for the recovery branch the existing crash test didn't cover — a
crash during the **first-ever** append (empty→partial), which must reconcile
chunks/embeddings/bm25 back to a *pristine, zero-document* index (embedder_id still None),
distinct from the populated→partial case (heal back to the previous document).

**Why:** the two branches take different code paths (truncation target is 0 rows vs N; the
manifest's embedder identity is still unset). Verified it **fails if `_recover()`'s
truncation is disabled**, so it's a real control, not a happy-path rubber stamp.

---

## 5. Migration mapping — review verdict (the two uncommitted files)

`benchmarks/chunk_id_migration_map.json` and `benchmarks/CHUNK_ID_MIGRATION_REPORT.md` are
the output of `scripts/migrate_chunk_ids.py`. They are **reproducible run artifacts, left
uncommitted on purpose** pending human sign-off before anything downstream adopts the new
IDs. Reviewed this session and found **trustworthy**:

- 47 entries, keys `0..46` contiguous; all values unique and well-formed `sha8:ordinal`.
- Per-document ordinals contiguous and in old-ID order.
- **Every `sha8` prefix matches the real SHA-256 of its source PDF** and covers exactly
  the old-ID range the report claims (e.g. General_Terms `1df1cd8d` = ids 0–21).
- **Independent byte-identity check (my own parser, not the script's self-report):
  47/47 chunks identical**, including the trailing-space subtlety noted in §3.

Document→ID ranges:

| document | old ids | new ids |
|---|---|---|
| General_Terms_for_Sellers_and_Buyers.pdf | 0–21 | `1df1cd8d:0`..`:21` |
| Privacy_Policy.pdf | 22–35 | `21d0ee2c:0`..`:13` |
| Return_Policy.pdf | 36–38 | `f232e5d3:0`..`:2` |
| Seek_Support.pdf | 39 | `a72cadc9:0` |
| Sellers_Terms_and_Conditions.pdf | 40–46 | `9a6d80d1:0`..`:6` |

**What adopting it would entail (NOT done):** remapping every `gold_chunks`/`retrieved`
reference in `data/questions/*.json` and every positional-ID-keyed benchmark result
through the map; and superseding `chunks_sme.txt`'s whole-corpus fingerprint gate with the
index's per-document `doc_sha256` identity. **This is a deliberate decision point left to
the human — the question sets are the source of truth for grading and must not be
rewritten without explicit sign-off.**

---

## 6. Current repository state

- **Branch:** `main`, in sync with `origin/main` (all 9 commits pushed).
- **Tests:** **61 passing** with the full dependency set
  (`numpy`, `tokenizers`, `pdfplumber`, `onnxruntime`). On a bare interpreter missing
  `tokenizers`/`onnxruntime`, the 4 `test_onnx_offline.py` tests error on import (unchanged,
  pre-existing environment gap) and everything else passes.
- **New files:** `src/core/__init__.py`, `src/core/index.py`, `tests/test_index.py`,
  `tests/test_r5_packet.py`, `scripts/migrate_chunk_ids.py`,
  `benchmarks/generation/R5_validation_result.md`, `benchmarks/core_index/REPORT.md`,
  and this report.
- **Uncommitted (intentional):** the two migration output files in §5.
- **No existing runtime code was modified by the index work** — it is entirely additive.
  The only edits to existing files were the R5 doc updates (Task A) and the index's own
  `stats()`/tests follow-up (Task C).

---

## 7. Open items & follow-ups (for whoever continues)

1. **Migration adoption is a pending human decision** (§5). The mapping is verified and
   safe to hand off; nothing downstream has been rewritten.
2. **Risk R5 remains Open** by design — 71.4% is Layer A's automated pass rate, and the
   defensible claim now includes the 90% hand-validated precision plus the confirmed Q19
   ungrounded case. Do not quote 71.4% as "accuracy" bare.
3. **No `.onnx` model exists** (DECISION-002 §9). The index and migration tool both run
   today only via a stub encoder for text/ID verification. Real dense-quality numbers and a
   real production index need that export first.
4. **BM25 rebuild-per-append cost** is the first thing to revisit if the corpus ever
   reaches the thousands (§4). Not a concern at 47 chunks.
5. **Risk R1 (co-resident 8 GB memory fit) is still unmeasured** — all timings today are
   from the i5-4300U dev machine, not the deployment reference.
6. **`search()` reloads `bm25.json` and re-reads `chunks.jsonl` on every query** (no warm
   cache). Fine for a CLI invocation; would matter for a long-lived query server.

---

## 8. Standing lessons reinforced today

- **Fail loud, never degrade silently** — the encoder-identity check, the migration
  byte-identity refusal, and keeping R5 Open on a single confirmed failure all follow the
  project's defining rule (born from the v1 extraction defect and the silent-tokenizer-
  fallback defect).
- **Reuse locked components exactly, don't re-derive them** — BM25/RRF are called
  unmodified; where reuse wasn't possible (`HybridRetriever`'s eager full-corpus embed),
  the reason is documented rather than worked around quietly.
- **A metric you haven't watched fail is untested** — both the `stats()` memory metric and
  the first-append recovery path were only trustworthy once shown to fail when broken.
