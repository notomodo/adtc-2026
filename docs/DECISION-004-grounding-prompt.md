# DECISION-004 — Grounding prompt for the generation layer

**Status:** Accepted
**Date:** 2026-07-19
**Supersedes:** none
**Related:** DECISION-002 (retrieval architecture), DECISION-003 (reranker rejected, n=19),
DECISION-005 (reranker reopened on n=35 evidence, decided: not shipped in v1)
**Scope:** the `SYSTEM_PROMPT` used by the answer pass (`gen_answer.py`) — i.e. how the
local LLM is instructed to use retrieved chunks. Does **not** change retrieval, chunking,
`k`, or the model.

---

## Decision

**Lock the v3 grounding prompt.** Strict grounding, prominent "answer directly" instruction,
abstention reduced to a single bare token `NOT_IN_DOCUMENTS`, and **no general-knowledge
note**.

**Consequence to accept explicitly:** the product no longer offers "abstain, then optionally
add a clearly-labelled general-knowledge note." That behaviour was measured as actively
harmful (see Evidence). The assistant now either answers from the documents or abstains with
a bare token. Nothing else.

---

## Context

Retrieval was locked in DECISION-002 (BM25 + bge-small-en-v1.5, RRF k=60, k=3 chunks into
context). The generation half — whether Qwen2.5-3B-Instruct actually *uses* the chunks it is
handed — was unmeasured until this session, and was the largest unquantified risk in the
system: it is what the human panel experiences.

The required behaviour has two halves:
1. **Faithfulness** — answer from the retrieved passages, including synthesising across them.
2. **Abstention** — when the passages genuinely lack the answer, say so rather than
   fabricating a policy for the business.

Half 2 matters more than half 1 for an SME assistant. A fluent, confident, wrong answer about
a business's own returns window is worse than no answer.

---

## Evidence

Benchmark: 35 answerable questions (v3 set, `corpus_fingerprint 592a602f845dce20`) plus 6
purpose-built **unanswerable probes** (U01–U06) whose answers are genuinely absent from the
corpus. k=3, Qwen2.5-3B-Instruct via local Ollama, `temperature=0, seed=42`, fully offline,
committed retriever reused unchanged. Graded by **Layer A** — a deterministic, model-free
token-overlap + abstention checker — applied identically to all three answer sets in one
execution.

| Metric | v1 | v2 | **v3** |
|---|---|---|---|
| Answerable PASS | 16/35 (45.7%) | 6/35 (17.1%) | **25/35 (71.4%)** |
| Wrongly abstained (answerable) | 14 | 27 | **5** |
| "Laundered" answers (sentinel + content) | 19 | 23 | **0** |
| Answers with `[GENERAL KNOWLEDGE` label | 15 | 23 | **0** |
| Abstention probes correct (U01–U06) | 6/6 | 6/6 | **6/6** |

Per-stratum PASS:

| Stratum | v1 | v2 | **v3** |
|---|---|---|---|
| exact_fact (10) | 4 | 4 | **10** |
| paraphrase (8) | 4 | 1 | **4** |
| near_miss (4) | 2 | 1 | **3** |
| prose (8) | 3 | 0 | **5** |
| multi_chunk (5) | 3 | 0 | **3** |

Churn: **v1→v3 — 9 improved, 0 regressed. v2→v3 — 19 improved, 0 regressed.** Every flip in
both comparisons goes the same direction.

### Corrected denominator — the number that actually characterises generation

The 25/35 headline conflates two systems. Of the 35 answerable questions, retrieval delivered
the gold chunk into the k=3 context on only **28**. On the other 7 the model was never shown
the answer, so generation cannot be charged for them.

Of those 28, the model wrongly abstained on exactly **one** (Q08).

> **Generation, conditioned on what retrieval provides: 27/28 = 96%.**

The remaining shortfall is a **retrieval** limitation, not a generation one. Four of the five
v3 abstentions (Q17, Q27, Q29, Q35) are *correct behaviour*: the gold chunk was absent from
context, and the model said so. All four are prose/legal-inference questions — the same
weakness independently measured on the **n=35 retrieval re-run** (prose R@5 = 62%; see
`benchmarks/retrieval_n35/REPORT.md`). Note this is a different, larger evidence base than
DECISION-003's own n=19 measurement, where prose R@5 is 75% — the two figures are not
interchangeable. *(Corrected 2026-07-22: this citation originally, and incorrectly, pointed
at DECISION-003.)*

---

## Rationale

**Why v2 failed (the mechanism worth recording).** v2 restructured the prompt into
"STEP 1 — DECIDE / STEP 2 — ACT" with FORM A (answer) and FORM B (abstain), and kept the
general-knowledge note. The abstain branch ended up **longer, more detailed and more emphatic**
than the answer branch. Result: a new failure mode, *laundered abstention* — the model produced
the correct, document-grounded answer, then emitted `NOT_IN_DOCUMENTS` and placed that correct
answer inside the sanctioned general-knowledge note. 20 of 27 v2 abstentions contained the real
answer hidden in the note, with 100% correct label formatting.

**Generalised finding:** for a 3B-class model, *prompt salience acts as a behavioural prior,
not merely as a constraint*. Elaborating the rule for the behaviour you do **not** want makes
that behaviour more likely. Length and emphasis are themselves signals.

**Why v3 works.** It removes the general-knowledge slot entirely and inverts the salience: a
long, prominent instruction to answer directly (explicitly licensing synthesis across passages,
partial answers, and wording mismatches between question and passage), with abstention compressed
to one line and a bare token. This was framed as a falsifiable experiment — the pre-registered
refutation condition was PASS ≤ 16/35. Observed 25/35: **hypothesis supported.**

**Why no general-knowledge note in the shipped product.** We now have direct evidence that this
feature is an attractor which pulls a small model into abstaining on questions it can answer, and
into mislabelling grounded answers as outside knowledge. A bare, unambiguous abstention is safer,
simpler, and more defensible. If the note is ever reintroduced, it must be re-tested against v3
as the baseline — not v1/v2 — specifically for whether it reproduces the attractor effect.

---

## Alternatives considered

| Option | Why not |
|---|---|
| Keep v1 | Strictly dominated by v3 on every measured axis (45.7% vs 71.4% PASS; 19 vs 0 laundered). |
| Keep v2 | A measured regression. Retained in the repo as a negative result, not as a candidate. |
| Keep the GK note but shrink it | Untested. The evidence says the note is the attractor; re-adding it needs its own run against the v3 baseline. Deferred, not rejected. |
| Fine-tune the model for grounding | Rejected project-wide (no GPU, no labelled pairs, breaks the "works on any SME's documents" story, per-corpus retraining). |
| Fix the LLM judge and re-grade | The judge was measured unreliable (46% agreement with Layer A; it echoed the sentinel instead of using its labels). Deterministic Layer A + human review is the trusted path. Deferred. |
| Chase Q08 with a fourth prompt | One failure in 28. Not worth a ~45-minute run and the risk of another regression. |

---

## Consequences

**Positive**
- Generation behaves correctly on 27 of the 28 questions where retrieval succeeds.
- The dangerous failure mode — fabricating business policy — did **not occur once** across
  three prompt versions and 18 probe evaluations (6 probes × 3 runs).
- The abstention safety property held under three materially different prompts, which is
  stronger evidence than a single passing run.
- `exact_fact` is now perfect (10/10).

**Negative / accepted**
- The general-knowledge fallback is gone. Users get a bare abstention with no helpful aside.
- Q08 ("Can a teenager open an account?") abstains despite the gold chunk being retrieved at
  rank 1 — an unexplained single-case generation failure, documented not fixed.
- Prose/legal-inference questions still fail, but at the **retrieval** layer, not the prompt.
  DECISION-005 weighed a reranker against this gap on n=35 evidence and decided not to ship
  it in v1 (thin margin, k=3 regression); selective reranking remains an untested v2 lever.

---

## Known limitations of this evidence

- **Layer A is a token-overlap heuristic, not a truth oracle.** 25/35 means "materially overlaps
  the gold chunk," not "factually correct and complete." Hand-validated 2026-07-23 against a
  13-item adversarial sample (weighted toward `prose` and `multi_chunk`): 9/10 sampled PASSes
  confirmed correct, 1 confirmed ungrounded (Q19 — model answered from a non-gold chunk, scored
  PASS anyway). Implied precision 90%, a lower bound on an adversarial sample. **71.4% must
  carry this caveat wherever it is quoted as accuracy** — see
  [`R5_validation_result.md`](../benchmarks/generation/R5_validation_result.md).
- **Gold labels on the 16 newer questions and all 6 probes are single-annotator, unverified
  against the source PDFs.**
- **n = 35 + 6.** One question ≈ 2.9pp. The curve is coarse.
- **Generation is not bit-identical across an Ollama model reload** (stable within one warm
  process). All three runs were single continuous processes; that is the reproducible artifact.
- Latency ~65–105 s/question on the i5-4300U floor. No measurements on the deployment reference
  machine.

---

## Follow-ups

1. **Done 2026-07-23.** Hand-read 13 of the 25 v3 passes (adversarial sample weighted toward
   `prose`/`multi_chunk`) to validate Layer A's verdicts: 9/10 sampled PASSes confirmed correct,
   1 confirmed ungrounded (Q19). See
   [`R5_validation_result.md`](../benchmarks/generation/R5_validation_result.md). 71.4% is
   Layer A's automated pass rate; it may not be quoted as accuracy without this caveat.
2. Reranker not shipped in v1 (DECISION-005). Selective reranking — firing the cross-encoder
   only on low-confidence queries — remains the untested lever for the prose retrieval gap
   if it becomes the binding constraint for v2.
3. Optional: re-introduce a general-knowledge note and re-test against the v3 baseline.
4. Optional: fix the LLM judge (constrained decoding to its four labels) if automated grading
   at scale is later needed.

---

## Artifacts

`gen_answer.py` (harness), `gen_judge.py` (Layer A grader), `make_unanswerable.py` +
`questions_unanswerable.json` (probes), `grade_v3.py` (three-way driver),
`answers.v1.jsonl` / `answers.new.jsonl` / `answers.v3.jsonl`,
`layerA_verdicts.v3.json`, `gen_report.md` (v1), `gen_report_v2.md`, `gen_report_v3.md`,
`gen_run_notes.md`, `gen_prompt_revision_proposal.md`, `smoke_test.log`.

The v2 regression artifacts are retained deliberately: a measured failed hypothesis with a
diagnosed root cause is part of the engineering record.
