# Proposed grounding-prompt revision (for approval — NOT yet applied)

Companion to `gen_report.md` / `gen_run_notes.md`. This proposes a change to the
`SYSTEM_PROMPT` in `gen_answer.py` (lines 46–59). Nothing in the harness has been
edited. The abstention token (`NOT_IN_DOCUMENTS`) and the GK label are kept
byte-identical so `gen_judge.py` (which keys on `ABSTAIN_SENTINEL` / `GK_MARKER`)
keeps working unchanged.

## The problem this fixes
On the 3B model, the current prompt produces **spurious abstention**: 9 of 35 answerable
questions returned `NOT_IN_DOCUMENTS` even though the gold chunk was retrieved (usually
rank 1) and the fact was present verbatim. Worse, the model routinely **emits the sentinel
and then answers correctly anyway** — a self-contradiction the harness cannot score cleanly.

Evidence (from `answers.jsonl`, this run):
- **Q05** → `NOT_IN_DOCUMENTS Customer Support Email: support@kibuga.com` (email is in chunk 39, rank 1)
- **Q23** → `NOT_IN_DOCUMENTS [21] passage states that … registered office is at Muganzirwaza…` (cites the very chunk it claims lacks the answer)
- **Q08** → `NOT_IN_DOCUMENTS [GENERAL KNOWLEDGE — from external sources]: …` (also a *malformed* label — spec is "not from the documents")
- Full list of wrong abstentions: **Q02, Q05, Q06, Q07, Q08, Q23, Q24, Q31, Q34**

### Root cause (why the wording invites this)
1. **The two outputs aren't stated as mutually exclusive.** Rule 3 says "if absent, begin
   with NOT_IN_DOCUMENTS"; nothing says "if present, you MUST answer and MUST NOT emit the
   sentinel." The model hedges by doing both.
2. **No positive answer instruction.** There is a strong rule for *abstaining* but no
   equally strong rule for *answering when the fact is present*.
3. **Fear-weighted framing biases toward abstention.** "Do not use outside knowledge" +
   "You will lose all credit for stating a fact that is not supported" pushes a small,
   risk-averse model to default to the sentinel — abstaining feels "safe."
4. **The GK label is shown once and not pinned as verbatim**, so the model paraphrases it
   ("from external sources").

## Proposed replacement for `SYSTEM_PROMPT`
Drop-in replacement for the string on lines 46–59 of `gen_answer.py`:

```python
SYSTEM_PROMPT = """You are a document assistant for a business. You answer questions using ONLY the numbered context passages provided by the user.

Follow this procedure for EVERY question:

STEP 1 — DECIDE. Read the passages and decide whether they contain the information needed to answer the question. Support counts even if it is partial, paraphrased, or spread across several passages: if the fact is stated in the passages in ANY wording, treat it as PRESENT.

STEP 2 — ACT. Your reply is EXACTLY ONE of the two forms below. They are mutually exclusive — never combine them.

  FORM A — the answer IS present in the passages:
    Answer the question directly and concisely, using only the passages. You MAY combine, order, and rephrase information across passages; synthesising is expected and good. Quote figures, names, emails, dates and terms exactly as they appear. In this case you MUST NOT write NOT_IN_DOCUMENTS anywhere in your reply.

  FORM B — the answer is NOT present in the passages:
    Begin your reply with this exact token, alone on the first line, with nothing before it:
    NOT_IN_DOCUMENTS
    Do not invent an answer, do not guess, and do not present outside knowledge as this business's fact or policy. After the token you MAY add ONE clearly-separated note, formatted with this label copied EXACTLY, character for character:
    [GENERAL KNOWLEDGE — not from the documents]: <your note>
    That note is general information only and must never be presented as this business's policy.

HARD RULES
- Never both abstain and answer. Emitting NOT_IN_DOCUMENTS asserts the passages lack the answer; if you can answer from the passages, you must NOT emit it.
- Never state a fact about this business that the passages do not support.
- Be concise. Do not pad."""
```

### What changed and why
| Change | Fixes |
|---|---|
| Explicit **decide → act** procedure with two **mutually exclusive** forms | The "sentinel + answer" self-contradiction (Q05, Q23, …) |
| Positive **FORM A** instruction ("answer directly … MUST NOT write NOT_IN_DOCUMENTS") | The missing "you must answer when it's present" rule |
| "Support counts even if partial / paraphrased / across passages … treat as PRESENT" | Over-abstention on paraphrase/multi-chunk questions (Q07, Q08, …) |
| Removed "You will lose all credit…" fear line; kept a plain no-hallucination rule | The bias that made abstaining feel "safe" |
| "label copied EXACTLY, character for character" | The malformed `— from external sources` label (Q08) |
| Token/label strings unchanged | `gen_judge.py` still detects abstention & GK notes |

(Optional, smaller nudge — leave `USER_TEMPLATE` as-is, or change its last line to:
`"Answer using only the context above. If the context contains the answer, give it directly; only if it truly does not, follow FORM B."`)

## How to validate the change (must re-run — determinism caveat applies)
This is a behavioural change, so the answer pass must be regenerated and re-judged. Do it
in **one warm process** (see the determinism note in `gen_run_notes.md`).

1. Preserve the current baseline so it isn't overwritten:
   `mv answers.jsonl answers.v1.jsonl && mv verdicts.jsonl verdicts.v1.jsonl && mv gen_report.md gen_report.v1.md`
2. Edit only the `SYSTEM_PROMPT` string in `gen_answer.py` (no other logic).
3. Re-run the answer pass fresh, then the judge, with the same commands as this run
   (`--fresh` on the answer pass).

**Success criteria**
- The 9 wrong abstentions (**Q02, Q05, Q06, Q07, Q08, Q23, Q24, Q31, Q34**) flip to
  grounded answers that match gold.
- **No** answer contains both `NOT_IN_DOCUMENTS` and a substantive answer.
- The 6 unanswerable probes (**U01–U06**) still abstain **6/6** — this is the key
  regression to watch (a less abstention-happy prompt could start hallucinating on them).
- GK notes, when present, use the exact `[GENERAL KNOWLEDGE — not from the documents]:` label.
- Layer A answerable PASS rate rises materially above the current 46%.

**Rollback:** restore the `SYSTEM_PROMPT` string and the `*.v1` files.

## Out of scope but related (separate decision)
The low **46% A/B agreement** is driven mainly by the **judge** (Layer B) echoing
`NOT_IN_DOCUMENTS` as its verdict instead of its 4-label set. That is a *judge-prompt* /
decoding issue, independent of the grounding prompt above. If you want, a companion fix
would be to constrain the judge to its four labels (e.g., reject/repair any verdict not in
the allowed set, or use JSON-schema-constrained decoding). Flagging only — not proposed in
detail here, since you asked specifically for the grounding-prompt revision.
