# Session report — chunk-dump parser byte-fidelity + fidelity gate

**Date:** 2026-07-23
**Branch:** `main` — pushed (`8f5b2da..a00cd51`)
**Scope:** deliberately narrow — the canonical chunk-dump parser and the gate
that protects it. No changes to ONNX, `src/core/index.py`, retrieval logic, or
any published metric.
**Status:** complete. 5 commits, full suite **67 passed**, no metric moved.

This report is self-contained and can be handed to Claude chat without repo
access.

---

## 1. One-paragraph summary

Every chunk-dump parser did `"\n".join(buf).strip()` (or `parts[i].strip()`),
which deleted a **real trailing space** present in `benchmarks/chunks_sme.txt`
for 2 of 47 chunks: **id 0** (`General_Terms…`, header `len=74`) and **id 22**
(`Privacy_Policy…`, header `len=52`). The corpus fingerprint stamped in the dump
(`c7f23f29b738b08d`) is computed over the **raw** bodies; the stripping parsers
reproduced `592a602f845dce20` instead. The file passed its own gate, then the
parser altered the text *after* the gate — the exact failure mode the gate
exists to prevent. Fixed all five parsers to be byte-faithful, added a **fatal
parser-fidelity gate** (recompute the fingerprint over parsed text, raise on
mismatch) as a new stdlib-only module `src/chunk_dump.py`, consolidated the five
parser copies into that one module, and corrected a labels file whose stored
fingerprint had been contaminated by the bug. **No retrieval metric changed** —
proven offline two ways (§5).

---

## 2. The defect, confirmed independently (task Step 1)

Reproduced from a throwaway pure-stdlib parser (no repo imports), using the
fingerprint formula copied verbatim from `ingest_sme.py` (`sha256("\n".join(
f"{i}\x00{text}"))[:16]`):

| quantity | value |
|---|---|
| stamped in `chunks_sme.txt` | `c7f23f29b738b08d` |
| recompute over **raw** bodies | `c7f23f29b738b08d` ✓ match |
| recompute over **`.strip()`ed** bodies | `592a602f845dce20` |

- Raw parse matches the header `len=` field for **all 47** chunks.
- Stripped parse loses exactly 1 char on **id 0** (74→73) and **id 22** (52→51).

So `ingest_sme.py` and the on-disk dump are mutually consistent and correct; the
parser was the sole defect.

---

## 3. Parser audit (task Step 2)

| # | parser | style | mutation before fix | reach |
|---|---|---|---|---|
| 1 | `eval_retriever.load_chunks` | line-based | `"\n".join(buf).strip()` | **canonical** — imported by eval_reranker, eval_sme_v3, gen_answer (retriever path), gen_judge |
| 2 | `label_questions.load_chunks` | line copy | `.strip()` ×2 | offline hand-tool |
| 3 | `gen_answer.load_chunks` | regex→dict | `parts[i].strip()` | legacy/unused — `main()` retrieves via eval_retriever |
| 4 | `gen_judge.load_chunks` | delegated→#1, regex fallback | fallback `.strip()` | gen_judge, grade_v3 |
| 5 | `autolabel.load_chunks` | line copy | `.strip()` ×2 | superseded by #2 |

Excluded: `gen_answer.v_prev.py` (`.v_prev` backup, not live); `norm()` helpers
elsewhere collapse whitespace but only on *comparison copies*, never the stored
chunk text.

### Two surprises found during the audit (reported before any edit)

**Surprise 1 — the fidelity gate already existed in 2 harnesses, and the bug was
actively breaking them.** `eval_sme_v3.py` and `eval_reranker.py` already
recompute `content_fingerprint(ids, texts)` over parsed text and **FATAL if it ≠
the dump's stamp**. Because `load_chunks` stripped, that recompute was `592a…`
while the stamp was `c7f2…`, so **both harnesses aborted** on `chunks_sme.txt`
("*Dump was tampered post-ingest*"). The strip bug was not latent there — it was
an outright breakage. The byte-faithful fix flips them FATAL→PASS. This refined
Step 4: **reuse** the existing fingerprint helpers rather than invent a gate.

**Surprise 2 — the bug was baked into a committed labels file.**
`questions_unanswerable.json` stored `corpus_fingerprint: 592a…` (the stripped
value), while the dump and both answerable sets carry the raw `c7f2…`. Someone
had recomputed the fingerprint *through the stripping parser* and committed it.
It was dead (no live path verifies the unanswerable set's fingerprint), so it
broke nothing, but it was the bug's contamination sitting in ground-truth
metadata.

Both surprises were reported and two decisions taken by the user: (a) implement
the gate as a **shared stdlib-only `chunk_dump.py`**; (b) **correct** the
unanswerable fingerprint in its own commit.

---

## 4. What shipped — 5 commits

All on `main`, pushed. Each was verified before commit.

### `dc23a00` fix(eval): byte-faithful chunk dump parsing
Removed `.strip()` from all five parsers. Line parsers now drop only the
writer's single trailing blank spacer line (`buf[:-1] if buf[-1]==""`); regex
parsers strip only the one trailing `"\n"` the split leaves. **Why:** the
trailing space on ids 0/22 is part of the text the fingerprint was computed
over; deleting it makes the parser reproduce a corpus the stamp was never taken
of. Verified: all five reproduce `c7f2`, both chunks retain their space, `len=`
matches for all 47. Files: eval_retriever, label_questions, autolabel,
gen_answer, gen_judge.

### `adcf997` feat(eval): fatal parser-fidelity check — *the real deliverable*
New `src/chunk_dump.py` (stdlib only). `verify_fidelity(texts, path)` recomputes
the fingerprint over parsed text and **raises `ParserFidelityError`** if it ≠
the dump's stamp. **Why stdlib-only:** the offline hand-tools (`label_questions`,
`autolabel`) import it and must not be coupled to numpy / the retrieval stack.
**Why fatal, not a warning:** a warning is discovered by hand months later; the
whole point is to catch a parser regression the instant it loads a dump. **Why
no-op on a stampless dump:** it declines to invent a check it has no reference
for; the callers' file-level gates still refuse a stampless corpus.
`verify_fidelity` is wired into every parser's load path;
`eval_retriever.load_chunks` was restructured to parse the **full** dump, gate
over the whole (unfiltered) corpus — the stamp is positional over every chunk in
order — then apply the optional `source` filter to the returned rows.

### `66369c2` test(eval): parser fidelity controls
`tests/test_chunk_parser.py`, 6 checks, auto-collected by the existing `pytest`
CI job:
- **KNOWN-BAD control (load-bearing):** a stripping parser reproduces `592a…` and
  **must** be rejected by `verify_fidelity`. A gate that never fires is a
  placebo; this proves it fires.
- **known-good:** the real dump parses to 47 chunks and reproduces `c7f2…`.
- **byte-fidelity:** chunks 0 and 22 retain their trailing space; `len(text)` ==
  header `len=` for all 47 (independent corroboration written by `ingest_sme.py`,
  not a tautology of the parser under test).
- **stampless dump:** the gate returns `''` without raising.
Core invariants run on the stdlib parser so they need no numpy; a separate test
cross-checks the canonical `eval_retriever` parser and skips if that stack is
unavailable.

### `4c65253` refactor(eval): consolidate dump parsers onto chunk_dump
The five parser copies collapse into one canonical `chunk_dump.parse_dump`
(byte-faithful, gated) and `chunk_dump.load_chunk_map` (the `{id: text}` shape).
`eval_retriever`/`label_questions`/`autolabel` → `parse_dump`;
`gen_answer`/`gen_judge` → `load_chunk_map` (gen_judge's regex fallback removed —
chunk_dump is stdlib, so the fallback's reason to exist no longer applies);
`eval_sme_v3.content_fingerprint`/`embedded_fingerprint` now delegate to
chunk_dump so the fingerprint formula lives in exactly one place (`eval_reranker`
imports those names; they keep working). **Why:** the bug had to be fixed in five
places; one canonical parser means the next such bug can exist only once and can
pass the gate only once. Dead `HEADER_RE` + its unused `import re` removed from
eval_retriever. No behaviour change — all five still reproduce `c7f2`.

### `a00cd51` fix(data): correct unanswerable set corpus_fingerprint
`questions_unanswerable.json` `_meta.corpus_fingerprint`: `592a… → c7f2…`. Dead
metadata today, so a hygiene/correctness fix with no behaviour change; the 6
probes are untouched. Its own commit, separable from the parser work.

---

## 5. Impact — no metric moved (task Step 6)

Proven offline, two independent ways (the real embedder is not available
offline, but the impact question is fully decidable without it):

1. **BM25** — the only two chunks that differ are 0 and 22 (document titles).
   Their `tokenize()` output (`_TOKEN_RE.findall(text.lower())`) is **identical**
   raw-vs-stripped — a trailing space produces no token. BM25-only rankings over
   **all 35** v3 questions: **0 changed**.
2. **Dense** — the vendored offline tokenizer (`src/tokenizer.json`) produces
   **identical token ids** for both affected chunks raw-vs-stripped, so the dense
   encoder's input is byte-unchanged → dense/hybrid rankings unchanged.

No published number changed, so none was touched. The one behavioural change is
positive and not a metric: `eval_sme_v3` / `eval_reranker`, which were
FATAL-aborting on `chunks_sme.txt`, now pass.

---

## 6. Current repo state

- **`main` pushed at `a00cd51`.** 5 new commits this task (on top of the day's
  earlier 9).
- **Full suite: 67 passed** (61 prior + 6 new). CI runs `pytest -v` and picks up
  the new test file with no extra wiring.
- **Fingerprint alignment now:** dump stamp, both answerable sets, and the
  unanswerable set all = `c7f23f29b738b08d`. The canonical parser reproduces it.
- **New module:** `src/chunk_dump.py` (172 lines) — the single source of truth
  for parsing + fingerprint gate. `src/core/index.py` untouched.
- **Working tree:** three untracked leftovers from the earlier session remain
  uncommitted by design — `benchmarks/CHUNK_ID_MIGRATION_REPORT.md`,
  `benchmarks/chunk_id_migration_map.json`, `docs/SESSION_REPORT_2026-07-23.md`
  (plus this report). None were touched by this task.

---

## 7. Open items / follow-ups

- **Verify on a fresh checkout in CI** that `eval_sme_v3` / `eval_reranker` now
  run green against `chunks_sme.txt` (they were latent-FATAL; the fix should have
  repaired them, but the reproducibility CI job does not currently invoke them).
- **`grade_v3.py`** points at `chunks_sme.fp.txt`, a filename absent from the
  repo — a stale one-off driver, not on any live path. Left as-is; worth a future
  cleanup.
- **`gen_answer.load_chunks`** was legacy/unused by `main()` even before this
  work; it now delegates to `chunk_dump`. Could be deleted outright later.

---

## 8. Standing lessons reinforced

- **A gate that validates the file must also validate that the parser reproduced
  it.** The corpus fingerprint guarded dump-vs-labels but nothing guarded
  parser-vs-dump; that gap is exactly how a `.strip()` survived. The fix closes
  it structurally, at load time, fatally.
- **A test that only passes on correct input proves nothing.** The load-bearing
  test here is the known-bad control: a stripping parser *must* be rejected.
- **Consolidate duplicated parsers.** The same one-line bug lived in five copies;
  one canonical implementation bounds the blast radius of the next one.
- **Report surprises, don't work around them.** Both the pre-existing latent-FATAL
  gate and the contaminated labels file were surfaced for a decision before any
  edit, not silently absorbed.
