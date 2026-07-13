#!/usr/bin/env python3
"""Retrieval benchmark — grades EMBEDDERS IN ISOLATION.

WHAT THIS MEASURES
==================
Given a question, did the chunk containing the answer land in the top-k?

    Recall@k : fraction of questions where a gold chunk appears in the top k.
    MRR      : mean reciprocal rank of the FIRST gold chunk. 1.0 = always rank 1.

WHAT THIS DELIBERATELY DOES NOT MEASURE
---------------------------------------
End-to-end answer accuracy. That conflates retrieval with generation: a weak
embedder can be rescued by a 3B model filling gaps from parametric knowledge --
precisely the failure mode the grounding architecture exists to prevent. Grade
the retriever, not the pipeline.

WHY BM25 IS INCLUDED AS A BASELINE
----------------------------------
It is the honest control. If an embedding model cannot beat keyword matching on
this corpus, it is not earning its RAM. Q11 ("fibre" vs the document's "fiber")
is in the set specifically because BM25 MUST miss it and a good embedder should
not -- it demonstrates, rather than assumes, where semantic retrieval pays.

USAGE
-----
    # baseline only, zero dependencies:
    python benchmark_retrieval.py --dump chunk_dump.txt --questions questions.json

    # full bake-off (needs: pip install sentence-transformers):
    python benchmark_retrieval.py --dump chunk_dump.txt --questions questions.json \
        --models BAAI/bge-small-en-v1.5 thenlper/gte-small \
                 intfloat/e5-small-v2 sentence-transformers/all-MiniLM-L6-v2

NOTE ON MODEL PREFIXES
----------------------
E5 and BGE models were trained with asymmetric prefixes ("query: " / "passage: ").
Omitting them measurably degrades retrieval. This harness applies them
automatically -- benchmarking a model in a configuration its authors did not
intend produces a meaningless number.
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import re
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


# --- Corpus ------------------------------------------------------------------

CHUNK_HEADER = re.compile(
    r"^\[(\d+)\] source=(\S+) type=(\S+) page=(\d+) len=(\d+)", re.M
)


@dataclass
class Chunk:
    id: int
    source: str
    kind: str
    page: int
    text: str


def load_dump(path: Path, source_filter: str | None = None) -> list[Chunk]:
    """Parse a `dump_chunks.py` output file.

    Chunk IDs here are the SAME IDs the question set's `gold_chunks` refer to.
    That correspondence is the whole point: ground truth must match what the
    index actually contains, or Recall@k is unmeasurable.
    """
    raw = path.read_text(encoding="utf-8", errors="replace")
    marks = list(CHUNK_HEADER.finditer(raw))
    chunks: list[Chunk] = []

    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(raw)
        body = raw[m.start():end].split("\n", 1)[1] if "\n" in raw[m.start():end] else ""
        body = re.sub(r"^-{20,}$", "", body, flags=re.M)
        body = re.sub(r"^#{20,}.*$", "", body, flags=re.M).strip()

        src = m.group(2)
        if source_filter and source_filter not in src:
            continue
        chunks.append(
            Chunk(int(m.group(1)), src, m.group(3), int(m.group(4)), body)
        )
    return chunks


# --- Retrievers --------------------------------------------------------------

class Retriever:
    """Interface: index a corpus, rank chunk indices for a query."""

    name = "base"

    def index(self, texts: list[str]) -> None:
        raise NotImplementedError

    def rank(self, query: str) -> list[int]:
        raise NotImplementedError


class BM25(Retriever):
    """Lexical baseline. Zero dependencies. The control, not a contender.

    An embedder that cannot beat this is not worth its RAM.
    """

    name = "BM25 (lexical baseline)"
    K1, B = 1.5, 0.75

    def __init__(self) -> None:
        self.docs: list[list[str]] = []
        self.df: Counter = Counter()
        self.avgdl = 0.0

    @staticmethod
    def _tok(s: str) -> list[str]:
        return re.findall(r"[a-z0-9]+", s.lower())

    def index(self, texts: list[str]) -> None:
        self.docs = [self._tok(t) for t in texts]
        self.avgdl = sum(len(d) for d in self.docs) / max(len(self.docs), 1)
        self.df = Counter()
        for d in self.docs:
            self.df.update(set(d))

    def _score(self, q: list[str], i: int) -> float:
        d = self.docs[i]
        tf = Counter(d)
        n = len(self.docs)
        s = 0.0
        for t in q:
            if t not in tf:
                continue
            idf = math.log(1 + (n - self.df[t] + 0.5) / (self.df[t] + 0.5))
            denom = tf[t] + self.K1 * (1 - self.B + self.B * len(d) / self.avgdl)
            s += idf * tf[t] * (self.K1 + 1) / denom
        return s

    def rank(self, query: str) -> list[int]:
        q = self._tok(query)
        scores = [self._score(q, i) for i in range(len(self.docs))]
        return sorted(range(len(scores)), key=lambda i: -scores[i])


#: Asymmetric prefixes. Omitting these measurably degrades E5/BGE retrieval --
#: benchmarking a model in a configuration its authors did not intend yields a
#: meaningless number.
PREFIXES: dict[str, tuple[str, str]] = {
    "e5": ("query: ", "passage: "),
    "bge": ("Represent this sentence for searching relevant passages: ", ""),
    "gte": ("", ""),
    "minilm": ("", ""),
}


def _prefix_for(model_name: str) -> tuple[str, str]:
    low = model_name.lower()
    for key, pair in PREFIXES.items():
        if key in low:
            return pair
    return ("", "")


class DenseRetriever(Retriever):
    """sentence-transformers embedder. Cosine similarity over normalised vectors."""

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer  # lazy import

        self.name = model_name
        self.model = SentenceTransformer(model_name)
        self.qpre, self.dpre = _prefix_for(model_name)
        self.emb = None
        self.encode_seconds = 0.0

    def index(self, texts: list[str]) -> None:
        import numpy as np  # noqa: F401  (sentence-transformers brings numpy)

        t0 = time.perf_counter()
        self.emb = self.model.encode(
            [self.dpre + t for t in texts],
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        self.encode_seconds = time.perf_counter() - t0

    def rank(self, query: str) -> list[int]:
        import numpy as np

        q = self.model.encode(
            [self.qpre + query], normalize_embeddings=True, show_progress_bar=False
        )[0]
        sims = self.emb @ q
        return list(np.argsort(-sims))


# --- Metrics -----------------------------------------------------------------

@dataclass
class Result:
    name: str
    recall: dict[int, float] = field(default_factory=dict)
    mrr: float = 0.0
    per_question: list[tuple[str, int, str]] = field(default_factory=list)
    index_seconds: float = 0.0


KS = (1, 3, 5, 10)


def evaluate(retr: Retriever, chunks: list[Chunk], questions: list[dict]) -> Result:
    id_to_pos = {c.id: i for i, c in enumerate(chunks)}

    t0 = time.perf_counter()
    retr.index([c.text for c in chunks])
    idx_time = time.perf_counter() - t0

    res = Result(name=retr.name, index_seconds=idx_time)
    hits = {k: 0 for k in KS}
    rr_total = 0.0

    for q in questions:
        gold = {id_to_pos[g] for g in q["gold_chunks"] if g in id_to_pos}
        if not gold:
            print(f"  [WARN] {q['id']}: gold chunk(s) {q['gold_chunks']} not in corpus")
            continue

        order = retr.rank(q["question"])
        rank = next((i + 1 for i, pos in enumerate(order) if pos in gold), None)

        for k in KS:
            if rank and rank <= k:
                hits[k] += 1
        rr_total += (1.0 / rank) if rank else 0.0

        res.per_question.append((q["id"], rank or 0, q.get("stratum", "-")))

    n = len(questions)
    res.recall = {k: hits[k] / n for k in KS}
    res.mrr = rr_total / n
    return res


# --- Report ------------------------------------------------------------------

def report(results: list[Result], questions: list[dict], n_chunks: int) -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print("=" * 78)
    print("RETRIEVAL BENCHMARK — embedders graded IN ISOLATION")
    print(f"{stamp} | python {platform.python_version()} | "
          f"{platform.system()} {platform.machine()}")
    print(f"corpus: {n_chunks} chunks | questions: {len(questions)}")
    print("=" * 78)

    print(f"\n{'MODEL':44}" + "".join(f"{'R@'+str(k):>7}" for k in KS) + f"{'MRR':>7}")
    print("-" * 78)
    for r in sorted(results, key=lambda x: -x.mrr):
        row = f"{r.name[:43]:44}"
        row += "".join(f"{r.recall[k]:>6.0%} " for k in KS)
        row += f"{r.mrr:>6.3f}"
        print(row)

    # Per-stratum: where does each model actually win or lose?
    strata = sorted({q.get("stratum", "-") for q in questions})
    print(f"\n{'PER-STRATUM RECALL@5':44}" + "".join(f"{s[:9]:>11}" for s in strata))
    print("-" * 78)
    for r in sorted(results, key=lambda x: -x.mrr):
        row = f"{r.name[:43]:44}"
        for s in strata:
            ids = {q["id"] for q in questions if q.get("stratum") == s}
            rel = [rank for qid, rank, _ in r.per_question if qid in ids]
            hit = sum(1 for x in rel if 0 < x <= 5) / len(rel) if rel else 0
            row += f"{hit:>10.0%} "
        print(row)

    # Failures are more informative than the aggregate.
    print("\nFAILURES (gold chunk NOT in top-5)")
    print("-" * 78)
    qmap = {q["id"]: q for q in questions}
    any_fail = False
    for r in sorted(results, key=lambda x: -x.mrr):
        bad = [(qid, rk) for qid, rk, _ in r.per_question if rk == 0 or rk > 5]
        if not bad:
            continue
        any_fail = True
        print(f"\n  {r.name}")
        for qid, rk in bad:
            q = qmap[qid]
            where = f"rank {rk}" if rk else "NOT FOUND"
            print(f"    {qid} [{q.get('stratum','-'):11}] {where:11} "
                  f"{q['question'][:44]}")
    if not any_fail:
        print("  none")

    print("\n" + "=" * 78)
    print("REMINDER: single-document corpus. This is a PRELIMINARY ranking.")
    print("Do NOT lock a model on this alone — re-run when the SME corpus lands.")
    print("=" * 78)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", required=True, type=Path)
    ap.add_argument("--questions", required=True, type=Path)
    ap.add_argument("--source", default=None,
                    help="substring filter to select one document from the dump")
    ap.add_argument("--models", nargs="*", default=[],
                    help="sentence-transformers model names")
    args = ap.parse_args()

    chunks = load_dump(args.dump, args.source)
    if not chunks:
        print("No chunks parsed. Check --dump / --source.", file=sys.stderr)
        return 2

    qs = json.loads(args.questions.read_text())["questions"]

    retrievers: list[Retriever] = [BM25()]
    for m in args.models:
        try:
            retrievers.append(DenseRetriever(m))
        except Exception as e:
            print(f"  [SKIP] {m}: {type(e).__name__}: {e}", file=sys.stderr)

    if len(retrievers) == 1:
        print("NOTE: no embedding models loaded — BM25 baseline only.\n"
              "      pip install sentence-transformers, then pass --models\n",
              file=sys.stderr)

    results = [evaluate(r, chunks, qs) for r in retrievers]
    report(results, qs, len(chunks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
