# Decision Records

Every architectural decision, why it was made, what was rejected, and what would reverse it.

**Reading this file should tell you not just *what* the system does, but *why it does it that
way* — and where we were wrong.**

Status values: **Locked** (decided, evidence recorded) · **Deferred** (blocked on an upstream
measurement) · **Reversed** (locked, then found defective — see D6).

---

## D1 — Domain: Entrepreneurship / SME productivity

**Status:** Locked · 6 July 2026

**Decision.** Build an offline document question-answering assistant for small and medium
enterprises. Target workload: *retrieve and report stated facts from business documents* —
financial statements, handbooks, contracts, policy documents.

**Why.** SMEs in Uganda hold their institutional knowledge in documents nobody has time to
read. Connectivity is unreliable and metered, so a cloud tool is unusable exactly when it is
needed. An offline tool that answers "what did we agree on payment terms?" from the actual
contract solves a real problem, not a demo problem.

**Rejected.** Consumer-facing chat assistants (no differentiation, no offline advantage),
agriculture advisory (crowded, and the hard part is agronomy, not AI).

**Scope boundary.** The system **retrieves stated facts**; it does not compute across them.
"What was service revenue?" is in scope. "What was the average margin across three years?"
is not. This boundary is deliberate and is enforced in the question set (see Q13).

---

## D2 — RAG over fine-tuning

**Status:** Locked · 6 July 2026

**Decision.** Retrieval-augmented generation with disciplined grounding prompts. No
fine-tuning.

**Why.** Fine-tuning teaches a model *style*, not *facts* — and the facts here live in
documents the user supplies at runtime, which by definition were not in any training set. A
fine-tuned model would still need retrieval, and would additionally hallucinate with more
confidence. Fine-tuning also requires labelled data we do not have and GPU time we cannot
afford.

**Trade-off accepted.** RAG's answer quality is bounded by retrieval quality. A retrieval
miss is an answer miss. This is why retrieval is graded in isolation (D8) rather than
end-to-end.

**Would reverse this:** evidence that a small model cannot follow grounding instructions even
with correct context. **Tested and refuted** — see D5.

---

## D3 — African-language bonus declined

**Status:** Locked · 6 July 2026

**Decision.** English-only. Do not pursue the competition's African-language scoring bonus.

**Why.** The bonus is real but the practical constraints outweigh it. Luganda, Runyankole,
Acholi, and Ateso are low-resource: there is not enough training text for embedding or
generation quality to be usable. Swahili is better-supported but is not the working language
of Ugandan SME documents. **Shipping a broken feature scores worse than not shipping it.**

**What we lose.** Bonus points, and a genuinely valuable capability.

**Would reverse this:** SME source documents arriving in Swahili at meaningful volume.

---

## D4 — LLM: Qwen2.5-3B-Instruct (fallback: Qwen2.5-1.5B-Instruct)

**Status:** Locked · 7 July 2026 · **Measured**

**Decision.** Qwen2.5-3B-Instruct, ~2.1 GB true resident RAM.

**Why.** Benchmarked against real known-answer questions on real hardware. The 3B follows
grounding instructions reliably; the 1.5B does not — it fills gaps from parametric knowledge,
which is the exact failure this architecture exists to prevent.

**Fallback documented.** 1.5B is retained as the fallback if co-resident memory (LLM +
embedder + index + app) does not fit in 8 GB. **This has not yet been measured on the
reference machine** — see Open Risks.

---

## D5 — Prompting cannot rescue a smaller model

**Status:** Locked · 7 July 2026 · **Hypothesis formally rejected**

**Hypothesis tested.** That structured chain-of-thought prompting could close the accuracy
gap between the 1.5B and the 3B, letting us ship the smaller model.

**Result.** **Refuted.** Structured prompts slightly improved the 1.5B on constraint-application
but could not close the gap. Prompting does not fix arithmetic errors or grounding failures in
a model that lacks the capacity for them.

**Recorded because a rejected hypothesis is evidence.** It is why D4 is locked rather than
provisional.

---

## D6 — Extraction & chunking

**Status:** **REVERSED**, then re-locked · locked 8 July → **reversed 11 July** → re-locked 13 July

### This is the most important record in this file. Read it.

**What was locked on 8 July.** A four-module ingestion pipeline (detect → extract → chunk →
verify), validated against a 47-page LaTeX engineering report. All quality metrics green.

**What was found on 11 July.** The pipeline was **semantically destroying financial documents**.
`pdfplumber.extract_text()` flattens a table into lines of text; the header row became just
another line, and the chunker split between it and the data. Output:

```
Total revenue    1,522,676   1,267,089   20.2%   772,184   639,161   20.8%
```

Six numbers, **zero column headers**. Which is H1 2024? **Unanswerable.** No embedding model
can retrieve what is not semantically present, and the LLM must *hallucinate* the column
mapping because the grounding context genuinely does not contain it.

### Root cause: fixture selection bias

The bug is not the root cause. **The root cause is that v1 was validated against a prose-heavy
LaTeX report while the target workload is table-dense financial documents. The hardest content
class was absent from the validation corpus at lock time.**

The pipeline's own quality metrics reported all-green throughout — including
`pipe-table lines: 0` on a *financial annual report*. **Zero tables detected in a financial
report was reported as a clean pass.**

### The lesson, which recurred four times

> **Structural checks cannot detect semantic corruption. This applies to the extractor, to the
> chunker, and to the gates that check them.**

| Layer | The check said | Reality |
|---|---|---|
| Chunker (v1) | `chunk count: 49`, no tiny chunks — green | Corpus destroyed |
| Chunk metrics (v1) | `pipe-table lines: 0` on a financial report | Zero tables — reported as clean |
| Gate (v2.0) | Fires on known-bad ✓ | **Never tested on known-good** — over-fired on a table of contents |
| Gate (v2.1) | Label markers present ✓ | Labels were `col1:` and `XGU` (= `UGX` reversed) — meaningless |
| Gate (v3.0) | Every value labelled ✓ | Three columns, three **identical** headers — unresolvable |

**Corollary, learned the hard way:** a gate validated only against known-bad input is proven
able to **fail** but never proven able to **pass**. It needs **both** controls.

### The fix (v3.1)

1. **Tables extracted first**, as structured rows, before any prose pass.
2. **Row serialisation** — every row carries its own headers:
   ```
   Service revenue | H1 2024: 1,505,398 | H1 2023: 1,250,059 | YoY: 20.4%
   ```
   Every number travels with **both** its column name and its row name, in the same chunk.
   The embedding encodes the association. The LLM **reads** the mapping instead of inventing it.
3. **Strategy cascade** — `lines` first (ruled tables), falling back to `text` (whitespace-aligned
   tables, which have no grid to detect).
4. **Multi-row header stacks merged** — statutory statements stack period / audit-status / units
   three deep. A single-row picker took *units*, producing three identical `Shs '000` columns.
5. **Four semantic gates**, each with **both** a positive and a negative control, run as a
   mandatory self-test that aborts if any gate misbehaves.

### Why not a Markdown pipe table?

A pipe table is human-readable but **embeds poorly**: the header appears once, at the top, so
any chunk holding only middle rows loses it the moment a table spans a chunk boundary —
reintroducing the original defect. **Row serialisation makes every row independently
self-contained**, which is exactly the property chunking requires. The pipe table is still
emitted, but **for human inspection only**; the serialised rows are what get embedded.

### Standing rules adopted (enforced in code)

1. **Representative-fixture rule.** No ingestion or retrieval decision is locked unless the
   validation corpus contains the **hardest target content class**.
2. **Bidirectional gate rule.** Every gate ships with known-bad (must fire) and known-good
   (must stay silent) fixtures, and **aborts** if either fails. A gate whose verdicts cannot
   be trusted is worse than no gate.

`tests/fixtures/CORRUPTED_v1_output.txt` is a **permanent** negative control. It stays in the
repository forever.

---

## D7 — Runtime: benchmark on sentence-transformers, ship on ONNX Runtime

**Status:** Locked · 11 July 2026

**Decision.** Two runtimes, two purposes.

- **Benchmark** on `sentence-transformers` — every candidate model loads out of the box; fast
  iteration across a shortlist.
- **Ship** on **ONNX Runtime** — a lean C++ engine tuned for CPU inference, with lower memory
  overhead than PyTorch. For a RAM-bound, CPU-only, offline target this is the correct
  deployment runtime.

**The critical caveat.** Retrieval *quality* transfers across runtimes (the vectors are
essentially identical). **Speed and RAM do not** and must be re-measured on the deployment
runtime. Do not quote benchmark-runtime performance numbers as shipped performance.

**Confidence.** ONNX's CPU advantage over PyTorch is well-established generally, but the exact
delta on *this* hardware is an **informed inference, not a measurement**, until measured.

---

## D8 — Grade retrieval in isolation, not end-to-end

**Status:** Locked · 11 July 2026

**Decision.** Embedding models are graded on **Recall@k and MRR against a labelled question
set** — did the chunk containing the answer land in the top k? Not on end-to-end answer
accuracy.

**Why this matters more than it sounds.** End-to-end grading **conflates retrieval quality with
generation quality**. A weak embedder can be *rescued* by a 3B model filling gaps from
parametric knowledge — which is precisely the failure mode the grounding architecture exists to
prevent. You would measure the wrong thing and reward the wrong behaviour.

**Grade the retriever, not the pipeline.**

**Ground truth must be chunk IDs from our own chunker's output** — not page numbers. If ground
truth does not match what the index actually contains, Recall@k is unmeasurable.

**Baseline.** BM25 (lexical) is included as an **honest control**. An embedder that cannot beat
keyword matching is not earning its RAM.

Measured on the interim-results corpus (18 chunks, 18 questions):

| Retriever | R@1 | R@5 | MRR | paraphrase R@5 |
|---|---|---|---|---|
| BM25 baseline | 33% | 67% | 0.527 | **25%** |

**BM25 scores 100% on prose and 25% on paraphrase.** It fails on "fibre" vs the document's
"fiber", and on "first half of 2024" vs "H1 2024". **That gap is the entire case for dense
retrieval, and it is now the acceptance bar** — measured, not assumed.

---

## D9 — English-only for v1

**Status:** Locked · 11 July 2026

**Decision.** English-only retrieval and generation. Swahili deferred to v2.

**Why.** Multilingual embedders spread the same parameter budget across many languages, so on
English text a same-size English-specialised model **wins**. The multilingual models that close
that gap (BGE-M3, multilingual-e5-large) are **larger** — fighting the binding RAM constraint
directly. Target SME documents are in English.

**Would reverse this:** SME documents arriving in Swahili at meaningful volume.

---

## D10 — Reranker

**Status:** **DEFERRED**, then **RESOLVED** · deferred 11 July 2026 → resolved 15 July 2026
— see [`docs/DECISION-003-reranker.md`](docs/DECISION-003-reranker.md)

**Why deferred (original entry).** The reranker decision depends on a number we did not yet
have: the chosen embedder's Recall@5.

- **High Recall@5** → the reranker's marginal value shrinks. Possibly skip it entirely and
  save the RAM.
- **Low Recall@5** → it becomes essential.

**This is a deliberate deferral, not an oversight.** Deciding now would mean guessing.

**Note:** query embedding is cheap (tens of milliseconds), and generation on CPU dominates
end-to-end latency by orders of magnitude. **We can afford a reranker if we need one** — the
question is purely whether it earns its memory.

**Resolution (15 July 2026).** The locked hybrid (D2/DECISION-002) measured R@5 89%. A
reranker only reorders candidates a first-stage retriever already surfaced — it cannot
recover a chunk retrieval never surfaced, and it cannot aggregate information split across
multiple chunks. The two failures that survived the locked retriever (Q19: gold chunk absent
from the candidate set; Q22: multi-chunk paraphrase) are exactly those two shapes. **Rejected
for v1** — not merely postponed. Full argument, cost analysis, and reopen conditions in
`docs/DECISION-003-reranker.md`.

---

## D11 — Chunk-size cap

**Status:** **DEFERRED** — blocked on embedding model selection

**Why deferred.** The cap is set by the chosen embedder's **maximum input sequence length**
(typically 512 tokens). Setting it before choosing the model would mean either truncating
chunks the model could have handled, or emitting chunks it will silently truncate.

---

## D12 — Rotated/infographic text: out of scope for v1

**Status:** Locked · 13 July 2026

**Decision.** Heavily designed marketing layouts — infographic panels with rotated or curved
text — are **out of scope**. They are **detected and flagged**, not silently corrupted.

**The defect.** Character-level garbling from glyph-ordering problems in the source layout:

```
1.1 tn XGU | col1: UGX 947.5 bn        ← "XGU" is "UGX" read backwards
Profit after tax rose Taxes contribu 678.8 XG 1.6 XG | .7 bn: ted
```

**Why out of scope, and this is an inference not a measurement.** Rotated-text handling is
deep, fragile work, and the document class — a 200-page designed corporate annual report — is
**almost certainly not representative of SME documents**. The target user has invoices,
handbooks, supplier contracts, and accounting exports: ordinary business documents with ruled
or whitespace-aligned tables. They do not have a design agency laying out text on curves.

**Chasing it would be fixture-selection bias for a third time, in the opposite direction.**

**GATE 3 detects and flags these blocks.** A known boundary with a gate that finds it is a
**strength**, not a blemish.

**Would reverse this:** SME documents exhibiting the same garbling.

---

## D13 — Grounding prompt for the generation layer (v3 locked)

**Status:** Locked · 19 July 2026 · **Measured**

**Decision.** Lock the v3 grounding prompt for `gen_answer.py`: strict grounding, a prominent
"answer directly" instruction, abstention reduced to the single bare token
`NOT_IN_DOCUMENTS`, and **no general-knowledge note**.

**Why.** Benchmarked three prompt versions (v1, v2, v3) against the identical 35-question +
6-probe set, `k=3`, Qwen2.5-3B-Instruct, offline, `temperature=0 seed=42`. v3 scored 25/35
(71.4%) answerable pass, 0 laundered answers, 6/6 abstention probes correct — strictly
dominating v1 (16/35, 19 laundered) and v2 (6/35, 23 laundered) on every measured axis.
Conditioned on retrieval actually supplying the gold chunk, generation is correct on
27/28 (96%).

**Rejected.** v2's general-knowledge note. Measured to be an attractor: a 3B model treats
prompt salience as a behavioural prior, and an emphatic abstain branch made abstention the
default even when the model held the correct answer — 20 of 27 v2 abstentions "laundered" a
correct answer under a false `NOT_IN_DOCUMENTS` label.

**Recorded because a rejected hypothesis is evidence** (cf. D5). See
[`docs/DECISION-004-grounding-prompt.md`](docs/DECISION-004-grounding-prompt.md) for the full
record, including the v2 regression retained deliberately as part of the record.

**Would reverse this:** a re-test showing the general-knowledge note no longer attracts
abstention when reintroduced against the v3 baseline; or the outstanding hand-read validation
of the Layer A passes (see DECISION-004 Open Items) showing the 71.4% figure does not hold up
as an accuracy figure.

---

## Open risks

| # | Risk | Status |
|---|---|---|
| R1 | **Co-resident memory fit is unmeasured.** Qwen2.5-3B + embedder + index + app in 8 GB has been an *assumption* since 6 July. Every number in this project comes from a 2-core Haswell dev floor; **the 8 GB reference machine has produced zero data.** If it does not fit, this invalidates architecture, not tuning. | **Open — highest** |
| R2 | Accuracy-prompt evaluation mechanics unknown. How the competition's accuracy prompts are scored (pass/fail vs partial credit; human vs automated vs LLM judge) determines what we should optimise. Open since 6 July. | Open |
| R3 | v3.1 has never been tested against a real SME document. The corpus that justifies every extraction decision is still MTN's investor-relations material. | **Resolved** — Kibuga (5 PDFs, 47 chunks) is now the working corpus for retrieval (D2) and generation (D13) |
| R4 | Model licences. Qwen2.5 and the BGE/GTE/E5 families each carry **their own terms**, distinct from the library licences. A common and avoidable audit failure. | Unverified |
| R5 | Layer A (D13) is a token-overlap heuristic, not a truth oracle. The 71.4% v3 pass rate has not been hand-validated against the actual answer text. **Blocking** before that figure is quoted as accuracy anywhere. | Open |

---

## Environment notes

**Claude project containers silently convert uploaded PDFs.** Files mounted as `.pdf` arrive as
derivatives — one as a plain-text dump, four as ZIP archives of page JPEGs. `pdfplumber` cannot
read any of them. **Consequence: no Claude session can run extraction against real PDF bytes.**
All extraction verification runs locally; chunk dumps are returned as `.txt`, which survives
conversion. HuggingFace is also network-blocked in that container, so the dense bake-off runs
locally too.

Structural, not a fixable upload mistake. Recorded so it is not rediscovered.
