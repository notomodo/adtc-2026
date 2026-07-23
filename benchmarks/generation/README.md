# Generation eval — answer-layer faithfulness & abstention

Measures whether Qwen2.5-3B-Instruct, under a grounding prompt, actually *uses* the chunks
retrieval hands it: **faithfulness** (does it answer correctly from the retrieved passages,
including synthesis across passages), **abstention** (does it correctly refuse when the
passages genuinely lack the answer), and — from the v1 run — the reliability of an LLM-judge
grader.

## Method

- **35 answerable questions** (v3 gold set, stratified: `exact_fact`, `paraphrase`,
  `near_miss`, `prose`, `multi_chunk`) plus **6 purpose-built "unanswerable" probes**
  (U01–U06) whose absence from the corpus was verified by keyword scan.
- **Retrieval:** the committed hybrid retriever (BM25 + `bge-small-en-v1.5`, RRF k=60,
  DECISION-002) reused unchanged, `k=3` chunks into context.
- **Generation:** Qwen2.5-3B-Instruct via local Ollama, `temperature=0, seed=42`, fully
  offline (no network, no API keys).
- **Corpus fingerprint:** `592a602f845dce20`, verified on every run.
- **Grading:** Layer A — a deterministic, model-free token-overlap + abstention checker —
  applied identically to all three answer sets in one execution. Layer B, an LLM judge, was
  tried in the v1 run, found unreliable (46% agreement with Layer A), and dropped.
- Three grounding-prompt variants (v1, v2, v3) run against the identical question set and
  retriever; only the `SYSTEM_PROMPT` string changed between runs.

## Results

| Metric | v1 | v2 | v3 |
|---|---|---|---|
| Answerable pass | 16/35 (45.7%) | 6/35 (17.1%) | **25/35 (71.4%)** |
| Wrongly abstained (answerable) | 14 | 27 | **5** |
| Laundered answers (sentinel + content) | 19 | 23 | **0** |
| Stray general-knowledge labels | 15 | 23 | **0** |
| Abstention probes correct (U01–U06) | 6/6 | 6/6 | **6/6** |

Per-stratum pass (of the count in parentheses):

| Stratum | v1 | v2 | v3 |
|---|---|---|---|
| exact_fact (10) | 4 | 4 | **10** |
| paraphrase (8) | 4 | 1 | **4** |
| near_miss (4) | 2 | 1 | **3** |
| prose (8) | 3 | 0 | **5** |
| multi_chunk (5) | 3 | 0 | **3** |

Churn: v1→v3 — 9 improved, 0 regressed. v2→v3 — 19 improved, 0 regressed. Every flip in both
comparisons goes the same direction.

**[DECISION-004](../../docs/DECISION-004-grounding-prompt.md) locks the v3 grounding prompt.**

## Findings

- **v2 regression, root cause diagnosed.** v2 restructured the prompt into a two-step
  DECIDE/ACT form and kept a general-knowledge note; the abstain branch ended up longer and
  more emphatic than the answer branch. Result: "laundered" answers — the model retrieved
  the right chunk, produced the correct answer, then emitted `NOT_IN_DOCUMENTS` and hid that
  correct answer inside the general-knowledge note (20 of 27 v2 abstentions). Generalised
  finding: **for a 3B-class model, prompt salience acts as a behavioural prior, not merely a
  constraint** — elaborating the rule for an unwanted behaviour makes that behaviour more
  likely.
- **v3 fix.** Removed the general-knowledge note entirely and inverted the salience: a long,
  prominent instruction to answer directly, with abstention compressed to a single bare
  token. The refutation condition (pass ≤ 16/35) was pre-registered before the run; observed
  25/35 — hypothesis supported.
- **Retrieval-conditioned generation: 27/28 = 96%.** Of the 35 answerable questions,
  retrieval placed the gold chunk in the k=3 context on only 28; of those, v3 answered
  correctly on 27. The one failure (Q08) is unexplained and documented, not fixed. Four of
  the five v3 abstentions are *correct* behaviour — the gold chunk was never in context (a
  retrieval limitation, not a generation one), all four in the prose/legal-inference stratum,
  matching DECISION-003's independently measured prose R@5 = 62%.
- **Abstention safety property held across all three prompts.** 6/6 probes correct under v1,
  v2, and v3 alike — zero fabrication events across 18 probe evaluations (6 probes × 3 runs).
- **LLM-judge reliability: 46% agreement with the deterministic Layer A checker.** Qwen
  judging Qwen shares its own blind spots and frequently echoed the abstention sentinel
  instead of using its verdict labels. Layer B was dropped after the v1 run; Layer A + human
  review is the trusted path.

## Limitations (stated honestly)

- **Layer A is a token-overlap heuristic, not a truth oracle.** "Pass" means the answer
  materially overlaps the gold chunk — not that it is factually correct and complete.
  Hand-validated 2026-07-23 against a 13-item adversarial sample (weighted toward `prose` and
  `multi_chunk`): 9/10 sampled PASSes confirmed correct, 1 confirmed ungrounded (Q19 — see
  `R5_review_packet.md`). Implied precision 90%, a lower bound on an adversarial sample.
  **71.4% is Layer A's automated pass rate, not a validated accuracy figure — see
  `R5_validation_result.md`.**
- Gold labels on the 16 newer questions and all 6 probes are single-annotator and unverified
  against the source PDFs.
- `n = 35 + 6` — small; one question is ≈2.9pp.
- Generation is not bit-identical across an Ollama model reload (stable within one warm
  process); each of the three runs was a single continuous process.
- Latency ~65–105 s/question on the i5-4300U floor — no measurements yet on the deployment
  reference machine.

## Layout

```
src/gen_answer.py              answer pass: retrieve k=3, generate under the grounding
                                prompt, resumable, temperature=0 seed=42
src/gen_answer.v_prev.py       the v2 prompt, kept for provenance
src/gen_judge.py               grading harness (Layer A deterministic checker;
                                Layer B LLM judge, unused after v1)
src/make_unanswerable.py       generates the 6 abstention probes
src/grade_v3.py                three-way v1/v2/v3 comparison driver

data/questions/questions_unanswerable.json   the 6 abstention probes (U01-U06)

benchmarks/generation/         this directory: per-version answers, verdicts, reports,
                                logs for v1, v2, v3 -- including the v2 regression,
                                kept deliberately as part of the record

docs/DECISION-004-grounding-prompt.md    the locked decision
docs/SESSION_REPORT_generation.html      full session report
```
