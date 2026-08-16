# Technical Report — Kibuga SME Document Q&A (offline RAG on Qwen2.5-3B)

**Team ID:** (see metadata.json — team_id to be confirmed on the ADTF portal)
**Domain:** corporate_enterprise
**Model:** Qwen2.5-3B-Instruct-Q4_K_M (GGUF, llama.cpp)
**Repo:** https://github.com/notomodo/adtc-2026 (public, MIT)

---

## Problem

Small and medium enterprises in Uganda hold their institutional knowledge in
PDFs — terms and conditions, privacy policies, returns policies, seller terms,
support pages — and need plain-language answers grounded in those documents.
Connectivity is unreliable and metered, so a cloud chatbot is unusable exactly
when it is needed, and commercial-grade search tools are out of reach. The
target user is a small business owner or employee who must answer questions
like *"what is the returns window?"* or *"can I ask Kibuga to delete my data?"*
without a lawyer, a support call, or an internet connection.

This submission is a **retrieval-augmented generation (RAG) system**: it
retrieves the relevant passages from the business's own PDFs (hybrid BM25 +
dense, reciprocal-rank fusion) and answers strictly from them under a
grounding prompt, with citations — or explicitly abstains
(`NOT_IN_DOCUMENTS`) when the documents do not contain the answer. The
submitted model is the generation component (Qwen2.5-3B-Instruct Q4_K_M);
the full pipeline is open source in this repo and runs end-to-end offline on
the 8 GB budget-laptop profile.

## Design Decisions

- **Base model: Qwen2.5-3B-Instruct, quantized GGUF Q4_K_M.** Chosen from a
  controlled three-way comparison (2026-08-02: Qwen2.5-3B vs Qwen2.5-1.5B vs
  Qwen3-4B, identical retrieval, temperature 0, seed 42, 35 answerable + 6
  unanswerable questions). The 3B was the only model with **zero confident
  hallucinations**, scored 6/6 on abstention probes, and is the lightest
  option that follows grounding instructions reliably. A faithfulness-aware
  Layer-B grade (2026-08-14, 41 questions × 3 models, see
  `docs/LAYER_B_GRADE_2026-08-14.md`) confirmed: faithfulness 29/35 on
  answerable questions (27/28 when the gold chunk was retrieved), zero unique
  hallucinations, 6/6 abstention probes.
- **Quantization: Q4_K_M** — the standard CPU sweet spot (~2.1 GB resident
  for the 3B). Alternatives evaluated: **Qwen2.5-1.5B Q4_K_M** (faster but
  materially weaker faithfulness — 2 substantive unique hallucinations,
  including a wrong-chunk answer) and **Qwen3-4B Q4_K_M** (faithfulness
  parity but 2.83 tok/s vs 4.98, a 7.4 GB system peak that nearly saturates
  the 8 GB budget — an OOM/disqualification risk under the rules — and one
  hallucination on an unanswerable probe). 7B-class models were rejected
  without testing: Q4 7B (~4.4 GB) plus the retrieval layer and app would not
  co-reside in 8 GB.
- **License (checked against the primary rules, 2026-08-14):** the official
  Devpost rules and Challenge Participation Agreement impose **no model-weight
  license eligibility constraint**; the open-source requirement applies to the
  submission repository (this repo is public, MIT). The Qwen Research
  (non-commercial) license is therefore not disqualifying under the published
  rules.
- **System design (why the numbers are what they are):** retrieval is a
  hand-rolled Okapi BM25 (stdlib) fused with a CLS-pooled
  `bge-small-en-v1.5` encoder exported to **ONNX Runtime** (no PyTorch in the
  runtime path), fused by Reciprocal Rank Fusion (k=60), top-k=3 chunks into
  a locked v3 grounding prompt. The tokenizer is vendored and all runtime
  dependencies are pinned, because chunk IDs are positional — an unpinned
  tokenizer once silently produced 47 chunks on one machine and 57 on
  another, invalidating a benchmark. A corpus-fingerprint gate in CI exists
  specifically to catch that class of failure.

## Constraints

- **Hardware:** the ADTC Standard Laptop profile — Intel Core i5 10th–12th gen
  or AMD Ryzen 5, **8 GB DDR4 RAM**, integrated graphics only, 256 GB SSD,
  Ubuntu 22.04 LTS. Pure CPU inference (llama.cpp/GGUF).
- **Memory:** 8 GB ceiling is strict; OOM during evaluation is automatic
  disqualification. The model at Q4_K_M (~2.1 GB resident) plus the ONNX
  embedder, index and app fits with margin (measured peak on the dev floor
  box: 4.6 GB system — see Benchmarks).
- **Connectivity:** zero network at runtime — weights are downloaded before
  evaluation (`download_model.sh`), and the RAG pipeline performs no outbound
  calls (local Ollama/llama.cpp + local ONNX).
- **Data:** a real Ugandan SME corpus (Kibuga Business Ventures — terms,
  privacy, returns, seller terms, support: 5 PDFs, 47 chunks, 22 pages,
  prose-only). Scope is deliberately narrow: retrieve and report *stated
  facts*, not cross-document computation.
- **Power/thermal:** laptop-class CPU — long generations are the cost driver;
  retrieval is ~25 ms and negligible.

## Benchmarks

Self-reported development benchmarks from the dev floor machine
(i5-4300U-class, 7.7 GB RAM, CPU-only, Ubuntu). Official scores are measured
by the ADTC profiler on the standard evaluation machine; a local participant-
mode profiler run and the reference-machine run are pending and will be
appended when complete.

| Metric | Value |
|---|---|
| Machine | dev floor, i5-4300U-class, 7.7 GB, CPU-only (older than the standard laptop) |
| Model resident RAM (llama-server runner RSS) | ~2.05 GB |
| Peak system RAM (full RAG app, 41-question run) | 4584 MB (baseline idle 1418 MB) |
| Generation speed (Ollama/llama.cpp counters) | median 4.98 tok/s (mean 5.22, min 4.61, max 6.12) |
| Prompt-processing speed | median 23.5 tok/s (mean 58.7) |
| Retrieval latency (BM25+dense+RRF, k=3) | median 25.3 ms |
| Generation wall-clock per question | median ~54 s |
| Thermal throttling | none observed in RAG runs (harness flags on >85 °C); **see profiler row below** |

**Official ADTC profiler run (2026-08-14, participant mode, dev floor machine)** —
full report `results/profiler_participant_20260814.md`, raw `submission.json`:

| Metric | Value |
|---|---|
| Accuracy (arc_easy, n=50, acc_norm) — S_acc | **0.80** |
| Generation speed (llama-bench, 512 ctx) | 4.32 tok/s |
| First-token latency (512-token prompt) | 46.4 s |
| Peak RSS | 3456 MB (of the 7.0 GB evaluation limit) |
| Core temp peak / throttled | 94.0 °C / throttled ⚠ (old dev CPU; reference machine must be checked) |
| Score preview (official formula) | ≈48.8 on the dev floor, dominated by S_acc 80; S_eff 50.6, S_perf 28.8 (floor-limited), −10 thermal |

**Accuracy framing (honest, not overclaimed):** the official ADTC scoring is
**S_total = 0.50·S_acc + 0.30·S_perf + 0.20·S_eff − P_thermal**, where S_acc is
the model's response quality on our submitted prompts plus hidden judge prompts
(measured by the official profiler — **pending on this submission**), S_perf is
throughput normalised to 15 tok/s, and S_eff is RAM normalised to a 7.0 GB
limit. Our internal end-to-end RAG accuracy is a Layer-A token-overlap proxy
(26/35 = 74.3% on the dev floor) with a **known overestimate** (one
confirmed false positive, Q19) and a known length bias — it is *not* quoted
as accuracy anywhere in this repo. The defensible claim is the Layer-B
faithfulness grade: 29/35 answerable (82.9%), 27/28 (96.4%) when the gold
chunk was retrieved, 6/6 abstention probes, zero unique hallucinations
(`docs/LAYER_B_GRADE_2026-08-14.md`).

**Reproducibility:** `make verify` asserts the corpus fingerprint
(`c7f23f29b738b08d`) matches the gold-label set; CI enforces 47 chunks +
fingerprint + auto-label reproducibility from a clean clone. Full test suite:
92 passed, 2 skipped (torch-dependent parity and the live-Ollama e2e gate).

---

*See `DECISIONS.md`, `STATUS.md`, `docs/model_comparison.md`, `benchmarks/`
and `results/` in this repo for the complete evidence trail.*
