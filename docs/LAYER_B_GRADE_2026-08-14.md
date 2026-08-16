# Layer-B faithfulness grade — 3B vs 1.5B vs Qwen3-4B (2026-08-14)

**Graded from:** `docs/grading_pack.md` (self-contained substrate, generated 2026-08-02 from
`results/benchmark_*`, commit `3169512`). **Grader:** LLM-as-judge (in-session), applying the
pack's rubric per question to the retrieved context shown to all three models. **Scope:**
35 answerable + 6 unanswerable probes, 123 model-answer judgments.

**Rubric (as specified in the pack):** *Answerable* — `FAITHFUL` (every claim supported by
the retrieved context; concise/paraphrased OK), `UNFAITHFUL` (a claim not supported by or
contradicting the context), `WRONG_ABSTENTION` (said NOT_IN_DOCUMENTS although the context
contained the answer). *Probes* — `CORRECT_ABSTENTION` or `UNFAITHFUL` (answered anyway).
Severity of UNFAITHFUL is annotated **substantive** (a real policy misstatement or
fabricated fact) vs **minor** (a benign procedural embellishment with no policy fact
misstated). Retrieval was byte-identical across models (`gold_chunk_hit` 28/28), so every
delta is generation-only.

**Not a human-in-the-loop grade.** This is an independent machine read of the pack; it is
deterministic enough to reproduce but should be spot-checked by a human before it is quoted
externally. The verdict table below is also appended to `grading_pack.md` (filled column).

---

## 1. Headline results

| Metric | 3B | 1.5B | Qwen3-4B |
|---|---|---|---|
| Layer-A pass rate (the biased proxy, for reference) | 26/35 = **74.3%** | 22/35 = 62.9% | 23/35 = 65.7% |
| **Layer-B faithfulness, all answerable (FAITHFUL/35)** | **29/35 = 82.9%** | 28/35 = 80.0% | **30/35 = 85.7%** |
| **Layer-B faithfulness, gold-chunk-retrieved only (FAITHFUL/28)** | 27/28 = 96.4% | 26/28 = 92.9% | **28/28 = 100%** |
| Answered (did not abstain) / 35 answerable | 31 | 32 | 32 |
| Correct abstention on retrieval-miss (answerable) | 4 (Q17 Q27 Q29 Q35) | 3 (Q17 Q29 Q35) | 3 (Q17 Q27 Q35) |
| Wrong abstention (context had the answer) | **1 (Q08)** | 0 | 0 |
| Probe abstention (6 unanswerable) | **6/6** | 6/6 | **5/6** (U04) |
| UNFAITHFUL total (answerable + probes) | 1 | 4 | 3 |
| — of which substantive (excl. minor) | 1 (Q19) | 3 (Q19 Q27 Q33) | 3 (Q19 Q29 U04) |
| — of which unique to this model | **0** | 2 (Q27 Q33) | 2 (Q29 U04) |

> Q19's UNFAITHFUL is **shared by all three models** (all assert "suspend **without telling
> you**", which the retrieved context does not state — the notice-free clause was not
> retrieved). It is the R5 confirmed false positive, and this grade shows it generalises to
> all three, not just the 3B.

## 2. The corrected three-way ranking

1. **Faithfulness when the answer was in context: Qwen3-4B (28/28) > 3B (27/28) > 1.5B (26/28).**
   The 3B's single loss is Q08, where it abstained although the age rule was in the retrieved
   chunk (the others answered it correctly). Qwen3-4B's 100% is genuine: on gold-hit
   questions it had zero unsupported claims.
2. **Safety: 3B (1 hallucination, 6/6 probes) > 1.5B ≈ Qwen3-4B** (each with 2 unique
   hallucinations; Qwen3-4B's includes a probe — U04, "physical store in Kampala" — i.e. it
   answered a question the corpus deliberately cannot answer).
3. **Efficiency (from the benchmark, not this grade): 3B ≈ 1.5B > Qwen3-4B** (2.83 tok/s,
   peak 7437 MB — near-OOM on the 8 GB target, a disqualification risk under the published
   rules).

**Bottom line: the 3B remains the right submission choice**, but for slightly different
reasons than Layer-A suggested. Its raw pass-rate lead over Qwen3-4B (74.3 vs 65.7) is
**largely a grader length-bias artifact** — on substance the two are at parity or Qwen3-4B is
ahead on faithfulness. The 3B's real, defensible advantages are (a) **safety** — zero unique
hallucinations and 6/6 probe abstentions, vs one confident probe hallucination for Qwen3-4B
and two substantive hallucinations for the 1.5B; (b) **efficiency** — Qwen3-4B nearly
saturates the 8 GB box; and (c) **conservatism** — it abstains rather than fabricate, at the
cost of one genuinely wrong abstention (Q08). The 1.5B is clearly weakest on faithfulness
and has the most unique hallucinations; nothing in Layer-B rehabilitates it.

## 3. Layer-A bias quantification (the point of this exercise)

Layer-A's three-way gap is **substantially overlap/length artifact, not faithfulness**:

- **False positives** (Layer-A PASS/WEAK, actually UNFAITHFUL): 3B **1** (Q19),
  1.5B **3** (Q19, Q33, Q38-minor), Qwen3-4B **0**.
- **False negatives** (Layer-A FAIL/WEAK, actually FAITHFUL): 3B **4** (Q14 Q16 Q21 Q22),
  1.5B **7** (Q14 Q16 Q21 Q22 Q25 Q30 Q32), Qwen3-4B **7** (Q07 Q14 Q16 Q22 Q30 Q32 Q33).
  The false negatives are terse-but-correct answers (e.g. 1.5B's correct `support@kibuga.com`
  scored FAIL on Q25; Q16's faithful data-type enumerations scored FAIL for all three) —
  exactly the length bias the pack warned about, and it hits the two alternatives harder
  than the 3B, inflating the 3B's lead.
- **Framing-only corrections** (Layer-A FAIL, but the model behaved correctly by abstaining
  because retrieval missed the gold chunk): Q17/Q27/Q29/Q35 for the 3B, Q17/Q29/Q35 for the
  others. These are **retrieval failures handled correctly**, not generation failures.

**Correction to the pack's own hint:** the pack flags Q19 *and Q32* as "known Layer-A false
positives with the gold chunk NOT retrieved". This grade confirms **Q19** as a genuine
faithfulness false positive, but **Q32 is not one**: the 3B's Q32 answer is fully supported
by the retrieved context (formal warnings / suspension / penalties / legal action are in the
retrieved Sellers-T&C chunk); it is incomplete versus the gold answer (misses IP-blocking,
which was in the unretrieved chunk) but not ungrounded.

## 4. The five 3B "false abstentions" — refined

The floor benchmark listed 5 abstentions on answerable questions (Q08 Q17 Q27 Q29 Q35) as
"the top accuracy lever". Layer-B refines this:

- **Q08 — a real generation failure** (gold chunk retrieved; 3B abstained anyway). The one
  fixable-in-generation abstention.
- **Q17 Q27 Q29 Q35 — correct abstention behavior on retrieval misses** (the gold chunk was
  not retrieved; the context genuinely lacked the answer). These are retrieval problems
  (the deep prose/paraphrase misses already tracked in DECISION-005), not generation
  problems. Fixing them is the selective-reranking / retrieval work, not a prompt fix.

So the 3B's conservatism costs one truly wrong abstention (Q08), and its other four
abstentions were the model doing the right thing under a retrieval miss — which is exactly
the failure mode the v3 grounding prompt is designed to produce (abstain rather than
fabricate).

## 5. Per-question verdicts

Verdict legend: **F** = FAITHFUL, **U** = UNFAITHFUL (s = substantive, m = minor),
**WA** = WRONG_ABSTENTION, **CA** = CORRECT_ABSTENTION (on retrieval-miss answerable or
probe). "Gold?" = was the gold chunk retrieved. Shaded rows mark Layer-A disagreements.

| Q | Gold? | 3B | 1.5B | Qwen3-4B | Notes |
|---|---|---|---|---|---|
| Q01 | Y | F | F | F | |
| Q02 | Y | F | F | F | |
| Q03 | Y | F | F | F | 1.5B partial (one number) but faithful |
| Q04 | Y | F | F | F | |
| Q05 | Y | F | F | F | |
| Q06 | Y | F | F | F | |
| Q07 | Y | F | F | F | Qwen3-4B Layer-A WEAK = false negative |
| Q08 | Y | **WA** | F | F | 3B wrong abstention — real failure; Layer-A FAIL agrees in outcome |
| Q09 | Y | F | F | F | |
| Q10 | Y | F | F | F | 1.5B superset incl. damaged/broken-screen items — inside the same "do not accept returns" block, supported |
| Q12 | Y | F | F | F | |
| Q13 | Y | F | F | F | |
| Q14 | Y | F | F | F | Layer-A WEAK ×3 = false negatives |
| Q15 | Y | F | F | F | |
| Q16 | Y | F | F | F | Layer-A FAIL ×3 = false negatives (faithful enumerations) |
| Q17 | N | CA | CA | CA | correct abstention on retrieval miss (warranty clause not retrieved) |
| Q19 | N | **U-s** | **U-s** | **U-s** | all three assert "without telling you" — unsupported; R5 false positive confirmed, generalised |
| Q21 | Y | F | F | F | Layer-A WEAK ×2 (3B, 1.5B) = false negatives |
| Q22 | N | F | F | F | faithful-but-incomplete (refund methods not in retrieved context); Layer-A FAIL ×3 = false negatives |
| Q23 | Y | F | F | F | |
| Q24 | Y | F | F | F | |
| Q25 | Y | F | F | F | 1.5B Layer-A FAIL = false negative (terse correct answer) |
| Q26 | Y | F | F | F | |
| Q27 | N | CA | **U-s** | CA | 1.5B answers wrong chunk (returned-product storage, not data retention) — known Q27 hallucination confirmed |
| Q28 | Y | F | F | F | |
| Q29 | N | CA | CA | **U-s** | Qwen3-4B asserts "yes, you can ask to delete everything" — deletion not in retrieved context (context over-reach); 3B/1.5B abstain correctly |
| Q30 | Y | F | F | F | Layer-A WEAK ×2 (1.5B, Qwen3-4B) = false negatives |
| Q31 | Y | F | F | F | |
| Q32 | N | F | F | F | all grounded in retrieved Sellers-T&C chunk; Layer-A WEAK ×2 (1.5B, Qwen3-4B) = false negatives; **not a faithfulness false positive for the 3B** (see §3) |
| Q33 | Y | F | **U-s** | F | 1.5B invents sharing parties ("website visitors, users of social media platforms") — unsupported |
| Q34 | Y | F | F | F | |
| Q35 | N | CA | CA | CA | correct abstention on retrieval miss (jurisdiction clause not retrieved) |
| Q36 | Y | F | F | F | |
| Q37 | Y | F | F | F | partial but faithful |
| Q38 | Y | F | **U-m** | F | 1.5B adds "follow up with your order number for tracking" + shifts quality-check agent — minor embellishment |
| U01 | — | CA | CA | CA | |
| U02 | — | CA | CA | CA | |
| U03 | — | CA | CA | CA | |
| U04 | — | CA | CA | **U-s** | Qwen3-4B conflates HQ with a physical store — known U04 hallucination confirmed |
| U05 | — | CA | CA | CA | |
| U06 | — | CA | CA | CA | Qwen3-4B wraps sentinel in prose but abstains correctly |

Totals: 3B **F 29 / WA 1 / U 1 / CA 10** (answerable: F 29, WA 1, U 1, CA 4; probes: CA 6).
1.5B **F 28 / U 4 / CA 9** (answerable: F 28, U 4, CA 3; probes: CA 6).
Qwen3-4B **F 30 / U 3 / CA 8** (answerable: F 30, U 2, CA 3; probes: CA 5, U 1).

## 6. Implications

1. **Model choice: unchanged — 3B.** The Layer-B grade confirms the 3B is the correct
   submission model on the grounds that matter for a *grounded Q&A product*: zero unique
   hallucinations, 6/6 probe safety, top-tier faithfulness (96.4% on gold-hit), and the
   lightest memory footprint. Qwen3-4B is a genuine faithfulness rival (100% on gold-hit)
   but fails one unanswerable probe and near-saturates the 8 GB box (disqualification risk);
   the 1.5B is not competitive on faithfulness.
2. **Do not quote Layer-A numbers as accuracy** (already policy): this grade quantifies the
   bias — ~4–7 false-negative verdicts per model from terseness, 1–3 false positives, and a
   Layer-A gap (3B vs Qwen3-4B) that is mostly artifact. The defensible claim is now:
   *"A faithfulness-aware grade (2026-08-14) puts the 3B and Qwen3-4B at parity on
   faithfulness-when-given-the-chunk (27/28 vs 28/28), with the 3B uniquely clean on safety
   (zero unique hallucinations, 6/6 abstention probes) and clearly better on RAM/latency."*
3. **The 5 "false abstentions" are mostly retrieval misses** (4 of 5): the generation fix
   space is one question (Q08); the abstention lever is a retrieval lever (DECISION-005
   selective-reranking / prose-recall work), not a prompt lever.
4. **Q19's ungrounded PASS generalises to all three models** — worth stating in the R5
   follow-up, and it means Q19 should be treated as an open abstention-or-answer design
   case (the correct behavior given the retrieved context was abstention).

**Validate:** have a human spot-check the shaded rows (§5) and the three UNFAITHFUL
judgments (Q19 shared, Q27 1.5B, Q29 Qwen3-4B, Q33 1.5B, U04 Qwen3-4B) before quoting the
grade externally.
