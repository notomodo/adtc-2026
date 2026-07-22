#!/usr/bin/env python3
"""One-off driver: apply gen_judge.layer_a identically to v1, v2, v3 answer sets
in a single execution so the three sets of numbers are genuinely comparable.
Layer A only — no LLM judge, per task instructions."""
import json
from pathlib import Path
from gen_judge import layer_a, load_chunks, ABSTAIN_SENTINEL, GK_MARKER

CHUNKS_PATH = "chunks_sme.fp.txt"
RUNS = {
    "v1": "answers.v1.jsonl",
    "v2": "answers.new.jsonl",
    "v3": "answers.v3.jsonl",
}
STRATA = ["exact_fact", "paraphrase", "near_miss", "prose", "multi_chunk"]

chunks = load_chunks(CHUNKS_PATH)

all_results = {}
summary = {}

for tag, path in RUNS.items():
    recs = [json.loads(l) for l in open(path)]
    verdicts = []
    for rec in recs:
        a = layer_a(rec, chunks)
        v = {
            "id": rec["id"],
            "stratum": rec["stratum"],
            "gold_chunks": rec["gold_chunks"],
            "is_unanswerable": rec["gold_chunks"] == [],
            "answer": rec["answer"],
            **a,
        }
        verdicts.append(v)
    all_results[tag] = verdicts

    ans = [v for v in verdicts if not v["is_unanswerable"]]
    un = [v for v in verdicts if v["is_unanswerable"]]

    n_pass = sum(1 for v in ans if v["a_verdict"] == "PASS")
    n_abstained_answerable = sum(1 for v in ans if v["a_abstained"])
    n_laundered = sum(
        1 for v in verdicts
        if ABSTAIN_SENTINEL.lower() in v["answer"].lower()
        and len(v["answer"]) - len(ABSTAIN_SENTINEL) > 25
    )
    n_gk_label = sum(1 for v in verdicts if GK_MARKER.lower() in v["answer"].lower())
    probes_correct = sum(1 for v in un if v["a_verdict"] == "PASS")
    probe_detail = {v["id"]: v["a_verdict"] for v in un}

    per_stratum = {}
    for s in STRATA:
        s_ans = [v for v in ans if v["stratum"] == s]
        s_pass = sum(1 for v in s_ans if v["a_verdict"] == "PASS")
        per_stratum[s] = {"pass": s_pass, "total": len(s_ans)}

    summary[tag] = {
        "answerable_total": len(ans),
        "answerable_pass": n_pass,
        "answerable_pass_pct": round(100 * n_pass / max(1, len(ans)), 1),
        "answerable_abstained": n_abstained_answerable,
        "per_stratum": per_stratum,
        "laundered_abstention_count": n_laundered,
        "gk_label_count": n_gk_label,
        "unanswerable_total": len(un),
        "unanswerable_probes_correct": probes_correct,
        "probe_detail": probe_detail,
    }

out = {"summary": summary, "verdicts": all_results}
Path("layerA_verdicts.v3.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))

print("=" * 70)
for tag in RUNS:
    s = summary[tag]
    print(f"\n--- {tag} ---")
    print(f"answerable PASS: {s['answerable_pass']}/{s['answerable_total']} "
          f"({s['answerable_pass_pct']}%)")
    print(f"answerable abstained (wrongly): {s['answerable_abstained']}")
    for st, d in s["per_stratum"].items():
        print(f"  {st:<12} {d['pass']}/{d['total']}")
    print(f"laundered abstention (sentinel + >25 extra chars): {s['laundered_abstention_count']}")
    print(f"answers containing [GENERAL KNOWLEDGE label: {s['gk_label_count']}")
    print(f"abstention probes correct: {s['unanswerable_probes_correct']}/{s['unanswerable_total']}  "
          f"detail={s['probe_detail']}")
print("\nSaved -> layerA_verdicts.v3.json")
