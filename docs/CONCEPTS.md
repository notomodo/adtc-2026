# Concepts — Retrieval Metrics, Dense Models, and Gold Labels

A reference for the terms used throughout this project's benchmarks and decision records.

---

## 1. The retrieval problem

Your corpus is 47 chunks of text. A user asks a question. The retriever's job is to
**rank all 47 chunks** by how likely each is to contain the answer, and hand the top
few to the LLM.

Everything below is a way of asking: **how good is that ranking?**

---

## 2. Gold labels — the ground truth

A **gold label** is the answer key: *for question Q, chunk 36 contains the answer.*

```json
{
  "id": "Q01",
  "question": "What is Kibuga's returns window?",
  "answer": "Two (2) days free returns policy",
  "gold_chunks": [36],
  "stratum": "exact_fact"
}
```

Without gold labels **no retrieval metric can be computed at all.** You cannot ask
"did the retriever find the right chunk?" without knowing which chunk is right.

### The definition that matters

> **A chunk is gold if a correct, grounded answer could be produced from that chunk
> alone.**

Not "related to." Not "mentions returns." If an LLM given *only* that chunk could
answer the question, it is gold. If it could not, it is not — however topically similar.

### Why gold labels are dangerous

They are **hand-made ground truth**, and if they are wrong, **every number downstream
is fiction.** This project has already lost one entire benchmark to bad gold labels: an
auto-labeller marked 26–28 of 37 chunks as gold on four questions, making those
questions *unmissable* and inflating the scores of every retriever equally.

The JSON was well-formed. Every structural check passed. The labels were simply wrong.

### The circularity trap

> A labeller and a retriever are **the same class of algorithm.** Both rank chunks by
> relevance to a query.
>
> **If a script could reliably identify the answer chunk, you would ship it instead of
> a retriever.**

So generating ground truth with algorithm A and using it to grade algorithm B measures
**how similar B is to A** — not how good B is. A lexical labeller makes BM25 look
excellent. An embedding labeller makes embeddings look excellent. The benchmark becomes
a mirror.

**The only fully trustworthy labels are hand-made.** Automated labelling is acceptable
*only* when it labels by **proof** (a literal verbatim span, a unique email address) and
**abstains** everywhere else — which is what `autolabel.py` does.

### Other kinds of labels

| Label type | What it is | Do we use it? |
|---|---|---|
| **Gold chunk** | Which chunk(s) contain the answer | ✅ Yes — the core label |
| **Stratum** | Question *category* (exact_fact, paraphrase, prose, multi_chunk, near_miss) | ✅ Yes — lets us see *where* a retriever fails, not just *how often* |
| **Answer string** | The expected answer text | ✅ Yes — used to *find* gold chunks by proof, and later to grade the LLM |
| **Graded relevance** | A 0–3 score per chunk (irrelevant → perfect) rather than binary gold/not-gold | ❌ No — needed for nDCG; overkill at n=19 |
| **Hard negative** | A chunk that *looks* right but is not — used to train embedders | ❌ No — we are not fine-tuning |

**Strata** are worth dwelling on. Aggregate Recall hides *which* questions fail.
Stratifying revealed the central finding of DECISION-002: BM25 scores **100% on
paraphrase but 50% on multi_chunk**, while dense scores **100% on multi_chunk but 50%
on prose.** They fail on *opposite* questions — which is the entire argument for
fusing them.

---

## 3. The metrics

Suppose the retriever ranks all 47 chunks for a question whose gold chunk is **36**:

```
rank 1: chunk 12     rank 2: chunk 36  ← gold, found at rank 2
rank 3: chunk 4      rank 4: chunk 36 ...
```

### Recall@k — "is the answer in the top k?"

**Binary, per question. Then averaged across all questions.**

> **Recall@k = (number of questions where a gold chunk appears in the top k) / (total questions)**

For the example above: R@1 = 0 (gold was rank 2, not 1). R@3 = 1. R@5 = 1.

Across 19 questions, if 10 have their gold chunk at rank 1:

> **R@1 = 10/19 = 53%**

**It does not care *where* in the top k the chunk landed** — rank 1 and rank 5 both count
as a hit for R@5. That is the metric's blind spot, and it is why we also report MRR.

### R@1, R@3, R@5 — and why R@1 is the one that matters here

| Metric | Question it answers | What it is good for |
|---|---|---|
| **R@1** | Is the answer the **top hit**? | The strictest test. **Our primary gate.** |
| **R@3** | Is it in the top 3? | Realistic context-window budget |
| **R@5** | Is it in the top 5? | Generous — "did retrieval work *at all*" |
| **R@10** | Top 10? | Mostly a debugging signal |

**Why R@1 is the deployment metric for this project:**

Retrieved chunks are fed to Qwen2.5-3B running **CPU-only on 8 GB RAM**. Every chunk in
the context window costs **prefill latency and memory**.

- **R@5** asks: *is the answer somewhere in five chunks?*
- **R@1** asks: *is the answer the top hit?*

A high R@1 means we can pass **fewer chunks to the LLM**. On this hardware that is a
direct latency and RAM saving.

> **R@5 measures whether retrieval works. R@1 measures whether it works cheaply enough
> to deploy.**

This distinction is not academic — it **reversed a decision** in this project. The
benchmark harness gated on R@5, found a tie at 89%, and printed *"Hybrid does NOT beat
BM25."* On R@1, **all four hybrids beat BM25.** The gate was measuring the wrong thing.

### MRR — Mean Reciprocal Rank

Recall@k is binary and throws away information: it cannot distinguish a retriever that
puts the answer at rank 1 from one that puts it at rank 5. **MRR keeps that
information.**

For each question, take the **reciprocal of the rank** of the first gold chunk:

| Gold found at rank | Reciprocal rank |
|---|---|
| 1 | 1/1 = **1.000** |
| 2 | 1/2 = **0.500** |
| 3 | 1/3 = **0.333** |
| 5 | 1/5 = **0.200** |
| 10 | 1/10 = **0.100** |
| not found | **0** |

> **MRR = the mean of those reciprocal ranks across all questions.**

Worked example, 4 questions with gold at ranks 1, 2, 5, and not-found:

```
MRR = (1.000 + 0.500 + 0.200 + 0) / 4 = 0.425
```

**Range: 0 to 1.** MRR = 1.0 means every question had its answer at rank 1.
Our BM25 baseline: **0.664**. Our chosen hybrid: **0.703**.

**The key property:** the reciprocal **falls off steeply**. Moving a chunk from rank 2 to
rank 1 gains 0.5; moving it from rank 9 to rank 8 gains only 0.014. MRR **heavily
rewards getting the answer to the top** — which is exactly the behaviour we want on
constrained hardware.

**Its limitation:** it only looks at the **first** gold chunk. For a question whose answer
genuinely spans three chunks, MRR is blind to whether the other two were found. (The
metric that handles that is **nDCG**; we do not use it — it needs graded relevance
labels, which is more labelling effort than n=19 justifies.)

### Reading the two together

| | R@5 | MRR | Interpretation |
|---|---|---|---|
| High | High | Answers found, and found **at the top**. Ideal. |
| High | Low | Answers found, but **buried at rank 4–5.** Must pass many chunks to the LLM → slow, RAM-hungry. |
| Low | — | Retrieval is failing. Nothing downstream can fix it. |

---

## 4. Dense models (embedding models)

### The problem BM25 cannot solve

**BM25** is a **lexical** retriever. It scores a chunk by counting *shared words*, weighted
so that rare words matter more. It is fast (1.1 ms), needs no model, and is genuinely
strong.

But it can only match words it **literally sees**. Consider:

> **Query:** *"What are all the ways Kibuga can refund me?"*
> **Document:** *"store credits, wallet refunds, vouchers, mobile money transfer"*

Almost **no shared vocabulary**. BM25 scores this near zero and **misses the chunk
entirely** (this is real — it is Q22 in our benchmark). The document and the query mean
the same thing in different words, and BM25 has no notion of *meaning*.

### What a dense model does

An **embedding model** (a small transformer, typically 20–110M parameters) converts a
piece of text into a **vector** — a list of ~384 numbers:

```
"What are the ways to refund me?"  →  [0.021, -0.114, 0.087, ..., 0.043]   (384 numbers)
"store credits, wallet refunds"    →  [0.019, -0.121, 0.091, ..., 0.038]   (384 numbers)
```

The model is trained so that **texts with similar meaning land close together in this
384-dimensional space**, even when they share no words. Closeness is measured by
**cosine similarity** — the angle between the two vectors.

Retrieval becomes: *embed the query, embed every chunk, return the chunks whose vectors
are closest.*

**"Dense"** refers to the vector. A BM25 representation is **sparse** — one dimension per
vocabulary word, almost all zeros. An embedding is **dense** — 384 dimensions, all
non-zero, each capturing some abstract feature of meaning.

### The models we benchmarked

| Model | Params | Dim | Notes |
|---|---|---|---|
| **`bge-small-en-v1.5`** ✅ | 33M | 384 | BAAI. **Selected.** Best all-round; only model non-negative on every metric. |
| `e5-small-v2` | 33M | 384 | Microsoft. Best MRR (0.717) but **regresses R@5** (89% → 84%). |
| `gte-small` | 33M | 384 | Alibaba. Solid, but ~1.7× slower. |
| `all-MiniLM-L6-v2` | 22M | 384 | The classic baseline. **Fastest** (17.6 ms), but weakest — misses `exact_fact` questions. |

**These are not LLMs.** They do not generate text. They only produce vectors. That is why
a 33M-parameter model is enough — the task is far narrower than generation.

### Asymmetric prefixes — a trap

`e5` and `bge` were **trained with instruction prefixes**, and omitting them measurably
degrades retrieval:

```python
# e5:   "query: how long is the returns window?"
#       "passage: Two (2) days free returns policy..."
# bge:  "Represent this sentence for searching relevant passages: <query>"
```

Benchmarking these models **without** their prefixes produces numbers that describe
nothing. `retriever.py` applies them automatically per model.

### Why we do not ship `sentence-transformers`

`sentence-transformers` is the standard library for these models — but it pulls in
**PyTorch (~800 MB–2.5 GB installed)**. On an 8 GB offline target where Qwen already
holds ~2.1 GB resident, shipping a deep-learning **training** framework to run forward
passes on a 33M-parameter encoder is indefensible.

What it actually *does* for these models is small enough to reproduce exactly:

1. Tokenize
2. Forward pass through the transformer
3. **Mean-pool** the last hidden state over the attention mask
4. **L2-normalise**

`OnnxEncoder` does those four steps with `onnxruntime` + `tokenizers` — roughly **50 MB**
of dependency instead of 800+. **Same vectors, no PyTorch.**

We **benchmark** with `sentence-transformers` (so numbers are comparable to published
results) and **ship** ONNX. Both sit behind the same `Encoder` protocol, so the retriever
never knows which is in use.

> ⚠️ **Required verification:** the ONNX export must reproduce the sentence-transformers
> vectors to ~1e-5. If it does not, **the benchmark numbers no longer describe the shipped
> system.**

---

## 5. Hybrid retrieval and RRF

Since BM25 and dense models **fail on opposite questions**, use both and **fuse the
rankings**.

The naive approach — add the scores — **does not work**. BM25 scores are unbounded
TF-IDF sums (0 to ∞); cosine similarities are bounded (−1 to 1). Normalising two
distributions whose shapes change per query is unstable, and one runaway top hit
distorts the whole list.

**Reciprocal Rank Fusion (RRF)** sidesteps this by **discarding scores entirely and
fusing ranks**:

> **RRF(chunk) = Σ over retrievers r of 1 / (k + rank_r(chunk))**

With `k = 60` (Cormack et al., SIGIR 2009). A chunk ranked 1st by BM25 and 3rd by dense
scores `1/61 + 1/63 = 0.0323`.

**Why it works:**
- **Scale-free** — never compares a BM25 score to a cosine similarity.
- **`k` damps the top** — a single confident-but-wrong retriever cannot dominate.
- **Absent chunks are not penalised**, merely not boosted.
- **One constant, no training.** Nothing to overfit on 19 questions.

---

## 6. Glossary

| Term | Meaning |
|---|---|
| **Chunk** | A passage of a document, sized to fit the embedder's input limit (400 tokens here) |
| **Gold chunk** | A chunk from which the answer could be correctly produced |
| **Stratum** | Question category — reveals *where* a retriever fails |
| **Recall@k** | Fraction of questions with a gold chunk in the top *k* |
| **MRR** | Mean of 1/(rank of first gold chunk) — rewards ranking the answer **first** |
| **Sparse retrieval** | Word-matching (BM25). Fast, exact, no semantics |
| **Dense retrieval** | Vector-matching (embeddings). Handles paraphrase, costs RAM |
| **Embedding** | A ~384-number vector representing a text's meaning |
| **Cosine similarity** | Angle between two vectors — the closeness measure |
| **RRF** | Reciprocal Rank Fusion — combines rankings without comparing scores |
| **BM25** | Best Match 25. The standard lexical ranking function |
| **Corpus fingerprint** | Hash of all chunks — detects when chunk IDs shift and labels go stale |
