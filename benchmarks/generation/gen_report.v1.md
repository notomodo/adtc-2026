# Generation eval — faithfulness, abstention, judge reliability

- answers graded: **41** (35 answerable, 6 unanswerable probes)
- **A/B judge agreement rate: 46%**  (the measured reliability of the LLM judge on this task)
- flagged for human review: **23** (disagreements + all abstention probes + weak/parse-error cases)

## Layer A (deterministic) headline
- answerable PASS: 46%  FAIL: 46%  REVIEW(weak): 9%
- unanswerable correct-abstention (A): 6/6

## Layer B (LLM judge) headline
- answerable FAITHFUL: 19/35   UNFAITHFUL: 1/35
- unanswerable CORRECT_ABSTENTION (B): 1/6

## HUMAN REVIEW QUEUE (read these by hand)
| id | stratum | A | B | agree | why flagged |
|----|---------|---|---|-------|-------------|
| Q01 | exact_fact | REVIEW | PASS | NO | A/B disagree |
| Q06 | exact_fact | FAIL | PASS | NO | A/B disagree |
| Q08 | paraphrase | FAIL | REVIEW | NO | A/B disagree |
| Q10 | paraphrase | PASS | FAIL | NO | A/B disagree |
| Q14 | near_miss | REVIEW | PASS | NO | A/B disagree |
| Q16 | prose | FAIL | PASS | NO | A/B disagree |
| Q17 | prose | FAIL | REVIEW | NO | A/B disagree |
| Q19 | prose | FAIL | REVIEW | NO | A/B disagree |
| Q21 | multi_chunk | REVIEW | PASS | NO | A/B disagree |
| Q22 | multi_chunk | FAIL | PASS | NO | A/B disagree |
| Q24 | exact_fact | FAIL | REVIEW | NO | A/B disagree |
| Q25 | exact_fact | PASS | FAIL | NO | A/B disagree |
| Q27 | paraphrase | FAIL | REVIEW | NO | A/B disagree |
| Q29 | paraphrase | FAIL | REVIEW | NO | A/B disagree |
| Q31 | near_miss | FAIL | PASS | NO | A/B disagree |
| Q34 | prose | FAIL | REVIEW | NO | A/B disagree |
| Q35 | prose | FAIL | REVIEW | NO | A/B disagree |
| U01 | unanswerable | PASS | REVIEW | NO | abstention probe |
| U02 | unanswerable | PASS | PASS | yes | abstention probe |
| U03 | unanswerable | PASS | REVIEW | NO | abstention probe |
| U04 | unanswerable | PASS | REVIEW | NO | abstention probe |
| U05 | unanswerable | PASS | REVIEW | NO | abstention probe |
| U06 | unanswerable | PASS | REVIEW | NO | abstention probe |

## Full verdicts
| id | stratum | A verdict | B verdict | B evidence (quote) |
|----|---------|-----------|-----------|--------------------|
| Q01 | exact_fact | WEAK | FAITHFUL | [36] Return Policy
All items sold on Kibuga if faulty, can b |
| Q02 | exact_fact | FAIL | WRONG_ABSTENTION | 2. Registration and account: You may not register with our m |
| Q03 | exact_fact | PASS | FAITHFUL | Phone: +256740063330 Phone: +256200959991 |
| Q04 | exact_fact | PASS | FAITHFUL | [39] Seek Support
Headquarters: Muganzirwazza Commercial Pla |
| Q05 | exact_fact | FAIL | WRONG_ABSTENTION | Data We Collect About You
● Data you provide:
● Customer Sup |
| Q06 | exact_fact | FAIL | FAITHFUL | We will make 3 attempts within 2 working days to pick-up the |
| Q07 | paraphrase | FAIL | WRONG_ABSTENTION | [37] states that you have 2 days to notify us of your return |
| Q08 | paraphrase | FAIL | NOT_IN_DOCUMENTS | [GENERAL KNOWLEDGE — from external sources]: The provided co |
| Q09 | paraphrase | PASS | FAITHFUL | Requirement for a valid procedure • Proof of purchase – the  |
| Q10 | paraphrase | PASS | WRONG_ABSTENTION | For such purchases, please inspect the item carefully upon d |
| Q12 | paraphrase | PASS | FAITHFUL | We can contact our Customer Service Call Center at 074251138 |
| Q13 | near_miss | PASS | CORRECT_ABSTENTION | [36] How do I return an item/ What happens once I have retur |
| Q14 | near_miss | WEAK | FAITHFUL | Note that we will make two (2) attempts to return the produc |
| Q15 | prose | PASS | FAITHFUL | You are forbidden from posting content that is offensive, ob |
| Q16 | prose | FAIL | FAITHFUL | We provide options for managing your personal data, includin |
| Q17 | prose | FAIL | NOT_IN_DOCUMENTS | The provided context does not specify any warranty given by  |
| Q19 | prose | FAIL | NOT_IN_DOCUMENTS | [GENERAL KNOWLEDGE — not from the documents]: In the provide |
| Q21 | multi_chunk | WEAK | FAITHFUL | We will perform a careful quality check. If the claim is val |
| Q22 | multi_chunk | FAIL | FAITHFUL | We will perform a careful quality check. • If the claim is v |
| Q23 | exact_fact | FAIL | WRONG_ABSTENTION | [21] passage states that Kibuga business ventures' registere |
| Q24 | exact_fact | FAIL | NOT_IN_DOCUMENTS | The relevant information about whether shipping charges are  |
| Q25 | exact_fact | PASS | UNFAITHFUL | [34] 12. Data Controllers & Contact For questions, concerns, |
| Q26 | exact_fact | PASS | FAITHFUL | In this section 8 words “marketplace” and "website" shall be |
| Q27 | paraphrase | FAIL | NOT_IN_DOCUMENTS | [23] Notice This Privacy Notice provides information on how  |
| Q28 | paraphrase | PASS | FAITHFUL | [41] Sellers Terms and Conditions
You must not advertise, bu |
| Q29 | paraphrase | FAIL | NOT_IN_DOCUMENTS | [25] We provide options for managing your personal data, inc |
| Q30 | near_miss | PASS | FAITHFUL | The prices shown on the marketplace are stated inclusive of  |
| Q31 | near_miss | FAIL | CORRECT_ABSTENTION | [GENERAL KNOWLEDGE — not from the documents]: The relevant p |
| Q32 | prose | PASS | FAITHFUL | Notice This Privacy Notice provides information on how Kibug |
| Q33 | prose | PASS | FAITHFUL | [29] 7. How We Share Your Personal Data Third-party sharing: |
| Q34 | prose | FAIL | NOT_IN_DOCUMENTS | While the exact details are not explicitly stated, the conte |
| Q35 | prose | FAIL | NOT_IN_DOCUMENTS | The specific jurisdiction for legal disputes involving Kibug |
| Q36 | multi_chunk | PASS | FAITHFUL | [40] Sellers Terms and Conditions
1. Seller stores c. You sh |
| Q37 | multi_chunk | PASS | FAITHFUL | Kibuga may make tax-related deductions to payments processed |
| Q38 | multi_chunk | PASS | FAITHFUL | You have 2 days from receiving the purchase to notify Kibuga |
| U01 | unanswerable | PASS | NOT_IN_DOCUMENTS | [24] 2. Who
We Are Kibuga is an e-commerce platform in Ugand |
| U02 | unanswerable | PASS | CORRECT_ABSTENTION | [GENERAL KNOWLEDGE — not from the documents] |
| U03 | unanswerable | PASS | NOT_IN_DOCUMENTS | [36] Return Policy, [37] Return Policy, [38] Return Policy d |
| U04 | unanswerable | PASS | NOT_IN_DOCUMENTS | [39] Seek Support: Headquarters: Muganzirwazza Commercial Pl |
| U05 | unanswerable | PASS | NOT_IN_DOCUMENTS | The provided passages do not contain any information about l |
| U06 | unanswerable | PASS | NOT_IN_DOCUMENTS | [GENERAL KNOWLEDGE — not from the documents]: The provided r |