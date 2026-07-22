# Generation eval — run notes

Companion to `gen_report.md`. Read this first. Nothing was committed. No prompt
or harness logic was edited.

## Environment / how it was run
- **Ollama model tag used:** `qwen2.5:3b-instruct` (verified present via `ollama list` /
  `/api/tags`: Q4_K_M, 3.1B, digest `357c53fb659c…`). Used for BOTH the answer and
  judge passes. Fallbacks (`qwen2.5:1.5b-instruct-q4_K_M`, `qwen2.5:0.5b-instruct`)
  were NOT used.
- **Ollama version:** `0.31.1`.
- **Python interpreter:** `/home/omodo/ml/.venv/bin/python` (sentence-transformers
  5.6.0, numpy 2.5.1). Note: the shell's `python` is 2.7 and the base `python3`
  (3.13) lacks sentence-transformers — neither can run the harness. The `.venv`
  referenced in the task was not actually active (`VIRTUAL_ENV` empty); the working
  venv is `ml/.venv`.
- **Offline:** ran with `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 CUDA_VISIBLE_DEVICES=""`.
  bge-small loaded from local HF cache; generation via local Ollama. No cloud calls.
- **Retriever:** committed `retriever.HybridRetriever` + `eval_retriever.load_chunks`
  reused unchanged (BM25 + bge-small-en-v1.5 + RRF k=60), k=3.

## Server diagnosis (the "bug to fix first")
The model tag was already correct; the earlier failures were the **server, not the model**.
- **Step A —** `curl /api/tags` responded and listed `qwen2.5:3b-instruct`. Server was
  already up this session (no restart needed). Earlier `Connection refused` = server
  simply not running at that time.
- **Step B —** one-shot `POST /api/chat` (`stream:false, temperature:0, seed:42`)
  returned valid JSON with `message.content`. **No 404** → this build serves `/api/chat`;
  **no harness adaptation to `/api/generate` was needed.**

## Fingerprint gate
`chunks_sme.fp.txt` and `questions_sme_v3.fp.json` both carry `592a602f845dce20`.
`verify_fingerprint` passed with no warning/abort. (Consistent with the known note that
the gate is a soft check — it only aborts on an explicit mismatch.)

## Timing (wall clock)
- **Answer pass:** 70.9 min generation time (script-reported), **~104 s/question** over 41
  (CPU-bound; first question included ~70 s cold model load).
- **Judge pass:** ~80 min wall clock, ~2 min/question (Layer B does one Qwen call each).
- Total end-to-end ≈ 2.5 h.

## Determinism — a real caveat (flagged, not papered over)
Config is correct: `temperature:0, seed:42, num_ctx:4096` on every call.
- **Within a warm process:** stable — 6/6 repeat calls of the same prompt were byte-identical.
- **Across a cold-call / model-reload boundary:** NOT bit-for-bit deterministic. Two
  back-to-back calls of the same prompt differed by one character (`banana` vs `Banana`).
  This is a known llama.cpp/Ollama CPU trait (numeric / batch state across loads), not a
  harness bug.
- **Consequence:** the eval ran as ONE continuous warm process, so `answers.jsonl` is
  internally consistent. But because the answer pass is resumable, a resume *after a
  process restart* could produce a marginally different answer for the boundary question.
  For a fully reproducible artifact, regenerate in a single warm run (which is what was done).

## Prompt-behaviour concerns (evidence — NOT acted on; proposed for your approval)
### 1. Answer model over-abstains on ANSWERABLE questions (the headline weakness)
14/35 answerable questions returned `NOT_IN_DOCUMENTS`. Of those, **9 are WRONG
abstentions** — the gold chunk WAS retrieved (usually at rank 1) and the fact is present
verbatim: **Q02, Q05, Q06, Q07, Q08, Q23, Q24, Q31, Q34**. The other 5 (Q17, Q19, Q27,
Q29, Q35) abstained because retrieval did not surface the gold chunk — those are defensible.
Worse, the model frequently emits the sentinel and then **answers correctly anyway**,
contradicting itself:
- Q05: `NOT_IN_DOCUMENTS Customer Support Email: support@kibuga.com` (email is in chunk 39, rank 1).
- Q23: `NOT_IN_DOCUMENTS [21] passage states that … registered office is at Muganzirwaza…` (cites the chunk it "doesn't have").
- Q08: `NOT_IN_DOCUMENTS [GENERAL KNOWLEDGE — from external sources]: …` — also a **malformed GK label** (spec is "not from the documents").
The 3B model appears to treat `NOT_IN_DOCUMENTS` as a reflexive preamble. This likely warrants
a grounding-prompt revision (e.g., "emit the sentinel ONLY when the answer is absent; never
both abstain and answer"). **Not changed — awaiting your approval per the task constraints.**

### 2. Unanswerable probes behaved correctly
All **6/6** unanswerable probes abstained (deterministic Layer A), and 5/6 added a
correctly-labelled `[GENERAL KNOWLEDGE — not from the documents]` note. This is the clean win.

### 3. LLM judge (Layer B) is unreliable on this task
The same 3B model as judge frequently **echoes `NOT_IN_DOCUMENTS` as its "verdict"** instead
of using its 4-label set (FAITHFUL/UNFAITHFUL/CORRECT_ABSTENTION/WRONG_ABSTENTION) — 8
answerable + 4 of the 6 probes. That is the main reason **A/B agreement is only 46%** and why
Layer B credits just 1/6 correct-abstentions while deterministic Layer A shows 6/6. Trust the
deterministic Layer A + the human-review queue; do not trust Layer B unsupervised. A stronger
judge model or constrained/JSON-schema decoding would help.

## Headline numbers (see gen_report.md for the full table)
- Answerable answered: **21/35** (14 abstained; 9 of them wrong).
- Faithfulness pass rate — Layer A (deterministic): **46%** (16/35); Layer B: 60% (21/35, unreliable).
- Abstention correctness on the 6 probes: **6/6** (Layer A); 1/6 (Layer B — judge echo bug).
- A/B judge agreement: **46%** (19/41). Human-review queue: **23** items.
