#!/usr/bin/env python3
"""
gen_answer.py — Generation pass (LAYER: the model under test).

Runs Qwen2.5-3B-Instruct over the 35 answerable questions + 6 unanswerable probes,
using the LOCKED retriever (BM25 + bge-small + RRF, k=60) to fetch top-k chunks,
then generates a grounded answer under a strict-grounding-with-labelled-fallback
prompt.

Design decisions baked in:
  * k = 3 chunks into context (confirmed defensible on the v3 set).
  * Grounding policy = "abstain by default; general knowledge only as a
    clearly-labelled separate note" (user's choice).
  * temperature = 0, fixed seed  -> deterministic, reproducible.
  * RESUMABLE: every answer is checkpointed to answers.jsonl as it completes;
    re-running skips questions already done. A 90-min run that dies at Q30
    resumes from Q30.
  * This script ONLY answers. Judging is a separate script (gen_judge.py) so the
    slow answer pass runs once and can be inspected before judging.

Offline: talks to a local Ollama server (no network, no API key).

USAGE
  python gen_answer.py \
      --questions ../questions_sme_v3_fp.json \
      --unanswerable questions_unanswerable.json \
      --chunks ../chunks_sme_fp.txt \
      --model qwen2.5:3b-instruct \
      --k 3 \
      --out answers.jsonl

  # resume after interruption: just run the same command again.
  # force a clean re-run: add --fresh (deletes the checkpoint first).
"""
from __future__ import annotations
import argparse, json, os, re, sys, time, hashlib
from pathlib import Path

# ---------------------------------------------------------------------------
# Grounding prompt — the accuracy mechanism. This is the heart of the system.
# Policy: answer ONLY from the provided context; if the context does not
# contain the answer, abstain with the exact sentinel, THEN optionally add a
# clearly-delimited general-knowledge note. The note must never be presented as
# if it came from the documents.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a document assistant for a business. You answer questions using ONLY the numbered context passages provided by the user.

Rules, in priority order:
1. Answer strictly from the context passages. Do not use outside knowledge to state facts about this business.
2. You MAY reason over the passages: combine, order, and rephrase information that IS present. Synthesising across several passages is expected and good.
3. If the context does NOT contain the answer, you MUST begin your reply with exactly:
   NOT_IN_DOCUMENTS
   Do not invent an answer. Do not guess. Do not fill the gap with general knowledge as if it were fact about this business.
4. ONLY after a NOT_IN_DOCUMENTS abstention, you MAY add a general note if it would help, formatted exactly as:
   [GENERAL KNOWLEDGE — not from the documents]: <your note>
   This note must be clearly separate and must never be presented as this business's policy.
5. Be concise. Do not pad. Quote figures and terms exactly as they appear in the context.

You will lose all credit for stating a fact that is not supported by the context."""

USER_TEMPLATE = """Context passages:
{context}

Question: {question}

Answer using only the context above, following the rules."""


def load_chunks(path: str) -> dict[int, str]:
    """Parse the fingerprinted chunk dump into {index: body_text}."""
    txt = Path(path).read_text()
    parts = re.split(
        r"\n-+\n\[(\d+)\] source=(\S+) type=\w+ page=(\d+) len=\d+ tokens=(\d+)\n-+\n",
        txt,
    )
    chunks: dict[int, str] = {}
    i = 1
    while i + 4 < len(parts):
        chunks[int(parts[i])] = parts[i + 4].strip()
        i += 5
    if not chunks:
        sys.exit("FATAL: parsed 0 chunks — dump format changed; fix the parser.")
    return chunks


def verify_fingerprint(chunks_path: str, questions_meta: dict) -> None:
    """Fatal gate: the dump's fingerprint must match the question set's."""
    want = questions_meta.get("corpus_fingerprint")
    got = None
    for line in Path(chunks_path).read_text().splitlines():
        m = re.search(r"corpus_fingerprint:\s*(\S+)", line)
        if m:
            got = m.group(1)
            break
    if want and got and want != got:
        sys.exit(f"FATAL fingerprint mismatch: questions={want} dump={got}")
    if not got:
        print("WARN: no fingerprint found in dump — proceeding unverified", file=sys.stderr)


def build_retriever(chunks_path: str, k: int, embed_model: str):
    """Import the COMMITTED retriever and build the LOCKED hybrid exactly as
    eval_retriever.py does it. Do not reimplement retrieval here.

    Mirrors the committed usage:
      ids, texts, metas = load_chunks(dump, source=None)
      enc = SentenceTransformerEncoder(embed_model)
      r = HybridRetriever(texts, encoder=enc)          # BM25 + dense + RRF k=60
      hits = r.search(question, top_k)                 # -> list[Hit]
      chunk_id = pos2id[hit.chunk_id]                  # position -> real chunk id
    """
    sys.path.insert(0, str(Path(chunks_path).resolve().parent))
    try:
        from retriever import HybridRetriever, SentenceTransformerEncoder
        from eval_retriever import load_chunks as rl
    except Exception as e:
        sys.exit(
            "FATAL: could not import the committed retriever "
            f"(retriever.HybridRetriever / SentenceTransformerEncoder / "
            f"eval_retriever.load_chunks): {e}\n"
            "This harness must reuse the locked pipeline, not a lookalike."
        )
    ids, texts, _metas = rl(chunks_path, None)          # 3-tuple, source=None
    pos2id = {pos: cid for pos, cid in enumerate(ids)}  # position -> real chunk id
    try:
        enc = SentenceTransformerEncoder(embed_model)   # bge-small, offline
    except Exception as e:
        sys.exit(f"FATAL: could not load embedder '{embed_model}': {e}")
    r = HybridRetriever(texts, encoder=enc)             # LOCKED hybrid, RRF k=60 default

    def retrieve(question: str) -> list[int]:
        hits = r.search(question, top_k=k)              # list[Hit], best-first
        return [pos2id[h.chunk_id] for h in hits]       # -> real chunk ids

    # also return the id->text map so the caller can render context by real id
    id2text = {cid: txt for cid, txt in zip(ids, texts)}
    return retrieve, id2text


def call_ollama(model: str, system: str, user: str, host: str) -> tuple[str, float]:
    """Deterministic local generation. Returns (text, seconds)."""
    import urllib.request
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "options": {"temperature": 0, "seed": 42, "num_ctx": 4096},
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{host}/api/chat", data=data, headers={"Content-Type": "application/json"}
    )
    t = time.perf_counter()
    with urllib.request.urlopen(req, timeout=600) as resp:
        out = json.loads(resp.read())
    dt = time.perf_counter() - t
    return out["message"]["content"].strip(), dt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--questions", required=True)
    ap.add_argument("--unanswerable", required=True)
    ap.add_argument("--chunks", required=True)
    ap.add_argument("--model", default="qwen2.5:3b-instruct")
    ap.add_argument("--embed-model", default="BAAI/bge-small-en-v1.5",
                    help="dense embedder for the locked hybrid (must match the eval)")
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--host", default="http://localhost:11434")
    ap.add_argument("--out", default="answers.jsonl")
    ap.add_argument("--fresh", action="store_true", help="delete checkpoint and restart")
    args = ap.parse_args()

    if args.fresh and Path(args.out).exists():
        Path(args.out).unlink()

    qdoc = json.load(open(args.questions))
    udoc = json.load(open(args.unanswerable))
    verify_fingerprint(args.chunks, qdoc.get("_meta", {}))

    retrieve, id2text = build_retriever(args.chunks, args.k, args.embed_model)

    questions = qdoc["questions"] + udoc["questions"]

    # resume: which ids are already done?
    done: set[str] = set()
    if Path(args.out).exists():
        for line in open(args.out):
            try:
                done.add(json.loads(line)["id"])
            except Exception:
                pass
    if done:
        print(f"resuming — {len(done)} already done, {len(questions)-len(done)} to go")

    fout = open(args.out, "a")
    total_gen = 0.0
    for i, q in enumerate(questions, 1):
        if q["id"] in done:
            continue
        top = retrieve(q["question"])[: args.k]
        context = "\n\n".join(f"[{j}] {id2text[j]}" for j in top if j in id2text)
        user = USER_TEMPLATE.format(context=context, question=q["question"])
        try:
            answer, dt = call_ollama(args.model, SYSTEM_PROMPT, user, args.host)
        except Exception as e:
            print(f"  {q['id']}: generation error: {e}", file=sys.stderr)
            return 2
        total_gen += dt
        rec = {
            "id": q["id"],
            "stratum": q["stratum"],
            "question": q["question"],
            "gold_chunks": q["gold_chunks"],
            "gold_answer": q.get("answer", ""),
            "retrieved": top,
            "answer": answer,
            "gen_seconds": round(dt, 1),
            "origin": q.get("origin", ""),
        }
        fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
        fout.flush()
        print(f"  [{i:>2}/{len(questions)}] {q['id']:<4} {dt:5.1f}s  {q['answer'][:0]}"
              f"{'ABSTAIN?' if q['gold_chunks']==[] else ''} {q['question'][:48]}")

    fout.close()
    print(f"\nDONE. generation time this run: {total_gen/60:.1f} min "
          f"({total_gen/max(1,len(questions)-len(done)):.0f}s/q avg)")
    print(f"answers -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
