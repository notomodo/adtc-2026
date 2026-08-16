# Build-in-action captures — 2026-08-14

Terminal captures for the ADTC 2026 Gate-1 submission (requirement: *"Screenshots or
short videos showing your build in action"*). Text captures are committed as artifacts;
the video is scripted in `docs/GATE1_SUBMISSION.md` §6.

| File | What it shows |
|---|---|
| `cli_help.txt` | The `adtc-rag` CLI surface: `ingest` + `ask` commands and options |
| `ingest_run.txt` | Real offline ingest of the 5 Kibuga PDFs → 47 chunks → ONNX embedding → append-only index (idempotency per-document, per-doc progress) |
| `ask_demo.txt` *(pending Ollama)* | `adtc-rag ask` — retrieval → streamed grounded answer with citations, and the `NOT_IN_DOCUMENTS` abstention with near-misses |

To reproduce: `pip install -e .` (runtime venv), then `adtc-rag ingest data/raw/*.pdf`
and `adtc-rag ask "What is Kibuga's returns window?"` (the ask step needs the local
Ollama serving `qwen2.5:3b-instruct`). The ingest capture was made with a throwaway
`--index-dir /tmp/adtc-demo-index` so the default index is untouched.
