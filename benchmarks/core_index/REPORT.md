# ADTC 2026 — `src/core/index.py` Performance Benchmark

**Date:** 2026-07-23
**Author:** Claude Code (automated run)
**Status:** complete — real-corpus baseline plus a synthetic scaling curve; one real bug
found and fixed in the module under test as a direct result of this benchmark.
**Machine:** i5-4300U @ 1.90GHz, 4 cores, Python 3.13.5, Linux x86_64 — the same
development machine referenced elsewhere in this repo (e.g. DECISION-002 §7). No
measurements yet on the 8 GB deployment reference machine (see risk R1, `DECISIONS.md`).

---

## 1. One-paragraph summary

Two things were measured: (a) the real 47-chunk Kibuga corpus as a sanity baseline, and
(b) a synthetic scaling curve at 50/500/2000/10,000 chunks, since the real corpus is too
small to show scaling behaviour. Headline: **BM25 dominates both append and search cost
and scales roughly linearly with corpus size** — exactly what the module's own docstring
predicts (IDF is a corpus-global statistic, so `bm25.json` is fully rebuilt on every
append, not patched incrementally). At 10,000 chunks, a single append costs **~5.4 s**
and a single search **~816 ms**, almost entirely BM25; dense scoring barely moves (0.8 ms
→ 6.5 ms) because it's a vectorised, mmapped dot product. **A real bug was found and
fixed as a direct result of running this benchmark**: `stats().bm25_load_rss_delta_bytes`
read exactly 0 at every corpus size tested, for two compounding reasons (§4) — fixed by
switching the measurement from process-level RSS tracking to `tracemalloc` (stdlib, no
new dependency).

---

## 2. What was tested (scope)

- **Module under test:** `src/core/index.py` (`Index.append_document`, `Index.search`,
  `Index.stats`) — committed 2026-07-23 in `7902ad8`/`1c73b33`/`b4d5d1b`.
- **Part A — real corpus:** the 5 real Kibuga PDFs (`data/raw/*.pdf`), extracted and
  chunked via the unmodified `ingest_sme.py` pipeline, appended one document at a time.
- **Part B — synthetic scaling curve:** since 47 chunks cannot show scaling behaviour,
  a synthetic corpus was grown incrementally through four target sizes — 50, 500, 2000,
  10,000 chunks — each step appending the batch needed to reach that size as a single
  document, then measuring `search()` (10 queries × 3 repeats = 30 calls per size, k=5)
  and `stats()`.
- **Encoder:** a deterministic, seeded stub (SHA-256-seeded `numpy` RNG, unit-normalised,
  384-dim) — **not** a real embedding model. No `.onnx` model file exists anywhere in this
  repo (DECISION-002 §9 lists the ONNX export as still-outstanding), so `dense_ms` here
  reflects the index's own dot-product/argsort overhead against a mmapped matrix, **not**
  real inference latency. Real per-batch encode cost is a separate, already-measured
  number (the `retriever.py` bake-off, ~36–70 ms/batch on this same machine) and is not
  part of any number in this report.
- **Not tested:** concurrent/multi-process access, disk-full or permission-error paths,
  behaviour under the 8 GB deployment reference machine's actual memory ceiling (R1 is
  still open), and anything beyond 10,000 chunks.

---

## 3. Results

### 3.1 Real corpus baseline (47 chunks, 5 PDFs)

| document | chunks | append time |
|---|---:|---:|
| General_Terms_for_Sellers_and_Buyers.pdf | 22 | 18.7 ms |
| Privacy_Policy.pdf | 14 | 16.5 ms |
| Return_Policy.pdf | 3 | 14.6 ms |
| Seek_Support.pdf | 1 | 11.3 ms |
| Sellers_Terms_and_Conditions.pdf | 7 | 14.9 ms |
| **total** | **47** | **76.0 ms** |

Disk footprint at 47 chunks: `manifest.json` 1.6 KB, `chunks.jsonl` 58.6 KB,
`embeddings.npy` 72.3 KB, `bm25.json` 94.6 KB.

Search (avg over 50 calls, k=5): **bm25 4.8 ms · dense 0.8 ms · fuse 0.05 ms · total 6.5 ms.**

### 3.2 Synthetic scaling curve

| n_chunks | append_ms | bm25_ms | dense_ms | fuse_ms | total_ms | chunks.jsonl | embeddings.npy | bm25.json | bm25-load (tracemalloc) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 50 | 19.5 | 2.2 | 0.8 | 0.06 | 3.8 | 103 KB | 77 KB | 24 KB | 84 KB |
| 500 | 176.7 | 32.2 | 1.5 | 0.11 | 40.6 | 1.0 MB | 768 KB | 245 KB | 784 KB |
| 2000 | 890.6 | 143.1 | 4.7 | 0.12 | 185.9 | 4.1 MB | 3.1 MB | 1.0 MB | 3.1 MB |
| 10000 | 5442.9 | 656.8 | 6.5 | 0.18 | 815.6 | 20.7 MB | 15.4 MB | 5.3 MB | 15.3 MB |

`search()` and `stats()` timings are averaged over 30 calls per row. `append_ms` is a
single measurement of the batch that reached that row's size (not averaged — each step
appends a different, larger batch to a growing corpus, so there is nothing to average
against).

---

## 4. Bug found and fixed: `stats().bm25_load_rss_delta_bytes` always read 0

This was not a pre-existing defect being hunted — it surfaced directly from running
this benchmark and seeing every single row report `0`.

**Root cause, in two layers:**

1. **`resource.getrusage(...).ru_maxrss` is a monotonic high-water mark** that never
   falls within a process. `Index.open()` itself already reads the *entire*
   `chunks.jsonl` during `_recover()`'s crash-consistency check — for a 10,000-chunk
   corpus that's a ~20 MB read — which peaks RSS far higher than loading a 5.3 MB
   `bm25.json` ever does. There is no way to obtain an `Index` instance without paying
   that cost first, so a monotonic watermark can structurally never isolate the
   bm25-load cost on its own.
2. **Switching to `/proc/self/status`'s `VmRSS`** (current usage, not a watermark) did
   not fix it either. Verified directly: Python/glibc's allocator can satisfy the
   `bm25.json` load entirely out of memory that `_recover()`'s own temporary chunk list
   *just freed*, so genuinely real allocation can still read as zero net RSS growth.
   Confirmed empirically — identical input reproduced 0 in some runs and a real,
   positive delta (270 KB–1 MB) in others, purely from allocator-reuse timing.

**Fix:** switched to `tracemalloc` (stdlib, no new dependency), which tracks Python-level
allocations directly rather than OS-level process memory, and is therefore immune to
both problems above. Verified deterministic across repeated runs on identical input
(within single-digit bytes, from incidental path-string allocation) — where the two RSS
approaches varied 0×–4× run to run. `src/core/index.py`'s `stats()` and
`tests/test_index.py` were updated; a new regression test
(`test_bm25_load_rss_delta_is_actually_measured`) pins this failure mode directly so it
cannot silently regress.

**Status of the fix:** written and verified locally (`60/60` tests passing with the real
dependency set); **not yet committed** — pending confirmation, since commits in this
session only happen when explicitly requested.

---

## 5. What this means for the module going forward

- **BM25 rebuild-per-append is the load-bearing cost, not mmap or dense scoring.** This
  is the documented, deliberate tradeoff in `src/core/index.py`'s own module docstring
  (IDF is corpus-global; there is no correct incremental update without reimplementing
  the formula). This benchmark is the first time that tradeoff has been quantified: at
  10,000 chunks it is a multi-second cost per append and a sub-second cost per search.
  If this index is ever pointed at a corpus in the thousands, this — not the storage
  layer's mmap/atomicity design — is what will need addressing first.
- **The Kibuga corpus (47 chunks) is nowhere near this regime.** Nothing here suggests
  changing anything for the current target corpus; this is forward-looking scaling
  information, requested explicitly for that purpose.
- **`bm25_load_rss_delta_bytes` is now a real number**, not a placebo — confirmed to
  scale sensibly with `bm25.json`'s on-disk size across all four corpus sizes tested
  (roughly a 3–3.5× expansion from JSON bytes to live Python `Counter`/`dict` objects,
  which is a normal ratio for that kind of structure, not a red flag).

---

## Artifacts

The benchmark script itself was a one-off run (per instruction, not committed) using a
deterministic stub encoder — see §2 for why a real encoder could not be used. This
report and the code fix in §4 are the persisted output of that run.
