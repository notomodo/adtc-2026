#!/usr/bin/env python3
"""
gen_judge.py — Grading pass. Three layers, per the agreed design.

  LAYER A (deterministic anchor): cheap substring/heuristic checks. No model.
          Reproducible. This is the INDEPENDENT check that guards against the
          LLM judge sharing the answerer's blind spots.
  LAYER B (LLM-as-judge): Qwen grades each answer BUT must quote the supporting
          chunk span and give a one-line reason. The reasoning trace is the
          product, not just the label.
  LAYER C (reconciliation): compares A vs B. Agreement rate is reported as a
          MEASUREMENT of judge reliability. Disagreements are flagged for human
          review. All abstention (unanswerable) cases are flagged for human
          review regardless of agreement — highest-stakes, lowest-volume.

Consumes answers.jsonl from gen_answer.py. Also resumable.

USAGE
  python gen_judge.py \
      --answers answers.jsonl \
      --chunks ../chunks_sme_fp.txt \
      --model qwen2.5:3b-instruct \
      --out verdicts.jsonl \
      --report gen_report.md
"""
from __future__ import annotations
import argparse, json, re, sys, time
from pathlib import Path

ABSTAIN_SENTINEL = "NOT_IN_DOCUMENTS"
GK_MARKER = "[GENERAL KNOWLEDGE"

# ---------------------------------------------------------------------------
# LAYER A — deterministic checks. Returns a verdict WITHOUT any model.
# ---------------------------------------------------------------------------
def load_chunks(path: str) -> dict[int, str]:
    """Use the COMMITTED loader so chunk ids/text are identical to what the
    answerer saw. Falls back to a local regex only if the import fails."""
    import sys as _sys
    _sys.path.insert(0, str(Path(path).resolve().parent))
    try:
        from eval_retriever import load_chunks as rl
        ids, texts, _ = rl(path, None)
        return {cid: txt for cid, txt in zip(ids, texts)}
    except Exception:
        txt = Path(path).read_text()
        parts = re.split(
            r"\n-+\n\[(\d+)\] source=(\S+) type=\w+ page=(\d+) len=\d+ tokens=(\d+)\n-+\n", txt)
        chunks, i = {}, 1
        while i + 4 < len(parts):
            # Byte-faithful: strip only the one trailing "\n" the split leaves
            # (the writer's blank spacer), never .strip() -- see gen_answer.py.
            body = parts[i + 4]
            chunks[int(parts[i])] = body[:-1] if body.endswith("\n") else body
            i += 5
        return chunks


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()


def layer_a(rec: dict, chunks: dict[int, str]) -> dict:
    """Deterministic verdict.
    For ANSWERABLE (gold_chunks non-empty): PASS if the answer overlaps the gold
      chunk text materially AND did not wrongly abstain.
    For UNANSWERABLE (gold_chunks empty): PASS if the answer abstained
      (sentinel present) AND any general-knowledge part is properly labelled.
    """
    ans = rec["answer"]
    ans_n = norm(ans)
    abstained = ABSTAIN_SENTINEL.lower() in ans_n
    is_unanswerable = (rec["gold_chunks"] == [])

    if is_unanswerable:
        # correct behavior = abstain; if it added GK it must be labelled
        gk_present = GK_MARKER.lower() in ans.lower()
        # smuggled fact = made a definite claim without abstaining
        verdict = "PASS" if abstained else "FAIL"
        note = ("abstained" if abstained else "did NOT abstain — likely hallucination")
        if abstained and gk_present:
            note += " (+labelled GK note)"
        return {"a_verdict": verdict, "a_reason": note,
                "a_abstained": abstained, "a_gk_labelled": gk_present}

    # answerable: wrongly abstaining is a FAIL
    if abstained:
        return {"a_verdict": "FAIL", "a_reason": "abstained on an answerable question",
                "a_abstained": True, "a_gk_labelled": False}

    # material overlap with gold chunk(s): token-set containment heuristic.
    gold_text = " ".join(norm(chunks[g]) for g in rec["gold_chunks"] if g in chunks)
    gold_tokens = set(re.findall(r"[a-z0-9@.]+", gold_text))
    ans_tokens = set(re.findall(r"[a-z0-9@.]+", ans_n))
    # distinctive tokens: length>3 or containing digit/@ (dampen stopword noise)
    distinctive = {t for t in ans_tokens if len(t) > 3 or any(c.isdigit() or c == "@" for c in t)}
    overlap = distinctive & gold_tokens
    ratio = len(overlap) / max(1, len(distinctive))
    verdict = "PASS" if ratio >= 0.5 else ("WEAK" if ratio >= 0.3 else "FAIL")
    return {"a_verdict": verdict,
            "a_reason": f"gold-overlap ratio {ratio:.2f} ({len(overlap)}/{len(distinctive)} distinctive toks)",
            "a_abstained": False, "a_gk_labelled": False}


# ---------------------------------------------------------------------------
# LAYER B — LLM judge. Must quote evidence + reason. Deterministic decode.
# ---------------------------------------------------------------------------
JUDGE_SYSTEM = """You are a strict grading assistant. You decide whether an ANSWER is faithful to the CONTEXT passages that were available. You must be rigorous and cite evidence.

Output ONLY a JSON object, no other text:
{"verdict": "FAITHFUL" | "UNFAITHFUL" | "CORRECT_ABSTENTION" | "WRONG_ABSTENTION",
 "evidence": "<short quote from the context that supports your verdict, or 'none'>",
 "reason": "<one sentence>"}

Definitions:
- FAITHFUL: every factual claim in the answer is supported by the context; reasoning/synthesis over the context is allowed.
- UNFAITHFUL: the answer states a fact not supported by the context, or contradicts it (a hallucination).
- CORRECT_ABSTENTION: the context genuinely lacks the answer AND the answer abstained (said it's not in the documents). A clearly-labelled general-knowledge note after abstaining is still CORRECT_ABSTENTION.
- WRONG_ABSTENTION: the answer abstained but the context DID contain the answer, OR the answer presented outside knowledge as if it were from the documents."""

JUDGE_USER = """CONTEXT passages that were available to the answerer:
{context}

QUESTION: {question}

ANSWER to grade:
{answer}

Grade it. Output only the JSON object."""


def call_ollama(model, system, user, host):
    import urllib.request
    payload = {"model": model,
               "messages": [{"role": "system", "content": system},
                            {"role": "user", "content": user}],
               "stream": False,
               "options": {"temperature": 0, "seed": 42, "num_ctx": 4096}}
    req = urllib.request.Request(f"{host}/api/chat",
                                data=json.dumps(payload).encode(),
                                headers={"Content-Type": "application/json"})
    t = time.perf_counter()
    with urllib.request.urlopen(req, timeout=600) as r:
        out = json.loads(r.read())
    return out["message"]["content"].strip(), time.perf_counter() - t


def parse_judge(raw: str) -> dict:
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return {"verdict": "PARSE_ERROR", "evidence": "", "reason": raw[:120]}
    try:
        return json.loads(m.group(0))
    except Exception:
        return {"verdict": "PARSE_ERROR", "evidence": "", "reason": raw[:120]}


def layer_b(rec, chunks, model, host):
    context = "\n\n".join(f"[{j}] {chunks[j]}" for j in rec["retrieved"] if j in chunks)
    user = JUDGE_USER.format(context=context, question=rec["question"], answer=rec["answer"])
    raw, dt = call_ollama(model, JUDGE_SYSTEM, user, host)
    j = parse_judge(raw)
    j["_seconds"] = round(dt, 1)
    return j


# ---------------------------------------------------------------------------
# LAYER C — reconcile A vs B into an agreement flag + review queue.
# ---------------------------------------------------------------------------
def a_to_binary(a_verdict, is_unanswerable):
    # map A's verdict to pass/fail for agreement comparison
    if a_verdict in ("PASS",):
        return "PASS"
    if a_verdict in ("WEAK",):
        return "REVIEW"
    return "FAIL"


def b_to_binary(b_verdict, is_unanswerable):
    if b_verdict in ("FAITHFUL", "CORRECT_ABSTENTION"):
        return "PASS"
    if b_verdict in ("UNFAITHFUL", "WRONG_ABSTENTION"):
        return "FAIL"
    return "REVIEW"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", required=True)
    ap.add_argument("--chunks", required=True)
    ap.add_argument("--model", default="qwen2.5:3b-instruct")
    ap.add_argument("--host", default="http://localhost:11434")
    ap.add_argument("--out", default="verdicts.jsonl")
    ap.add_argument("--report", default="gen_report.md")
    ap.add_argument("--fresh", action="store_true")
    args = ap.parse_args()

    if args.fresh and Path(args.out).exists():
        Path(args.out).unlink()

    chunks = load_chunks(args.chunks)
    answers = [json.loads(l) for l in open(args.answers)]

    done = set()
    if Path(args.out).exists():
        for l in open(args.out):
            try: done.add(json.loads(l)["id"])
            except Exception: pass

    fout = open(args.out, "a")
    for i, rec in enumerate(answers, 1):
        if rec["id"] in done:
            continue
        is_un = (rec["gold_chunks"] == [])
        a = layer_a(rec, chunks)
        b = layer_b(rec, chunks, args.model, args.host)
        ab = a_to_binary(a["a_verdict"], is_un)
        bb = b_to_binary(b.get("verdict", ""), is_un)
        agree = (ab == bb)
        # review queue: disagreement, any WEAK/REVIEW, any parse error, ALL unanswerables
        needs_review = (not agree) or ("REVIEW" in (ab, bb)) or is_un \
                       or b.get("verdict") == "PARSE_ERROR"
        v = {**rec, **a, "b_verdict": b.get("verdict"), "b_evidence": b.get("evidence", ""),
             "b_reason": b.get("reason", ""), "a_bin": ab, "b_bin": bb,
             "agree": agree, "needs_review": needs_review}
        fout.write(json.dumps(v, ensure_ascii=False) + "\n")
        fout.flush()
        flag = "AGREE " if agree else "DISAGREE"
        print(f"  [{i:>2}/{len(answers)}] {rec['id']:<4} A={ab:<6} B={bb:<6} {flag}"
              f"{' [REVIEW]' if needs_review else ''}")
    fout.close()

    write_report(args.out, args.report)
    return 0


def write_report(verdicts_path, report_path):
    V = [json.loads(l) for l in open(verdicts_path)]
    ans = [v for v in V if v["gold_chunks"] != []]
    un = [v for v in V if v["gold_chunks"] == []]
    agree_rate = sum(v["agree"] for v in V) / max(1, len(V))
    review = [v for v in V if v["needs_review"]]

    def rate(items, key, val):
        return sum(1 for v in items if v[key] == val) / max(1, len(items))

    L = []
    p = L.append
    p("# Generation eval — faithfulness, abstention, judge reliability\n")
    p(f"- answers graded: **{len(V)}** ({len(ans)} answerable, {len(un)} unanswerable probes)")
    p(f"- **A/B judge agreement rate: {agree_rate:.0%}**  "
      f"(the measured reliability of the LLM judge on this task)")
    p(f"- flagged for human review: **{len(review)}** "
      f"(disagreements + all abstention probes + weak/parse-error cases)\n")

    p("## Layer A (deterministic) headline")
    p(f"- answerable PASS: {rate(ans,'a_bin','PASS'):.0%}  "
      f"FAIL: {rate(ans,'a_bin','FAIL'):.0%}  REVIEW(weak): {rate(ans,'a_bin','REVIEW'):.0%}")
    p(f"- unanswerable correct-abstention (A): {sum(v['a_verdict']=='PASS' for v in un)}/{len(un)}\n")

    p("## Layer B (LLM judge) headline")
    fb = sum(v['b_verdict']=='FAITHFUL' for v in ans)
    uf = sum(v['b_verdict']=='UNFAITHFUL' for v in ans)
    p(f"- answerable FAITHFUL: {fb}/{len(ans)}   UNFAITHFUL: {uf}/{len(ans)}")
    p(f"- unanswerable CORRECT_ABSTENTION (B): "
      f"{sum(v['b_verdict']=='CORRECT_ABSTENTION' for v in un)}/{len(un)}\n")

    p("## HUMAN REVIEW QUEUE (read these by hand)")
    p("| id | stratum | A | B | agree | why flagged |")
    p("|----|---------|---|---|-------|-------------|")
    for v in review:
        why = ("abstention probe" if v["gold_chunks"]==[] else
               ("A/B disagree" if not v["agree"] else "weak/parse"))
        p(f"| {v['id']} | {v['stratum']} | {v['a_bin']} | {v['b_bin']} | "
          f"{'yes' if v['agree'] else 'NO'} | {why} |")

    p("\n## Full verdicts")
    p("| id | stratum | A verdict | B verdict | B evidence (quote) |")
    p("|----|---------|-----------|-----------|--------------------|")
    for v in V:
        ev = (v.get("b_evidence","") or "")[:60].replace("|","/")
        p(f"| {v['id']} | {v['stratum']} | {v['a_verdict']} | {v.get('b_verdict')} | {ev} |")

    Path(report_path).write_text("\n".join(L))
    print(f"\nreport -> {report_path}")
    print(f"A/B agreement: {agree_rate:.0%} | review queue: {len(review)} items")


if __name__ == "__main__":
    raise SystemExit(main())
