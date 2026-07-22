"""Generate 6 grounded UNANSWERABLE probes: plausible SME questions the Kibuga
corpus genuinely does NOT answer. Verified absent by keyword scan against
chunks_sme_fp.txt. Labels are single-annotator-unverified (same discipline as v3)."""
import json

probes = [
    dict(id="U01", stratum="unanswerable",
         question="Does Kibuga ship internationally to Kenya, and what are the rates?",
         why_absent="Corpus covers returns/privacy/seller terms; no international shipping clause. 'International' appears only re: data transfers."),
    dict(id="U02", stratum="unanswerable",
         question="Can I pay for my order in instalments or with cash on delivery?",
         why_absent="No payment-method or instalment/COD clause anywhere in the 5 documents."),
    dict(id="U03", stratum="unanswerable",
         question="What is the warranty period in months on electronics bought from Kibuga?",
         why_absent="Sellers give a warranty (Q17) but no PERIOD/duration in months is stated."),
    dict(id="U04", stratum="unanswerable",
         question="Does Kibuga have a physical store I can visit in Kampala?",
         why_absent="Registered office address exists (Q23) but no retail/physical-store clause."),
    dict(id="U05", stratum="unanswerable",
         question="What loyalty points or discount codes does Kibuga offer repeat buyers?",
         why_absent="No loyalty/rewards/discount-code content in corpus."),
    dict(id="U06", stratum="unanswerable",
         question="How many days does delivery take after I place an order?",
         why_absent="Return pickup is 2 working days (Q06); outbound DELIVERY time is never stated."),
]
for p in probes:
    p["gold_chunks"] = []          # deliberately empty: correct behavior is ABSTAIN
    p["answer"] = "NOT_IN_CORPUS"  # sentinel for the harness
    p["origin"] = "claude_unans_v1"
    p["label_status"] = "single_annotator_unverified"

json.dump({"_meta": {"purpose": "abstention probes; gold_chunks empty by design",
                     "n": len(probes), "corpus_fingerprint": "592a602f845dce20"},
           "questions": probes},
          open("questions_unanswerable.json", "w"), indent=2, ensure_ascii=False)
print(f"wrote {len(probes)} unanswerable probes")
