# Generation eval v2 — grounding-prompt fix, Layer A only

**Headline: the approved prompt revision is a REGRESSION, not a fix.** Layer A
(deterministic) answerable PASS rate fell from 45% (16/35) to 17% (6/35).
Judge (Layer B) was intentionally skipped this run per instructions — not needed
to see this; the deterministic signal alone is unambiguous. Do not run the full
LLM-judge pass on `answers.new.jsonl` until the prompt is revisited.

## What was run
- `SYSTEM_PROMPT` in `gen_answer.py` replaced verbatim with the block from
  `gen_prompt_revision_proposal.md` (diff shown to you before the run; confined
  to lines 46-66, `USER_TEMPLATE` and all logic untouched — confirmed via
  `diff files/gen_answer.py gen_answer.py`, 34-line diff, entirely inside
  `SYSTEM_PROMPT`).
- Invariants held: `NOT_IN_DOCUMENTS` sentinel and the
  `[GENERAL KNOWLEDGE — not from the documents]:` label are byte-identical to
  before and to `gen_judge.py`'s `ABSTAIN_SENTINEL` / `GK_MARKER`.
- Full answer pass: 41/41 questions, one continuous warm process, 44.7 min
  (65 s/q avg), no errors. `answers.new.jsonl` preserved; `answers.v1.jsonl` /
  `verdicts.v1.jsonl` / `gen_report.v1.md` untouched.
- Graded with Layer A (`gen_judge.py:layer_a`) only, via the driver script from
  the task, run against **both** `answers.new.jsonl` and (for a clean baseline)
  re-run against `answers.v1.jsonl` with the identical driver/definitions —
  so every number below is apples-to-apples, same code, same day.
  (v1's report quoted 46% from the original run's own summary — that used
  `round()`; the driver here uses integer floor `//`, so the re-derived
  baseline reads 45%. Same 16/35 underneath; not a real discrepancy.)

## Layer A answerable PASS%: v1 45% (16/35) → v2 **17%** (6/35)

| stratum | v1 | v2 |
|---|---|---|
| exact_fact | 4/10 | 4/10 |
| multi_chunk | 3/5 | **0/5** |
| near_miss | 2/4 | 1/4 |
| paraphrase | 4/8 | **1/8** |
| prose | 3/8 | **0/8** |
| **total** | **16/35 (45%)** | **6/35 (17%)** |

Every stratum except `exact_fact` (flat) got worse; `multi_chunk` and `prose`
collapsed to zero.

## Question-level churn (same driver, same day, id-by-id)
- **12 questions that PASSED in v1 now FAIL in v2:** Q03, Q10, Q12, Q15, Q25,
  Q28, Q30 (→WEAK), Q32, Q33, Q36, Q37, Q38.
- **Only 2 improved:** Q01 (WEAK→PASS) and Q23 (FAIL→PASS).
- Net: **-10 correct answers** for this run.

## The 9 v1 wrong-abstentions — did they flip?
| id | v1 → v2 | status |
|---|---|---|
| Q02 | still abstains | not flipped |
| Q05 | still abstains | not flipped |
| Q06 | still abstains | not flipped |
| Q07 | still abstains | not flipped |
| Q08 | still abstains | not flipped |
| Q23 | now answers, matches gold | **flipped** |
| Q24 | still abstains | not flipped |
| Q31 | still abstains | not flipped |
| Q34 | still abstains | not flipped |

**1/9 flipped.** Worse, 12 *previously-correct* answers broke in exchange for
that one fix — a clearly negative trade.

## The new, dominant failure mode: laundered abstention
This is not the same bug as v1, and it's more insidious. v1's self-contradiction
was a bare or malformed assertion glued to the sentinel (no GK label, or a wrong
one). v2's abstentions are **correctly formatted** — exact GK label, every time
(0 malformed/missing labels found across all abstaining answers, an actual
improvement over v1's one malformed case) — but the model now routes the
*entire correct, document-grounded answer* through the "general knowledge" note
instead of answering directly. Examples, verbatim from `answers.new.jsonl`:

- **Q10** ("goods that can't be sent back") — gold: *innerwear, swimsuits, gym
  wear, sleep wear, perfumes, jewelry, health & wellness products, adult toys*.
  Answer: `NOT_IN_DOCUMENTS` then `[GENERAL KNOWLEDGE — not from the
  documents]: Innerwear, swimsuits, gym wear, sleep wear; Perfumes, jewelry,
  health & wellness products, adult toys.` — the "general knowledge" is the
  gold answer, word for word.
- **Q36** ("enforcement actions against a seller") — same shape: sentinel, then
  a near-verbatim reproduction of the gold enforcement-action list inside the
  GK note.
- **Q12** — by contrast, honestly abstains with no leaked content ("This
  information is not present in the provided document snippets"), which is
  wrong (the phone/email answer is in chunk 39) but at least isn't
  self-contradictory in the leak sense.

So the driver's "self-contradiction" count (21 for v2, vs 14 for v1 using the
identical driver) is a mix of two different things it can't distinguish: (a)
genuine content-leakage like Q10/Q36 above, and (b) merely a >25-character
abstention explanation that adds no leaked fact, like Q12. Treat the 21/14
figures as an upper bound on true contradictions, not a precise count — the
qualitative pattern (correct answers laundered as "general knowledge") is the
real finding, and it now affects roughly a third of answerable questions,
worse than v1's more contained pattern.

**Likely root cause:** the new prompt's two-step "STEP 1 — DECIDE, STEP 2 —
ACT" framing and its FORM B block (longer, more detailed, with emphatic
"copied EXACTLY, character for character" language) is more salient to this
weak 3B model than the terser FORM A block. Rather than fixing the coin-flip
between the two forms, it seems to have made FORM B *more* attractive as the
default completion path, and the model compensates by cramming the real answer
into the now-sanctioned "GK note" slot.

## Abstention-probe regression check: U01–U06 = **6/6** — no regression
All 6 unanswerable probes still abstain correctly, matching v1. This is the
one area where the fix didn't make anything worse.

## GK-label correctness
All 27 abstaining answers in v2 use the exact
`[GENERAL KNOWLEDGE — not from the documents]:` string — 0 malformed/missing
labels (v1 had 1 malformed instance, Q08's "— from external sources"). Formatting
compliance genuinely improved; it's the *content routing* that got worse.

## Success criteria — met or not
| Criterion | Result |
|---|---|
| 9 wrong-abstentions flip to grounded answers | **1/9** — not met |
| No answer contains both sentinel + substantive unlabelled answer | Partially — no *malformed*-label cases, but labelled leakage is now the dominant pattern in a different guise |
| U01–U06 stay 6/6 | **Met** |
| GK notes use exact label | **Met** (100%) |
| Layer A PASS rises materially above 46% | **Not met — it fell to 17%** |

**Overall: success criteria not met. This is a regression and should not replace
v1 as the working prompt.** Recommend reverting `SYSTEM_PROMPT` to the v1
wording (or trying a materially different revision — e.g. drop the two-step
DECIDE/ACT scaffold, shrink FORM B back down, and/or move the "if present you
must answer" rule to be the more prominent, later instruction) before spending
another full run + judge pass.

## Does the LLM judge look necessary now?
No — not for this decision. Layer A alone (deterministic, near-instant) made
the regression completely unambiguous: PASS rate more than halved, 12
previously-correct answers broke, only 1 of 9 target fixes landed. The judge's
own known unreliability (46% A/B agreement, echo bug) would only add noise here.
The judge may still earn its keep later for fine-grained FAITHFUL/WEAK
distinctions once a prompt candidate is actually improving on Layer A — but
it's not needed to tell you this candidate failed.
