# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Prior to this file the
history lived only in the module docstrings of `extract.py` and
`verify_extraction.py`; it is consolidated here so the repository is the single
source of truth.

## [Unreleased]

### Added
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
