.PHONY: setup ingest label bench verify all

setup:
	pip install -r requirements-bench.txt
	python scripts/vendor_tokenizer.py

ingest:
	python src/ingest_sme.py data/raw/*.pdf --out benchmarks/chunks_sme.txt

label:
	python src/autolabel.py --dump benchmarks/chunks_sme.txt \
	  --draft data/questions/questions_sme_draft.json \
	  --out data/questions/questions_sme_auto.json \
	  --review benchmarks/review.txt

bench:
	python src/eval_retriever.py --dump benchmarks/chunks_sme.txt \
	  --questions data/questions/questions_sme_auto.json \
	  --models intfloat/e5-small-v2 BAAI/bge-small-en-v1.5 \
	           thenlper/gte-small sentence-transformers/all-MiniLM-L6-v2 \
	  2>&1 | tee benchmarks/eval_sme_output.log

verify:
	python scripts/verify_reproducibility.py

all: ingest label bench verify
