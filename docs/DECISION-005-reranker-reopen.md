# DECISION-005 — Cross-Encoder Reranker Reopened on n=35 Evidence

**Status:** Open — evidence recorded, ship/no-ship pending owner decision
**Date:** evidence produced 2026-07-16 · recorded as a decision record 2026-07-22
**Revisits:** DECISION-003 (rejected a reranker for v1, n=19). **Does not delete, rewrite,
or reverse DECISION-003** — that record stands as correct on its own evidence base. This
record adds a larger evidence base (n=35) that changes the picture and leaves the ship
call open.
**Depends on:** DECISION-002 (retrieval architecture), DECISION-004 (generation eval — the
27/28=96% conditioned-generation figure that sharpens the case for revisiting this)

---

## 1. Summary

DECISION-003 rejected a cross-encoder reranker on n=19 evidence: the two failures that
survived the locked retriever (an absent gold chunk; a multi-chunk aggregation question)
were both shapes a reranker cannot fix, so reranking had nothing to do.

A later, larger retrieval re-run — the same locked retriever, unmodified, on the expanded
**35-question set** (16 new questions added) — surfaces a **different** failure shape that
DECISION-003 did not have data on: **prose R@5 drops to 62%** (from 75% on n=19), and some
of those new prose misses land within reach of a reranker. A reranker was tested on top of
the unmodified locked hybrid; **the source report makes no ship/no-ship call, and neither
does this record.** Full evidence: `benchmarks/retrieval_n35/REPORT.md` (retrieval re-run)
and `benchmarks/retrieval_n35/REPORT_reranker.md` (reranker study).

---

## 2. The evidence (n=35, `cross-encoder/ms-marco-MiniLM-L6-v2`, N swept {10,15,20})

Best config, N=10:

| Metric | baseline (no rerank) | + rerank top-10 |
|---|---|---|
| R@3 | 80% | 86% |
| R@5 | 83% | 89% |
| MRR | 0.704 | 0.783 |
| prose R@5 | 62% | 75% |
| multi_chunk R@5 | 80% | 100% |

Net at N=10: **7 improved, 2 worsened** (Q31 near_miss rank 1→4; Q27 paraphrase rank
8→10). Widening N to 15 or 20 rescues nothing further and adds more regressions — the
three deepest prose misses (Q19, Q29, Q35) are not reachable by reranking at any N tested;
the cross-encoder scores those gold chunks *lower*, not higher. Full per-stratum tables and
the regression/rescue audit are in `benchmarks/retrieval_n35/REPORT_reranker.md` §4.

---

## 3. Corrected cost framing

DECISION-003's cost argument compared reranker latency against **retrieval** latency alone
(~40 ms) and called the added cost prohibitive. That comparison used the wrong denominator.

> **End-to-end query time is dominated by generation, not retrieval.** Measured generation
> latency is **65-105 s/question** on the same i5-4300U floor (DECISION-004), against ~86 ms
> for retrieval. The reranker's ~1.3-2.7 s therefore adds roughly **2-3% to end-to-end
> latency**, not the 25-50× implied by comparing it to retrieval alone. The original framing
> overstated the cost by comparing against the wrong denominator.

This does not make the reranker free, and it does not decide the question — it corrects
the terms the question should be weighed in.

---

## 4. The counterweight, stated honestly

The corrected cost framing is not a case for shipping without qualification:

- **At `k=3`, Q31's rank 1→4 regression pushes a previously-correct chunk out of the
  context window entirely.** A question that generation would have answered correctly no
  longer gets the chance to.
- **The deep prose misses (Q19, Q29, Q35) are unreachable** at any N tested — the
  reranker's usefulness here is entirely within the top-10, and it actively disagrees with
  those three gold chunks rather than merely failing to reach them.
- **Net gain at `k=3` is modest: about +2 questions (R@3 80%→86%).** This is a real but
  small effect, not a transformative one, set against real regressions and a non-trivial
  latency cost even at 2-3% of the end-to-end budget.
- The 2-3% latency figure is itself measured on the same pessimistic dev-floor CPU as
  everything else in this project (DECISION-004, DECISION-002 §7) — **not yet measured on
  the deployment reference machine.**

---

## 5. The sharpened case *for* revisiting this

DECISION-004's generation evaluation found that, conditioned on retrieval actually
supplying the gold chunk, generation answers correctly on **27/28 (96%)**. That is close to
ceiling. **Retrieval is now the binding constraint on end-to-end accuracy, not generation**
— which is precisely the situation in which a retrieval-side lever like reranking is worth
re-examining, even at a real (if now-corrected) latency cost.

---

## 6. What this record does NOT do

- It does not decide to ship a reranker.
- It does not reverse or edit DECISION-003, which remains correct on its own (n=19)
  evidence.
- It does not choose a specific reranking strategy (e.g. "selective" reranking — firing the
  cross-encoder only on low-confidence queries so most queries pay no latency — is named in
  DECISION-004's follow-ups as the outstanding idea, but it was not tested here; only a
  blanket rerank-every-query N-sweep was measured).

**Status stays open until the owner weighs §3 against §4 and makes the ship/no-ship call.**

---

## 7. Known limitations of this evidence

- **n = 35 is still thin.** One question ≈ 2.9pp.
- The 16 new (`claude_v3`) gold labels are single-annotator, unverified against the source
  PDFs (`data/questions/questions_sme_v3.json` `_meta.WARNING`).
- Only one reranker model was tested (`ms-marco-MiniLM-L6-v2`), at one N-range. This is not
  a search over reranker architectures.
- Latency figures (both the reranker's and generation's) come from the i5-4300U dev floor,
  not the deployment reference machine (open risk R1 in `DECISIONS.md`).

---

## 8. What would resolve this

A ship decision requires weighing: +2 questions of R@3 recall and the prose-stratum gain,
against a real (if small, ~2-3%) latency cost and two concrete regressions, one of which
(Q31) removes a previously-correct answer from the context window. That weighing is an
owner judgement call, not a further measurement — the evidence needed to make it is now
recorded here and in `benchmarks/retrieval_n35/`.
