#!/usr/bin/env python3
"""Full-corpus end-to-end benchmark harness — performance AND accuracy.

WHAT THIS MEASURES (read this before quoting any number)
========================================================
This driver runs the SHIPPING pipeline (retrieve → ground → Qwen synthesis)
over the whole question set and records, per question, both cost (latency,
tokens/sec, RAM) and correctness. The headline accuracy figure it produces is:

    RAG END-TO-END, Layer-A automated pass rate.

Three things it is emphatically NOT — do not conflate them:
  * It is NOT S_acc. S_acc is the profiler's lm_eval MCQ score on the bare
    GGUF. This number folds in retrieval and grounding; it cannot be compared
    to, or called, "leaderboard accuracy."
  * The grader is the EXISTING Layer A token-overlap heuristic
    (gen_judge.layer_a), reused verbatim — no new grader. Layer A has
    CONFIRMED false positives (the R5 / Q19 finding), so this pass rate is a
    KNOWN OVERESTIMATE of true faithfulness. Every surface that prints it
    states that caveat.
  * The gold_chunk_hit rate here is a retrieval sanity signal, NOT the
    DECISION-002 R@k (which was measured against clean gold with a different
    method). Cite DECISION-002 separately; do not recompute it from this.

Generation metrics come from OLLAMA'S OWN response JSON (eval_count /
eval_duration etc.), never wall clock — wall clock folds in HTTP, encoder init
and streaming overhead. Generation params are untouched (temp 0, seed 42,
num_ctx 4096): this is metrics-only instrumentation on top of the exact
benchmarked generation.

WHY INCREMENTAL WRITES
======================
The full sweep is ~60–100 min of CPU-pinned generation. Every question's
result is written to the .jsonl and flushed the instant it completes, and the
run resumes from whatever is already there. One question crashing (or the box
losing power at minute 88) must never void the rest — the summary notes any
question that failed rather than silently dropping it.

RUNTIME DEPS ONLY
=================
stdlib + the app package. /proc/meminfo and Ollama's JSON supply every metric;
no psutil, no torch, nothing new. Intended to run inside .venv-runtime.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

# --- make the app package + the flat src modules importable ----------------
# scripts/ sits beside src/; add src/ so `app.pipeline`, `gen_judge` and the
# canonical chunk loader resolve whether or not the package is pip-installed.
_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
for _p in (str(_SRC), str(_ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app.pipeline import Pipeline  # noqa: E402
from gen_judge import layer_a, load_chunks  # noqa: E402 -- the EXISTING Layer A grader, verbatim

# Answerable strata, in report order. Unanswerable probes are scored separately
# (abstention), never mixed into the pass rate.
ANSWERABLE_STRATA = ["exact_fact", "paraphrase", "near_miss", "multi_chunk", "prose"]

DEFAULT_QUESTIONS = [
    _ROOT / "data" / "questions" / "questions_sme_v3.json",
    _ROOT / "data" / "questions" / "questions_unanswerable.json",
]
DEFAULT_CHUNKS = _ROOT / "benchmarks" / "chunks_sme.txt"
DEFAULT_MAP = _ROOT / "benchmarks" / "chunk_id_migration_map.json"

# The known Layer-A overestimate caveat, stated wherever the pass rate appears.
R5_CAVEAT = (
    "Layer-A automated pass rate — a KNOWN OVERESTIMATE. The grader is a "
    "token-overlap heuristic with confirmed false positives (the R5 / Q19 "
    "finding); treat this as an upper bound on faithfulness, not ground truth."
)


# =============================================================================
# question loading
# =============================================================================


def load_questions(paths: list[Path]) -> list[dict]:
    """Flatten every question set into one list, preserving order. Answerable
    and unanswerable are distinguished by gold_chunks == [] (the same signal
    gen_judge.layer_a uses), so the two files can be concatenated safely."""
    out: list[dict] = []
    for p in paths:
        obj = json.loads(Path(p).read_text())
        out.extend(obj["questions"])
    return out


# =============================================================================
# gold-chunk mapping (positional int -> stable id)  ·  retrieval sanity only
# =============================================================================


def load_gold_map(path: Path) -> dict[str, str]:
    """migrate_chunk_ids' verified positional->stable map. Keys are stringified
    integers ("36"), values are stable ids ("f232e5d3:0")."""
    return json.loads(Path(path).read_text())


def gold_chunk_hit(gold_positional: list[int], retrieved_ids: list[str],
                   gold_map: dict[str, str]) -> tuple[bool | None, list[str], list[int]]:
    """Did retrieval surface any gold chunk?

    Translates POSITIONAL gold ids to STABLE ids via the verified map, then
    tests membership in the retrieved (stable) ids. Returns
    (hit, mapped_stable_ids, unmapped_positional).

    Unanswerable questions have no gold, so the notion doesn't apply -> None.
    An unmappable gold id is a DATA problem: it is surfaced in
    `unmapped_positional` and the hit is computed only over the ids that DID
    map — it is never silently scored as a hit or a miss.
    """
    if not gold_positional:
        return None, [], []
    mapped: list[str] = []
    unmapped: list[int] = []
    for g in gold_positional:
        stable = gold_map.get(str(g))
        if stable is None:
            unmapped.append(g)
        else:
            mapped.append(stable)
    retrieved = set(retrieved_ids)
    hit = any(m in retrieved for m in mapped) if mapped else None
    return hit, mapped, unmapped


# =============================================================================
# generation metrics from Ollama's own counters (never wall clock)
# =============================================================================


def derive_gen_metrics(gen_stats: dict | None) -> dict:
    """Turn Ollama's raw ns/count fields into tokens/sec. Missing or zero
    durations yield None (not a divide-by-zero crash) so one odd response can't
    void the run."""
    if not gen_stats:
        return {"generation_tps": None, "prompt_tps": None, **{k: None for k in
                ("eval_count", "eval_duration", "prompt_eval_count", "prompt_eval_duration")}}

    def tps(count, dur_ns):
        if not count or not dur_ns:
            return None
        return round(count / (dur_ns / 1e9), 2)

    ec = gen_stats.get("eval_count")
    ed = gen_stats.get("eval_duration")
    pc = gen_stats.get("prompt_eval_count")
    pd = gen_stats.get("prompt_eval_duration")
    return {
        "eval_count": ec, "eval_duration": ed,
        "prompt_eval_count": pc, "prompt_eval_duration": pd,
        "total_duration": gen_stats.get("total_duration"),
        "load_duration": gen_stats.get("load_duration"),
        "generation_tps": tps(ec, ed),
        "prompt_tps": tps(pc, pd),
    }


# =============================================================================
# RAM sampler — model lives in the OLLAMA process, not the Python CLI
# =============================================================================


class RamSampler(threading.Thread):
    """Polls system used-memory AND the ollama server-process RSS every
    `interval` s, keeping the running peak of each. Sampling only the Python CLI
    would miss the ~2 GB model (it is resident in the ollama runner process),
    producing a meaningless number — so we sum RSS across every ollama-named
    process."""

    def __init__(self, interval: float = 0.5):
        super().__init__(daemon=True)
        self.interval = interval
        self._stop = threading.Event()
        self.peak_used_mb = 0.0
        self.peak_ollama_rss_mb = 0.0

    @staticmethod
    def _system_used_mb() -> float:
        info = {}
        for line in Path("/proc/meminfo").read_text().splitlines():
            k, _, rest = line.partition(":")
            info[k] = float(rest.strip().split()[0])  # kB
        return (info["MemTotal"] - info["MemAvailable"]) / 1024.0

    @staticmethod
    def ollama_rss_mb() -> float:
        """Sum VmRSS over every process whose comm mentions ollama (server +
        model runner). Pure /proc, no psutil."""
        total_kb = 0.0
        proc = Path("/proc")
        for entry in proc.iterdir():
            if not entry.name.isdigit():
                continue
            try:
                comm = (entry / "comm").read_text().strip()
                if "ollama" not in comm.lower():
                    continue
                for line in (entry / "status").read_text().splitlines():
                    if line.startswith("VmRSS:"):
                        total_kb += float(line.split()[1])
                        break
            except (FileNotFoundError, ProcessLookupError, PermissionError):
                continue  # process vanished mid-scan; ignore
        return total_kb / 1024.0

    def sample_once(self) -> tuple[float, float]:
        return self._system_used_mb(), self.ollama_rss_mb()

    def run(self):
        while not self._stop.is_set():
            used, oll = self.sample_once()
            self.peak_used_mb = max(self.peak_used_mb, used)
            self.peak_ollama_rss_mb = max(self.peak_ollama_rss_mb, oll)
            self._stop.wait(self.interval)

    def stop(self):
        self._stop.set()


# =============================================================================
# the run
# =============================================================================


def already_done(results_path: Path) -> set[str]:
    """Ids already written — the resume set. A crashed run picks up here."""
    done: set[str] = set()
    if results_path.exists():
        for line in results_path.read_text().splitlines():
            try:
                done.add(json.loads(line)["id"])
            except Exception:
                pass
    return done


def run_benchmark(args) -> Path:
    questions = load_questions([Path(p) for p in args.questions])
    chunks = load_chunks(str(args.chunks))          # positional-keyed, for the grader
    gold_map = load_gold_map(Path(args.map))        # positional -> stable, for gold_chunk_hit

    results_path = Path(args.results)
    results_path.parent.mkdir(parents=True, exist_ok=True)
    done = already_done(results_path)
    if done:
        print(f"[resume] {len(done)} question(s) already in {results_path.name}; "
              f"skipping those.", flush=True)

    pipe = Pipeline(index_dir=Path(args.index_dir), model=args.model, host=args.host)

    # --- baseline RAM: evict the model first so the first question pays load ---
    # The plan wants this run to capture the model LOAD, so start from a state
    # where Qwen is NOT resident and record the floor before anything runs.
    print(f"[ram] evicting {args.model} so the first question pays the load cost…", flush=True)
    try:
        subprocess.run(["ollama", "stop", args.model], timeout=30,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        print(f"[ram] warning: could not run 'ollama stop' ({e}); baseline may "
              f"include a resident model.", flush=True)
    time.sleep(2.0)  # let the runner release its RSS

    sampler = RamSampler(interval=0.5)
    baseline_used_mb, baseline_ollama_rss_mb = sampler.sample_once()
    print(f"[ram] baseline system used: {baseline_used_mb:.0f} MB "
          f"(ollama resident: {baseline_ollama_rss_mb:.0f} MB)", flush=True)
    sampler.start()

    n_total = len(questions)
    failures: list[dict] = []
    t_run = time.perf_counter()
    try:
        with results_path.open("a") as fout:
            for i, q in enumerate(questions, 1):
                qid = q["id"]
                if qid in done:
                    continue
                print(f"\n[{i:>2}/{n_total}] {qid} ({q['stratum']}): {q['question'][:70]}", flush=True)
                try:
                    rec = _run_one(pipe, q, chunks, gold_map, k=args.k)
                except Exception as e:  # noqa: BLE001 -- one bad question must not void the run
                    failures.append({"id": qid, "error": repr(e)})
                    rec = {"id": qid, "stratum": q.get("stratum"), "question": q.get("question"),
                           "error": repr(e), "failed": True}
                    print(f"      FAILED: {e!r} (recorded, continuing)", flush=True)
                fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                fout.flush()
                if not rec.get("failed"):
                    _print_one_line(rec)
    finally:
        sampler.stop()
        sampler.join(timeout=2.0)

    peak = {
        "baseline_used_mb": round(baseline_used_mb, 1),
        "baseline_ollama_rss_mb": round(baseline_ollama_rss_mb, 1),
        "peak_used_mb": round(sampler.peak_used_mb, 1),
        "peak_ollama_rss_mb": round(sampler.peak_ollama_rss_mb, 1),
        "delta_mb": round(sampler.peak_used_mb - baseline_used_mb, 1),
    }
    wall_total_s = round(time.perf_counter() - t_run, 1)
    summary_path = write_summary(results_path, args, peak, wall_total_s, failures)
    print(f"\n[done] {n_total} question(s) in {wall_total_s:.0f}s "
          f"({len(failures)} failed). Peak system RAM {peak['peak_used_mb']:.0f} MB "
          f"(+{peak['delta_mb']:.0f} over baseline), ollama RSS {peak['peak_ollama_rss_mb']:.0f} MB.", flush=True)
    print(f"[done] per-question:  {results_path}", flush=True)
    print(f"[done] summary:       {summary_path}", flush=True)
    return summary_path


def _run_one(pipe: Pipeline, q: dict, chunks: dict, gold_map: dict, k: int) -> dict:
    """One question, fully instrumented. Returns the jsonl record."""
    t0 = time.perf_counter()
    result = pipe.answer(q["question"], k=k)  # no streaming callbacks: metrics, not display
    wall_clock_s = round(time.perf_counter() - t0, 3)

    retrieved_ids = [h.id for h in result.hits]
    # Layer A grades in POSITIONAL space (gold_chunks + the positional chunk map),
    # exactly as gen_judge/grade_v3 do — no stable mapping involved here.
    a = layer_a({"answer": result.answer, "gold_chunks": q["gold_chunks"]}, chunks)
    hit, mapped_gold, unmapped_gold = gold_chunk_hit(q["gold_chunks"], retrieved_ids, gold_map)
    gen = derive_gen_metrics(result.gen_stats)

    return {
        "id": q["id"],
        "stratum": q["stratum"],
        "question": q["question"],
        "expected_answer": q.get("answer"),
        "answer_text": result.answer,
        "abstained": result.abstained,
        "is_unanswerable": q["gold_chunks"] == [],
        # accuracy
        "layerA_verdict": a["a_verdict"],
        "layerA_reason": a.get("a_reason"),
        # retrieval
        "retrieved": [
            {"id": h.id, "filename": h.filename, "page": h.page,
             "bm25_rank": h.bm25_rank, "dense_rank": h.dense_rank,
             "rrf_score": round(h.rrf_score, 6)}
            for h in result.hits
        ],
        "gold_chunks_positional": q["gold_chunks"],
        "gold_chunks_stable": mapped_gold,
        "gold_chunks_unmapped": unmapped_gold,   # surfaced, never papered over
        "gold_chunk_hit": hit,
        "retrieval_timings_ms": result.timings,
        # performance
        "encoder_init_s": round(result.encoder_init_s, 3),
        "retrieval_s": round(result.retrieval_s, 4),
        "generation_s": round(result.generation_s, 3),
        "wall_clock_s": wall_clock_s,
        "gen_stats": result.gen_stats,   # raw Ollama counters, for auditability
        **gen,                            # derived tps + surfaced counts/durations
        "failed": False,
    }


def _print_one_line(rec: dict) -> None:
    tps = rec.get("generation_tps")
    tps_s = f"{tps:.1f} tok/s" if tps else "n/a"
    hit = rec.get("gold_chunk_hit")
    hit_s = "-" if hit is None else ("hit" if hit else "MISS")
    print(f"      A={rec['layerA_verdict']:<5} abstained={str(rec['abstained']):<5} "
          f"gold={hit_s:<4} gen={rec['generation_s']:.1f}s ({tps_s})", flush=True)


# =============================================================================
# aggregation
# =============================================================================


def _stats_block(values: list[float]) -> dict:
    vals = [v for v in values if v is not None]
    if not vals:
        return {"n": 0, "mean": None, "median": None, "min": None, "max": None}
    return {
        "n": len(vals),
        "mean": round(statistics.mean(vals), 2),
        "median": round(statistics.median(vals), 2),
        "min": round(min(vals), 2),
        "max": round(max(vals), 2),
    }


def write_summary(results_path: Path, args, peak: dict, wall_total_s: float,
                  failures: list[dict]) -> Path:
    records = [json.loads(l) for l in results_path.read_text().splitlines() if l.strip()]
    ok = [r for r in records if not r.get("failed")]
    answerable = [r for r in ok if not r["is_unanswerable"]]
    unanswerable = [r for r in ok if r["is_unanswerable"]]

    def pass_rate(items):
        n = sum(1 for r in items if r["layerA_verdict"] == "PASS")
        return n, len(items), (round(100 * n / len(items), 1) if items else None)

    overall_pass, overall_n, overall_pct = pass_rate(answerable)

    per_stratum = {}
    for s in ANSWERABLE_STRATA:
        s_items = [r for r in answerable if r["stratum"] == s]
        per_stratum[s] = pass_rate(s_items)

    # abstention
    correct_abstentions = sum(1 for r in unanswerable if r["abstained"])
    false_abstentions = [r for r in answerable if r["abstained"]]

    # perf
    gen_tps = _stats_block([r.get("generation_tps") for r in answerable + unanswerable])
    prompt_tps = _stats_block([r.get("prompt_tps") for r in answerable + unanswerable])
    retrieval_ms = _stats_block([r["retrieval_timings_ms"].get("total_ms")
                                 for r in ok if r.get("retrieval_timings_ms")])
    gen_wall = _stats_block([r.get("generation_s") for r in ok])

    # retrieval sanity (NOT DECISION-002 R@k)
    graded_hits = [r for r in answerable if r["gold_chunk_hit"] is not None]
    n_hit = sum(1 for r in graded_hits if r["gold_chunk_hit"])
    unmapped_any = [r for r in answerable if r.get("gold_chunks_unmapped")]

    utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    commit = _git_commit()

    L: list[str] = []
    p = L.append
    p(f"# Floor-hardware end-to-end benchmark — {utc}")
    p("")
    p(f"- **Machine:** dev floor (i5-4300U class, CPU-only Ollama), commit `{commit}`")
    p(f"- **Model:** `{args.model}` · retrieval k={args.k} · generation params unchanged "
      f"(temp 0, seed 42, num_ctx 4096)")
    p(f"- **Corpus:** fresh isolated index from `data/raw` · questions: "
      f"{len(answerable)} answerable + {len(unanswerable)} unanswerable probes")
    p(f"- **Wall time:** {wall_total_s:.0f}s total"
      + (f" · **{len(failures)} question(s) FAILED** (see end)" if failures else ""))
    p("")
    p("> **What this number is.** RAG **end-to-end** accuracy (retrieval × grounding ×")
    p("> Qwen synthesis), scored by the **Layer A** token-overlap heuristic. It is **not**")
    p("> S_acc (the profiler's lm_eval MCQ on the bare GGUF) and must never be called")
    p("> \"leaderboard accuracy.\" Layer A has **confirmed false positives (R5 / Q19)**, so")
    p("> the pass rate below is a **known overestimate** — an upper bound on faithfulness.")
    p("")

    p("## RAG end-to-end accuracy (Layer-A pass rate — known overestimate)")
    p("")
    p(f"**Overall: {overall_pass}/{overall_n} = {overall_pct}%** answerable questions PASS. "
      f"_{R5_CAVEAT}_")
    p("")
    p("| stratum | PASS / total | pass rate |")
    p("|---------|--------------|-----------|")
    for s in ANSWERABLE_STRATA:
        n, tot, pct = per_stratum[s]
        p(f"| {s} | {n}/{tot} | {pct if pct is not None else '—'}% |")
    p(f"| **overall** | **{overall_pass}/{overall_n}** | **{overall_pct}%** |")
    p("")

    p("## Abstention")
    p("")
    p(f"- **Correct abstentions: {correct_abstentions}/{len(unanswerable)}** on the "
      f"unanswerable probe set (emitted `NOT_IN_DOCUMENTS`).")
    if false_abstentions:
        p(f"- **False abstentions: {len(false_abstentions)}** — answerable questions that "
          f"wrongly abstained (these are FAILURES): "
          + ", ".join(r["id"] for r in false_abstentions))
    else:
        p("- **False abstentions: 0** — no answerable question wrongly abstained.")
    p("")

    p("## Generation throughput (from Ollama's own counters, not wall clock)")
    p("")
    p("| metric | mean | median | min | max |")
    p("|--------|------|--------|-----|-----|")
    p(f"| generation tok/s (eval_count/eval_duration) | {gen_tps['mean']} | {gen_tps['median']} "
      f"| {gen_tps['min']} | {gen_tps['max']} |")
    p(f"| prompt-processing tok/s (prompt_eval_count/prompt_eval_duration) | {prompt_tps['mean']} "
      f"| {prompt_tps['median']} | {prompt_tps['min']} | {prompt_tps['max']} |")
    p(f"| generation wall-clock (s) | {gen_wall['mean']} | {gen_wall['median']} "
      f"| {gen_wall['min']} | {gen_wall['max']} |")
    p("")
    p("Prompt processing is reported separately because the context is large "
      "(~1.2k tokens/question); it is why wall-clock generation time exceeds pure "
      "decode time.")
    p("")

    p("## Retrieval latency (negligible — generation dominates)")
    p("")
    p(f"- total retrieval: mean {retrieval_ms['mean']} ms · median {retrieval_ms['median']} ms "
      f"· max {retrieval_ms['max']} ms. Retrieval is ~0.1% of a question's cost; "
      f"generation is the entire budget.")
    p("")

    p("## Peak RAM footprint (system + ollama process)")
    p("")
    p(f"- baseline system used (model evicted): **{peak['baseline_used_mb']:.0f} MB**")
    p(f"- peak system used during run: **{peak['peak_used_mb']:.0f} MB** "
      f"(**+{peak['delta_mb']:.0f} MB** over baseline)")
    p(f"- peak ollama-process RSS (where the model actually lives): "
      f"**{peak['peak_ollama_rss_mb']:.0f} MB**")
    p("")
    p("> This is **system RAM footprint**, distinct from the profiler's llama-bench GGUF")
    p("> RAM (**S_eff**). It samples the ollama server+runner RSS (the model is resident")
    p("> there, not in the Python CLI). Do not call this S_eff or map it to the leaderboard.")
    p("")

    p("## Retrieval gold-chunk hit rate (sanity signal — NOT DECISION-002 R@k)")
    p("")
    p(f"- gold chunk retrieved for **{n_hit}/{len(graded_hits)}** answerable questions "
      f"whose gold mapped cleanly.")
    if unmapped_any:
        p(f"- ⚠️ **{len(unmapped_any)} question(s) had unmappable gold labels** "
          f"(a data problem, surfaced not hidden): "
          + ", ".join(f"{r['id']}→{r['gold_chunks_unmapped']}" for r in unmapped_any))
    else:
        p("- all gold labels mapped cleanly via the verified positional→stable map.")
    p("- This is a coarse retrieval sanity check at k={}. It is **not** the DECISION-002 "
      "R@k (measured against clean gold with a different method) — cite that separately."
      .format(args.k))
    p("")

    p("## Per-question appendix")
    p("")
    p("| id | stratum | A | abstain | gold hit | gen s | gen tok/s | prompt tok/s |")
    p("|----|---------|---|---------|----------|-------|-----------|--------------|")
    for r in records:
        if r.get("failed"):
            p(f"| {r['id']} | {r.get('stratum','?')} | FAILED | — | — | — | — | — |")
            continue
        hit = r["gold_chunk_hit"]
        hit_s = "—" if hit is None else ("✓" if hit else "✗")
        gt = r.get("generation_tps"); pt = r.get("prompt_tps")
        p(f"| {r['id']} | {r['stratum']} | {r['layerA_verdict']} | "
          f"{'yes' if r['abstained'] else 'no'} | {hit_s} | {r.get('generation_s','?')} | "
          f"{gt if gt is not None else '—'} | {pt if pt is not None else '—'} |")
    p("")

    if failures:
        p("## Failures")
        p("")
        for f in failures:
            p(f"- `{f['id']}`: {f['error']}")
        p("")

    summary_path = results_path.with_name(results_path.stem + "_summary.md")
    summary_path.write_text("\n".join(L))
    return summary_path


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       cwd=str(_ROOT), text=True).strip()
    except Exception:
        return "unknown"


# =============================================================================
# cli
# =============================================================================


def build_parser() -> argparse.ArgumentParser:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ap = argparse.ArgumentParser(prog="run_benchmark",
                                 description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--index-dir", required=True,
                    help="the (freshly built, isolated) index to query")
    ap.add_argument("--questions", nargs="+", default=[str(p) for p in DEFAULT_QUESTIONS],
                    help="question set json file(s)")
    ap.add_argument("--chunks", default=str(DEFAULT_CHUNKS),
                    help="positional chunk dump for the Layer A grader")
    ap.add_argument("--map", default=str(DEFAULT_MAP),
                    help="positional->stable chunk id map for gold_chunk_hit")
    ap.add_argument("--results", default=str(_ROOT / "results" / f"benchmark_{ts}.jsonl"),
                    help="incremental per-question jsonl (resumable)")
    ap.add_argument("--model", default="qwen2.5:3b-instruct", help="Ollama model")
    ap.add_argument("--host", default="http://localhost:11434", help="Ollama host")
    ap.add_argument("-k", type=int, default=3, help="passages retrieved per question")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_benchmark(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
