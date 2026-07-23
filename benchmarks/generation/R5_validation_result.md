# R5 Validation Result

Tabulated from the human-completed `R5_review_packet.md`. This sample is deliberately adversarial (weighted toward multi_chunk and prose strata, the shapes where token overlap is least reliable), so the precision figure below is a **lower bound** on Layer A's true precision across the full 25 PASSes, not an unbiased estimate.

## Layer A PASS items (n=10)

- CORRECT: 9
- UNGROUNDED: 1
- WRONG: 0
- LABEL ISSUE: 0

**Implied precision of Layer A's PASS verdict on this sample: 9/10 (90.0%)** -- lower bound, adversarial sample, see caveat above.

## Layer A WEAK items (n=3) -- for context, excluded from the precision figure above

- CORRECT: 3
- UNGROUNDED: 0
- WRONG: 0
- LABEL ISSUE: 0

## Per-question verdicts

| ID | Stratum | Layer A | Human |
|---|---|---|---|
| Q19 | prose | PASS | UNGROUNDED |
| Q36 | multi_chunk | PASS | CORRECT |
| Q37 | multi_chunk | PASS | CORRECT |
| Q38 | multi_chunk | PASS | CORRECT |
| Q15 | prose | PASS | CORRECT |
| Q32 | prose | PASS | CORRECT |
| Q33 | prose | PASS | CORRECT |
| Q34 | prose | PASS | CORRECT |
| Q01 | exact_fact | PASS | CORRECT |
| Q05 | exact_fact | PASS | CORRECT |
| Q07 | paraphrase | WEAK | CORRECT |
| Q14 | near_miss | WEAK | CORRECT |
| Q21 | multi_chunk | WEAK | CORRECT |

