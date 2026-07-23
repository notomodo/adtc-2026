# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Prior to this file the
history lived only in the module docstrings of `extract.py` and
`verify_extraction.py`; it is consolidated here so the repository is the single
source of truth.

## [Unreleased]

### Added
- **R5 hand-validated: risk stays Open.** `benchmarks/generation/R5_review_packet.md` was
  hand-completed and validated 2026-07-23: of 10 sampled Layer A PASSes, 9 confirmed CORRECT
  and 1 confirmed **UNGROUNDED** (Q19 — the model answered from a non-gold chunk and Layer A
  scored it PASS anyway, the exact failure mode R5 exists to catch, now confirmed real, not
  hypothetical). Implied precision 9/10 (90%), a lower bound on an adversarial sample. Result
  in `benchmarks/generation/R5_validation_result.md` (produced by `src/r5_tabulate.py`);
  packet integrity now asserted by `tests/test_r5_packet.py`, running in CI. Risk R5 in
  `DECISIONS.md` **stays Open**: 71.4% is Layer A's automated pass rate, not a validated
  accuracy figure.
- **R5 hand-validation review packet.** `benchmarks/generation/R5_review_packet.md` samples
  13 of the 25 v3 Layer A PASSes (weighted toward multi_chunk/prose, the strata where token
  overlap is least reliable, plus 2 exact_fact controls and the 3 WEAK borderline cases),
  including the confirmed Q19 false-positive (gold chunk never in context, scored PASS
  anyway). `src/r5_tabulate.py` will tabulate the human's verdicts once the packet is filled
  in and compute the implied precision of Layer A's PASS verdict as a lower bound. Risk R5 in
  `DECISIONS.md` stays **Open** — no verdicts exist yet, this only prepares the material, and
  the 71.4% figure is unchanged pending that adjudication.
- **Reranker decision: not shipped in v1.** `docs/DECISION-005-reranker-reopen.md`'s
  ship/no-ship call is now made: the n=35 evidence (R@3 80%→86%, prose R@5 62%→75%) is not
  enough to justify the reranker against its k=3 regression (Q31 drops out of the context
  window) and the three prose misses it cannot reach at any N. The corrected latency framing
  (~2-3% of end-to-end time, not 25-50×) was considered and was not the deciding factor. Not
  reversed, deferred — selective reranking remains untested as a v2 lever. `README.md`,
  `DECISIONS.md` (D10, D14) updated to stop describing this as open.
- **Retrieval re-run at n=35 and reranker reopened.** The locked retriever (unchanged)
  re-run against the expanded 35-question set
  (`data/questions/questions_sme_v3.json`), plus a cross-encoder reranker study
  reopening DECISION-003 on this larger evidence base. Harnesses `src/eval_sme_v3.py`,
  `src/eval_reranker.py`; results and reports in `benchmarks/retrieval_n35/`. New
  `docs/DECISION-005-reranker-reopen.md` records the evidence with **no ship/no-ship
  call made** — status is explicitly open. `docs/DECISION-004-grounding-prompt.md`'s
  two citations that pointed at DECISION-003 for n=35-only figures are corrected to
  point at this new evidence instead.
- **Generation eval harness and results (v1-v3).** First measurement of the generation
  layer: `src/gen_answer.py` (answer pass), `src/gen_judge.py` (Layer A deterministic
  grader; Layer B LLM judge measured unreliable, 46% agreement, and dropped),
  `src/make_unanswerable.py` + `data/questions/questions_unanswerable.json` (6 abstention
  probes), `src/grade_v3.py` (three-way comparison driver). Results for all three
  grounding-prompt variants — including the v2 regression, retained deliberately — live in
  `benchmarks/generation/`. See `docs/DECISION-004-grounding-prompt.md` and
  `benchmarks/generation/README.md`.
- **Repository consolidation.** Artifacts previously delivered piecemeal across
  several chat sessions are gathered into one reproducible git repository
  (`adtc-2026`) with a conventional `src/ tests/ benchmarks/ tools/ docs/`
  layout. A clean clone now satisfies
  `pip install -r requirements.txt && pytest`. See
  [`docs/REPO_CONSOLIDATION.md`](docs/REPO_CONSOLIDATION.md).
- **Permanent negative-control fixture.** `tests/fixtures/CORRUPTED_v1_output.txt`
  freezes the project's defining bug (a financial table whose column headers were
  lost in extraction, leaving unlabelled numbers). `test_extraction.py` asserts
  GATE 1 fires on it. A gate that has never failed is untested; this fixture
  stays in the repo forever.
- Continuous integration (`.github/workflows/ci.yml`): Python 3.12,
  `pip install -r requirements.txt`, `pytest -v`.
- `LICENSE` (MIT, © 2026 Andrew) with a note distinguishing source-code terms
  from model-weight terms.

## Extraction / verification history

The stage-1 ingestion pipeline evolved through several revisions. Each defect in
its history passed a *structural* check while remaining *semantically* broken —
the recurring lesson that shaped the semantic quality gates.

### v3.1 — 2026-07-12
- **Multi-row header stacks merged** (`find_header_span`, `merge_header_stack`).
  Statutory statements stack headers three deep (period / audit status / units);
  a single-row picker took the units row, yielding three identical column names.
- **GATE 4 (`has_ambiguous_headers`)** added: fires when a row's headers are
  duplicated, so its values are labelled but unresolvable.

### v3.0 — 2026-07-12
- **Unruled-table support.** Falls back from pdfplumber's `lines` strategy to the
  `text` strategy on whitespace-aligned tables, gated on page digit density.
- **Structural header detection.** Header row is identified by a blank stub cell
  rather than by "non-numeric", which failed on year-only headers.
- **GATE 3 (`is_garbled`)** added: detects corruption artifacts (placeholder
  `col1:` headers, stranded suffixes, orphaned decimals) from rotated/curved
  source text, without keying on vocabulary.

### v2.1 — 2026-07-12
- Fixed a false positive in which GATE 1 fired on tables of contents: a numeric
  token must now contain a digit, so dot-leaders no longer score as numbers.
  Front matter is exempted structurally.

### v2.0
- First semantic gate (GATE 1, `is_orphan_number_block`): flags unlabelled
  digit-walls. Validated only against known-bad input — proven able to fail but
  never proven able to pass, which is why it over-fired. Later versions require
  both a positive and a negative control for every gate.

### v1
- Initial extraction. Reported all-green on a corpus that was semantically
  destroyed: financial tables were flattened into unlabelled numbers. This is the
  defect the whole project exists to prevent, preserved as
  `tests/fixtures/CORRUPTED_v1_output.txt`.
