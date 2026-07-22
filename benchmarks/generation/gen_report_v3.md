# Grounding-prompt experiment v3 — Layer A results and verdict

Graded with `gen_judge.layer_a` (deterministic, model-free token-overlap + abstention
checker) applied identically, in one execution, to all three answer sets:
`answers.v1.jsonl`, `answers.new.jsonl` (v2), `answers.v3.jsonl`. No LLM judge (Layer B)
was used, per task instructions. Full per-question verdicts are in
`layerA_verdicts.v3.json`.

Note on filenames: the task brief refers to the v1 run as `answers.jsonl`, but the file
actually present in the working directory is `answers.v1.jsonl`. That is the file used
for all "v1" numbers below; it was not modified.

## Three-way comparison

| Metric | v1 | v2 | v3 |
|---|---|---|---|
| Answerable PASS | 16/35 (45.7%) | 6/35 (17.1%) | **25/35 (71.4%)** |
| Wrongly abstained (answerable) | 14 | 27 | **5** |
| Answers with sentinel + >25 extra chars ("laundered") | 19 | 23 | **0** |
| Answers containing `[GENERAL KNOWLEDGE` label | 15 | 23 | **0** |
| Abstention probes correct (U01–U06) | 6/6 | 6/6 | 6/6 |

### Per-stratum PASS (of total in that stratum)

| Stratum | v1 | v2 | v3 |
|---|---|---|---|
| exact_fact (10) | 4/10 | 4/10 | **10/10** |
| paraphrase (8) | 4/8 | 1/8 | **4/8** |
| near_miss (4) | 2/4 | 1/4 | **3/4** |
| prose (8) | 3/8 | 0/8 | **5/8** |
| multi_chunk (5) | 3/5 | 0/5 | **3/5** |

v3 is at or above v1 in every stratum, with the largest gain on `exact_fact` (10/10, up
from 4/10) — consistent with the "general-knowledge note" no longer competing for the
model's attention on questions with a single, clear factual answer.

## Per-question churn

**v1 → v3** — 9 improved, 0 regressed:
`Q01, Q02, Q05, Q06, Q19, Q23, Q24, Q31, Q34` flipped FAIL/WEAK → PASS. No question that
passed under v1 failed under v3.

**v2 → v3** — 19 improved, 0 regressed:
`Q02, Q03, Q05, Q06, Q10, Q12, Q15, Q19, Q24, Q25, Q28, Q30, Q31, Q32, Q33, Q34, Q36, Q37,
Q38` flipped FAIL/WEAK → PASS. No question that passed under v2 failed under v3.

v3 is a strict improvement over both prior prompts on this benchmark — every flip goes in
the same direction, in both comparisons.

## Hypothesis verdict: **SUPPORTED**

The hypothesis was: removing the general-knowledge slot and inverting salience (long
"answer directly" instruction, abstention reduced to a bare token) would raise PASS above
v1's 16/35 and drop answerable-abstentions below v1's 14.

Both conditions hold clearly:
- PASS: 25/35 (71.4%) > 16/35 (45.7%)
- Wrongly abstained: 5 < 14

The v2 "laundered abstention" bug (correct answer hidden inside the general-knowledge
note after a spurious `NOT_IN_DOCUMENTS`) is also gone: 0 instances in v3, versus 19 in v1
and 23 in v2. This is consistent with the theory that the note itself — not the grounding
rules — was the attractor pulling the model into abstaining even when it knew the answer.

## Safety regression check

**No regression.** All 6 abstention probes (U01–U06) still correctly abstain under v3,
identical to v1 and v2. Removing the general-knowledge slot did not cause the model to
answer from outside knowledge on questions the corpus genuinely cannot answer — the
"answer directly from the passages" instruction did not bleed into fabricating facts absent
from context. This was the main risk of this diagnostic change and it did not materialize.

## Recommendation

**Lock v3.** It strictly dominates v1 and v2 on every measured axis: highest PASS rate,
fewest wrong abstentions, zero laundered-abstention incidents, zero stray general-knowledge
leakage, and unchanged (perfect) abstention-probe safety. There is no metric on which v1 or
v2 outperforms it.

One caveat carried over from the task brief: v3 as tested here has no general-knowledge
note at all — that was a deliberate, temporary diagnostic simplification, not the final
product spec. If the product still wants an optional, clearly-labelled general-knowledge
note after a genuine abstention, that behavior needs to be reintroduced and re-tested
specifically for whether it reproduces the v2 attractor effect at a smaller scale — the
result here does not confirm that a re-added note would be safe, only that removing it
entirely fixed the measured bugs. Any future prompt change reintroducing that note should be
evaluated against this v3 result, not against v1/v2, as the new baseline to beat.
