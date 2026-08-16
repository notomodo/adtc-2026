# Layer-B grading pack — 3B vs 1.5B vs Qwen3-4B (self-contained)

**Generated:** 2026-08-02 · from `results/benchmark_*` (commit `3169512`).

## What this is and how to use it

This is the **self-contained substrate for a Layer-B (human/LLM-as-judge) faithfulness grade** of three generation models on the adtc-rag pipeline. It exists because the raw benchmark `Layer-A` pass rate is a **token-overlap heuristic** with two known biases: it **overestimates** faithfulness (confirmed false positives, the R5/Q19 finding) AND it **length-penalizes terser models** (a correct one-line answer can score FAIL on overlap). The three-way Layer-A numbers (3B 74.3% > Qwen3-4B 65.7% > 1.5B 62.9%) therefore cannot be trusted as a faithfulness ranking. **Your job: grade each answer on faithfulness to the retrieved context, independent of token overlap.**

**Grading rubric (per model, per question):**

- **Answerable questions:** `FAITHFUL` (every claim supported by the retrieved context below; concise/paraphrased is fine), `UNFAITHFUL` (a claim not supported by / contradicting the context — a hallucination), or `WRONG_ABSTENTION` (said NOT_IN_DOCUMENTS when the context did contain the answer).
- **Unanswerable probes (gold empty):** `CORRECT_ABSTENTION` (declined / said NOT_IN_DOCUMENTS, possibly with a labelled general-knowledge note) or `UNFAITHFUL` (answered anyway = hallucination).
- Then note where your Layer-B verdict **disagrees with Layer-A** — those disagreements are the whole point (they tell us how much the 74.3/65.7/62.9 gap is real vs artifact).

**Critical framing (do not conflate):** this is RAG **end-to-end** faithfulness, NOT `S_acc` (the profiler's lm_eval MCQ on the bare GGUF) and NOT DECISION-002 R@k. **Retrieval was byte-identical across all three models** (same context shown below for all three), so any answer difference is generation-only.

**Known Layer-A false positives to sanity-check first:** Q19 and Q32 (both PASS on the 3B with the gold chunk NOT retrieved). **Known genuine hallucinations:** 1.5B on Q27, Qwen3-4B on U04.

---

## Q01 — exact_fact

**Question:** What is Kibuga's returns window?

**Gold / expected answer:** Two (2) days free returns policy

**Gold chunk retrieved?** YES

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Return_Policy.pdf p.1 (`f232e5d3:0`):** Return Policy Return Policy What are the conditions for returning an item? Two (2) days free returns policy, subject to Terms and conditions. Requirement for a valid procedure • Proof of purchase – the document handed over to you together with the product, on delivery. • Original packaging – the manufacturer packaging • Any free promotional items – gifts or accessories delivered with the purchased item • Valid return reason i.e. If Item is Faulty Please Note: We do not accept returns for the items below. For such purchases, please inspect the item carefully upon delivery or pick up and if necessary, reject it on the spot: • Innerwear, swimsuits, gym wear, sleep wear • Perfumes, jewelry, health & wellness products, adult toys • For missing items and damaged products especially, broken screens please check with our riders during delivery and reject on the spot. How do I return an item/ What happens once I have returned an item? For any return request please contact our Customer Service Call Center at 0742511381/0742511394. and fill the form. What happens once I have returned an item? • We will perform a careful quality check. • If the claim is valid, we will refund you according to your requested refund method. • The process may take up to 2 days from when your return request was submitted. • If the claim is invalid the item will be sent back to you. • We keep track of all return requests and use the data to improve our product quality and service, as well as for customer profiling. Customers with unjustified/invalid returns may be denied the right to return items or even shop on Kibuga in the future. How much time do I have to return a product to Kibuga? • All items sold on Kibuga if faulty, can be returned within a period of 2 days from delivery date.

> **[2] General_Terms_for_Sellers_and_Buyers.pdf p.2 (`1df1cd8d:4`):** 4. Returns and refunds Returns of products by buyers and acceptance of returned products by sellers shall be managed by us in accordance with the returns page on the marketplace, as may be amended from time to time. Acceptance of returns shall be in our discretion, subject to compliance with applicable laws of the territory. Refunds in respect of returned products shall be managed in accordance with the refunds page on the marketplace, as may be amended from time to time. Our rules on refunds shall be exercised in our discretion, subject to applicable laws of the territory. We may offer refunds, in our discretion: Payments In respect of the product price. Shipping fees (as stated on the refunds page); and ● By way of store credits, wallet refunds, vouchers, mobile money transfer, bank transfers or such other method as we may determine from time to time. Returned products shall be accepted and refunds issued by Kibuga, for and on behalf of the seller.

> **[3] Return_Policy.pdf p.1 (`f232e5d3:2`):** Return Policy What now? • On delivery, kindly ensure to verify that the item delivered is in good condition and reject if it does not match your order. Can I return my items after the timeline to return has expired? • Sorry, returns are not possible after the 2-day return period. Do I have to return the gift when I return a product? • Yes, any gift must also be returned. Do I have to pay for shipping charges when I return a product? • There are no charges for shipping a product back to Kibuga.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | Kibuga's returns window is 2 days from the delivery date. | |
| 1.5B | PASS | Kibuga's returns window is two days from delivery date. | |
| Qwen3-4B | PASS | Kibuga's returns window is 2 days from the delivery date. | |

---

## Q02 — exact_fact

**Question:** What is the minimum age to register on the marketplace?

**Gold / expected answer:** 18 years of age

**Gold chunk retrieved?** YES

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] General_Terms_for_Sellers_and_Buyers.pdf p.1 (`1df1cd8d:2`):** 2. Registration and account You may not register with our marketplace if you are under 18 years of age (by using our marketplace or agreeing to these general terms and conditions, you warrant and represent to us that you are at least 18 years of age). ● You may register for an account with our marketplace by completing and submitting the registration form on our marketplace. ● You represent and warrant that all information provided in the registration form is complete and accurate. If you register for an account with our marketplace, you will be asked to provide an email address/user ID and you agree to: ● keep your password confidential. ● Notify us in writing immediately (using our contact details provided) if you become aware of any disclosure of your password; and Be responsible for any activity on our marketplace arising out of any failure to keep your password confidential, and that you may be held liable for any losses arising out of such a failure. Your account shall be used exclusively by you, and you shall not transfer your account to any third party. If you authorize any third party to manage your account on your behalf this shall be at your own risk. We may suspend or cancel your account, and/or edit your account details, at any time in our sole discretion and without notice or explanation, providing that if we cancel any products or services you have paid for but not received, and you have not breached these general terms and conditions, we will refund you in respect of the same. ● You may cancel your account on our marketplace by contacting us. 3. Terms and conditions of sale ● You acknowledge and agree that: ● The marketplace provides an online location for sellers to sell and buyers to purchase products.

> **[2] Sellers_Terms_and_Conditions.pdf p.1 (`9a6d80d1:0`):** Sellers Terms and Conditions Sellers Terms and Conditions Introduction Kibuga Investment operates an e-commerce platform consisting of a website and mobile application (“marketplace”), together with supporting logistics and payment infrastructure, for the sale and purchase of consumer products in Uganda (“territory”). These seller terms and conditions shall apply to all sellers on the marketplace, together with our general terms and conditions of the use of the marketplace. If you register with our marketplace as a seller: a. you accept these seller terms and conditions, the general terms and conditions, and the Kibuga codes, policies and guidelines, and as may be amended by Kibuga from time to time. b. We will ask you to expressly agree to these seller terms and conditions. 1. Seller stores a. If you register with our marketplace as a seller you will be able to create a store on the marketplace, using the “Kibuga” portal. b. Seller stores that are submitted may be reviewed for approval, at Kibuga’s discretion before they are operational. c. You shall be solely responsible for your store, listings and products and you hereby agree that: a. You shall obtain any licenses required for sale of your products on the marketplace. b. To the extent required by applicable law, you shall register with relevant tax authorities and pay all relevant taxes in relation to your product sales. d. d. You shall conduct your business on the marketplace: a. In compliance with the Kibuga Partner Code of Conduct, and other Kibuga codes, policies and guidelines as published on the marketplace from time to time. b. In accordance with ethical business practices and industry best practices; and 1. Without prejudice to our other rights, we reserve the right to reject, unpublish and/or delete any seller store that breaches these seller terms and conditions, the general terms and conditions, or any Kibuga codes, policies and guidelines. 1.

> **[3] General_Terms_for_Sellers_and_Buyers.pdf p.8 (`1df1cd8d:14`):** 1. Limitations and exclusions of liability We accept that we have an interest in limiting the personal liability of our officers and employees and, having regard to that interest, you acknowledge that we are a limited liability entity; you agree that you will not bring any claim personally against our officers or employees in respect of any losses you suffer in connection with the marketplace or these general terms and conditions (this will not limit or exclude the liability of the limited liability entity itself for the acts and omissions of our officers and employees). Our marketplace includes hyperlinks to other websites owned and operated by third parties; such hyperlinks are not recommendations. We have no control over third party websites and their contents, and we accept no responsibility for them or for any loss or damage that may arise from your use of them. 14. Indemnification ● You hereby indemnify us, and undertake to keep us indemnified, against: all losses, damages, costs, liabilities and expenses (including without limitation legal expenses and any amounts paid by us to any third party in settlement of a claim or dispute) incurred or suffered by us and arising directly or indirectly out of your use of our marketplace or any breach by you of any provision of these general terms and conditions or the Kibuga codes, policies or guidelines; and any VAT liability or other tax liability that we may incur in relation to any sale, supply or purchase made through our marketplace, where that liability arises out of your failure to pay, withhold, declare or register to pay any VAT or other tax properly due in any jurisdiction. 1. Breaches of these general terms and conditions If we permit the registration of an account on our marketplace it will remain open indefinitely, subject to these general terms and conditions.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | You may not register with our marketplace if you are under 18 years of age. | |
| 1.5B | PASS | The minimum age to register on the marketplace is 18 years old. | |
| Qwen3-4B | PASS | The minimum age to register on the marketplace is 18 years of age. | |

---

## Q03 — exact_fact

**Question:** What is Kibuga's customer support phone number?

**Gold / expected answer:** +256200959991 / +256740063330

**Gold chunk retrieved?** YES

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Seek_Support.pdf p.1 (`a72cadc9:0`):** Seek Support Seek Support Headquarters: Muganzirwazza Commercial Plaza, Lubiri Road, Plot 1446 Bulange - Mengo, P.O BOX 163315, Kampala, Uganda Customer Support: Email: support@kibuga.com Phone: +256200959991 Phone: +256740063330 Social Media: Follow us on Facebook, Twitter, and Instagram @KibugaOnlineShop Business Hours: Monday to Friday: 08:00 AM - 05:00 PM Saturday: 08:00 AM - 02:00 PM Sunday: Closed For any inquiries, feedback, or support, please contact us through the provided details. Our team is dedicated to assisting you with any questions or concerns you may have.

> **[2] Privacy_Policy.pdf p.3 (`21d0ee2c:12`):** 12. Data Controllers & Contact For questions, concerns, or to exercise your rights, contact our Data Privacy Officer at support@kibuga.com. We will respond to complaints within prescribed timelines.

> **[3] Return_Policy.pdf p.1 (`f232e5d3:0`):** Return Policy Return Policy What are the conditions for returning an item? Two (2) days free returns policy, subject to Terms and conditions. Requirement for a valid procedure • Proof of purchase – the document handed over to you together with the product, on delivery. • Original packaging – the manufacturer packaging • Any free promotional items – gifts or accessories delivered with the purchased item • Valid return reason i.e. If Item is Faulty Please Note: We do not accept returns for the items below. For such purchases, please inspect the item carefully upon delivery or pick up and if necessary, reject it on the spot: • Innerwear, swimsuits, gym wear, sleep wear • Perfumes, jewelry, health & wellness products, adult toys • For missing items and damaged products especially, broken screens please check with our riders during delivery and reject on the spot. How do I return an item/ What happens once I have returned an item? For any return request please contact our Customer Service Call Center at 0742511381/0742511394. and fill the form. What happens once I have returned an item? • We will perform a careful quality check. • If the claim is valid, we will refund you according to your requested refund method. • The process may take up to 2 days from when your return request was submitted. • If the claim is invalid the item will be sent back to you. • We keep track of all return requests and use the data to improve our product quality and service, as well as for customer profiling. Customers with unjustified/invalid returns may be denied the right to return items or even shop on Kibuga in the future. How much time do I have to return a product to Kibuga? • All items sold on Kibuga if faulty, can be returned within a period of 2 days from delivery date.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | Kibuga's customer support phone numbers are +256200959991 and +256740063330. | |
| 1.5B | PASS | +256740063330 | |
| Qwen3-4B | PASS | +256200959991 and +256740063330 | |

---

## Q04 — exact_fact

**Question:** Where are Kibuga's headquarters?

**Gold / expected answer:** Muganzirwazza Commercial Plaza, Lubiri Road, Plot 1446 Bulange - Mengo, Kampala

**Gold chunk retrieved?** YES

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Seek_Support.pdf p.1 (`a72cadc9:0`):** Seek Support Seek Support Headquarters: Muganzirwazza Commercial Plaza, Lubiri Road, Plot 1446 Bulange - Mengo, P.O BOX 163315, Kampala, Uganda Customer Support: Email: support@kibuga.com Phone: +256200959991 Phone: +256740063330 Social Media: Follow us on Facebook, Twitter, and Instagram @KibugaOnlineShop Business Hours: Monday to Friday: 08:00 AM - 05:00 PM Saturday: 08:00 AM - 02:00 PM Sunday: Closed For any inquiries, feedback, or support, please contact us through the provided details. Our team is dedicated to assisting you with any questions or concerns you may have.

> **[2] General_Terms_for_Sellers_and_Buyers.pdf p.5 (`1df1cd8d:10`):** 2. Use of website and mobile applications Use data collected from our website for any direct marketing activity (including without limitation email marketing, SMS marketing, telemarketing and direct mailing); or ● Do anything that interferes with the normal use of our website. 3. Copyright and trademarks ● Subject to the express provisions of these general terms and conditions: we, together with our licensors, own and control all the copyright and other intellectual property rights in our website and the material on our website; and ● All the copyright and other intellectual property rights in our website and the material on our website are reserved. Kibuga’s logos and our other registered and unregistered trademarks are trademarks belonging to us; we give no permission for the use of these trademarks, and such use may constitute an infringement of our rights. The third party registered and unregistered trademarks or service marks on our website are the property of their respective owners and we do not endorse and are not affiliated with any of the holders of any such rights and as such we cannot grant any license to exercise such rights.

> **[3] Privacy_Policy.pdf p.1 (`21d0ee2c:2`):** 2. Who We Are Kibuga is an e-commerce platform in Uganda. Our platform includes our marketplace, logistics service, and payment service, connecting sellers with consumers and facilitating transactions and deliveries. The website and/or mobile app you are using is operated by a member of the Kibuga Business Ventures Limited. Personal data provided or collected by Kibuga is controlled by the relevant subsidiary.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | Kibuga's headquarters are at Muganzirwazza Commercial Plaza, Lubiri Road, Plot 1446 Bulange - Mengo, P.O BOX 163315, Kampala, Uganda. | |
| 1.5B | PASS | Muganzirwazza Commercial Plaza, Lubiri Road, Plot 1446 Bulange - Mengo, P.O BOX 163315, Kampala, Uganda | |
| Qwen3-4B | PASS | The headquarters of Kibuga is located at Muganzirwazza Commercial Plaza, Lubiri Road, Plot 1446 Bulange - Mengo, P.O BOX 163315, Kampala, Uganda. | |

---

## Q05 — exact_fact

**Question:** What is the customer support email address?

**Gold / expected answer:** support@kibuga.com

**Gold chunk retrieved?** YES

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Seek_Support.pdf p.1 (`a72cadc9:0`):** Seek Support Seek Support Headquarters: Muganzirwazza Commercial Plaza, Lubiri Road, Plot 1446 Bulange - Mengo, P.O BOX 163315, Kampala, Uganda Customer Support: Email: support@kibuga.com Phone: +256200959991 Phone: +256740063330 Social Media: Follow us on Facebook, Twitter, and Instagram @KibugaOnlineShop Business Hours: Monday to Friday: 08:00 AM - 05:00 PM Saturday: 08:00 AM - 02:00 PM Sunday: Closed For any inquiries, feedback, or support, please contact us through the provided details. Our team is dedicated to assisting you with any questions or concerns you may have.

> **[2] Privacy_Policy.pdf p.1 (`21d0ee2c:3`):** 3. The Data We Collect About You Personal data refers to information that can identify a specific individual, either directly or indirectly. We collect personal data to provide tailored products and services and to continuously improve them. We may collect, use, store, and transfer various types of personal data for marketing and optimization purposes. Kibuga also uses Google Digital Marketing for targeted offers. Data you provide: ● Contact details: Name, postal addresses, phone numbers, email addresses. ● Demographic information: Date of birth, age, gender. ● Online registration information: Passwords, authentication information. ● Payment information: Credit card information, billing address. ● Survey responses: Customer satisfaction surveys, market research. ● Competition entries and submissions. ● Marketing preferences. Automatically collected data or data from third parties: ● Device information: PC, tablet, mobile device, operating system, browser, IP address. ● Usage information: Searches, views, downloads, purchases, web pages visited. ● User-generated content: Blogs, social media postings. ● Social media data: Username or ID, profile photo, followers. We provide options for managing your personal data, including opting out of personalized experiences and targeted advertising. You can close your account or adjust preferences by contacting us at uganda.legal@Kibuga.com.

> **[3] Privacy_Policy.pdf p.3 (`21d0ee2c:12`):** 12. Data Controllers & Contact For questions, concerns, or to exercise your rights, contact our Data Privacy Officer at support@kibuga.com. We will respond to complaints within prescribed timelines.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | The customer support email address is support@kibuga.com. | |
| 1.5B | PASS | support@kibuga.com | |
| Qwen3-4B | PASS | The customer support email address is support@kibuga.com. | |

---

## Q06 — exact_fact

**Question:** How many pick-up attempts will Kibuga make for a return?

**Gold / expected answer:** 3 attempts within 2 working days

**Gold chunk retrieved?** YES

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Return_Policy.pdf p.1 (`f232e5d3:1`):** Return Policy NOTE: You have 2 days to notify us of your return by calling Customer Service, from the day you received your purchase. For defective items, we also advise you to contact the manufacturer if the product has a warranty. How do I send my product to Kibuga? • We will make 3 attempts within 2 working days to pick-up the returning item after you submit the return request .Note that You can also drop your return item at our offices/Warehouse. However, after 3 pick-up attempts, we will cancel the return procedure and you will not be able to return your product to us anymore. Please ensure that the package of the returning item is in good condition for the return; any package found to be damaged will be rejected by the rider during collection or sent back after quality check is done. How do I track my return status? • We will keep you updated by email and SMS about the status of your return. For any inquiries contact our Customer Service Call Center at 0742511381 / 0742511394.. Is my product under warranty? • We advise you to check our warranty page to get more information about our warranty policy. If my returned product is not validated for refund, how do I get informed? • If your return is invalid, then we will call you to explain the issue and send the item(s) back to you. We will arrange the delivery of the item."Note that we will make two (2) attempts to return the product to you at no cost. However, after two (2) failed attempts, we will cancel the return process and store the product at our warehouse for up to seven (7) days awaiting your collection. If you do not collect the product within these seven (7) days, it will be deemed as forfeited and we will dispose off in accordance with the Ugandan law I received something I didn't order.

> **[2] Return_Policy.pdf p.1 (`f232e5d3:0`):** Return Policy Return Policy What are the conditions for returning an item? Two (2) days free returns policy, subject to Terms and conditions. Requirement for a valid procedure • Proof of purchase – the document handed over to you together with the product, on delivery. • Original packaging – the manufacturer packaging • Any free promotional items – gifts or accessories delivered with the purchased item • Valid return reason i.e. If Item is Faulty Please Note: We do not accept returns for the items below. For such purchases, please inspect the item carefully upon delivery or pick up and if necessary, reject it on the spot: • Innerwear, swimsuits, gym wear, sleep wear • Perfumes, jewelry, health & wellness products, adult toys • For missing items and damaged products especially, broken screens please check with our riders during delivery and reject on the spot. How do I return an item/ What happens once I have returned an item? For any return request please contact our Customer Service Call Center at 0742511381/0742511394. and fill the form. What happens once I have returned an item? • We will perform a careful quality check. • If the claim is valid, we will refund you according to your requested refund method. • The process may take up to 2 days from when your return request was submitted. • If the claim is invalid the item will be sent back to you. • We keep track of all return requests and use the data to improve our product quality and service, as well as for customer profiling. Customers with unjustified/invalid returns may be denied the right to return items or even shop on Kibuga in the future. How much time do I have to return a product to Kibuga? • All items sold on Kibuga if faulty, can be returned within a period of 2 days from delivery date.

> **[3] Return_Policy.pdf p.1 (`f232e5d3:2`):** Return Policy What now? • On delivery, kindly ensure to verify that the item delivered is in good condition and reject if it does not match your order. Can I return my items after the timeline to return has expired? • Sorry, returns are not possible after the 2-day return period. Do I have to return the gift when I return a product? • Yes, any gift must also be returned. Do I have to pay for shipping charges when I return a product? • There are no charges for shipping a product back to Kibuga.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | Kibuga will make 3 attempts within 2 working days to pick up the returning item after you submit the return request. | |
| 1.5B | PASS | Kibuga will make 3 attempts within 2 working days to pick up the returning item after you submit the return request. | |
| Qwen3-4B | PASS | Kibuga will make 3 attempts within 2 working days to pick-up the returning item after you submit the return request. | |

---

## Q07 — paraphrase

**Question:** How long do I have to send something back?

**Gold / expected answer:** 2 days from delivery date

**Gold chunk retrieved?** YES

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Return_Policy.pdf p.1 (`f232e5d3:1`):** Return Policy NOTE: You have 2 days to notify us of your return by calling Customer Service, from the day you received your purchase. For defective items, we also advise you to contact the manufacturer if the product has a warranty. How do I send my product to Kibuga? • We will make 3 attempts within 2 working days to pick-up the returning item after you submit the return request .Note that You can also drop your return item at our offices/Warehouse. However, after 3 pick-up attempts, we will cancel the return procedure and you will not be able to return your product to us anymore. Please ensure that the package of the returning item is in good condition for the return; any package found to be damaged will be rejected by the rider during collection or sent back after quality check is done. How do I track my return status? • We will keep you updated by email and SMS about the status of your return. For any inquiries contact our Customer Service Call Center at 0742511381 / 0742511394.. Is my product under warranty? • We advise you to check our warranty page to get more information about our warranty policy. If my returned product is not validated for refund, how do I get informed? • If your return is invalid, then we will call you to explain the issue and send the item(s) back to you. We will arrange the delivery of the item."Note that we will make two (2) attempts to return the product to you at no cost. However, after two (2) failed attempts, we will cancel the return process and store the product at our warehouse for up to seven (7) days awaiting your collection. If you do not collect the product within these seven (7) days, it will be deemed as forfeited and we will dispose off in accordance with the Ugandan law I received something I didn't order.

> **[2] Return_Policy.pdf p.1 (`f232e5d3:2`):** Return Policy What now? • On delivery, kindly ensure to verify that the item delivered is in good condition and reject if it does not match your order. Can I return my items after the timeline to return has expired? • Sorry, returns are not possible after the 2-day return period. Do I have to return the gift when I return a product? • Yes, any gift must also be returned. Do I have to pay for shipping charges when I return a product? • There are no charges for shipping a product back to Kibuga.

> **[3] Return_Policy.pdf p.1 (`f232e5d3:0`):** Return Policy Return Policy What are the conditions for returning an item? Two (2) days free returns policy, subject to Terms and conditions. Requirement for a valid procedure • Proof of purchase – the document handed over to you together with the product, on delivery. • Original packaging – the manufacturer packaging • Any free promotional items – gifts or accessories delivered with the purchased item • Valid return reason i.e. If Item is Faulty Please Note: We do not accept returns for the items below. For such purchases, please inspect the item carefully upon delivery or pick up and if necessary, reject it on the spot: • Innerwear, swimsuits, gym wear, sleep wear • Perfumes, jewelry, health & wellness products, adult toys • For missing items and damaged products especially, broken screens please check with our riders during delivery and reject on the spot. How do I return an item/ What happens once I have returned an item? For any return request please contact our Customer Service Call Center at 0742511381/0742511394. and fill the form. What happens once I have returned an item? • We will perform a careful quality check. • If the claim is valid, we will refund you according to your requested refund method. • The process may take up to 2 days from when your return request was submitted. • If the claim is invalid the item will be sent back to you. • We keep track of all return requests and use the data to improve our product quality and service, as well as for customer profiling. Customers with unjustified/invalid returns may be denied the right to return items or even shop on Kibuga in the future. How much time do I have to return a product to Kibuga? • All items sold on Kibuga if faulty, can be returned within a period of 2 days from delivery date.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | You have 2 days to notify us of your return by calling Customer Service, from the day you received your purchase. For defective items, we also advise you to contact the manufacturer if the product has a warranty. How do I send my product to Kibuga? • We will make 3 attempts within 2 working days to pick-up the returning item after you submit the return request . | |
| 1.5B | PASS | You have 2 days to notify us of your return by calling Customer Service, from the day you received your purchase. | |
| Qwen3-4B | WEAK | You have 2 days to notify us of your return by calling Customer Service, from the day you received your purchase. We will make 3 attempts within 2 working days to pick-up the returning item after you submit the return request. However, after 3 pick-up attempts, we will cancel the return procedure and you will not be able to return your product to us anymore. Please ensure that the package of the returning item is in good condition for the return; any package found to be damaged will be rejected  … | |

---

## Q08 — paraphrase

**Question:** Can a teenager open an account?

**Gold / expected answer:** No - you may not register if under 18 years of age

**Gold chunk retrieved?** YES

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] General_Terms_for_Sellers_and_Buyers.pdf p.1 (`1df1cd8d:2`):** 2. Registration and account You may not register with our marketplace if you are under 18 years of age (by using our marketplace or agreeing to these general terms and conditions, you warrant and represent to us that you are at least 18 years of age). ● You may register for an account with our marketplace by completing and submitting the registration form on our marketplace. ● You represent and warrant that all information provided in the registration form is complete and accurate. If you register for an account with our marketplace, you will be asked to provide an email address/user ID and you agree to: ● keep your password confidential. ● Notify us in writing immediately (using our contact details provided) if you become aware of any disclosure of your password; and Be responsible for any activity on our marketplace arising out of any failure to keep your password confidential, and that you may be held liable for any losses arising out of such a failure. Your account shall be used exclusively by you, and you shall not transfer your account to any third party. If you authorize any third party to manage your account on your behalf this shall be at your own risk. We may suspend or cancel your account, and/or edit your account details, at any time in our sole discretion and without notice or explanation, providing that if we cancel any products or services you have paid for but not received, and you have not breached these general terms and conditions, we will refund you in respect of the same. ● You may cancel your account on our marketplace by contacting us. 3. Terms and conditions of sale ● You acknowledge and agree that: ● The marketplace provides an online location for sellers to sell and buyers to purchase products.

> **[2] Privacy_Policy.pdf p.3 (`21d0ee2c:11`):** 11. Your Legal Rights You have rights under data protection laws, including accessing, correcting, or erasing your personal data, objecting to or restricting its processing, requesting data transfer to a third party, and unsubscribing from communications. You can close your account or contact us to exercise these rights.

> **[3] General_Terms_for_Sellers_and_Buyers.pdf p.8 (`1df1cd8d:15`):** 1. Limitations and exclusions of liability If you breach these general terms and conditions, or if we reasonably suspect that you have breached these general terms and conditions or any Kibuga codes, policies or guidelines in any way we may: 1. temporarily suspend your access to our marketplace. 2. permanently prohibit you from accessing our marketplace. ● Block computers using your IP address from accessing our marketplace. ● Contact any or all your internet service providers and request that they block your access to our marketplace. ● Suspend or delete your account on our marketplace; and/or ● Commence legal action against you, whether for breach of contract or otherwise. Where we suspend, prohibit or block your access to our marketplace or a part of our marketplace you must not take any action to circumvent such suspension or prohibition or blocking (including without limitation creating and/or using a different account).

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | FAIL | NOT_IN_DOCUMENTS | |
| 1.5B | PASS | No, a teenager cannot register with our marketplace if they are under 18 years of age. | |
| Qwen3-4B | PASS | No, a teenager cannot open an account. The passage states that you may not register with the marketplace if you are under 18 years of age. | |

---

## Q09 — paraphrase

**Question:** What paperwork do I need to bring back a purchase?

**Gold / expected answer:** Proof of purchase, original packaging, any free promotional items

**Gold chunk retrieved?** YES

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Return_Policy.pdf p.1 (`f232e5d3:0`):** Return Policy Return Policy What are the conditions for returning an item? Two (2) days free returns policy, subject to Terms and conditions. Requirement for a valid procedure • Proof of purchase – the document handed over to you together with the product, on delivery. • Original packaging – the manufacturer packaging • Any free promotional items – gifts or accessories delivered with the purchased item • Valid return reason i.e. If Item is Faulty Please Note: We do not accept returns for the items below. For such purchases, please inspect the item carefully upon delivery or pick up and if necessary, reject it on the spot: • Innerwear, swimsuits, gym wear, sleep wear • Perfumes, jewelry, health & wellness products, adult toys • For missing items and damaged products especially, broken screens please check with our riders during delivery and reject on the spot. How do I return an item/ What happens once I have returned an item? For any return request please contact our Customer Service Call Center at 0742511381/0742511394. and fill the form. What happens once I have returned an item? • We will perform a careful quality check. • If the claim is valid, we will refund you according to your requested refund method. • The process may take up to 2 days from when your return request was submitted. • If the claim is invalid the item will be sent back to you. • We keep track of all return requests and use the data to improve our product quality and service, as well as for customer profiling. Customers with unjustified/invalid returns may be denied the right to return items or even shop on Kibuga in the future. How much time do I have to return a product to Kibuga? • All items sold on Kibuga if faulty, can be returned within a period of 2 days from delivery date.

> **[2] Return_Policy.pdf p.1 (`f232e5d3:1`):** Return Policy NOTE: You have 2 days to notify us of your return by calling Customer Service, from the day you received your purchase. For defective items, we also advise you to contact the manufacturer if the product has a warranty. How do I send my product to Kibuga? • We will make 3 attempts within 2 working days to pick-up the returning item after you submit the return request .Note that You can also drop your return item at our offices/Warehouse. However, after 3 pick-up attempts, we will cancel the return procedure and you will not be able to return your product to us anymore. Please ensure that the package of the returning item is in good condition for the return; any package found to be damaged will be rejected by the rider during collection or sent back after quality check is done. How do I track my return status? • We will keep you updated by email and SMS about the status of your return. For any inquiries contact our Customer Service Call Center at 0742511381 / 0742511394.. Is my product under warranty? • We advise you to check our warranty page to get more information about our warranty policy. If my returned product is not validated for refund, how do I get informed? • If your return is invalid, then we will call you to explain the issue and send the item(s) back to you. We will arrange the delivery of the item."Note that we will make two (2) attempts to return the product to you at no cost. However, after two (2) failed attempts, we will cancel the return process and store the product at our warehouse for up to seven (7) days awaiting your collection. If you do not collect the product within these seven (7) days, it will be deemed as forfeited and we will dispose off in accordance with the Ugandan law I received something I didn't order.

> **[3] Return_Policy.pdf p.1 (`f232e5d3:2`):** Return Policy What now? • On delivery, kindly ensure to verify that the item delivered is in good condition and reject if it does not match your order. Can I return my items after the timeline to return has expired? • Sorry, returns are not possible after the 2-day return period. Do I have to return the gift when I return a product? • Yes, any gift must also be returned. Do I have to pay for shipping charges when I return a product? • There are no charges for shipping a product back to Kibuga.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | To return a purchase, you need to bring Proof of Purchase, the original packaging, and any free promotional items such as gifts or accessories delivered with the purchased item. | |
| 1.5B | PASS | Proof of purchase – the document handed over to you together with the product, on delivery. | |
| Qwen3-4B | PASS | The paperwork needed to return a purchase includes proof of purchase – the document handed over to you together with the product, on delivery. Original packaging – the manufacturer packaging, and any free promotional items – gifts or accessories delivered with the purchased item. | |

---

## Q10 — paraphrase

**Question:** Which goods can't be sent back?

**Gold / expected answer:** Innerwear, swimsuits, gym wear, sleep wear, perfumes, jewelry, health & wellness products, adult toys

**Gold chunk retrieved?** YES

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Return_Policy.pdf p.1 (`f232e5d3:2`):** Return Policy What now? • On delivery, kindly ensure to verify that the item delivered is in good condition and reject if it does not match your order. Can I return my items after the timeline to return has expired? • Sorry, returns are not possible after the 2-day return period. Do I have to return the gift when I return a product? • Yes, any gift must also be returned. Do I have to pay for shipping charges when I return a product? • There are no charges for shipping a product back to Kibuga.

> **[2] Return_Policy.pdf p.1 (`f232e5d3:1`):** Return Policy NOTE: You have 2 days to notify us of your return by calling Customer Service, from the day you received your purchase. For defective items, we also advise you to contact the manufacturer if the product has a warranty. How do I send my product to Kibuga? • We will make 3 attempts within 2 working days to pick-up the returning item after you submit the return request .Note that You can also drop your return item at our offices/Warehouse. However, after 3 pick-up attempts, we will cancel the return procedure and you will not be able to return your product to us anymore. Please ensure that the package of the returning item is in good condition for the return; any package found to be damaged will be rejected by the rider during collection or sent back after quality check is done. How do I track my return status? • We will keep you updated by email and SMS about the status of your return. For any inquiries contact our Customer Service Call Center at 0742511381 / 0742511394.. Is my product under warranty? • We advise you to check our warranty page to get more information about our warranty policy. If my returned product is not validated for refund, how do I get informed? • If your return is invalid, then we will call you to explain the issue and send the item(s) back to you. We will arrange the delivery of the item."Note that we will make two (2) attempts to return the product to you at no cost. However, after two (2) failed attempts, we will cancel the return process and store the product at our warehouse for up to seven (7) days awaiting your collection. If you do not collect the product within these seven (7) days, it will be deemed as forfeited and we will dispose off in accordance with the Ugandan law I received something I didn't order.

> **[3] Return_Policy.pdf p.1 (`f232e5d3:0`):** Return Policy Return Policy What are the conditions for returning an item? Two (2) days free returns policy, subject to Terms and conditions. Requirement for a valid procedure • Proof of purchase – the document handed over to you together with the product, on delivery. • Original packaging – the manufacturer packaging • Any free promotional items – gifts or accessories delivered with the purchased item • Valid return reason i.e. If Item is Faulty Please Note: We do not accept returns for the items below. For such purchases, please inspect the item carefully upon delivery or pick up and if necessary, reject it on the spot: • Innerwear, swimsuits, gym wear, sleep wear • Perfumes, jewelry, health & wellness products, adult toys • For missing items and damaged products especially, broken screens please check with our riders during delivery and reject on the spot. How do I return an item/ What happens once I have returned an item? For any return request please contact our Customer Service Call Center at 0742511381/0742511394. and fill the form. What happens once I have returned an item? • We will perform a careful quality check. • If the claim is valid, we will refund you according to your requested refund method. • The process may take up to 2 days from when your return request was submitted. • If the claim is invalid the item will be sent back to you. • We keep track of all return requests and use the data to improve our product quality and service, as well as for customer profiling. Customers with unjustified/invalid returns may be denied the right to return items or even shop on Kibuga in the future. How much time do I have to return a product to Kibuga? • All items sold on Kibuga if faulty, can be returned within a period of 2 days from delivery date.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | Innerwear, swimsuits, gym wear, sleep wear, Perfumes, jewelry, health & wellness products, adult toys. | |
| 1.5B | PASS | Innerwear, swimsuits, gym wear, sleep wear, Perfumes, jewelry, health & wellness products, adult toys, Missing items and damaged products especially, broken screens. | |
| Qwen3-4B | PASS | The goods that cannot be sent back are: innerwear, swimsuits, gym wear, sleep wear, perfumes, jewelry, health & wellness products, and adult toys. | |

---

## Q12 — paraphrase

**Question:** How do I get in touch if something goes wrong?

**Gold / expected answer:** Customer Service Call Center 0742511381/0742511394, or support@kibuga.com

**Gold chunk retrieved?** YES

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Return_Policy.pdf p.1 (`f232e5d3:1`):** Return Policy NOTE: You have 2 days to notify us of your return by calling Customer Service, from the day you received your purchase. For defective items, we also advise you to contact the manufacturer if the product has a warranty. How do I send my product to Kibuga? • We will make 3 attempts within 2 working days to pick-up the returning item after you submit the return request .Note that You can also drop your return item at our offices/Warehouse. However, after 3 pick-up attempts, we will cancel the return procedure and you will not be able to return your product to us anymore. Please ensure that the package of the returning item is in good condition for the return; any package found to be damaged will be rejected by the rider during collection or sent back after quality check is done. How do I track my return status? • We will keep you updated by email and SMS about the status of your return. For any inquiries contact our Customer Service Call Center at 0742511381 / 0742511394.. Is my product under warranty? • We advise you to check our warranty page to get more information about our warranty policy. If my returned product is not validated for refund, how do I get informed? • If your return is invalid, then we will call you to explain the issue and send the item(s) back to you. We will arrange the delivery of the item."Note that we will make two (2) attempts to return the product to you at no cost. However, after two (2) failed attempts, we will cancel the return process and store the product at our warehouse for up to seven (7) days awaiting your collection. If you do not collect the product within these seven (7) days, it will be deemed as forfeited and we will dispose off in accordance with the Ugandan law I received something I didn't order.

> **[2] Return_Policy.pdf p.1 (`f232e5d3:0`):** Return Policy Return Policy What are the conditions for returning an item? Two (2) days free returns policy, subject to Terms and conditions. Requirement for a valid procedure • Proof of purchase – the document handed over to you together with the product, on delivery. • Original packaging – the manufacturer packaging • Any free promotional items – gifts or accessories delivered with the purchased item • Valid return reason i.e. If Item is Faulty Please Note: We do not accept returns for the items below. For such purchases, please inspect the item carefully upon delivery or pick up and if necessary, reject it on the spot: • Innerwear, swimsuits, gym wear, sleep wear • Perfumes, jewelry, health & wellness products, adult toys • For missing items and damaged products especially, broken screens please check with our riders during delivery and reject on the spot. How do I return an item/ What happens once I have returned an item? For any return request please contact our Customer Service Call Center at 0742511381/0742511394. and fill the form. What happens once I have returned an item? • We will perform a careful quality check. • If the claim is valid, we will refund you according to your requested refund method. • The process may take up to 2 days from when your return request was submitted. • If the claim is invalid the item will be sent back to you. • We keep track of all return requests and use the data to improve our product quality and service, as well as for customer profiling. Customers with unjustified/invalid returns may be denied the right to return items or even shop on Kibuga in the future. How much time do I have to return a product to Kibuga? • All items sold on Kibuga if faulty, can be returned within a period of 2 days from delivery date.

> **[3] Return_Policy.pdf p.1 (`f232e5d3:2`):** Return Policy What now? • On delivery, kindly ensure to verify that the item delivered is in good condition and reject if it does not match your order. Can I return my items after the timeline to return has expired? • Sorry, returns are not possible after the 2-day return period. Do I have to return the gift when I return a product? • Yes, any gift must also be returned. Do I have to pay for shipping charges when I return a product? • There are no charges for shipping a product back to Kibuga.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | If something goes wrong with your order or return process, you can contact our Customer Service Call Center at 0742511381/0742511394 for any inquiries. They will assist you in resolving issues and guide you through the return procedure. | |
| 1.5B | PASS | You can contact our Customer Service Call Center at 0742511381/0742511394 for inquiries or to inform us of any issues with your return process. | |
| Qwen3-4B | PASS | To get in touch if something goes wrong, you can contact the Customer Service Call Center at 0742511381 or 0742511394. Additionally, you can reach out to them for any inquiries related to returns, tracking your return status, or other issues. If your returned product is not validated for a refund, you will be called to explain the issue and the item will be sent back to you. If there are any problems with the return process, you can also contact Customer Service for assistance. | |

---

## Q13 — near_miss

**Question:** How long does a refund take to process?

**Gold / expected answer:** The process may take up to 2 days from when the return request was submitted

**Gold chunk retrieved?** YES

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Return_Policy.pdf p.1 (`f232e5d3:0`):** Return Policy Return Policy What are the conditions for returning an item? Two (2) days free returns policy, subject to Terms and conditions. Requirement for a valid procedure • Proof of purchase – the document handed over to you together with the product, on delivery. • Original packaging – the manufacturer packaging • Any free promotional items – gifts or accessories delivered with the purchased item • Valid return reason i.e. If Item is Faulty Please Note: We do not accept returns for the items below. For such purchases, please inspect the item carefully upon delivery or pick up and if necessary, reject it on the spot: • Innerwear, swimsuits, gym wear, sleep wear • Perfumes, jewelry, health & wellness products, adult toys • For missing items and damaged products especially, broken screens please check with our riders during delivery and reject on the spot. How do I return an item/ What happens once I have returned an item? For any return request please contact our Customer Service Call Center at 0742511381/0742511394. and fill the form. What happens once I have returned an item? • We will perform a careful quality check. • If the claim is valid, we will refund you according to your requested refund method. • The process may take up to 2 days from when your return request was submitted. • If the claim is invalid the item will be sent back to you. • We keep track of all return requests and use the data to improve our product quality and service, as well as for customer profiling. Customers with unjustified/invalid returns may be denied the right to return items or even shop on Kibuga in the future. How much time do I have to return a product to Kibuga? • All items sold on Kibuga if faulty, can be returned within a period of 2 days from delivery date.

> **[2] Return_Policy.pdf p.1 (`f232e5d3:1`):** Return Policy NOTE: You have 2 days to notify us of your return by calling Customer Service, from the day you received your purchase. For defective items, we also advise you to contact the manufacturer if the product has a warranty. How do I send my product to Kibuga? • We will make 3 attempts within 2 working days to pick-up the returning item after you submit the return request .Note that You can also drop your return item at our offices/Warehouse. However, after 3 pick-up attempts, we will cancel the return procedure and you will not be able to return your product to us anymore. Please ensure that the package of the returning item is in good condition for the return; any package found to be damaged will be rejected by the rider during collection or sent back after quality check is done. How do I track my return status? • We will keep you updated by email and SMS about the status of your return. For any inquiries contact our Customer Service Call Center at 0742511381 / 0742511394.. Is my product under warranty? • We advise you to check our warranty page to get more information about our warranty policy. If my returned product is not validated for refund, how do I get informed? • If your return is invalid, then we will call you to explain the issue and send the item(s) back to you. We will arrange the delivery of the item."Note that we will make two (2) attempts to return the product to you at no cost. However, after two (2) failed attempts, we will cancel the return process and store the product at our warehouse for up to seven (7) days awaiting your collection. If you do not collect the product within these seven (7) days, it will be deemed as forfeited and we will dispose off in accordance with the Ugandan law I received something I didn't order.

> **[3] Return_Policy.pdf p.1 (`f232e5d3:2`):** Return Policy What now? • On delivery, kindly ensure to verify that the item delivered is in good condition and reject if it does not match your order. Can I return my items after the timeline to return has expired? • Sorry, returns are not possible after the 2-day return period. Do I have to return the gift when I return a product? • Yes, any gift must also be returned. Do I have to pay for shipping charges when I return a product? • There are no charges for shipping a product back to Kibuga.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | The process may take up to 2 days from when your return request was submitted. | |
| 1.5B | PASS | The process may take up to 2 days from when your return request was submitted. | |
| Qwen3-4B | PASS | The process may take up to 2 days from when your return request was submitted. | |

---

## Q14 — near_miss

**Question:** What happens if my return claim is rejected?

**Gold / expected answer:** If the claim is invalid the item will be sent back to you

**Gold chunk retrieved?** YES

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Return_Policy.pdf p.1 (`f232e5d3:0`):** Return Policy Return Policy What are the conditions for returning an item? Two (2) days free returns policy, subject to Terms and conditions. Requirement for a valid procedure • Proof of purchase – the document handed over to you together with the product, on delivery. • Original packaging – the manufacturer packaging • Any free promotional items – gifts or accessories delivered with the purchased item • Valid return reason i.e. If Item is Faulty Please Note: We do not accept returns for the items below. For such purchases, please inspect the item carefully upon delivery or pick up and if necessary, reject it on the spot: • Innerwear, swimsuits, gym wear, sleep wear • Perfumes, jewelry, health & wellness products, adult toys • For missing items and damaged products especially, broken screens please check with our riders during delivery and reject on the spot. How do I return an item/ What happens once I have returned an item? For any return request please contact our Customer Service Call Center at 0742511381/0742511394. and fill the form. What happens once I have returned an item? • We will perform a careful quality check. • If the claim is valid, we will refund you according to your requested refund method. • The process may take up to 2 days from when your return request was submitted. • If the claim is invalid the item will be sent back to you. • We keep track of all return requests and use the data to improve our product quality and service, as well as for customer profiling. Customers with unjustified/invalid returns may be denied the right to return items or even shop on Kibuga in the future. How much time do I have to return a product to Kibuga? • All items sold on Kibuga if faulty, can be returned within a period of 2 days from delivery date.

> **[2] Return_Policy.pdf p.1 (`f232e5d3:1`):** Return Policy NOTE: You have 2 days to notify us of your return by calling Customer Service, from the day you received your purchase. For defective items, we also advise you to contact the manufacturer if the product has a warranty. How do I send my product to Kibuga? • We will make 3 attempts within 2 working days to pick-up the returning item after you submit the return request .Note that You can also drop your return item at our offices/Warehouse. However, after 3 pick-up attempts, we will cancel the return procedure and you will not be able to return your product to us anymore. Please ensure that the package of the returning item is in good condition for the return; any package found to be damaged will be rejected by the rider during collection or sent back after quality check is done. How do I track my return status? • We will keep you updated by email and SMS about the status of your return. For any inquiries contact our Customer Service Call Center at 0742511381 / 0742511394.. Is my product under warranty? • We advise you to check our warranty page to get more information about our warranty policy. If my returned product is not validated for refund, how do I get informed? • If your return is invalid, then we will call you to explain the issue and send the item(s) back to you. We will arrange the delivery of the item."Note that we will make two (2) attempts to return the product to you at no cost. However, after two (2) failed attempts, we will cancel the return process and store the product at our warehouse for up to seven (7) days awaiting your collection. If you do not collect the product within these seven (7) days, it will be deemed as forfeited and we will dispose off in accordance with the Ugandan law I received something I didn't order.

> **[3] Return_Policy.pdf p.1 (`f232e5d3:2`):** Return Policy What now? • On delivery, kindly ensure to verify that the item delivered is in good condition and reject if it does not match your order. Can I return my items after the timeline to return has expired? • Sorry, returns are not possible after the 2-day return period. Do I have to return the gift when I return a product? • Yes, any gift must also be returned. Do I have to pay for shipping charges when I return a product? • There are no charges for shipping a product back to Kibuga.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | WEAK | If your return claim is invalid, we will call you to explain the issue and send the item(s) back to you. We will arrange the delivery of the item. Note that we will make two (2) attempts to return the product to you at no cost. However, after two (2) failed attempts, we will cancel the return process and store the product at our warehouse for up to seven (7) days awaiting your collection. If you do not collect the product within these seven (7) days, it will be deemed as forfeited and we will di … | |
| 1.5B | WEAK | If your return claim is rejected, then we will call you to explain the issue and send the item(s) back to you. We will arrange the delivery of the item. Note that we will make two (2) attempts to return the product to you at no cost. However, after two (2) failed attempts, we will cancel the return process and store the product at our warehouse for up to seven (7) days awaiting your collection. If you do not collect the product within these seven (7) days, it will be deemed as forfeited and we w … | |
| Qwen3-4B | WEAK | If your return claim is rejected, the item will be sent back to you. We will call you to explain the issue and arrange the delivery of the item. We will make two (2) attempts to return the product to you at no cost. However, after two (2) failed attempts, we will cancel the return process and store the product at our warehouse for up to seven (7) days awaiting your collection. If you do not collect the product within these seven (7) days, it will be deemed as forfeited and we will dispose off in … | |

---

## Q15 — prose

**Question:** What kinds of content am I forbidden from posting?

**Gold / expected answer:** Offensive, obscene, indecent, pornographic, lewd, suggestive, sexually explicit; violence; blasphemous or hateful content

**Gold chunk retrieved?** YES

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] General_Terms_for_Sellers_and_Buyers.pdf p.3 (`1df1cd8d:6`):** 5. Rules about your content You must not use our marketplace to link to any website or web page consisting of or containing material that would, were it posted on our marketplace, breach the provisions of these general terms and conditions. ● You must not submit to our marketplace any material that is or has ever been the subject of any threatened or actual legal proceedings or other similar complaint. The review function on the marketplace may be used to facilitate buyer reviews on products. You shall not use the review function or any other form of communication to provide inaccurate, inauthentic or fake reviews. You must not interfere with a transaction by: (i) contacting another user to buy or sell an item listed on the marketplace outside of the marketplace; or (ii) communicating with a user involved in an active or completed transaction to warn them away from a particular buyer, seller or item; or (iii) contacting another user with the intent to collect any payments. You acknowledge that all users of the marketplace are solely responsible for interactions with other users, and you shall exercise caution and good judgment in your communication with users. You shall not send them personal information including credit card details. ● We may periodically review your content and we reserve the right to remove any content in our discretion for any reason whatsoever. activity that breaches these general terms and conditions, you may inform us by contacting us. Our rights to use your content You grant us a non-exclusive, royalty-free license to use, reproduce, store, adapt, publish, translate and distribute your content across our marketing channels and any existing or future media. ● You grant us the right to sub-license the rights licensed. ● You grant to us the right to bring an action for infringement of the rights licensed under section 7.1.

> **[2] General_Terms_for_Sellers_and_Buyers.pdf p.3 (`1df1cd8d:5`):** 5. Rules about your content In these general terms and conditions, "your content" means: All works and materials (including without limitation text, graphics, images, audio material, video material, audio-visual material, scripts, software and files) that you submit to us or our marketplace for storage or publication, processing by, or onward transmission; and ● All communications on the marketplace, including product reviews, feedback and comments. Your content, and the use of your content by us in accordance with these general terms and conditions, must be accurate, complete and truthful. Your content must be appropriate, civil and tasteful, and accord with generally accepted standards of etiquette and behavior on the internet, and must not: ● Be offensive, obscene, indecent, pornographic, lewd, suggestive or sexually explicit. Depict violence in an explicit, graphic or gratuitous manner; or ● Be blasphemous, in breach of racial or religious hatred or discrimination legislation. ● Be deceptive, fraudulent, threatening, abusive, harassing, anti-social, menacing, hateful, discriminatory or inflammatory. Cause annoyance, inconvenience or needless anxiety to any person; or Constitute spam. Your content must not be illegal or unlawful, infringe any person's legal rights, or be capable of giving rise to legal action against any person (in each case in any jurisdiction and under any applicable law). Your content must not infringe or breach: ● Any copyright, moral right, database right, trademark right, design right, right in passing off or other intellectual property right. ● Any right of confidence, right of privacy or right under data protection legislation. ● Any contractual obligation owed to any person; or ● Any court order.

> **[3] General_Terms_for_Sellers_and_Buyers.pdf p.3 (`1df1cd8d:7`):** 5. Rules about your content You hereby waive all your moral rights in your content to the maximum extent permitted by applicable law; and you warrant and represent that all other moral rights in your content have been waived to the maximum extent permitted by applicable law. Without prejudice to our other rights under these general terms and conditions, if you breach our rules on content in any way, or if we reasonably suspect that you have breached our rules on content, we may delete, unpublish or edit any or all your content.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | You are forbidden from posting offensive, obscene, indecent, pornographic, lewd, suggestive, sexually explicit, violent in an explicit, graphic or gratuitous manner, blasphemous, discriminatory, inflammatory, annoying, abusive, harassing, anti-social, hateful, or causing annoyance, inconvenience, or needless anxiety content. Your content must not be illegal or unlawful, infringe any person's legal rights, give rise to legal action against any person under any applicable law, infringe or breach a … | |
| 1.5B | PASS | You are forbidden from posting material that would breach provisions of these general terms and conditions, including but not limited to offensive, indecent, pornographic, blasphemous, deceptive, fraudulent, threatening, abusive, harassing, spam, or illegal content. Additionally, you must ensure your content is accurate, complete, truthful, appropriate, civil, tasteful, and does not infringe on intellectual property rights, moral rights, or contractual obligations. | |
| Qwen3-4B | PASS | You are forbidden from posting content that is offensive, obscene, indecent, pornographic, lewd, suggestive, or sexually explicit. You are also forbidden from depicting violence in an explicit, graphic, or gratuitous manner. The content must not be blasphemous, in breach of racial or religious hatred or discrimination legislation. It must not be deceptive, fraudulent, threatening, abusive, harassing, anti-social, menacing, hateful, discriminatory, or inflammatory. The content must not cause anno … | |

---

## Q16 — prose

**Question:** What personal data does Kibuga collect?

**Gold / expected answer:** Personal data collected when you visit the website or mobile applications

**Gold chunk retrieved?** YES

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Privacy_Policy.pdf p.1 (`21d0ee2c:3`):** 3. The Data We Collect About You Personal data refers to information that can identify a specific individual, either directly or indirectly. We collect personal data to provide tailored products and services and to continuously improve them. We may collect, use, store, and transfer various types of personal data for marketing and optimization purposes. Kibuga also uses Google Digital Marketing for targeted offers. Data you provide: ● Contact details: Name, postal addresses, phone numbers, email addresses. ● Demographic information: Date of birth, age, gender. ● Online registration information: Passwords, authentication information. ● Payment information: Credit card information, billing address. ● Survey responses: Customer satisfaction surveys, market research. ● Competition entries and submissions. ● Marketing preferences. Automatically collected data or data from third parties: ● Device information: PC, tablet, mobile device, operating system, browser, IP address. ● Usage information: Searches, views, downloads, purchases, web pages visited. ● User-generated content: Blogs, social media postings. ● Social media data: Username or ID, profile photo, followers. We provide options for managing your personal data, including opting out of personalized experiences and targeted advertising. You can close your account or adjust preferences by contacting us at uganda.legal@Kibuga.com.

> **[2] Privacy_Policy.pdf p.1 (`21d0ee2c:1`):** 1. About this Notice This Privacy Notice provides information on how Kibuga collects and processes your personal data when you visit our website or mobile applications. It outlines what we do with your personal data, how we keep it secure, and explains the rights you have regarding your personal data.

> **[3] Privacy_Policy.pdf p.1 (`21d0ee2c:2`):** 2. Who We Are Kibuga is an e-commerce platform in Uganda. Our platform includes our marketplace, logistics service, and payment service, connecting sellers with consumers and facilitating transactions and deliveries. The website and/or mobile app you are using is operated by a member of the Kibuga Business Ventures Limited. Personal data provided or collected by Kibuga is controlled by the relevant subsidiary.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | FAIL | Kibuga collects various types of personal data including contact details such as name and email addresses, demographic information like date of birth and gender, online registration information like passwords and authentication details, payment information such as credit card information and billing address, survey responses, competition entries and submissions, marketing preferences, device information, usage information, user-generated content, and social media data. | |
| 1.5B | FAIL | Kibuga collects various types of personal data including contact details (Name, postal addresses, phone numbers, email addresses), demographic information (Date of birth, age, gender), online registration information (passwords, authentication information), payment information (credit card information, billing address), survey responses (customer satisfaction surveys, market research), competition entries and submissions, marketing preferences, device information (PC, tablet, mobile device, oper … | |
| Qwen3-4B | FAIL | Kibuga collects the following personal data: - Data you provide: - Contact details: Name, postal addresses, phone numbers, email addresses. - Demographic information: Date of birth, age, gender. - Online registration information: Passwords, authentication information. - Payment information: Credit card information, billing address. - Survey responses: Customer satisfaction surveys, market research. - Competition entries and submissions. - Marketing preferences. - Automatically collected data or  … | |

---

## Q17 — prose

**Question:** What warranty does a seller give about the products?

**Gold / expected answer:** Seller warrants good title, sole legal and beneficial owner, no third-party rights or restrictions

**Gold chunk retrieved?** NO — retrieval missed the gold chunk

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Return_Policy.pdf p.1 (`f232e5d3:0`):** Return Policy Return Policy What are the conditions for returning an item? Two (2) days free returns policy, subject to Terms and conditions. Requirement for a valid procedure • Proof of purchase – the document handed over to you together with the product, on delivery. • Original packaging – the manufacturer packaging • Any free promotional items – gifts or accessories delivered with the purchased item • Valid return reason i.e. If Item is Faulty Please Note: We do not accept returns for the items below. For such purchases, please inspect the item carefully upon delivery or pick up and if necessary, reject it on the spot: • Innerwear, swimsuits, gym wear, sleep wear • Perfumes, jewelry, health & wellness products, adult toys • For missing items and damaged products especially, broken screens please check with our riders during delivery and reject on the spot. How do I return an item/ What happens once I have returned an item? For any return request please contact our Customer Service Call Center at 0742511381/0742511394. and fill the form. What happens once I have returned an item? • We will perform a careful quality check. • If the claim is valid, we will refund you according to your requested refund method. • The process may take up to 2 days from when your return request was submitted. • If the claim is invalid the item will be sent back to you. • We keep track of all return requests and use the data to improve our product quality and service, as well as for customer profiling. Customers with unjustified/invalid returns may be denied the right to return items or even shop on Kibuga in the future. How much time do I have to return a product to Kibuga? • All items sold on Kibuga if faulty, can be returned within a period of 2 days from delivery date.

> **[2] Return_Policy.pdf p.1 (`f232e5d3:1`):** Return Policy NOTE: You have 2 days to notify us of your return by calling Customer Service, from the day you received your purchase. For defective items, we also advise you to contact the manufacturer if the product has a warranty. How do I send my product to Kibuga? • We will make 3 attempts within 2 working days to pick-up the returning item after you submit the return request .Note that You can also drop your return item at our offices/Warehouse. However, after 3 pick-up attempts, we will cancel the return procedure and you will not be able to return your product to us anymore. Please ensure that the package of the returning item is in good condition for the return; any package found to be damaged will be rejected by the rider during collection or sent back after quality check is done. How do I track my return status? • We will keep you updated by email and SMS about the status of your return. For any inquiries contact our Customer Service Call Center at 0742511381 / 0742511394.. Is my product under warranty? • We advise you to check our warranty page to get more information about our warranty policy. If my returned product is not validated for refund, how do I get informed? • If your return is invalid, then we will call you to explain the issue and send the item(s) back to you. We will arrange the delivery of the item."Note that we will make two (2) attempts to return the product to you at no cost. However, after two (2) failed attempts, we will cancel the return process and store the product at our warehouse for up to seven (7) days awaiting your collection. If you do not collect the product within these seven (7) days, it will be deemed as forfeited and we will dispose off in accordance with the Ugandan law I received something I didn't order.

> **[3] Sellers_Terms_and_Conditions.pdf p.1 (`9a6d80d1:1`):** Sellers Terms and Conditions Product listings a. You shall be responsible for listing your products on the marketplace by uploading to the Seller Centre a completed product page which shall include prices, detailed information, specifications and images in respect of each product. b. You may not publish more than one listing in respect of each product. c. You agree to be solely responsible for all listings submitted to our marketplace and you agree that all listings must: ● constitute bona fide listings relating to products that comply with the categories and rules set out. ● comply with the rules on content in the general terms and conditions and further particularized in the Content and Image Guidelines; and d. Include all such information, specifications and guidelines as may be required pursuant to all applicable laws and regulations, including in respect of consumer protection. e. Listings that are submitted may be individually reviewed and approved at Kibuga’s discretion, before they are published on the marketplace, and you acknowledge and agree there may be a lead time between submission of the product page to the Seller Centre and the publishing of the Product page on the marketplace due to time required for Kibuga quality control operations. f. Without prejudice to our other rights, we reserve the right to reject, unpublish and/or delete any listings that breach these seller terms and conditions, the general terms and conditions or any Kibuga codes, policies or guidelines. g. You acknowledge and agree that: ● Notwithstanding that we may approve any listings, you shall be fully responsible for the same; and ● We reserve the right to impose penalties for breach of this section 3, without prejudice to our other rights. ● You must keep your listings up to date. You must deactivate any listings in respect of products that have ceased to be available. 1. The products a. The only products that may be the subject of a listing on our marketplace are products falling within the product categories specified on the marketplace. b.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | FAIL | NOT_IN_DOCUMENTS | |
| 1.5B | FAIL | NOT_IN_DOCUMENTS | |
| Qwen3-4B | FAIL | The documents do not explicitly state what warranty a seller gives about the products. However, they mention that customers should check the warranty page for more information about the warranty policy. Additionally, for defective items, the company advises contacting the manufacturer if the product has a warranty. Therefore, the information provided does not specify the warranty given by the seller. NOT_IN_DOCUMENTS | |

---

## Q19 — prose

**Question:** Can Kibuga suspend my account without telling me?

**Gold / expected answer:** We may suspend or cancel your account at any time in our sole discretion and without notice or explanation

**Gold chunk retrieved?** NO — retrieval missed the gold chunk

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] General_Terms_for_Sellers_and_Buyers.pdf p.8 (`1df1cd8d:15`):** 1. Limitations and exclusions of liability If you breach these general terms and conditions, or if we reasonably suspect that you have breached these general terms and conditions or any Kibuga codes, policies or guidelines in any way we may: 1. temporarily suspend your access to our marketplace. 2. permanently prohibit you from accessing our marketplace. ● Block computers using your IP address from accessing our marketplace. ● Contact any or all your internet service providers and request that they block your access to our marketplace. ● Suspend or delete your account on our marketplace; and/or ● Commence legal action against you, whether for breach of contract or otherwise. Where we suspend, prohibit or block your access to our marketplace or a part of our marketplace you must not take any action to circumvent such suspension or prohibition or blocking (including without limitation creating and/or using a different account).

> **[2] Sellers_Terms_and_Conditions.pdf p.1 (`9a6d80d1:6`):** Sellers Terms and Conditions If we reasonably determine that you have breached these seller terms and conditions, our general terms and conditions, or any Kibuga codes, policies or guidelines, we may: 1. send you one or more formal warnings. b. suspend, prohibit or block your access to our marketplace as provided in the general terms and conditions. c. apply penalties for breach as provided in our Seller Penalty Policy; and/or d. commence legal action against you, whether for breach of contract or otherwise. 2. We may vary the amount of the penalties for breach from time to time by updating the Seller Penalty Policy, but this will not affect any liability to pay penalties that accrue before the new amounts are posted. Confidentiality and data privacy All information and documents concerning the conduct of business pursuant to these general terms and conditions, including information relating to business methods, procedures, policies and sales information, is strictly confidential unless it is already in the public domain. You shall not use Kibuga’s confidential information for any purpose other than to perform your obligations under this Agreement and you shall not disclose Kibuga’s confidential information without our prior written consent. Sellers may not send advertising or promotional communications to buyers on the marketplace without the prior written consent of Kibuga and shall be directly responsible to marketplace users for any misuse of their personal data. If Kibuga is sued, fined, or otherwise incurs expenses because of the seller’s handling of personal data obtained through the marketplace, the seller shall indemnify Kibuga in respect of the same.

> **[3] Return_Policy.pdf p.1 (`f232e5d3:1`):** Return Policy NOTE: You have 2 days to notify us of your return by calling Customer Service, from the day you received your purchase. For defective items, we also advise you to contact the manufacturer if the product has a warranty. How do I send my product to Kibuga? • We will make 3 attempts within 2 working days to pick-up the returning item after you submit the return request .Note that You can also drop your return item at our offices/Warehouse. However, after 3 pick-up attempts, we will cancel the return procedure and you will not be able to return your product to us anymore. Please ensure that the package of the returning item is in good condition for the return; any package found to be damaged will be rejected by the rider during collection or sent back after quality check is done. How do I track my return status? • We will keep you updated by email and SMS about the status of your return. For any inquiries contact our Customer Service Call Center at 0742511381 / 0742511394.. Is my product under warranty? • We advise you to check our warranty page to get more information about our warranty policy. If my returned product is not validated for refund, how do I get informed? • If your return is invalid, then we will call you to explain the issue and send the item(s) back to you. We will arrange the delivery of the item."Note that we will make two (2) attempts to return the product to you at no cost. However, after two (2) failed attempts, we will cancel the return process and store the product at our warehouse for up to seven (7) days awaiting your collection. If you do not collect the product within these seven (7) days, it will be deemed as forfeited and we will dispose off in accordance with the Ugandan law I received something I didn't order.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | If you breach these general terms and conditions or if we reasonably suspect that you have breached any Kibuga codes, policies or guidelines in any way, we may temporarily suspend your access to our marketplace. Therefore, based on the information provided, Kibuga can suspend your account without telling you beforehand. | |
| 1.5B | WEAK | Yes, Kibuga may temporarily or permanently suspend your access to their marketplace without notifying you. | |
| Qwen3-4B | FAIL | Yes, Kibuga can suspend your account without telling you. According to passage [1], if you breach the general terms and conditions or any Kibuga codes, policies or guidelines, Kibuga may temporarily suspend your access to their marketplace. The passage also states that you must not take any action to circumvent such suspension, implying that the suspension may occur without prior notification. | |

---

## Q21 — multi_chunk

**Question:** What is the full returns procedure from request to refund?

**Gold / expected answer:** Contact call centre, 3 pickup attempts in 2 working days, quality check, refund per requested method within 2 days

**Gold chunk retrieved?** YES

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Return_Policy.pdf p.1 (`f232e5d3:0`):** Return Policy Return Policy What are the conditions for returning an item? Two (2) days free returns policy, subject to Terms and conditions. Requirement for a valid procedure • Proof of purchase – the document handed over to you together with the product, on delivery. • Original packaging – the manufacturer packaging • Any free promotional items – gifts or accessories delivered with the purchased item • Valid return reason i.e. If Item is Faulty Please Note: We do not accept returns for the items below. For such purchases, please inspect the item carefully upon delivery or pick up and if necessary, reject it on the spot: • Innerwear, swimsuits, gym wear, sleep wear • Perfumes, jewelry, health & wellness products, adult toys • For missing items and damaged products especially, broken screens please check with our riders during delivery and reject on the spot. How do I return an item/ What happens once I have returned an item? For any return request please contact our Customer Service Call Center at 0742511381/0742511394. and fill the form. What happens once I have returned an item? • We will perform a careful quality check. • If the claim is valid, we will refund you according to your requested refund method. • The process may take up to 2 days from when your return request was submitted. • If the claim is invalid the item will be sent back to you. • We keep track of all return requests and use the data to improve our product quality and service, as well as for customer profiling. Customers with unjustified/invalid returns may be denied the right to return items or even shop on Kibuga in the future. How much time do I have to return a product to Kibuga? • All items sold on Kibuga if faulty, can be returned within a period of 2 days from delivery date.

> **[2] General_Terms_for_Sellers_and_Buyers.pdf p.2 (`1df1cd8d:4`):** 4. Returns and refunds Returns of products by buyers and acceptance of returned products by sellers shall be managed by us in accordance with the returns page on the marketplace, as may be amended from time to time. Acceptance of returns shall be in our discretion, subject to compliance with applicable laws of the territory. Refunds in respect of returned products shall be managed in accordance with the refunds page on the marketplace, as may be amended from time to time. Our rules on refunds shall be exercised in our discretion, subject to applicable laws of the territory. We may offer refunds, in our discretion: Payments In respect of the product price. Shipping fees (as stated on the refunds page); and ● By way of store credits, wallet refunds, vouchers, mobile money transfer, bank transfers or such other method as we may determine from time to time. Returned products shall be accepted and refunds issued by Kibuga, for and on behalf of the seller.

> **[3] Return_Policy.pdf p.1 (`f232e5d3:1`):** Return Policy NOTE: You have 2 days to notify us of your return by calling Customer Service, from the day you received your purchase. For defective items, we also advise you to contact the manufacturer if the product has a warranty. How do I send my product to Kibuga? • We will make 3 attempts within 2 working days to pick-up the returning item after you submit the return request .Note that You can also drop your return item at our offices/Warehouse. However, after 3 pick-up attempts, we will cancel the return procedure and you will not be able to return your product to us anymore. Please ensure that the package of the returning item is in good condition for the return; any package found to be damaged will be rejected by the rider during collection or sent back after quality check is done. How do I track my return status? • We will keep you updated by email and SMS about the status of your return. For any inquiries contact our Customer Service Call Center at 0742511381 / 0742511394.. Is my product under warranty? • We advise you to check our warranty page to get more information about our warranty policy. If my returned product is not validated for refund, how do I get informed? • If your return is invalid, then we will call you to explain the issue and send the item(s) back to you. We will arrange the delivery of the item."Note that we will make two (2) attempts to return the product to you at no cost. However, after two (2) failed attempts, we will cancel the return process and store the product at our warehouse for up to seven (7) days awaiting your collection. If you do not collect the product within these seven (7) days, it will be deemed as forfeited and we will dispose off in accordance with the Ugandan law I received something I didn't order.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | WEAK | The full returns procedure from request to refund involves several steps: 1. **Notification**: You have 2 days to notify Kibuga of your return by calling Customer Service after receiving the purchase. 2. **Return Request Submission**: Submit a return request through the provided contact numbers (0742511381/0742511394) or via the form available on the marketplace's returns page. 3. **Pick-Up Attempts**: Kibuga will make 3 attempts within 2 working days to pick up your returned item after you subm … | |
| 1.5B | WEAK | The full returns procedure from request to refund includes: 1. Contacting Customer Service at 0742511381/0742511394. 2. Filling out a form for returning an item. 3. Returning the item within two days of delivery, with proof of purchase and original packaging. 4. Kibuga will perform a quality check on returned items. 5. If the claim is valid, refunds will be issued according to the requested method (payment, shipping fees, store credits, etc.) within 2 business days. 6. The process may take up to … | |
| Qwen3-4B | PASS | The full returns procedure from request to refund involves the following steps: 1. The customer must contact the Customer Service Call Center at 0742511381 or 0742511394 and fill out a return form. 2. The customer has 2 days from the day they received their purchase to notify Kibuga of their return. For defective items, they are advised to contact the manufacturer if the product has a warranty. 3. Kibuga will make 3 attempts within 2 working days to pick up the returning item. If the item is not … | |

---

## Q22 — multi_chunk

**Question:** What are all the ways Kibuga can refund me?

**Gold / expected answer:** Store credits, wallet refunds, vouchers, mobile money transfer, bank transfers

**Gold chunk retrieved?** NO — retrieval missed the gold chunk

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Return_Policy.pdf p.1 (`f232e5d3:0`):** Return Policy Return Policy What are the conditions for returning an item? Two (2) days free returns policy, subject to Terms and conditions. Requirement for a valid procedure • Proof of purchase – the document handed over to you together with the product, on delivery. • Original packaging – the manufacturer packaging • Any free promotional items – gifts or accessories delivered with the purchased item • Valid return reason i.e. If Item is Faulty Please Note: We do not accept returns for the items below. For such purchases, please inspect the item carefully upon delivery or pick up and if necessary, reject it on the spot: • Innerwear, swimsuits, gym wear, sleep wear • Perfumes, jewelry, health & wellness products, adult toys • For missing items and damaged products especially, broken screens please check with our riders during delivery and reject on the spot. How do I return an item/ What happens once I have returned an item? For any return request please contact our Customer Service Call Center at 0742511381/0742511394. and fill the form. What happens once I have returned an item? • We will perform a careful quality check. • If the claim is valid, we will refund you according to your requested refund method. • The process may take up to 2 days from when your return request was submitted. • If the claim is invalid the item will be sent back to you. • We keep track of all return requests and use the data to improve our product quality and service, as well as for customer profiling. Customers with unjustified/invalid returns may be denied the right to return items or even shop on Kibuga in the future. How much time do I have to return a product to Kibuga? • All items sold on Kibuga if faulty, can be returned within a period of 2 days from delivery date.

> **[2] Return_Policy.pdf p.1 (`f232e5d3:2`):** Return Policy What now? • On delivery, kindly ensure to verify that the item delivered is in good condition and reject if it does not match your order. Can I return my items after the timeline to return has expired? • Sorry, returns are not possible after the 2-day return period. Do I have to return the gift when I return a product? • Yes, any gift must also be returned. Do I have to pay for shipping charges when I return a product? • There are no charges for shipping a product back to Kibuga.

> **[3] Return_Policy.pdf p.1 (`f232e5d3:1`):** Return Policy NOTE: You have 2 days to notify us of your return by calling Customer Service, from the day you received your purchase. For defective items, we also advise you to contact the manufacturer if the product has a warranty. How do I send my product to Kibuga? • We will make 3 attempts within 2 working days to pick-up the returning item after you submit the return request .Note that You can also drop your return item at our offices/Warehouse. However, after 3 pick-up attempts, we will cancel the return procedure and you will not be able to return your product to us anymore. Please ensure that the package of the returning item is in good condition for the return; any package found to be damaged will be rejected by the rider during collection or sent back after quality check is done. How do I track my return status? • We will keep you updated by email and SMS about the status of your return. For any inquiries contact our Customer Service Call Center at 0742511381 / 0742511394.. Is my product under warranty? • We advise you to check our warranty page to get more information about our warranty policy. If my returned product is not validated for refund, how do I get informed? • If your return is invalid, then we will call you to explain the issue and send the item(s) back to you. We will arrange the delivery of the item."Note that we will make two (2) attempts to return the product to you at no cost. However, after two (2) failed attempts, we will cancel the return process and store the product at our warehouse for up to seven (7) days awaiting your collection. If you do not collect the product within these seven (7) days, it will be deemed as forfeited and we will dispose off in accordance with the Ugandan law I received something I didn't order.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | FAIL | For a valid return claim, Kibuga will refund you according to your requested refund method after performing a careful quality check. The process may take up to 2 days from when your return request was submitted. If the claim is invalid, the item will be sent back to you. There are no charges for shipping a product back to Kibuga. | |
| 1.5B | FAIL | Kibuga refunds you according to your requested refund method if the claim is valid. If the claim is invalid, the item will be sent back to you. | |
| Qwen3-4B | FAIL | According to the passage, Kibuga can refund you if the claim is valid. If the claim is valid, they will refund you according to your requested refund method. The process may take up to 2 days from when your return request was submitted. If the claim is invalid, the item will be sent back to you. If your returned product is not validated for refund, Kibuga will call you to explain the issue and send the item(s) back to you. They will arrange the delivery of the item. Note that they will make two  … | |

---

## Q23 — exact_fact

**Question:** Where is Kibuga's registered office located?

**Gold / expected answer:** Muganzirwaza Commercial building plaza, Lubiri ring road (registered in Uganda).

**Gold chunk retrieved?** YES

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] General_Terms_for_Sellers_and_Buyers.pdf p.11 (`1df1cd8d:21`):** 6. Our company details The marketplace is operated by Kibuga business ventures. We are registered in Uganda and our registered office is at Muganzirwaza Commercial building plaza Lubiri ring road. You can contact us by using our marketplace contact form.

> **[2] General_Terms_for_Sellers_and_Buyers.pdf p.5 (`1df1cd8d:10`):** 2. Use of website and mobile applications Use data collected from our website for any direct marketing activity (including without limitation email marketing, SMS marketing, telemarketing and direct mailing); or ● Do anything that interferes with the normal use of our website. 3. Copyright and trademarks ● Subject to the express provisions of these general terms and conditions: we, together with our licensors, own and control all the copyright and other intellectual property rights in our website and the material on our website; and ● All the copyright and other intellectual property rights in our website and the material on our website are reserved. Kibuga’s logos and our other registered and unregistered trademarks are trademarks belonging to us; we give no permission for the use of these trademarks, and such use may constitute an infringement of our rights. The third party registered and unregistered trademarks or service marks on our website are the property of their respective owners and we do not endorse and are not affiliated with any of the holders of any such rights and as such we cannot grant any license to exercise such rights.

> **[3] Privacy_Policy.pdf p.1 (`21d0ee2c:2`):** 2. Who We Are Kibuga is an e-commerce platform in Uganda. Our platform includes our marketplace, logistics service, and payment service, connecting sellers with consumers and facilitating transactions and deliveries. The website and/or mobile app you are using is operated by a member of the Kibuga Business Ventures Limited. Personal data provided or collected by Kibuga is controlled by the relevant subsidiary.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | Kibuga's registered office is located at Muganzirwaza Commercial building plaza Lubiri ring road. | |
| 1.5B | PASS | Muganzirwaza Commercial building plaza Lubiri ring road | |
| Qwen3-4B | PASS | The registered office of Kibuga is located at Muganzirwaza Commercial building plaza Lubiri ring road. | |

---

## Q24 — exact_fact

**Question:** Do I pay shipping charges when returning a product to Kibuga?

**Gold / expected answer:** No, there are no charges for shipping a product back to Kibuga.

**Gold chunk retrieved?** YES

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Return_Policy.pdf p.1 (`f232e5d3:2`):** Return Policy What now? • On delivery, kindly ensure to verify that the item delivered is in good condition and reject if it does not match your order. Can I return my items after the timeline to return has expired? • Sorry, returns are not possible after the 2-day return period. Do I have to return the gift when I return a product? • Yes, any gift must also be returned. Do I have to pay for shipping charges when I return a product? • There are no charges for shipping a product back to Kibuga.

> **[2] Return_Policy.pdf p.1 (`f232e5d3:0`):** Return Policy Return Policy What are the conditions for returning an item? Two (2) days free returns policy, subject to Terms and conditions. Requirement for a valid procedure • Proof of purchase – the document handed over to you together with the product, on delivery. • Original packaging – the manufacturer packaging • Any free promotional items – gifts or accessories delivered with the purchased item • Valid return reason i.e. If Item is Faulty Please Note: We do not accept returns for the items below. For such purchases, please inspect the item carefully upon delivery or pick up and if necessary, reject it on the spot: • Innerwear, swimsuits, gym wear, sleep wear • Perfumes, jewelry, health & wellness products, adult toys • For missing items and damaged products especially, broken screens please check with our riders during delivery and reject on the spot. How do I return an item/ What happens once I have returned an item? For any return request please contact our Customer Service Call Center at 0742511381/0742511394. and fill the form. What happens once I have returned an item? • We will perform a careful quality check. • If the claim is valid, we will refund you according to your requested refund method. • The process may take up to 2 days from when your return request was submitted. • If the claim is invalid the item will be sent back to you. • We keep track of all return requests and use the data to improve our product quality and service, as well as for customer profiling. Customers with unjustified/invalid returns may be denied the right to return items or even shop on Kibuga in the future. How much time do I have to return a product to Kibuga? • All items sold on Kibuga if faulty, can be returned within a period of 2 days from delivery date.

> **[3] Return_Policy.pdf p.1 (`f232e5d3:1`):** Return Policy NOTE: You have 2 days to notify us of your return by calling Customer Service, from the day you received your purchase. For defective items, we also advise you to contact the manufacturer if the product has a warranty. How do I send my product to Kibuga? • We will make 3 attempts within 2 working days to pick-up the returning item after you submit the return request .Note that You can also drop your return item at our offices/Warehouse. However, after 3 pick-up attempts, we will cancel the return procedure and you will not be able to return your product to us anymore. Please ensure that the package of the returning item is in good condition for the return; any package found to be damaged will be rejected by the rider during collection or sent back after quality check is done. How do I track my return status? • We will keep you updated by email and SMS about the status of your return. For any inquiries contact our Customer Service Call Center at 0742511381 / 0742511394.. Is my product under warranty? • We advise you to check our warranty page to get more information about our warranty policy. If my returned product is not validated for refund, how do I get informed? • If your return is invalid, then we will call you to explain the issue and send the item(s) back to you. We will arrange the delivery of the item."Note that we will make two (2) attempts to return the product to you at no cost. However, after two (2) failed attempts, we will cancel the return process and store the product at our warehouse for up to seven (7) days awaiting your collection. If you do not collect the product within these seven (7) days, it will be deemed as forfeited and we will dispose off in accordance with the Ugandan law I received something I didn't order.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | There are no charges for shipping a product back to Kibuga. | |
| 1.5B | PASS | No, there are no charges for shipping a product back to Kibuga. | |
| Qwen3-4B | PASS | No, there are no charges for shipping a product back to Kibuga. | |

---

## Q25 — exact_fact

**Question:** Who do I contact to exercise my data privacy rights?

**Gold / expected answer:** The Data Privacy Officer at support@kibuga.com.

**Gold chunk retrieved?** YES

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Privacy_Policy.pdf p.3 (`21d0ee2c:12`):** 12. Data Controllers & Contact For questions, concerns, or to exercise your rights, contact our Data Privacy Officer at support@kibuga.com. We will respond to complaints within prescribed timelines.

> **[2] Privacy_Policy.pdf p.3 (`21d0ee2c:11`):** 11. Your Legal Rights You have rights under data protection laws, including accessing, correcting, or erasing your personal data, objecting to or restricting its processing, requesting data transfer to a third party, and unsubscribing from communications. You can close your account or contact us to exercise these rights.

> **[3] General_Terms_for_Sellers_and_Buyers.pdf p.7 (`1df1cd8d:12`):** 4. Data privacy ● We do not warrant or represent: ● The completeness or accuracy of the information published on our marketplace. That the material on the marketplace is up to date. That the marketplace will operate without fault; or That the marketplace or any service on the marketplace will remain available. We reserve the right to discontinue or alter any or all our marketplace services, and to stop publishing our marketplace, at any time in our sole discretion without notice or explanation; and you will not be entitled to any compensation or other payment upon the discontinuance or alteration of any marketplace services, or if we stop publishing the marketplace. ● We do not guarantee any commercial results concerning the use of the marketplace. To the maximum extent permitted by applicable law and subject to section 13.1 below, we exclude all representations and warranties relating to the subject matter of these general terms and conditions, our marketplace and the use of our marketplace.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | You can contact our Data Privacy Officer at support@kibuga.com to exercise your data privacy rights. | |
| 1.5B | FAIL | support@kibuga.com | |
| Qwen3-4B | PASS | To exercise your data privacy rights, you should contact our Data Privacy Officer at support@kibuga.com. | |

---

## Q26 — exact_fact

**Question:** Am I allowed to print pages from Kibuga's website?

**Gold / expected answer:** Yes, for your own personal and non-commercial use, provided printing is not systematic or excessive.

**Gold chunk retrieved?** YES

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] General_Terms_for_Sellers_and_Buyers.pdf p.5 (`1df1cd8d:8`):** 2. Use of website and mobile applications In this section 8 words “marketplace” and "website” shall be used interchangeably to refer to Kibuga’s websites and mobile applications. ● You may: ● view pages from our website in a web browser. ● download pages from our website for caching in a web browser. ● print pages from our website for your own personal and noncommercial use, providing that such printing is not systematic or excessive. ● stream audio and video files from our website using the media player on our website; and ● use our marketplace services by means of a web browser, subject to the other provisions of these general terms and conditions. Except as expressly permitted or the other provisions of these general terms and conditions, you must not download any material from our website or save any such material to your computer. ● You may only use our website for your own personal and business purposes in respect of selling or purchasing products on the marketplace. ● Except as expressly permitted by these general terms and conditions, you must not edit or otherwise modify any material on our website. ● Unless you own or control the relevant rights in the material, you must not: ● Republish material from our website (including republication on another website). ● Sell, rent or sub-license material from our website. ● Show any material from our website in public. ● Exploit material from our website for a commercial purpose; or ● Redistribute material from our website. ● You may forward links to products on our website and redistribute our newsletter and promotional materials in print and electronic form to any person. We reserve the right to suspend or restrict access to our website, to areas of our website and/or to functionality upon our website. We may, for example, suspend access to the website during server maintenance or when we update the website.

> **[2] General_Terms_for_Sellers_and_Buyers.pdf p.5 (`1df1cd8d:10`):** 2. Use of website and mobile applications Use data collected from our website for any direct marketing activity (including without limitation email marketing, SMS marketing, telemarketing and direct mailing); or ● Do anything that interferes with the normal use of our website. 3. Copyright and trademarks ● Subject to the express provisions of these general terms and conditions: we, together with our licensors, own and control all the copyright and other intellectual property rights in our website and the material on our website; and ● All the copyright and other intellectual property rights in our website and the material on our website are reserved. Kibuga’s logos and our other registered and unregistered trademarks are trademarks belonging to us; we give no permission for the use of these trademarks, and such use may constitute an infringement of our rights. The third party registered and unregistered trademarks or service marks on our website are the property of their respective owners and we do not endorse and are not affiliated with any of the holders of any such rights and as such we cannot grant any license to exercise such rights.

> **[3] Sellers_Terms_and_Conditions.pdf p.1 (`9a6d80d1:0`):** Sellers Terms and Conditions Sellers Terms and Conditions Introduction Kibuga Investment operates an e-commerce platform consisting of a website and mobile application (“marketplace”), together with supporting logistics and payment infrastructure, for the sale and purchase of consumer products in Uganda (“territory”). These seller terms and conditions shall apply to all sellers on the marketplace, together with our general terms and conditions of the use of the marketplace. If you register with our marketplace as a seller: a. you accept these seller terms and conditions, the general terms and conditions, and the Kibuga codes, policies and guidelines, and as may be amended by Kibuga from time to time. b. We will ask you to expressly agree to these seller terms and conditions. 1. Seller stores a. If you register with our marketplace as a seller you will be able to create a store on the marketplace, using the “Kibuga” portal. b. Seller stores that are submitted may be reviewed for approval, at Kibuga’s discretion before they are operational. c. You shall be solely responsible for your store, listings and products and you hereby agree that: a. You shall obtain any licenses required for sale of your products on the marketplace. b. To the extent required by applicable law, you shall register with relevant tax authorities and pay all relevant taxes in relation to your product sales. d. d. You shall conduct your business on the marketplace: a. In compliance with the Kibuga Partner Code of Conduct, and other Kibuga codes, policies and guidelines as published on the marketplace from time to time. b. In accordance with ethical business practices and industry best practices; and 1. Without prejudice to our other rights, we reserve the right to reject, unpublish and/or delete any seller store that breaches these seller terms and conditions, the general terms and conditions, or any Kibuga codes, policies and guidelines. 1.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | You may print pages from our website for your own personal and noncommercial use, providing that such printing is not systematic or excessive. | |
| 1.5B | PASS | Yes, you may print pages from our website for your own personal and noncommercial use, provided that such printing is not systematic or excessive. | |
| Qwen3-4B | PASS | Yes, you are allowed to print pages from Kibuga's website for your own personal and noncommercial use, providing that such printing is not systematic or excessive. | |

---

## Q27 — paraphrase

**Question:** How long does Kibuga hang on to my information?

**Gold / expected answer:** As long as necessary for the purposes in the Privacy Notice; it is deleted or anonymized when no longer needed.

**Gold chunk retrieved?** NO — retrieval missed the gold chunk

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Return_Policy.pdf p.1 (`f232e5d3:1`):** Return Policy NOTE: You have 2 days to notify us of your return by calling Customer Service, from the day you received your purchase. For defective items, we also advise you to contact the manufacturer if the product has a warranty. How do I send my product to Kibuga? • We will make 3 attempts within 2 working days to pick-up the returning item after you submit the return request .Note that You can also drop your return item at our offices/Warehouse. However, after 3 pick-up attempts, we will cancel the return procedure and you will not be able to return your product to us anymore. Please ensure that the package of the returning item is in good condition for the return; any package found to be damaged will be rejected by the rider during collection or sent back after quality check is done. How do I track my return status? • We will keep you updated by email and SMS about the status of your return. For any inquiries contact our Customer Service Call Center at 0742511381 / 0742511394.. Is my product under warranty? • We advise you to check our warranty page to get more information about our warranty policy. If my returned product is not validated for refund, how do I get informed? • If your return is invalid, then we will call you to explain the issue and send the item(s) back to you. We will arrange the delivery of the item."Note that we will make two (2) attempts to return the product to you at no cost. However, after two (2) failed attempts, we will cancel the return process and store the product at our warehouse for up to seven (7) days awaiting your collection. If you do not collect the product within these seven (7) days, it will be deemed as forfeited and we will dispose off in accordance with the Ugandan law I received something I didn't order.

> **[2] Return_Policy.pdf p.1 (`f232e5d3:2`):** Return Policy What now? • On delivery, kindly ensure to verify that the item delivered is in good condition and reject if it does not match your order. Can I return my items after the timeline to return has expired? • Sorry, returns are not possible after the 2-day return period. Do I have to return the gift when I return a product? • Yes, any gift must also be returned. Do I have to pay for shipping charges when I return a product? • There are no charges for shipping a product back to Kibuga.

> **[3] Privacy_Policy.pdf p.1 (`21d0ee2c:1`):** 1. About this Notice This Privacy Notice provides information on how Kibuga collects and processes your personal data when you visit our website or mobile applications. It outlines what we do with your personal data, how we keep it secure, and explains the rights you have regarding your personal data.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | FAIL | NOT_IN_DOCUMENTS | |
| 1.5B | FAIL | Kibuga stores any returned product for up to seven (7) days awaiting a collection attempt or until it is deemed forfeited and disposed of in accordance with Ugandan law if not collected within these seven (7) days. | |
| Qwen3-4B | FAIL | NOT_IN_DOCUMENTS | |

---

## Q28 — paraphrase

**Question:** What sorts of goods are sellers banned from listing?

**Gold / expected answer:** Products that breach laws/regulations, infringe IP or other rights, contravene content rules, or relate to prohibited categories such as drugs.

**Gold chunk retrieved?** YES

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Sellers_Terms_and_Conditions.pdf p.1 (`9a6d80d1:1`):** Sellers Terms and Conditions Product listings a. You shall be responsible for listing your products on the marketplace by uploading to the Seller Centre a completed product page which shall include prices, detailed information, specifications and images in respect of each product. b. You may not publish more than one listing in respect of each product. c. You agree to be solely responsible for all listings submitted to our marketplace and you agree that all listings must: ● constitute bona fide listings relating to products that comply with the categories and rules set out. ● comply with the rules on content in the general terms and conditions and further particularized in the Content and Image Guidelines; and d. Include all such information, specifications and guidelines as may be required pursuant to all applicable laws and regulations, including in respect of consumer protection. e. Listings that are submitted may be individually reviewed and approved at Kibuga’s discretion, before they are published on the marketplace, and you acknowledge and agree there may be a lead time between submission of the product page to the Seller Centre and the publishing of the Product page on the marketplace due to time required for Kibuga quality control operations. f. Without prejudice to our other rights, we reserve the right to reject, unpublish and/or delete any listings that breach these seller terms and conditions, the general terms and conditions or any Kibuga codes, policies or guidelines. g. You acknowledge and agree that: ● Notwithstanding that we may approve any listings, you shall be fully responsible for the same; and ● We reserve the right to impose penalties for breach of this section 3, without prejudice to our other rights. ● You must keep your listings up to date. You must deactivate any listings in respect of products that have ceased to be available. 1. The products a. The only products that may be the subject of a listing on our marketplace are products falling within the product categories specified on the marketplace. b.

> **[2] General_Terms_for_Sellers_and_Buyers.pdf p.1 (`1df1cd8d:3`):** 2. Registration and account ● We shall accept binding sales, on behalf of sellers, but Kibuga is not a party to the transaction between the seller and the buyer; and A contract for the sale and purchase of a product or products will come into force between the buyer and seller, and accordingly you commit to buying or selling the relevant product or products, upon the buyer’s confirmation of purchase via the marketplace. Subject to these general terms and conditions, the seller’s terms of business shall govern the contract for sale and purchase between the buyer and the seller. Notwithstanding this, the following provisions will be incorporated into the contract of sale and purchase between the buyer and the seller: ● The price for a product will be as stated in the relevant product listing. ● The price for the product must include all taxes and comply with applicable laws in force from time to time. Delivery charges, packaging charges, handling charges, administrative charges, insurance costs, other ancillary costs and charges, will only be payable by the buyer if this is expressly and clearly stated in the product listing. Products must be of satisfactory quality, fit and safe for any purpose specified in, and conform in all material respects to, the product listing and any other description of the products supplied or made available by the seller to the buyer; and The seller warrants that the seller has good title to, and is the sole legal and beneficial owner of, the products, and that the products are not subject to any third-party rights or restrictions including in respect of third-party intellectual property rights and/or any criminal, insolvency or tax investigation or proceedings.

> **[3] Sellers_Terms_and_Conditions.pdf p.1 (`9a6d80d1:2`):** Sellers Terms and Conditions You must not advertise, buy, sell or supply through our marketplace any product that: ● Breaches any laws or regulations or infringes any person's intellectual property rights or other rights, or gives rise to a cause of action against any person, in each case in any jurisdiction and under any applicable law. ● Consists of or contains material that would, if published on our marketplace by you, contravene the rules on content in the general terms and conditions; or ● Is or relates to drugs, narcotics, steroids or controlled substances; pornography; obscene, indecent or sexually explicit materials; swords, firearms or other weapons; ammunition for any weapon; or items that are otherwise prohibited pursuant to the Prohibited and restricted Products Policy, as may be amended from time to time, or any applicable law. c. We operate a zero-tolerance to counterfeit products and any attempt to sell counterfeit products on the marketplace, or other breach of our Anti Counterfeit Policy may result in the penalties specified in the Seller Penalty Policy which include financial penalties, permanently prohibiting you from using the marketplace, and potentially in prosecution. d. Promptly, following receipt of a written request from us, you must supply us any information and documentation that we may reasonably request to verify the authenticity of products. 2. Pricing a. All prices of products shall be stated inclusive of VAT and any other tax applicable to the transaction and in the currency of the territory. b. You shall be solely responsible for setting the price of your products on the marketplace, which may be amended through the Seller Centre from time to time, including for the purpose of any seasonal or other discounts. c. The pricing of your products shall comply with all applicable laws, including competition laws. 3. Fulfilment, packaging and delivery a.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | Sellers are banned from advertising, buying, or supplying through our marketplace any product that breaches any laws or regulations, infringes any person's intellectual property rights or other rights, gives rise to a cause of action against any person in any jurisdiction and under any applicable law. The products also consist of or contain material that would contravene the rules on content in the general terms and conditions; are drugs, narcotics, steroids or controlled substances; pornography … | |
| 1.5B | PASS | Sellers are banned from listing any product that breaches any laws or regulations, infringes intellectual property rights, contains material prohibited by content guidelines, is related to drugs, narcotics, steroids, controlled substances, pornography, obscene, indecent or sexually explicit materials, swords, firearms or other weapons, ammunition for any weapon, or items otherwise prohibited pursuant to the Prohibited and restricted Products Policy. | |
| Qwen3-4B | PASS | Sellers are banned from listing products that: - Breach any laws or regulations or infringe any person's intellectual property rights or other rights, or give rise to a cause of action against any person, in each case in any jurisdiction and under any applicable law. - Consist of or contain material that would, if published on our marketplace by you, contravene the rules on content in the general terms and conditions. - Are or relate to drugs, narcotics, steroids or controlled substances; pornog … | |

---

## Q29 — paraphrase

**Question:** Can I ask Kibuga to delete everything they know about me?

**Gold / expected answer:** Yes — your legal rights include erasing your personal data, plus access, correction, restriction, portability and unsubscribing.

**Gold chunk retrieved?** NO — retrieval missed the gold chunk

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Privacy_Policy.pdf p.1 (`21d0ee2c:3`):** 3. The Data We Collect About You Personal data refers to information that can identify a specific individual, either directly or indirectly. We collect personal data to provide tailored products and services and to continuously improve them. We may collect, use, store, and transfer various types of personal data for marketing and optimization purposes. Kibuga also uses Google Digital Marketing for targeted offers. Data you provide: ● Contact details: Name, postal addresses, phone numbers, email addresses. ● Demographic information: Date of birth, age, gender. ● Online registration information: Passwords, authentication information. ● Payment information: Credit card information, billing address. ● Survey responses: Customer satisfaction surveys, market research. ● Competition entries and submissions. ● Marketing preferences. Automatically collected data or data from third parties: ● Device information: PC, tablet, mobile device, operating system, browser, IP address. ● Usage information: Searches, views, downloads, purchases, web pages visited. ● User-generated content: Blogs, social media postings. ● Social media data: Username or ID, profile photo, followers. We provide options for managing your personal data, including opting out of personalized experiences and targeted advertising. You can close your account or adjust preferences by contacting us at uganda.legal@Kibuga.com.

> **[2] Return_Policy.pdf p.1 (`f232e5d3:1`):** Return Policy NOTE: You have 2 days to notify us of your return by calling Customer Service, from the day you received your purchase. For defective items, we also advise you to contact the manufacturer if the product has a warranty. How do I send my product to Kibuga? • We will make 3 attempts within 2 working days to pick-up the returning item after you submit the return request .Note that You can also drop your return item at our offices/Warehouse. However, after 3 pick-up attempts, we will cancel the return procedure and you will not be able to return your product to us anymore. Please ensure that the package of the returning item is in good condition for the return; any package found to be damaged will be rejected by the rider during collection or sent back after quality check is done. How do I track my return status? • We will keep you updated by email and SMS about the status of your return. For any inquiries contact our Customer Service Call Center at 0742511381 / 0742511394.. Is my product under warranty? • We advise you to check our warranty page to get more information about our warranty policy. If my returned product is not validated for refund, how do I get informed? • If your return is invalid, then we will call you to explain the issue and send the item(s) back to you. We will arrange the delivery of the item."Note that we will make two (2) attempts to return the product to you at no cost. However, after two (2) failed attempts, we will cancel the return process and store the product at our warehouse for up to seven (7) days awaiting your collection. If you do not collect the product within these seven (7) days, it will be deemed as forfeited and we will dispose off in accordance with the Ugandan law I received something I didn't order.

> **[3] Privacy_Policy.pdf p.1 (`21d0ee2c:1`):** 1. About this Notice This Privacy Notice provides information on how Kibuga collects and processes your personal data when you visit our website or mobile applications. It outlines what we do with your personal data, how we keep it secure, and explains the rights you have regarding your personal data.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | FAIL | NOT_IN_DOCUMENTS | |
| 1.5B | FAIL | NOT_IN_DOCUMENTS | |
| Qwen3-4B | FAIL | Yes, you can ask Kibuga to delete everything they know about you. The document states that "We provide options for managing your personal data, including opting out of personalized experiences and targeted advertising." This implies that you have the right to request the deletion of your personal data. Additionally, the document mentions that you can "close your account or adjust preferences by contacting us at uganda.legal@Kibuga.com." This suggests that you can contact Kibuga directly to manag … | |

---

## Q30 — near_miss

**Question:** Are the prices shown on the marketplace inclusive of VAT?

**Gold / expected answer:** Yes — all amounts stated on the marketplace are inclusive of VAT and any other applicable taxes.

**Gold chunk retrieved?** YES

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Sellers_Terms_and_Conditions.pdf p.1 (`9a6d80d1:4`):** Sellers Terms and Conditions This will not affect any liability to pay commission that accrues before the new rates are posted or for services that have been previously paid. 5. VAT and other taxes a. All amounts stated on the marketplace are stated inclusive of VAT and any other taxes applicable to the transaction. The seller acknowledges that: ● Commissions shall be calculated as a percentage of the selling price (being the price set by the vendor at the time of the order) inclusive of VAT and any other taxes charged to the buyer. ● Commissions are inclusive of VAT and all other taxes thereon; and ● In the event of any upwards revision in the rate of VAT or any other applicable taxes, the amount of the commission shall be automatically adjusted to ensure that Kibuga’s net revenues remain constant. b. The seller shall be exclusively liable in respect of all taxes applicable to the transactions entered into on the marketplace with buyers, including VAT, and shall therefore be responsible for the reporting, filing and payment of the same. c. Should a competent tax authority determine that Kibuga is liable for payment of any taxes (including stamp, excise or customs duties) in respect of the transactions, notably, you hereby indemnify and hold harmless Kibuga in respect of the same. We may make tax-related deductions to payments processed by us on your behalf and remit such deducted amounts to the relevant government or tax authority. d. Promptly following receipt of a written request from us, you must supply to us any information and documentation that we may reasonably request in order to identify you or facilitate our compliance with our legal obligations relating to the taxation of payments made to us or processed by us. We may supply such information and/or documentation to relevant government and tax authorities. Remittances a.

> **[2] General_Terms_for_Sellers_and_Buyers.pdf p.8 (`1df1cd8d:14`):** 1. Limitations and exclusions of liability We accept that we have an interest in limiting the personal liability of our officers and employees and, having regard to that interest, you acknowledge that we are a limited liability entity; you agree that you will not bring any claim personally against our officers or employees in respect of any losses you suffer in connection with the marketplace or these general terms and conditions (this will not limit or exclude the liability of the limited liability entity itself for the acts and omissions of our officers and employees). Our marketplace includes hyperlinks to other websites owned and operated by third parties; such hyperlinks are not recommendations. We have no control over third party websites and their contents, and we accept no responsibility for them or for any loss or damage that may arise from your use of them. 14. Indemnification ● You hereby indemnify us, and undertake to keep us indemnified, against: all losses, damages, costs, liabilities and expenses (including without limitation legal expenses and any amounts paid by us to any third party in settlement of a claim or dispute) incurred or suffered by us and arising directly or indirectly out of your use of our marketplace or any breach by you of any provision of these general terms and conditions or the Kibuga codes, policies or guidelines; and any VAT liability or other tax liability that we may incur in relation to any sale, supply or purchase made through our marketplace, where that liability arises out of your failure to pay, withhold, declare or register to pay any VAT or other tax properly due in any jurisdiction. 1. Breaches of these general terms and conditions If we permit the registration of an account on our marketplace it will remain open indefinitely, subject to these general terms and conditions.

> **[3] Sellers_Terms_and_Conditions.pdf p.1 (`9a6d80d1:2`):** Sellers Terms and Conditions You must not advertise, buy, sell or supply through our marketplace any product that: ● Breaches any laws or regulations or infringes any person's intellectual property rights or other rights, or gives rise to a cause of action against any person, in each case in any jurisdiction and under any applicable law. ● Consists of or contains material that would, if published on our marketplace by you, contravene the rules on content in the general terms and conditions; or ● Is or relates to drugs, narcotics, steroids or controlled substances; pornography; obscene, indecent or sexually explicit materials; swords, firearms or other weapons; ammunition for any weapon; or items that are otherwise prohibited pursuant to the Prohibited and restricted Products Policy, as may be amended from time to time, or any applicable law. c. We operate a zero-tolerance to counterfeit products and any attempt to sell counterfeit products on the marketplace, or other breach of our Anti Counterfeit Policy may result in the penalties specified in the Seller Penalty Policy which include financial penalties, permanently prohibiting you from using the marketplace, and potentially in prosecution. d. Promptly, following receipt of a written request from us, you must supply us any information and documentation that we may reasonably request to verify the authenticity of products. 2. Pricing a. All prices of products shall be stated inclusive of VAT and any other tax applicable to the transaction and in the currency of the territory. b. You shall be solely responsible for setting the price of your products on the marketplace, which may be amended through the Seller Centre from time to time, including for the purpose of any seasonal or other discounts. c. The pricing of your products shall comply with all applicable laws, including competition laws. 3. Fulfilment, packaging and delivery a.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | All prices of products shall be stated inclusive of VAT and any other tax applicable to the transaction. This is stated in Sellers Terms and Conditions passage 1. | |
| 1.5B | WEAK | Yes, the prices shown on the marketplace are inclusive of VAT. | |
| Qwen3-4B | WEAK | Yes, the prices shown on the marketplace are inclusive of VAT. This is stated in passage [1], which mentions that "All amounts stated on the marketplace are stated inclusive of VAT and any other taxes applicable to the transaction." Passage [3] also supports this, as it states that "All prices of products shall be stated inclusive of VAT and any other tax applicable to the transaction." | |

---

## Q31 — near_miss

**Question:** Can Kibuga move my data to another country?

**Gold / expected answer:** Yes, where permissible by law, with measures to ensure a similar level of protection as the country of origin.

**Gold chunk retrieved?** YES

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Privacy_Policy.pdf p.2 (`21d0ee2c:8`):** 8. International Transfers We may transfer your personal data to other countries where permissible by law. We will implement necessary measures to protect your data and ensure a similar level of protection as in the country of origin, respecting your legal rights.

> **[2] Privacy_Policy.pdf p.1 (`21d0ee2c:3`):** 3. The Data We Collect About You Personal data refers to information that can identify a specific individual, either directly or indirectly. We collect personal data to provide tailored products and services and to continuously improve them. We may collect, use, store, and transfer various types of personal data for marketing and optimization purposes. Kibuga also uses Google Digital Marketing for targeted offers. Data you provide: ● Contact details: Name, postal addresses, phone numbers, email addresses. ● Demographic information: Date of birth, age, gender. ● Online registration information: Passwords, authentication information. ● Payment information: Credit card information, billing address. ● Survey responses: Customer satisfaction surveys, market research. ● Competition entries and submissions. ● Marketing preferences. Automatically collected data or data from third parties: ● Device information: PC, tablet, mobile device, operating system, browser, IP address. ● Usage information: Searches, views, downloads, purchases, web pages visited. ● User-generated content: Blogs, social media postings. ● Social media data: Username or ID, profile photo, followers. We provide options for managing your personal data, including opting out of personalized experiences and targeted advertising. You can close your account or adjust preferences by contacting us at uganda.legal@Kibuga.com.

> **[3] General_Terms_for_Sellers_and_Buyers.pdf p.5 (`1df1cd8d:8`):** 2. Use of website and mobile applications In this section 8 words “marketplace” and "website” shall be used interchangeably to refer to Kibuga’s websites and mobile applications. ● You may: ● view pages from our website in a web browser. ● download pages from our website for caching in a web browser. ● print pages from our website for your own personal and noncommercial use, providing that such printing is not systematic or excessive. ● stream audio and video files from our website using the media player on our website; and ● use our marketplace services by means of a web browser, subject to the other provisions of these general terms and conditions. Except as expressly permitted or the other provisions of these general terms and conditions, you must not download any material from our website or save any such material to your computer. ● You may only use our website for your own personal and business purposes in respect of selling or purchasing products on the marketplace. ● Except as expressly permitted by these general terms and conditions, you must not edit or otherwise modify any material on our website. ● Unless you own or control the relevant rights in the material, you must not: ● Republish material from our website (including republication on another website). ● Sell, rent or sub-license material from our website. ● Show any material from our website in public. ● Exploit material from our website for a commercial purpose; or ● Redistribute material from our website. ● You may forward links to products on our website and redistribute our newsletter and promotional materials in print and electronic form to any person. We reserve the right to suspend or restrict access to our website, to areas of our website and/or to functionality upon our website. We may, for example, suspend access to the website during server maintenance or when we update the website.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | Yes, Kibuga can move your data to another country as long as they implement necessary measures to protect your data and ensure a similar level of protection as in the country of origin, respecting your legal rights. | |
| 1.5B | PASS | Yes, Kibuga may transfer your personal data to other countries where permissible by law, ensuring that necessary measures are taken to protect your data and maintain a similar level of protection as in the country of origin, respecting your legal rights. | |
| Qwen3-4B | PASS | Yes, Kibuga can move your data to another country. The company mentions that they may transfer your personal data to other countries where permissible by law. They also state that they will implement necessary measures to protect your data and ensure a similar level of protection as in the country of origin, respecting your legal rights. | |

---

## Q32 — prose

**Question:** What can Kibuga do to me if I break the rules?

**Gold / expected answer:** Temporarily suspend or permanently prohibit access, block your IP, and ask your ISPs to block your access.

**Gold chunk retrieved?** NO — retrieval missed the gold chunk

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] General_Terms_for_Sellers_and_Buyers.pdf p.5 (`1df1cd8d:10`):** 2. Use of website and mobile applications Use data collected from our website for any direct marketing activity (including without limitation email marketing, SMS marketing, telemarketing and direct mailing); or ● Do anything that interferes with the normal use of our website. 3. Copyright and trademarks ● Subject to the express provisions of these general terms and conditions: we, together with our licensors, own and control all the copyright and other intellectual property rights in our website and the material on our website; and ● All the copyright and other intellectual property rights in our website and the material on our website are reserved. Kibuga’s logos and our other registered and unregistered trademarks are trademarks belonging to us; we give no permission for the use of these trademarks, and such use may constitute an infringement of our rights. The third party registered and unregistered trademarks or service marks on our website are the property of their respective owners and we do not endorse and are not affiliated with any of the holders of any such rights and as such we cannot grant any license to exercise such rights.

> **[2] Sellers_Terms_and_Conditions.pdf p.1 (`9a6d80d1:6`):** Sellers Terms and Conditions If we reasonably determine that you have breached these seller terms and conditions, our general terms and conditions, or any Kibuga codes, policies or guidelines, we may: 1. send you one or more formal warnings. b. suspend, prohibit or block your access to our marketplace as provided in the general terms and conditions. c. apply penalties for breach as provided in our Seller Penalty Policy; and/or d. commence legal action against you, whether for breach of contract or otherwise. 2. We may vary the amount of the penalties for breach from time to time by updating the Seller Penalty Policy, but this will not affect any liability to pay penalties that accrue before the new amounts are posted. Confidentiality and data privacy All information and documents concerning the conduct of business pursuant to these general terms and conditions, including information relating to business methods, procedures, policies and sales information, is strictly confidential unless it is already in the public domain. You shall not use Kibuga’s confidential information for any purpose other than to perform your obligations under this Agreement and you shall not disclose Kibuga’s confidential information without our prior written consent. Sellers may not send advertising or promotional communications to buyers on the marketplace without the prior written consent of Kibuga and shall be directly responsible to marketplace users for any misuse of their personal data. If Kibuga is sued, fined, or otherwise incurs expenses because of the seller’s handling of personal data obtained through the marketplace, the seller shall indemnify Kibuga in respect of the same.

> **[3] Privacy_Policy.pdf p.1 (`21d0ee2c:1`):** 1. About this Notice This Privacy Notice provides information on how Kibuga collects and processes your personal data when you visit our website or mobile applications. It outlines what we do with your personal data, how we keep it secure, and explains the rights you have regarding your personal data.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | If you reasonably determine that you have breached these seller terms and conditions, our general terms and conditions, or any Kibuga codes, policies or guidelines, Kibuga may: send you one or more formal warnings; suspend, prohibit or block your access to our marketplace as provided in the general terms and conditions; apply penalties for breach as provided in our Seller Penalty Policy; and commence legal action against you, whether for breach of contract or otherwise. | |
| 1.5B | WEAK | Kibuga may send a formal warning, suspend or block access, apply penalties for breach as provided in their Seller Penalty Policy, and commence legal action against you. | |
| Qwen3-4B | WEAK | If you break the rules, Kibuga may send you one or more formal warnings. They may suspend, prohibit, or block your access to our marketplace as provided in the general terms and conditions. They may also apply penalties for breach as provided in our Seller Penalty Policy; and/or commence legal action against you, whether for breach of contract or otherwise. Additionally, if Kibuga is sued, fined, or otherwise incurs expenses because of the seller’s handling of personal data obtained through the  … | |

---

## Q33 — prose

**Question:** Which outside parties might see my personal data?

**Gold / expected answer:** Third-party sellers, service providers (fulfilment, payment, marketing), parties in business transfers, and fraud/compliance bodies.

**Gold chunk retrieved?** YES

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Privacy_Policy.pdf p.2 (`21d0ee2c:7`):** 7. How We Share Your Personal Data Third-party sharing: ● Product and service delivery: Sharing data with third-party sellers. ● Service providers: Engaging third parties for functions like order fulfillment, payment processing, and marketing assistance. ● Business transfers: Customer information may be transferred in business transactions. Fraud detection: Sharing data for fraud protection and compliance with the law. We ensure that third parties use your data per this Privacy Notice and applicable laws and only for specified purposes.

> **[2] Privacy_Policy.pdf p.3 (`21d0ee2c:10`):** 10. Data Security We have implemented security measures to prevent unauthorized access, use, alteration, or disclosure of your personal data. Access is limited to employees, agents, contractors, and third parties who need it for business purposes and are bound by confidentiality.

> **[3] Privacy_Policy.pdf p.1 (`21d0ee2c:3`):** 3. The Data We Collect About You Personal data refers to information that can identify a specific individual, either directly or indirectly. We collect personal data to provide tailored products and services and to continuously improve them. We may collect, use, store, and transfer various types of personal data for marketing and optimization purposes. Kibuga also uses Google Digital Marketing for targeted offers. Data you provide: ● Contact details: Name, postal addresses, phone numbers, email addresses. ● Demographic information: Date of birth, age, gender. ● Online registration information: Passwords, authentication information. ● Payment information: Credit card information, billing address. ● Survey responses: Customer satisfaction surveys, market research. ● Competition entries and submissions. ● Marketing preferences. Automatically collected data or data from third parties: ● Device information: PC, tablet, mobile device, operating system, browser, IP address. ● Usage information: Searches, views, downloads, purchases, web pages visited. ● User-generated content: Blogs, social media postings. ● Social media data: Username or ID, profile photo, followers. We provide options for managing your personal data, including opting out of personalized experiences and targeted advertising. You can close your account or adjust preferences by contacting us at uganda.legal@Kibuga.com.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | Third-party sellers, service providers for functions like order fulfillment, payment processing, and marketing assistance, as well as business transfers in transactions, may see your personal data. Additionally, Google Digital Marketing might access your data for targeted offers. | |
| 1.5B | WEAK | Third-party sellers, service providers for order fulfillment, payment processing, and marketing assistance, employees, agents, contractors, third parties who need it for business purposes bound by confidentiality, Google Digital Marketing for targeted offers, Kibuga's website visitors, and users of social media platforms. | |
| Qwen3-4B | WEAK | Third-party sellers, service providers (for functions like order fulfillment, payment processing, and marketing assistance), and third parties involved in business transfers may see your personal data. Additionally, Google Digital Marketing may use your data for targeted offers. Employees, agents, contractors, and third parties who need access for business purposes and are bound by confidentiality may also have access to your personal data. | |

---

## Q34 — prose

**Question:** Does Kibuga use my data for advertising?

**Gold / expected answer:** Yes — data is collected for marketing/optimization and Kibuga uses Google Digital Marketing for targeted offers.

**Gold chunk retrieved?** YES

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Privacy_Policy.pdf p.1 (`21d0ee2c:3`):** 3. The Data We Collect About You Personal data refers to information that can identify a specific individual, either directly or indirectly. We collect personal data to provide tailored products and services and to continuously improve them. We may collect, use, store, and transfer various types of personal data for marketing and optimization purposes. Kibuga also uses Google Digital Marketing for targeted offers. Data you provide: ● Contact details: Name, postal addresses, phone numbers, email addresses. ● Demographic information: Date of birth, age, gender. ● Online registration information: Passwords, authentication information. ● Payment information: Credit card information, billing address. ● Survey responses: Customer satisfaction surveys, market research. ● Competition entries and submissions. ● Marketing preferences. Automatically collected data or data from third parties: ● Device information: PC, tablet, mobile device, operating system, browser, IP address. ● Usage information: Searches, views, downloads, purchases, web pages visited. ● User-generated content: Blogs, social media postings. ● Social media data: Username or ID, profile photo, followers. We provide options for managing your personal data, including opting out of personalized experiences and targeted advertising. You can close your account or adjust preferences by contacting us at uganda.legal@Kibuga.com.

> **[2] General_Terms_for_Sellers_and_Buyers.pdf p.5 (`1df1cd8d:10`):** 2. Use of website and mobile applications Use data collected from our website for any direct marketing activity (including without limitation email marketing, SMS marketing, telemarketing and direct mailing); or ● Do anything that interferes with the normal use of our website. 3. Copyright and trademarks ● Subject to the express provisions of these general terms and conditions: we, together with our licensors, own and control all the copyright and other intellectual property rights in our website and the material on our website; and ● All the copyright and other intellectual property rights in our website and the material on our website are reserved. Kibuga’s logos and our other registered and unregistered trademarks are trademarks belonging to us; we give no permission for the use of these trademarks, and such use may constitute an infringement of our rights. The third party registered and unregistered trademarks or service marks on our website are the property of their respective owners and we do not endorse and are not affiliated with any of the holders of any such rights and as such we cannot grant any license to exercise such rights.

> **[3] Sellers_Terms_and_Conditions.pdf p.1 (`9a6d80d1:6`):** Sellers Terms and Conditions If we reasonably determine that you have breached these seller terms and conditions, our general terms and conditions, or any Kibuga codes, policies or guidelines, we may: 1. send you one or more formal warnings. b. suspend, prohibit or block your access to our marketplace as provided in the general terms and conditions. c. apply penalties for breach as provided in our Seller Penalty Policy; and/or d. commence legal action against you, whether for breach of contract or otherwise. 2. We may vary the amount of the penalties for breach from time to time by updating the Seller Penalty Policy, but this will not affect any liability to pay penalties that accrue before the new amounts are posted. Confidentiality and data privacy All information and documents concerning the conduct of business pursuant to these general terms and conditions, including information relating to business methods, procedures, policies and sales information, is strictly confidential unless it is already in the public domain. You shall not use Kibuga’s confidential information for any purpose other than to perform your obligations under this Agreement and you shall not disclose Kibuga’s confidential information without our prior written consent. Sellers may not send advertising or promotional communications to buyers on the marketplace without the prior written consent of Kibuga and shall be directly responsible to marketplace users for any misuse of their personal data. If Kibuga is sued, fined, or otherwise incurs expenses because of the seller’s handling of personal data obtained through the marketplace, the seller shall indemnify Kibuga in respect of the same.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | Yes, Kibuga uses your data for marketing and optimization purposes as stated in the Data We Collect About You section where they mention collecting various types of personal data including payment information, survey responses, competition entries and submissions, and marketing preferences to provide tailored products and services and continuously improve them. They also use Google Digital Marketing for targeted offers which indicates advertising purposes. | |
| 1.5B | PASS | Yes, Kibuga uses your data for targeted offers and marketing purposes. Specifically, they collect various types of personal information such as contact details, demographic information, online registration information, payment information, survey responses, competition entries, and usage information. They also use Google Digital Marketing for targeted advertising. | |
| Qwen3-4B | PASS | Yes, Kibuga uses your data for advertising. The company uses Google Digital Marketing for targeted offers and collects various types of personal data for marketing and optimization purposes. Additionally, Kibuga provides options for managing personal data, including opting out of personalized experiences and targeted advertising. | |

---

## Q35 — prose

**Question:** If I have a legal dispute with Kibuga, whose courts decide it?

**Gold / expected answer:** The courts of the territory (Uganda) have exclusive jurisdiction; the terms are governed by the laws of the territory.

**Gold chunk retrieved?** NO — retrieval missed the gold chunk

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] General_Terms_for_Sellers_and_Buyers.pdf p.1 (`1df1cd8d:1`):** 1. Introduction Kibuga Investment operates an e-commerce platform consisting of a website and mobile application (“marketplace”), together with supporting logistics and payment infrastructure, for the sale and purchase of consumer products in Uganda (“territory”). These general terms and conditions shall apply to buyers and sellers on the marketplace and shall govern your use of the marketplace and related services. By using our marketplace, you accept these general terms and conditions in full. If you disagree with these general terms and conditions or any part of these general terms and conditions, you must not use our marketplace. If you use our marketplace in the course of a business or other organizational project, then by so doing you: Confirm that you have obtained the necessary authority to agree to these general terms and conditions. Bind both yourself and the person, company or other legal entity that operates that business or organizational project, to these general terms and conditions; and Agree that "you" in these general terms and conditions shall reference both the individual user and the relevant person, company or legal entity unless the context requires otherwise.

> **[2] Sellers_Terms_and_Conditions.pdf p.1 (`9a6d80d1:6`):** Sellers Terms and Conditions If we reasonably determine that you have breached these seller terms and conditions, our general terms and conditions, or any Kibuga codes, policies or guidelines, we may: 1. send you one or more formal warnings. b. suspend, prohibit or block your access to our marketplace as provided in the general terms and conditions. c. apply penalties for breach as provided in our Seller Penalty Policy; and/or d. commence legal action against you, whether for breach of contract or otherwise. 2. We may vary the amount of the penalties for breach from time to time by updating the Seller Penalty Policy, but this will not affect any liability to pay penalties that accrue before the new amounts are posted. Confidentiality and data privacy All information and documents concerning the conduct of business pursuant to these general terms and conditions, including information relating to business methods, procedures, policies and sales information, is strictly confidential unless it is already in the public domain. You shall not use Kibuga’s confidential information for any purpose other than to perform your obligations under this Agreement and you shall not disclose Kibuga’s confidential information without our prior written consent. Sellers may not send advertising or promotional communications to buyers on the marketplace without the prior written consent of Kibuga and shall be directly responsible to marketplace users for any misuse of their personal data. If Kibuga is sued, fined, or otherwise incurs expenses because of the seller’s handling of personal data obtained through the marketplace, the seller shall indemnify Kibuga in respect of the same.

> **[3] Return_Policy.pdf p.1 (`f232e5d3:1`):** Return Policy NOTE: You have 2 days to notify us of your return by calling Customer Service, from the day you received your purchase. For defective items, we also advise you to contact the manufacturer if the product has a warranty. How do I send my product to Kibuga? • We will make 3 attempts within 2 working days to pick-up the returning item after you submit the return request .Note that You can also drop your return item at our offices/Warehouse. However, after 3 pick-up attempts, we will cancel the return procedure and you will not be able to return your product to us anymore. Please ensure that the package of the returning item is in good condition for the return; any package found to be damaged will be rejected by the rider during collection or sent back after quality check is done. How do I track my return status? • We will keep you updated by email and SMS about the status of your return. For any inquiries contact our Customer Service Call Center at 0742511381 / 0742511394.. Is my product under warranty? • We advise you to check our warranty page to get more information about our warranty policy. If my returned product is not validated for refund, how do I get informed? • If your return is invalid, then we will call you to explain the issue and send the item(s) back to you. We will arrange the delivery of the item."Note that we will make two (2) attempts to return the product to you at no cost. However, after two (2) failed attempts, we will cancel the return process and store the product at our warehouse for up to seven (7) days awaiting your collection. If you do not collect the product within these seven (7) days, it will be deemed as forfeited and we will dispose off in accordance with the Ugandan law I received something I didn't order.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | FAIL | NOT_IN_DOCUMENTS | |
| 1.5B | FAIL | NOT_IN_DOCUMENTS | |
| Qwen3-4B | FAIL | NOT_IN_DOCUMENTS | |

---

## Q36 — multi_chunk

**Question:** Across all the policies, what enforcement actions can Kibuga take against a seller who breaches the terms?

**Gold / expected answer:** Formal warnings, suspension/prohibition/blocking of access, IP blocking, penalties under the Seller Penalty Policy, and legal action.

**Gold chunk retrieved?** YES

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Sellers_Terms_and_Conditions.pdf p.1 (`9a6d80d1:0`):** Sellers Terms and Conditions Sellers Terms and Conditions Introduction Kibuga Investment operates an e-commerce platform consisting of a website and mobile application (“marketplace”), together with supporting logistics and payment infrastructure, for the sale and purchase of consumer products in Uganda (“territory”). These seller terms and conditions shall apply to all sellers on the marketplace, together with our general terms and conditions of the use of the marketplace. If you register with our marketplace as a seller: a. you accept these seller terms and conditions, the general terms and conditions, and the Kibuga codes, policies and guidelines, and as may be amended by Kibuga from time to time. b. We will ask you to expressly agree to these seller terms and conditions. 1. Seller stores a. If you register with our marketplace as a seller you will be able to create a store on the marketplace, using the “Kibuga” portal. b. Seller stores that are submitted may be reviewed for approval, at Kibuga’s discretion before they are operational. c. You shall be solely responsible for your store, listings and products and you hereby agree that: a. You shall obtain any licenses required for sale of your products on the marketplace. b. To the extent required by applicable law, you shall register with relevant tax authorities and pay all relevant taxes in relation to your product sales. d. d. You shall conduct your business on the marketplace: a. In compliance with the Kibuga Partner Code of Conduct, and other Kibuga codes, policies and guidelines as published on the marketplace from time to time. b. In accordance with ethical business practices and industry best practices; and 1. Without prejudice to our other rights, we reserve the right to reject, unpublish and/or delete any seller store that breaches these seller terms and conditions, the general terms and conditions, or any Kibuga codes, policies and guidelines. 1.

> **[2] Sellers_Terms_and_Conditions.pdf p.1 (`9a6d80d1:6`):** Sellers Terms and Conditions If we reasonably determine that you have breached these seller terms and conditions, our general terms and conditions, or any Kibuga codes, policies or guidelines, we may: 1. send you one or more formal warnings. b. suspend, prohibit or block your access to our marketplace as provided in the general terms and conditions. c. apply penalties for breach as provided in our Seller Penalty Policy; and/or d. commence legal action against you, whether for breach of contract or otherwise. 2. We may vary the amount of the penalties for breach from time to time by updating the Seller Penalty Policy, but this will not affect any liability to pay penalties that accrue before the new amounts are posted. Confidentiality and data privacy All information and documents concerning the conduct of business pursuant to these general terms and conditions, including information relating to business methods, procedures, policies and sales information, is strictly confidential unless it is already in the public domain. You shall not use Kibuga’s confidential information for any purpose other than to perform your obligations under this Agreement and you shall not disclose Kibuga’s confidential information without our prior written consent. Sellers may not send advertising or promotional communications to buyers on the marketplace without the prior written consent of Kibuga and shall be directly responsible to marketplace users for any misuse of their personal data. If Kibuga is sued, fined, or otherwise incurs expenses because of the seller’s handling of personal data obtained through the marketplace, the seller shall indemnify Kibuga in respect of the same.

> **[3] General_Terms_for_Sellers_and_Buyers.pdf p.8 (`1df1cd8d:15`):** 1. Limitations and exclusions of liability If you breach these general terms and conditions, or if we reasonably suspect that you have breached these general terms and conditions or any Kibuga codes, policies or guidelines in any way we may: 1. temporarily suspend your access to our marketplace. 2. permanently prohibit you from accessing our marketplace. ● Block computers using your IP address from accessing our marketplace. ● Contact any or all your internet service providers and request that they block your access to our marketplace. ● Suspend or delete your account on our marketplace; and/or ● Commence legal action against you, whether for breach of contract or otherwise. Where we suspend, prohibit or block your access to our marketplace or a part of our marketplace you must not take any action to circumvent such suspension or prohibition or blocking (including without limitation creating and/or using a different account).

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | If we reasonably determine that you have breached these general terms and conditions or any Kibuga codes, policies or guidelines, We may: temporarily suspend your access to our marketplace; permanently prohibit you from accessing our marketplace; block computers using your IP address from accessing our marketplace; contact any or all your internet service providers and request that they block your access to our marketplace; suspend or delete your account on our marketplace; and commence legal ac … | |
| 1.5B | PASS | Kibuga Investment reserves the right to suspend, prohibit, block access, contact internet service providers, delete accounts, and commence legal action against sellers who breach these general terms and conditions or any Kibuga codes, policies, or guidelines. | |
| Qwen3-4B | PASS | Kibuga can take several enforcement actions against a seller who breaches the terms, including: sending formal warnings, suspending, prohibiting, or blocking the seller's access to the marketplace, applying penalties for breach as provided in the Seller Penalty Policy, commencing legal action against the seller, varying the amount of penalties for breach by updating the Seller Penalty Policy, temporarily suspending the seller's access to the marketplace, permanently prohibiting the seller from a … | |

---

## Q37 — multi_chunk

**Question:** How does Kibuga handle a seller's money — what gets deducted and what's left?

**Gold / expected answer:** Kibuga collects buyer payments, deducts commissions (a % of VAT-inclusive selling price), fees, taxes, penalties, refunds and other owed amounts, then remits the remainder.

**Gold chunk retrieved?** YES

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Sellers_Terms_and_Conditions.pdf p.1 (`9a6d80d1:4`):** Sellers Terms and Conditions This will not affect any liability to pay commission that accrues before the new rates are posted or for services that have been previously paid. 5. VAT and other taxes a. All amounts stated on the marketplace are stated inclusive of VAT and any other taxes applicable to the transaction. The seller acknowledges that: ● Commissions shall be calculated as a percentage of the selling price (being the price set by the vendor at the time of the order) inclusive of VAT and any other taxes charged to the buyer. ● Commissions are inclusive of VAT and all other taxes thereon; and ● In the event of any upwards revision in the rate of VAT or any other applicable taxes, the amount of the commission shall be automatically adjusted to ensure that Kibuga’s net revenues remain constant. b. The seller shall be exclusively liable in respect of all taxes applicable to the transactions entered into on the marketplace with buyers, including VAT, and shall therefore be responsible for the reporting, filing and payment of the same. c. Should a competent tax authority determine that Kibuga is liable for payment of any taxes (including stamp, excise or customs duties) in respect of the transactions, notably, you hereby indemnify and hold harmless Kibuga in respect of the same. We may make tax-related deductions to payments processed by us on your behalf and remit such deducted amounts to the relevant government or tax authority. d. Promptly following receipt of a written request from us, you must supply to us any information and documentation that we may reasonably request in order to identify you or facilitate our compliance with our legal obligations relating to the taxation of payments made to us or processed by us. We may supply such information and/or documentation to relevant government and tax authorities. Remittances a.

> **[2] General_Terms_for_Sellers_and_Buyers.pdf p.1 (`1df1cd8d:3`):** 2. Registration and account ● We shall accept binding sales, on behalf of sellers, but Kibuga is not a party to the transaction between the seller and the buyer; and A contract for the sale and purchase of a product or products will come into force between the buyer and seller, and accordingly you commit to buying or selling the relevant product or products, upon the buyer’s confirmation of purchase via the marketplace. Subject to these general terms and conditions, the seller’s terms of business shall govern the contract for sale and purchase between the buyer and the seller. Notwithstanding this, the following provisions will be incorporated into the contract of sale and purchase between the buyer and the seller: ● The price for a product will be as stated in the relevant product listing. ● The price for the product must include all taxes and comply with applicable laws in force from time to time. Delivery charges, packaging charges, handling charges, administrative charges, insurance costs, other ancillary costs and charges, will only be payable by the buyer if this is expressly and clearly stated in the product listing. Products must be of satisfactory quality, fit and safe for any purpose specified in, and conform in all material respects to, the product listing and any other description of the products supplied or made available by the seller to the buyer; and The seller warrants that the seller has good title to, and is the sole legal and beneficial owner of, the products, and that the products are not subject to any third-party rights or restrictions including in respect of third-party intellectual property rights and/or any criminal, insolvency or tax investigation or proceedings.

> **[3] Sellers_Terms_and_Conditions.pdf p.1 (`9a6d80d1:6`):** Sellers Terms and Conditions If we reasonably determine that you have breached these seller terms and conditions, our general terms and conditions, or any Kibuga codes, policies or guidelines, we may: 1. send you one or more formal warnings. b. suspend, prohibit or block your access to our marketplace as provided in the general terms and conditions. c. apply penalties for breach as provided in our Seller Penalty Policy; and/or d. commence legal action against you, whether for breach of contract or otherwise. 2. We may vary the amount of the penalties for breach from time to time by updating the Seller Penalty Policy, but this will not affect any liability to pay penalties that accrue before the new amounts are posted. Confidentiality and data privacy All information and documents concerning the conduct of business pursuant to these general terms and conditions, including information relating to business methods, procedures, policies and sales information, is strictly confidential unless it is already in the public domain. You shall not use Kibuga’s confidential information for any purpose other than to perform your obligations under this Agreement and you shall not disclose Kibuga’s confidential information without our prior written consent. Sellers may not send advertising or promotional communications to buyers on the marketplace without the prior written consent of Kibuga and shall be directly responsible to marketplace users for any misuse of their personal data. If Kibuga is sued, fined, or otherwise incurs expenses because of the seller’s handling of personal data obtained through the marketplace, the seller shall indemnify Kibuga in respect of the same.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | Kibuga may make tax-related deductions to payments processed by us on your behalf and remit such deducted amounts to the relevant government or tax authority. Therefore, taxes applicable to the transactions entered into on the marketplace with buyers are handled by Kibuga through these deductions from seller's payments. The amount of the commission is automatically adjusted in case of any upwards revision in the rate of VAT or other applicable taxes, ensuring that Kibuga’s net revenues remain co … | |
| 1.5B | PASS | Kibuga makes tax-related deductions to payments processed by it on behalf of sellers and remits such deducted amounts to relevant government or tax authorities. The seller is responsible for reporting, filing, and paying any taxes applicable to transactions entered into on the marketplace with buyers. If a competent tax authority determines that Kibuga is liable for payment of any taxes, the seller must indemnify Kibuga in respect thereof. | |
| Qwen3-4B | PASS | According to the context, Kibuga handles a seller's money as follows: - All amounts stated on the marketplace are stated inclusive of VAT and any other taxes applicable to the transaction. Commissions are calculated as a percentage of the selling price (inclusive of VAT and any other taxes charged to the buyer) and are inclusive of VAT and all other taxes thereon. - In the event of any upwards revision in the rate of VAT or any other applicable taxes, the amount of the commission shall be automa … | |

---

## Q38 — multi_chunk

**Question:** Walk me through everything I need to know to return an item and get my money back.

**Gold / expected answer:** Notify within 2 days by calling Customer Service with proof of purchase and original packaging; Kibuga makes 3 pickup attempts in 2 working days; no shipping charge; no returns after 2 days; gifts must be returned.

**Gold chunk retrieved?** YES

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Return_Policy.pdf p.1 (`f232e5d3:1`):** Return Policy NOTE: You have 2 days to notify us of your return by calling Customer Service, from the day you received your purchase. For defective items, we also advise you to contact the manufacturer if the product has a warranty. How do I send my product to Kibuga? • We will make 3 attempts within 2 working days to pick-up the returning item after you submit the return request .Note that You can also drop your return item at our offices/Warehouse. However, after 3 pick-up attempts, we will cancel the return procedure and you will not be able to return your product to us anymore. Please ensure that the package of the returning item is in good condition for the return; any package found to be damaged will be rejected by the rider during collection or sent back after quality check is done. How do I track my return status? • We will keep you updated by email and SMS about the status of your return. For any inquiries contact our Customer Service Call Center at 0742511381 / 0742511394.. Is my product under warranty? • We advise you to check our warranty page to get more information about our warranty policy. If my returned product is not validated for refund, how do I get informed? • If your return is invalid, then we will call you to explain the issue and send the item(s) back to you. We will arrange the delivery of the item."Note that we will make two (2) attempts to return the product to you at no cost. However, after two (2) failed attempts, we will cancel the return process and store the product at our warehouse for up to seven (7) days awaiting your collection. If you do not collect the product within these seven (7) days, it will be deemed as forfeited and we will dispose off in accordance with the Ugandan law I received something I didn't order.

> **[2] Return_Policy.pdf p.1 (`f232e5d3:0`):** Return Policy Return Policy What are the conditions for returning an item? Two (2) days free returns policy, subject to Terms and conditions. Requirement for a valid procedure • Proof of purchase – the document handed over to you together with the product, on delivery. • Original packaging – the manufacturer packaging • Any free promotional items – gifts or accessories delivered with the purchased item • Valid return reason i.e. If Item is Faulty Please Note: We do not accept returns for the items below. For such purchases, please inspect the item carefully upon delivery or pick up and if necessary, reject it on the spot: • Innerwear, swimsuits, gym wear, sleep wear • Perfumes, jewelry, health & wellness products, adult toys • For missing items and damaged products especially, broken screens please check with our riders during delivery and reject on the spot. How do I return an item/ What happens once I have returned an item? For any return request please contact our Customer Service Call Center at 0742511381/0742511394. and fill the form. What happens once I have returned an item? • We will perform a careful quality check. • If the claim is valid, we will refund you according to your requested refund method. • The process may take up to 2 days from when your return request was submitted. • If the claim is invalid the item will be sent back to you. • We keep track of all return requests and use the data to improve our product quality and service, as well as for customer profiling. Customers with unjustified/invalid returns may be denied the right to return items or even shop on Kibuga in the future. How much time do I have to return a product to Kibuga? • All items sold on Kibuga if faulty, can be returned within a period of 2 days from delivery date.

> **[3] Return_Policy.pdf p.1 (`f232e5d3:2`):** Return Policy What now? • On delivery, kindly ensure to verify that the item delivered is in good condition and reject if it does not match your order. Can I return my items after the timeline to return has expired? • Sorry, returns are not possible after the 2-day return period. Do I have to return the gift when I return a product? • Yes, any gift must also be returned. Do I have to pay for shipping charges when I return a product? • There are no charges for shipping a product back to Kibuga.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | To initiate the return process, you must notify Customer Service within 2 days of receiving your purchase by calling them at either 0742511381 or 0742511394. You can also drop off your returned item at Kibuga's offices/Warehouse. For defective items, it is advisable to contact the manufacturer if the product has a warranty. Ensure that the package of the returning item is in good condition and send it back within three attempts made by Kibuga. If after these attempts you still cannot return your … | |
| 1.5B | PASS | To return an item on Kibuga: 1. Ensure the item is in good condition upon delivery. 2. Contact Customer Service at 0742511381/0742511394 to initiate a return request and fill out the form. 3. Follow up with your order number for tracking purposes. 4. Perform a quality check on returned items. 5. If valid, you will receive a refund according to your requested method within 2 days of submitting the return request. 6. If invalid, the item will be sent back to you. 7. Returns are not possible after  … | |
| Qwen3-4B | PASS | To return an item and get your money back, follow these steps: 1. Notify Kibuga of your return within 2 days from the day you received your purchase by calling Customer Service at 0742511381 or 0742511394. 2. Ensure that the package of the returning item is in good condition. If it is damaged, it will be rejected by the rider during collection or sent back after quality check is done. 3. We will make 3 attempts within 2 working days to pick-up the returning item after you submit the return reque … | |

---

## U01 — UNANSWERABLE probe

**Question:** Does Kibuga ship internationally to Kenya, and what are the rates?

**Expected:** abstain (NOT_IN_DOCUMENTS) — not in the corpus by design.

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Privacy_Policy.pdf p.1 (`21d0ee2c:2`):** 2. Who We Are Kibuga is an e-commerce platform in Uganda. Our platform includes our marketplace, logistics service, and payment service, connecting sellers with consumers and facilitating transactions and deliveries. The website and/or mobile app you are using is operated by a member of the Kibuga Business Ventures Limited. Personal data provided or collected by Kibuga is controlled by the relevant subsidiary.

> **[2] Return_Policy.pdf p.1 (`f232e5d3:2`):** Return Policy What now? • On delivery, kindly ensure to verify that the item delivered is in good condition and reject if it does not match your order. Can I return my items after the timeline to return has expired? • Sorry, returns are not possible after the 2-day return period. Do I have to return the gift when I return a product? • Yes, any gift must also be returned. Do I have to pay for shipping charges when I return a product? • There are no charges for shipping a product back to Kibuga.

> **[3] Sellers_Terms_and_Conditions.pdf p.1 (`9a6d80d1:0`):** Sellers Terms and Conditions Sellers Terms and Conditions Introduction Kibuga Investment operates an e-commerce platform consisting of a website and mobile application (“marketplace”), together with supporting logistics and payment infrastructure, for the sale and purchase of consumer products in Uganda (“territory”). These seller terms and conditions shall apply to all sellers on the marketplace, together with our general terms and conditions of the use of the marketplace. If you register with our marketplace as a seller: a. you accept these seller terms and conditions, the general terms and conditions, and the Kibuga codes, policies and guidelines, and as may be amended by Kibuga from time to time. b. We will ask you to expressly agree to these seller terms and conditions. 1. Seller stores a. If you register with our marketplace as a seller you will be able to create a store on the marketplace, using the “Kibuga” portal. b. Seller stores that are submitted may be reviewed for approval, at Kibuga’s discretion before they are operational. c. You shall be solely responsible for your store, listings and products and you hereby agree that: a. You shall obtain any licenses required for sale of your products on the marketplace. b. To the extent required by applicable law, you shall register with relevant tax authorities and pay all relevant taxes in relation to your product sales. d. d. You shall conduct your business on the marketplace: a. In compliance with the Kibuga Partner Code of Conduct, and other Kibuga codes, policies and guidelines as published on the marketplace from time to time. b. In accordance with ethical business practices and industry best practices; and 1. Without prejudice to our other rights, we reserve the right to reject, unpublish and/or delete any seller store that breaches these seller terms and conditions, the general terms and conditions, or any Kibuga codes, policies and guidelines. 1.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | NOT_IN_DOCUMENTS | |
| 1.5B | PASS | NOT_IN_DOCUMENTS | |
| Qwen3-4B | PASS | The provided documents do not mention anything about Kibuga shipping internationally to Kenya or the rates for such shipments. Therefore, the answer is: NOT_IN_DOCUMENTS | |

---

## U02 — UNANSWERABLE probe

**Question:** Can I pay for my order in instalments or with cash on delivery?

**Expected:** abstain (NOT_IN_DOCUMENTS) — not in the corpus by design.

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Sellers_Terms_and_Conditions.pdf p.1 (`9a6d80d1:3`):** Sellers Terms and Conditions Upon receipt of a confirmation of sale from Kibuga, you shall: ● Process the order by packing and labeling the product(s) in accordance with the Packaging Guidelines; and ● Deliver the products to our drop-off point in accordance with the timelines, opening hours and procedures specified in the Delivery Guidelines. b. We may inspect any or all products we receive, and we reserve the right to return to you any product that fails to meet the packaging requirements set out in the Packaging Guidelines or that fails to pass our quality control checks or any other product requirements set out at section 4. c. You shall retain title to and ownership of the products until such time as the products are paid for in full by the buyer to Kibuga and delivered to the buyer. Upon delivery to the buyer, ownership of the products shall vest in the buyer. d. We shall bear the risk of loss or damage to the products upon receipt and until delivery to the buyer. Our liability to you in respect of your products in our possession pursuant to this shall be limited to the cost price of the products and shall be subject to the further limitations and exclusions on liability provided in the general terms and conditions. e. Without prejudice to all our rights, we may charge you incur penalties in respect of breaches of the Packaging Guidelines or the Delivery Guidelines. The amount of the penalties that may be charged pursuant to this shall be stated in the Seller Penalty Policy. 4. Commission and fees a. We shall charge you a commission in respect of each sale made on the marketplace and fees in respect of all marketplace services. b. We reserve the right to charge commissions and/or fees if the sale is not completed, by way of consideration for the costs of our services rendered. c. We may vary commissions and/or fees from time to time, on prior notice to you, and by updating the commissions and fees page of Seller Centre.

> **[2] Return_Policy.pdf p.1 (`f232e5d3:2`):** Return Policy What now? • On delivery, kindly ensure to verify that the item delivered is in good condition and reject if it does not match your order. Can I return my items after the timeline to return has expired? • Sorry, returns are not possible after the 2-day return period. Do I have to return the gift when I return a product? • Yes, any gift must also be returned. Do I have to pay for shipping charges when I return a product? • There are no charges for shipping a product back to Kibuga.

> **[3] General_Terms_for_Sellers_and_Buyers.pdf p.8 (`1df1cd8d:14`):** 1. Limitations and exclusions of liability We accept that we have an interest in limiting the personal liability of our officers and employees and, having regard to that interest, you acknowledge that we are a limited liability entity; you agree that you will not bring any claim personally against our officers or employees in respect of any losses you suffer in connection with the marketplace or these general terms and conditions (this will not limit or exclude the liability of the limited liability entity itself for the acts and omissions of our officers and employees). Our marketplace includes hyperlinks to other websites owned and operated by third parties; such hyperlinks are not recommendations. We have no control over third party websites and their contents, and we accept no responsibility for them or for any loss or damage that may arise from your use of them. 14. Indemnification ● You hereby indemnify us, and undertake to keep us indemnified, against: all losses, damages, costs, liabilities and expenses (including without limitation legal expenses and any amounts paid by us to any third party in settlement of a claim or dispute) incurred or suffered by us and arising directly or indirectly out of your use of our marketplace or any breach by you of any provision of these general terms and conditions or the Kibuga codes, policies or guidelines; and any VAT liability or other tax liability that we may incur in relation to any sale, supply or purchase made through our marketplace, where that liability arises out of your failure to pay, withhold, declare or register to pay any VAT or other tax properly due in any jurisdiction. 1. Breaches of these general terms and conditions If we permit the registration of an account on our marketplace it will remain open indefinitely, subject to these general terms and conditions.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | NOT_IN_DOCUMENTS | |
| 1.5B | PASS | NOT_IN_DOCUMENTS | |
| Qwen3-4B | PASS | NOT_IN_DOCUMENTS | |

---

## U03 — UNANSWERABLE probe

**Question:** What is the warranty period in months on electronics bought from Kibuga?

**Expected:** abstain (NOT_IN_DOCUMENTS) — not in the corpus by design.

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Return_Policy.pdf p.1 (`f232e5d3:0`):** Return Policy Return Policy What are the conditions for returning an item? Two (2) days free returns policy, subject to Terms and conditions. Requirement for a valid procedure • Proof of purchase – the document handed over to you together with the product, on delivery. • Original packaging – the manufacturer packaging • Any free promotional items – gifts or accessories delivered with the purchased item • Valid return reason i.e. If Item is Faulty Please Note: We do not accept returns for the items below. For such purchases, please inspect the item carefully upon delivery or pick up and if necessary, reject it on the spot: • Innerwear, swimsuits, gym wear, sleep wear • Perfumes, jewelry, health & wellness products, adult toys • For missing items and damaged products especially, broken screens please check with our riders during delivery and reject on the spot. How do I return an item/ What happens once I have returned an item? For any return request please contact our Customer Service Call Center at 0742511381/0742511394. and fill the form. What happens once I have returned an item? • We will perform a careful quality check. • If the claim is valid, we will refund you according to your requested refund method. • The process may take up to 2 days from when your return request was submitted. • If the claim is invalid the item will be sent back to you. • We keep track of all return requests and use the data to improve our product quality and service, as well as for customer profiling. Customers with unjustified/invalid returns may be denied the right to return items or even shop on Kibuga in the future. How much time do I have to return a product to Kibuga? • All items sold on Kibuga if faulty, can be returned within a period of 2 days from delivery date.

> **[2] Return_Policy.pdf p.1 (`f232e5d3:1`):** Return Policy NOTE: You have 2 days to notify us of your return by calling Customer Service, from the day you received your purchase. For defective items, we also advise you to contact the manufacturer if the product has a warranty. How do I send my product to Kibuga? • We will make 3 attempts within 2 working days to pick-up the returning item after you submit the return request .Note that You can also drop your return item at our offices/Warehouse. However, after 3 pick-up attempts, we will cancel the return procedure and you will not be able to return your product to us anymore. Please ensure that the package of the returning item is in good condition for the return; any package found to be damaged will be rejected by the rider during collection or sent back after quality check is done. How do I track my return status? • We will keep you updated by email and SMS about the status of your return. For any inquiries contact our Customer Service Call Center at 0742511381 / 0742511394.. Is my product under warranty? • We advise you to check our warranty page to get more information about our warranty policy. If my returned product is not validated for refund, how do I get informed? • If your return is invalid, then we will call you to explain the issue and send the item(s) back to you. We will arrange the delivery of the item."Note that we will make two (2) attempts to return the product to you at no cost. However, after two (2) failed attempts, we will cancel the return process and store the product at our warehouse for up to seven (7) days awaiting your collection. If you do not collect the product within these seven (7) days, it will be deemed as forfeited and we will dispose off in accordance with the Ugandan law I received something I didn't order.

> **[3] Return_Policy.pdf p.1 (`f232e5d3:2`):** Return Policy What now? • On delivery, kindly ensure to verify that the item delivered is in good condition and reject if it does not match your order. Can I return my items after the timeline to return has expired? • Sorry, returns are not possible after the 2-day return period. Do I have to return the gift when I return a product? • Yes, any gift must also be returned. Do I have to pay for shipping charges when I return a product? • There are no charges for shipping a product back to Kibuga.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | NOT_IN_DOCUMENTS | |
| 1.5B | PASS | NOT_IN_DOCUMENTS | |
| Qwen3-4B | PASS | NOT_IN_DOCUMENTS | |

---

## U04 — UNANSWERABLE probe

**Question:** Does Kibuga have a physical store I can visit in Kampala?

**Expected:** abstain (NOT_IN_DOCUMENTS) — not in the corpus by design.

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Seek_Support.pdf p.1 (`a72cadc9:0`):** Seek Support Seek Support Headquarters: Muganzirwazza Commercial Plaza, Lubiri Road, Plot 1446 Bulange - Mengo, P.O BOX 163315, Kampala, Uganda Customer Support: Email: support@kibuga.com Phone: +256200959991 Phone: +256740063330 Social Media: Follow us on Facebook, Twitter, and Instagram @KibugaOnlineShop Business Hours: Monday to Friday: 08:00 AM - 05:00 PM Saturday: 08:00 AM - 02:00 PM Sunday: Closed For any inquiries, feedback, or support, please contact us through the provided details. Our team is dedicated to assisting you with any questions or concerns you may have.

> **[2] Sellers_Terms_and_Conditions.pdf p.1 (`9a6d80d1:0`):** Sellers Terms and Conditions Sellers Terms and Conditions Introduction Kibuga Investment operates an e-commerce platform consisting of a website and mobile application (“marketplace”), together with supporting logistics and payment infrastructure, for the sale and purchase of consumer products in Uganda (“territory”). These seller terms and conditions shall apply to all sellers on the marketplace, together with our general terms and conditions of the use of the marketplace. If you register with our marketplace as a seller: a. you accept these seller terms and conditions, the general terms and conditions, and the Kibuga codes, policies and guidelines, and as may be amended by Kibuga from time to time. b. We will ask you to expressly agree to these seller terms and conditions. 1. Seller stores a. If you register with our marketplace as a seller you will be able to create a store on the marketplace, using the “Kibuga” portal. b. Seller stores that are submitted may be reviewed for approval, at Kibuga’s discretion before they are operational. c. You shall be solely responsible for your store, listings and products and you hereby agree that: a. You shall obtain any licenses required for sale of your products on the marketplace. b. To the extent required by applicable law, you shall register with relevant tax authorities and pay all relevant taxes in relation to your product sales. d. d. You shall conduct your business on the marketplace: a. In compliance with the Kibuga Partner Code of Conduct, and other Kibuga codes, policies and guidelines as published on the marketplace from time to time. b. In accordance with ethical business practices and industry best practices; and 1. Without prejudice to our other rights, we reserve the right to reject, unpublish and/or delete any seller store that breaches these seller terms and conditions, the general terms and conditions, or any Kibuga codes, policies and guidelines. 1.

> **[3] General_Terms_for_Sellers_and_Buyers.pdf p.11 (`1df1cd8d:21`):** 6. Our company details The marketplace is operated by Kibuga business ventures. We are registered in Uganda and our registered office is at Muganzirwaza Commercial building plaza Lubiri ring road. You can contact us by using our marketplace contact form.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | NOT_IN_DOCUMENTS | |
| 1.5B | PASS | NOT_IN_DOCUMENTS | |
| Qwen3-4B | FAIL | Yes, Kibuga has a physical store in Kampala. The headquarters of Kibuga is located at Muganzirwazza Commercial Plaza, Lubiri Road, Plot 1446 Bulange - Mengo, P.O BOX 163315, Kampala, Uganda. | |

---

## U05 — UNANSWERABLE probe

**Question:** What loyalty points or discount codes does Kibuga offer repeat buyers?

**Expected:** abstain (NOT_IN_DOCUMENTS) — not in the corpus by design.

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] General_Terms_for_Sellers_and_Buyers.pdf p.7 (`1df1cd8d:11`):** 4. Data privacy Buyers agree to processing of their personal data in accordance with the terms of Kibuga’s Privacy and Cookie Notice. Kibuga shall process all personal data obtained through the marketplace and related services in accordance with the terms of our Privacy and Cookie Notice and Privacy Policy. Sellers shall be directly responsible to buyers for any misuse of their personal data and Kibuga shall bear no liability to buyers in respect of any misuse by sellers of their personal data. 5. Due diligence and audit rights ● We operate an anti-money laundering compliance program and reserve the right to perform due diligence checks on all users of the marketplace. ● You agree to provide to us all such information, documentation and access to your business premises as we may require: To verify your adherence to, and performance of, your obligations under this Agreement. For the purpose of disclosures pursuant to a valid order by a court or other governmental body; or ● You acknowledge that: ● We do not confirm the identity of all marketplace users, check their credit worthiness or bona fide, or otherwise vet them. ● We do not check, audit or monitor all information contained in listings. ● We are not party to any contract for the sale or purchase of products advertised on the marketplace. We are not involved in any transaction between a buyer and a seller in any way, save that we facilitate a marketplace for buyers and sellers and process payments on behalf of sellers. We are not the agents for any buyer or seller, and accordingly, we will not be liable to any person in relation to the offer for sale, sale or purchase of any products advertised on our marketplace; furthermore, we are not responsible for the enforcement of any contractual obligations arising out of a contract for the sale or purchase of any products and we will have no obligation to mediate between the parties to any such contract.

> **[2] Sellers_Terms_and_Conditions.pdf p.1 (`9a6d80d1:0`):** Sellers Terms and Conditions Sellers Terms and Conditions Introduction Kibuga Investment operates an e-commerce platform consisting of a website and mobile application (“marketplace”), together with supporting logistics and payment infrastructure, for the sale and purchase of consumer products in Uganda (“territory”). These seller terms and conditions shall apply to all sellers on the marketplace, together with our general terms and conditions of the use of the marketplace. If you register with our marketplace as a seller: a. you accept these seller terms and conditions, the general terms and conditions, and the Kibuga codes, policies and guidelines, and as may be amended by Kibuga from time to time. b. We will ask you to expressly agree to these seller terms and conditions. 1. Seller stores a. If you register with our marketplace as a seller you will be able to create a store on the marketplace, using the “Kibuga” portal. b. Seller stores that are submitted may be reviewed for approval, at Kibuga’s discretion before they are operational. c. You shall be solely responsible for your store, listings and products and you hereby agree that: a. You shall obtain any licenses required for sale of your products on the marketplace. b. To the extent required by applicable law, you shall register with relevant tax authorities and pay all relevant taxes in relation to your product sales. d. d. You shall conduct your business on the marketplace: a. In compliance with the Kibuga Partner Code of Conduct, and other Kibuga codes, policies and guidelines as published on the marketplace from time to time. b. In accordance with ethical business practices and industry best practices; and 1. Without prejudice to our other rights, we reserve the right to reject, unpublish and/or delete any seller store that breaches these seller terms and conditions, the general terms and conditions, or any Kibuga codes, policies and guidelines. 1.

> **[3] Return_Policy.pdf p.1 (`f232e5d3:0`):** Return Policy Return Policy What are the conditions for returning an item? Two (2) days free returns policy, subject to Terms and conditions. Requirement for a valid procedure • Proof of purchase – the document handed over to you together with the product, on delivery. • Original packaging – the manufacturer packaging • Any free promotional items – gifts or accessories delivered with the purchased item • Valid return reason i.e. If Item is Faulty Please Note: We do not accept returns for the items below. For such purchases, please inspect the item carefully upon delivery or pick up and if necessary, reject it on the spot: • Innerwear, swimsuits, gym wear, sleep wear • Perfumes, jewelry, health & wellness products, adult toys • For missing items and damaged products especially, broken screens please check with our riders during delivery and reject on the spot. How do I return an item/ What happens once I have returned an item? For any return request please contact our Customer Service Call Center at 0742511381/0742511394. and fill the form. What happens once I have returned an item? • We will perform a careful quality check. • If the claim is valid, we will refund you according to your requested refund method. • The process may take up to 2 days from when your return request was submitted. • If the claim is invalid the item will be sent back to you. • We keep track of all return requests and use the data to improve our product quality and service, as well as for customer profiling. Customers with unjustified/invalid returns may be denied the right to return items or even shop on Kibuga in the future. How much time do I have to return a product to Kibuga? • All items sold on Kibuga if faulty, can be returned within a period of 2 days from delivery date.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | NOT_IN_DOCUMENTS | |
| 1.5B | PASS | NOT_IN_DOCUMENTS | |
| Qwen3-4B | PASS | NOT_IN_DOCUMENTS | |

---

## U06 — UNANSWERABLE probe

**Question:** How many days does delivery take after I place an order?

**Expected:** abstain (NOT_IN_DOCUMENTS) — not in the corpus by design.

**Retrieved context shown to ALL three models (k=3, identical):**

> **[1] Return_Policy.pdf p.1 (`f232e5d3:2`):** Return Policy What now? • On delivery, kindly ensure to verify that the item delivered is in good condition and reject if it does not match your order. Can I return my items after the timeline to return has expired? • Sorry, returns are not possible after the 2-day return period. Do I have to return the gift when I return a product? • Yes, any gift must also be returned. Do I have to pay for shipping charges when I return a product? • There are no charges for shipping a product back to Kibuga.

> **[2] Return_Policy.pdf p.1 (`f232e5d3:1`):** Return Policy NOTE: You have 2 days to notify us of your return by calling Customer Service, from the day you received your purchase. For defective items, we also advise you to contact the manufacturer if the product has a warranty. How do I send my product to Kibuga? • We will make 3 attempts within 2 working days to pick-up the returning item after you submit the return request .Note that You can also drop your return item at our offices/Warehouse. However, after 3 pick-up attempts, we will cancel the return procedure and you will not be able to return your product to us anymore. Please ensure that the package of the returning item is in good condition for the return; any package found to be damaged will be rejected by the rider during collection or sent back after quality check is done. How do I track my return status? • We will keep you updated by email and SMS about the status of your return. For any inquiries contact our Customer Service Call Center at 0742511381 / 0742511394.. Is my product under warranty? • We advise you to check our warranty page to get more information about our warranty policy. If my returned product is not validated for refund, how do I get informed? • If your return is invalid, then we will call you to explain the issue and send the item(s) back to you. We will arrange the delivery of the item."Note that we will make two (2) attempts to return the product to you at no cost. However, after two (2) failed attempts, we will cancel the return process and store the product at our warehouse for up to seven (7) days awaiting your collection. If you do not collect the product within these seven (7) days, it will be deemed as forfeited and we will dispose off in accordance with the Ugandan law I received something I didn't order.

> **[3] Return_Policy.pdf p.1 (`f232e5d3:0`):** Return Policy Return Policy What are the conditions for returning an item? Two (2) days free returns policy, subject to Terms and conditions. Requirement for a valid procedure • Proof of purchase – the document handed over to you together with the product, on delivery. • Original packaging – the manufacturer packaging • Any free promotional items – gifts or accessories delivered with the purchased item • Valid return reason i.e. If Item is Faulty Please Note: We do not accept returns for the items below. For such purchases, please inspect the item carefully upon delivery or pick up and if necessary, reject it on the spot: • Innerwear, swimsuits, gym wear, sleep wear • Perfumes, jewelry, health & wellness products, adult toys • For missing items and damaged products especially, broken screens please check with our riders during delivery and reject on the spot. How do I return an item/ What happens once I have returned an item? For any return request please contact our Customer Service Call Center at 0742511381/0742511394. and fill the form. What happens once I have returned an item? • We will perform a careful quality check. • If the claim is valid, we will refund you according to your requested refund method. • The process may take up to 2 days from when your return request was submitted. • If the claim is invalid the item will be sent back to you. • We keep track of all return requests and use the data to improve our product quality and service, as well as for customer profiling. Customers with unjustified/invalid returns may be denied the right to return items or even shop on Kibuga in the future. How much time do I have to return a product to Kibuga? • All items sold on Kibuga if faulty, can be returned within a period of 2 days from delivery date.

**Model answers + Layer-A verdict:**

| model | Layer-A | answer | Layer-B (fill in) |
|-------|---------|--------|-------------------|
| 3B | PASS | NOT_IN_DOCUMENTS | |
| 1.5B | PASS | NOT_IN_DOCUMENTS | |
| Qwen3-4B | PASS | The context provided does not mention the delivery time after placing an order. Therefore, the answer is NOT_IN_DOCUMENTS. | |

---

---

## Layer-B verdicts — FILLED 2026-08-14

Grader: LLM-as-judge (in-session). Full analysis, methodology, Layer-A disagreement
quantification and severity annotations: [`LAYER_B_GRADE_2026-08-14.md`](LAYER_B_GRADE_2026-08-14.md).
Legend: **F** = FAITHFUL, **U** = UNFAITHFUL (s = substantive, m = minor),
**WA** = WRONG_ABSTENTION, **CA** = CORRECT_ABSTENTION (retrieval-miss or probe).
"Gold?" = was the gold chunk retrieved (identical for all three models).

| Q | Gold? | 3B | 1.5B | Qwen3-4B |
|---|---|---|---|---|
| Q01 | Y | F | F | F |
| Q02 | Y | F | F | F |
| Q03 | Y | F | F | F |
| Q04 | Y | F | F | F |
| Q05 | Y | F | F | F |
| Q06 | Y | F | F | F |
| Q07 | Y | F | F | F |
| Q08 | Y | **WA** | F | F |
| Q09 | Y | F | F | F |
| Q10 | Y | F | F | F |
| Q12 | Y | F | F | F |
| Q13 | Y | F | F | F |
| Q14 | Y | F | F | F |
| Q15 | Y | F | F | F |
| Q16 | Y | F | F | F |
| Q17 | N | CA | CA | CA |
| Q19 | N | **U-s** | **U-s** | **U-s** |
| Q21 | Y | F | F | F |
| Q22 | N | F | F | F |
| Q23 | Y | F | F | F |
| Q24 | Y | F | F | F |
| Q25 | Y | F | F | F |
| Q26 | Y | F | F | F |
| Q27 | N | CA | **U-s** | CA |
| Q28 | Y | F | F | F |
| Q29 | N | CA | CA | **U-s** |
| Q30 | Y | F | F | F |
| Q31 | Y | F | F | F |
| Q32 | N | F | F | F |
| Q33 | Y | F | **U-s** | F |
| Q34 | Y | F | F | F |
| Q35 | N | CA | CA | CA |
| Q36 | Y | F | F | F |
| Q37 | Y | F | F | F |
| Q38 | Y | F | **U-m** | F |
| U01 | — | CA | CA | CA |
| U02 | — | CA | CA | CA |
| U03 | — | CA | CA | CA |
| U04 | — | CA | CA | **U-s** |
| U05 | — | CA | CA | CA |
| U06 | — | CA | CA | CA |

Headline: faithfulness 29/35 (3B), 28/35 (1.5B), 30/35 (Qwen3-4B); gold-hit faithfulness
27/28, 26/28, 28/28; substantive unique hallucinations 0, 2, 2; probe abstention 6/6, 6/6,
5/6. **Model choice unchanged: 3B** (safety + efficiency + top-tier faithfulness).
