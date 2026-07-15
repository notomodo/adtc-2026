# DECISION-003 — No Cross-Encoder Reranker (v1)

**Status:** Accepted
**Date:** 2026-07-15
**Depends on:** DECISION-002 (retrieval architecture; supplies the eval this rests on)
**Decision:** **Do not add a cross-encoder reranker.** Ship the locked
BM25 + `bge-small-en-v1.5` / RRF stack (DECISION-002) as-is.

This decision was previously *deferred pending embedder Recall@5 results*. Those
results are now in (DECISION-002 §1). This record closes the deferral: the reranker
is **rejected for v1**, not merely postponed. The data resolves it against a reranker.

---

## 1. Summary

A reranker was held open as a possible accuracy lever. With the eval now complete,
it is rejected because **it cannot address either of the two failures that survive the
locked retriever.** A reranker reorders candidates that retrieval already surfaced; it
cannot recover a chunk that retrieval never surfaced, and it does not solve multi-chunk
aggregation. Our surviving failures are exactly those two cases. So the mechanism is
structurally incapable of helping here — the decision does not depend on the small
sample size.

Locked config (from DECISION-002, n=19, 47 chunks, RRF k=60):

| Metric | BM25 + bge-small-en-v1.5 |
|---|---|
| R@1 | 58% |
| R@3 | 84% |
| R@5 | 89% |
| R@10 | 95% |
| MRR | 0.703 |
| Latency | ~40 ms/query |

---

## 2. What a reranker does — and what it therefore cannot do

A cross-encoder reranker takes the top-K chunks a first-stage retriever returned,
scores each `(query, chunk)` pair jointly, and **reorders** them. Its power and its
limit are the same fact: **it only ever sees the candidate set retrieval handed it.**

Two consequences fix the decision:

- **It cannot recover a chunk absent from the candidate set.** If the gold chunk is
  not in the top-K, no amount of re-scoring surfaces it. Reranking raises precision
  within a recalled set; it cannot raise recall.
- **It optimises for the single best chunk.** It ranks candidates against each other.
  It does not *aggregate* information split across several chunks. A question whose
  answer is spread over multiple chunks is not a ranking problem, and reranking does
  not address it.

A reranker is the right tool for exactly one failure shape: **the gold chunk is
present in the candidate set but ranked below the cutoff the LLM consumes** (e.g.
gold at rank 6–10 when we pass top-3). We have essentially none of those.

---

## 3. The surviving failures are the two shapes a reranker can't fix

Under the locked config, two questions fail Recall@5 (DECISION-002 §1, §3):

| Question | Failure | Shape | Reranker verdict |
|---|---|---|---|
| **Q19** — *"Can Kibuga suspend my account without telling me?"* | rank **miss** (not in top-10) | Gold chunk **absent** from the candidate set — dense misses it on all four models; only BM25's exact `suspend`+`account` match finds it at all. | **Cannot help.** A reranker never sees a chunk that isn't retrieved. |
| **Q22** — *"What are all the ways Kibuga can refund me?"* | rank **10** | **Multi-chunk** paraphrase — the answer (store credits, wallet refunds, vouchers, mobile money) is scattered across chunks, and the boundary-rank chunk is only one piece. | **Cannot help.** Reranking optimises for one best chunk; it does not aggregate across several, and lifting this one chunk would not complete the answer. |

This is the whole argument. Both surviving failures are precisely the shapes §2
identifies as outside a reranker's reach. **Zero of our failures are the
present-but-mis-ranked shape a reranker exists to fix.** Adding one would spend RAM,
latency, and a dependency to reorder chunks that are already correctly ranked (R@1 is
already 58%; R@5 already 89%; the top-5 the LLM consumes is already good).

---

## 4. Cost avoided

For an 8 GB CPU-only offline target, a reranker is not free:

| | Impact |
|---|---|
| RAM | +80–120 MB (MiniLM-class cross-encoder, int8) to +300 MB+ (bge-reranker-base) |
| Latency | A cross-encoder scores every `(query, candidate)` pair sequentially on CPU — added on top of the existing ~40 ms retrieval, per query |
| Dependency | Another model file to vendor, export to ONNX, and verify — more offline-reproducibility surface |
| Test surface | Another integration path to cover |

Against Qwen2.5-3B's ~2.1 GB resident and multi-second generation, the RAM is not the
issue; the point is we would be **paying any cost at all for zero recoverable failures.**

---

## 5. What the failures actually call for (not a reranker)

The reranker question, answered, redirects effort to what would move the number:

- **Q19 is a recall problem, not a ranking problem.** The gold chunk is unreachable for
  every dense model and sits at the edge for the hybrid. If we want it, the levers are
  **chunking** (did a chunk boundary split the relevant clause?) or **query expansion /
  alias handling** on the BM25 side — not reranking. First step: hand-inspect the gold
  chunk boundary for Q19.
- **Q22 is a known architectural limitation.** Single-vector retrieval + top-k does not
  do multi-hop aggregation well. The honest v1 answer is to **document it as a known
  limitation**, not to bolt on machinery that does not fix it.

---

## 6. Known limitations of this decision

- **n = 19.** Every failure is one question (~5.3pp). The *count* of failures is thin.
  But this decision does not rest on the count — it rests on the **type** of the two
  failures (absence, multi-chunk), which a reranker categorically cannot address. Small
  n does not weaken that; it would only change things if the *shape* of failures changed.
- **The verdict would flip** if a larger or hand-labelled held-out set (DECISION-002 §6,
  open action) surfaced failures of the *present-but-below-cutoff* shape — gold chunks
  ranked 3–8 that the LLM never sees. That is the one finding that reopens this. Until it
  appears, there is nothing for a reranker to do.
- This decision is scoped to **v1**. It is a rejection on current evidence, not a claim
  that reranking is never useful for this system.

---

## 7. What would reopen this

Re-evaluate a reranker if **any** of these hold:

1. The hand-labelled held-out set (DECISION-002 §6.Open) shows gold chunks landing
   **present in top-10 but below the LLM's context cutoff** — the shape §2 fixes.
2. The LLM's context budget forces a **smaller top-k** (e.g. top-2), turning
   currently-passing R@3/R@5 hits into failures a reranker could rescue.
3. The corpus grows enough that first-stage recall degrades and precision-within-recall
   becomes the bottleneck.

None hold today.

---

## 8. Decision

**No reranker in v1.** Ship BM25 + bge-small-en-v1.5 / RRF unchanged. Redirect the
effort the reranker would have consumed into: (a) hand-inspecting the Q19 chunk
boundary, and (b) documenting Q22 multi-chunk aggregation as a known limitation.
