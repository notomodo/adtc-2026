# R5 Hand-Validation Review Packet

This packet exists to hand-validate Layer A (the deterministic token-overlap grader) against
the actual answer text, for risk **R5** in `DECISIONS.md`: *"Layer A is a token-overlap
heuristic, not a truth oracle. The 71.4% v3 pass rate has not been hand-validated against the
actual answer text."* Token overlap can score an answer PASS when the model actually answered
from the wrong chunk, or when it is not grounded in what it saw at all — see Q19 below, which
is a confirmed instance. For each item, read the question, the gold chunk(s), the chunks the
model actually retrieved (these sometimes differ from gold — that is the point), and the
model's answer, then check exactly one of the four boxes:

- **CORRECT** — the answer is accurate and supported by the passages shown below.
- **UNGROUNDED** — the answer is plausible but not actually supported by the passages the
  model saw (it may be right by luck, general knowledge, or coincidental vocabulary overlap).
- **WRONG** — the answer contradicts the passages shown, or is factually incorrect.
- **LABEL ISSUE** — the answer is fine, but the gold label naming the "correct" chunk is
  wrong or incomplete (e.g. more than one chunk could support the question).

**Layer A's verdict and reason are shown for comparison only — not as a suggestion to agree
with.** Layer A measures token overlap between the answer and the gold chunk; it does not
read either for meaning. This validation exists precisely because that heuristic can be
wrong in either direction.

---

## Priority 1: Confirmed false-positive candidate — gold chunk absent from context

### Q19 — prose

> **Q19** is the confirmed example that motivates this packet: gold chunk is `[2]`. The
> retrieved context was `[15, 46, 37]`, so **the gold chunk was never in the model's context
> at all**. Layer A nonetheless scored it **PASS** at 0.52 overlap, because the model answered
> from chunk 15, which shares vocabulary with chunk 2. This is either an ungrounded answer
> scored as correct, **or** a gold-label problem (the question may have more than one valid
> supporting chunk and the label names only one). Only a human reading the text can tell
> which.

**Question:** Can Kibuga suspend my account without telling me?

**Layer A verdict:** PASS  
**Layer A reason:** gold-overlap ratio 0.52 (15/29 distinctive toks)

**Gold chunks:** [2]  
**Retrieved chunks:** [15, 46, 37]  
**Gold chunk in context: NO**

**Gold chunk text:**

**[2]** — `General_Terms_for_Sellers_and_Buyers.pdf`, page 1

> 2. Registration and account
> You may not register with our marketplace if you are under 18 years of age (by using our marketplace or agreeing to these general terms and conditions, you warrant and represent to us that you are at least 18 years of age). ● You may register for an account with our marketplace by completing and submitting the registration form on our marketplace. ● You represent and warrant that all information provided in the registration form is complete and accurate. If you register for an account with our marketplace, you will be asked to provide an email address/user ID and you agree to: ● keep your password confidential. ● Notify us in writing immediately (using our contact details provided) if you become aware of any disclosure of your password; and Be responsible for any activity on our marketplace arising out of any failure to keep your password confidential, and that you may be held liable for any losses arising out of such a failure. Your account shall be used exclusively by you, and you shall not transfer your account to any third party. If you authorize any third party to manage your account on your behalf this shall be at your own risk. We may suspend or cancel your account, and/or edit your account details, at any time in our sole discretion and without notice or explanation, providing that if we cancel any products or services you have paid for but not received, and you have not breached these general terms and conditions, we will refund you in respect of the same. ● You may cancel your account on our marketplace by contacting us. 3. Terms and conditions of sale ● You acknowledge and agree that: ● The marketplace provides an online location for sellers to sell and buyers to purchase products.

**Retrieved chunk text (what the model actually saw):**

**[15]** — `General_Terms_for_Sellers_and_Buyers.pdf`, page 8

> 1. Limitations and exclusions of liability
> If you breach these general terms and conditions, or if we reasonably suspect that you have breached these general terms and conditions or any Kibuga codes, policies or guidelines in any way we may: 1. temporarily suspend your access to our marketplace. 2. permanently prohibit you from accessing our marketplace. ● Block computers using your IP address from accessing our marketplace. ● Contact any or all your internet service providers and request that they block your access to our marketplace. ● Suspend or delete your account on our marketplace; and/or ● Commence legal action against you, whether for breach of contract or otherwise. Where we suspend, prohibit or block your access to our marketplace or a part of our marketplace you must not take any action to circumvent such suspension or prohibition or blocking (including without limitation creating and/or using a different account).

**[46]** — `Sellers_Terms_and_Conditions.pdf`, page 1

> Sellers Terms and Conditions
> If we reasonably determine that you have breached these seller terms and conditions, our general terms and conditions, or any Kibuga codes, policies or guidelines, we may: 1. send you one or more formal warnings. b. suspend, prohibit or block your access to our marketplace as provided in the general terms and conditions. c. apply penalties for breach as provided in our Seller Penalty Policy; and/or d. commence legal action against you, whether for breach of contract or otherwise. 2. We may vary the amount of the penalties for breach from time to time by updating the Seller Penalty Policy, but this will not affect any liability to pay penalties that accrue before the new amounts are posted. Confidentiality and data privacy All information and documents concerning the conduct of business pursuant to these general terms and conditions, including information relating to business methods, procedures, policies and sales information, is strictly confidential unless it is already in the public domain. You shall not use Kibuga’s confidential information for any purpose other than to perform your obligations under this Agreement and you shall not disclose Kibuga’s confidential information without our prior written consent. Sellers may not send advertising or promotional communications to buyers on the marketplace without the prior written consent of Kibuga and shall be directly responsible to marketplace users for any misuse of their personal data. If Kibuga is sued, fined, or otherwise incurs expenses because of the seller’s handling of personal data obtained through the marketplace, the seller shall indemnify Kibuga in respect of the same.

**[37]** — `Return_Policy.pdf`, page 1

> Return Policy
> NOTE: You have 2 days to notify us of your return by calling Customer Service, from the day you received your purchase. For defective items, we also advise you to contact the manufacturer if the product has a warranty. How do I send my product to Kibuga? • We will make 3 attempts within 2 working days to pick-up the returning item after you submit the return request .Note that You can also drop your return item at our offices/Warehouse. However, after 3 pick-up attempts, we will cancel the return procedure and you will not be able to return your product to us anymore. Please ensure that the package of the returning item is in good condition for the return; any package found to be damaged will be rejected by the rider during collection or sent back after quality check is done. How do I track my return status? • We will keep you updated by email and SMS about the status of your return. For any inquiries contact our Customer Service Call Center at 0742511381 / 0742511394.. Is my product under warranty? • We advise you to check our warranty page to get more information about our warranty policy. If my returned product is not validated for refund, how do I get informed? • If your return is invalid, then we will call you to explain the issue and send the item(s) back to you. We will arrange the delivery of the item."Note that we will make two (2) attempts to return the product to you at no cost. However, after two (2) failed attempts, we will cancel the return process and store the product at our warehouse for up to seven (7) days awaiting your collection. If you do not collect the product within these seven (7) days, it will be deemed as forfeited and we will dispose off in accordance with the Ugandan law I received something I didn't order.

**Model's answer (verbatim):**

> Sellers Terms and Conditions state that if we reasonably determine that you have breached these seller terms and conditions or any Kibuga codes, policies or guidelines, we may suspend, prohibit or block your access to our marketplace as provided in the general terms and conditions. This implies that Kibuga can suspend my account without telling me.

**Human verdict:**

```
  [ ] CORRECT      — answer is accurate and supported by the passages shown
  [X] UNGROUNDED   — plausible but not supported by the passages the model saw
  [ ] WRONG        — contradicts the passages, or is factually incorrect
  [ ] LABEL ISSUE  — answer is fine, but the gold label is wrong/incomplete
  Notes: the answer is correct, chunk 46 has text similar to what the query wants.
```

---

## Priority 2: All multi_chunk — synthesis quality, hardest for token overlap

### Q36 — multi_chunk

**Question:** Across all the policies, what enforcement actions can Kibuga take against a seller who breaches the terms?

**Layer A verdict:** PASS  
**Layer A reason:** gold-overlap ratio 0.62 (23/37 distinctive toks)

**Gold chunks:** [15, 46]  
**Retrieved chunks:** [40, 46, 15]  
**Gold chunk in context: YES**

**Gold chunk text:**

**[15]** — `General_Terms_for_Sellers_and_Buyers.pdf`, page 8

> 1. Limitations and exclusions of liability
> If you breach these general terms and conditions, or if we reasonably suspect that you have breached these general terms and conditions or any Kibuga codes, policies or guidelines in any way we may: 1. temporarily suspend your access to our marketplace. 2. permanently prohibit you from accessing our marketplace. ● Block computers using your IP address from accessing our marketplace. ● Contact any or all your internet service providers and request that they block your access to our marketplace. ● Suspend or delete your account on our marketplace; and/or ● Commence legal action against you, whether for breach of contract or otherwise. Where we suspend, prohibit or block your access to our marketplace or a part of our marketplace you must not take any action to circumvent such suspension or prohibition or blocking (including without limitation creating and/or using a different account).

**[46]** — `Sellers_Terms_and_Conditions.pdf`, page 1

> Sellers Terms and Conditions
> If we reasonably determine that you have breached these seller terms and conditions, our general terms and conditions, or any Kibuga codes, policies or guidelines, we may: 1. send you one or more formal warnings. b. suspend, prohibit or block your access to our marketplace as provided in the general terms and conditions. c. apply penalties for breach as provided in our Seller Penalty Policy; and/or d. commence legal action against you, whether for breach of contract or otherwise. 2. We may vary the amount of the penalties for breach from time to time by updating the Seller Penalty Policy, but this will not affect any liability to pay penalties that accrue before the new amounts are posted. Confidentiality and data privacy All information and documents concerning the conduct of business pursuant to these general terms and conditions, including information relating to business methods, procedures, policies and sales information, is strictly confidential unless it is already in the public domain. You shall not use Kibuga’s confidential information for any purpose other than to perform your obligations under this Agreement and you shall not disclose Kibuga’s confidential information without our prior written consent. Sellers may not send advertising or promotional communications to buyers on the marketplace without the prior written consent of Kibuga and shall be directly responsible to marketplace users for any misuse of their personal data. If Kibuga is sued, fined, or otherwise incurs expenses because of the seller’s handling of personal data obtained through the marketplace, the seller shall indemnify Kibuga in respect of the same.

**Retrieved chunk text (what the model actually saw):**

**[40]** — `Sellers_Terms_and_Conditions.pdf`, page 1

> Sellers Terms and Conditions
> Sellers Terms and Conditions Introduction Kibuga Investment operates an e-commerce platform consisting of a website and mobile application (“marketplace”), together with supporting logistics and payment infrastructure, for the sale and purchase of consumer products in Uganda (“territory”). These seller terms and conditions shall apply to all sellers on the marketplace, together with our general terms and conditions of the use of the marketplace. If you register with our marketplace as a seller: a. you accept these seller terms and conditions, the general terms and conditions, and the Kibuga codes, policies and guidelines, and as may be amended by Kibuga from time to time. b. We will ask you to expressly agree to these seller terms and conditions. 1. Seller stores a. If you register with our marketplace as a seller you will be able to create a store on the marketplace, using the “Kibuga” portal. b. Seller stores that are submitted may be reviewed for approval, at Kibuga’s discretion before they are operational. c. You shall be solely responsible for your store, listings and products and you hereby agree that: a. You shall obtain any licenses required for sale of your products on the marketplace. b. To the extent required by applicable law, you shall register with relevant tax authorities and pay all relevant taxes in relation to your product sales. d. d. You shall conduct your business on the marketplace: a. In compliance with the Kibuga Partner Code of Conduct, and other Kibuga codes, policies and guidelines as published on the marketplace from time to time. b. In accordance with ethical business practices and industry best practices; and 1. Without prejudice to our other rights, we reserve the right to reject, unpublish and/or delete any seller store that breaches these seller terms and conditions, the general terms and conditions, or any Kibuga codes, policies and guidelines. 1.

**[46]** — `Sellers_Terms_and_Conditions.pdf`, page 1

> Sellers Terms and Conditions
> If we reasonably determine that you have breached these seller terms and conditions, our general terms and conditions, or any Kibuga codes, policies or guidelines, we may: 1. send you one or more formal warnings. b. suspend, prohibit or block your access to our marketplace as provided in the general terms and conditions. c. apply penalties for breach as provided in our Seller Penalty Policy; and/or d. commence legal action against you, whether for breach of contract or otherwise. 2. We may vary the amount of the penalties for breach from time to time by updating the Seller Penalty Policy, but this will not affect any liability to pay penalties that accrue before the new amounts are posted. Confidentiality and data privacy All information and documents concerning the conduct of business pursuant to these general terms and conditions, including information relating to business methods, procedures, policies and sales information, is strictly confidential unless it is already in the public domain. You shall not use Kibuga’s confidential information for any purpose other than to perform your obligations under this Agreement and you shall not disclose Kibuga’s confidential information without our prior written consent. Sellers may not send advertising or promotional communications to buyers on the marketplace without the prior written consent of Kibuga and shall be directly responsible to marketplace users for any misuse of their personal data. If Kibuga is sued, fined, or otherwise incurs expenses because of the seller’s handling of personal data obtained through the marketplace, the seller shall indemnify Kibuga in respect of the same.

**[15]** — `General_Terms_for_Sellers_and_Buyers.pdf`, page 8

> 1. Limitations and exclusions of liability
> If you breach these general terms and conditions, or if we reasonably suspect that you have breached these general terms and conditions or any Kibuga codes, policies or guidelines in any way we may: 1. temporarily suspend your access to our marketplace. 2. permanently prohibit you from accessing our marketplace. ● Block computers using your IP address from accessing our marketplace. ● Contact any or all your internet service providers and request that they block your access to our marketplace. ● Suspend or delete your account on our marketplace; and/or ● Commence legal action against you, whether for breach of contract or otherwise. Where we suspend, prohibit or block your access to our marketplace or a part of our marketplace you must not take any action to circumvent such suspension or prohibition or blocking (including without limitation creating and/or using a different account).

**Model's answer (verbatim):**

> Kibuga can enforce several actions against a seller who breaches the terms of their agreements. These include sending formal warnings, suspending or permanently prohibiting access to the marketplace, blocking computers using the seller's IP address from accessing the marketplace, contacting any or all of the seller's internet service providers to block their access to the marketplace, suspending or deleting the seller's account on the marketplace, and commencing legal action against the seller.

**Human verdict:**

```
  [x] CORRECT      — answer is accurate and supported by the passages shown
  [ ] UNGROUNDED   — plausible but not supported by the passages the model saw
  [ ] WRONG        — contradicts the passages, or is factually incorrect
  [ ] LABEL ISSUE  — answer is fine, but the gold label is wrong/incomplete
  Notes: ______________________________________________
```

### Q37 — multi_chunk

**Question:** How does Kibuga handle a seller's money — what gets deducted and what's left?

**Layer A verdict:** PASS  
**Layer A reason:** gold-overlap ratio 0.88 (38/43 distinctive toks)

**Gold chunks:** [45, 44]  
**Retrieved chunks:** [44, 3, 46]  
**Gold chunk in context: PARTIAL — present: [44], absent: [45]**

**Gold chunk text:**

**[45]** — `Sellers_Terms_and_Conditions.pdf`, page 1

> Sellers Terms and Conditions
> We shall collect payments from buyers in respect of each product purchased from the marketplace, and we shall deduct from the same our commissions and, as may be applicable, any fees, charges, taxes, penalties, refunds and any other amounts that you owe to us in respect of any business whatsoever. b. We shall remit the proceeds of sale of the products, after all deductions, and remit the remaining funds to you. c. Evidence of payment to your nominated account shall constitute conclusive evidence of payment and receipt. d. You shall be entirely responsible for ensuring that the account details that you upload to the Seller Centre are accurate and up to date, and that the account is secure. We shall not be liable for any loss or damage to you that may result from fraud or error in respect of your account. e. We shall provide you with an account statement, via the Seller Center, which shall include details of all proceeds of sale of the products, deductions and remittances. f. operate more than one account. For the avoidance of any doubt, the account statement in the Seller Centre shall serve as such notice of set-off. g. In the event that we hold insufficient funds on your behalf for payment of any amounts that you owe us (your account is in debit): h. We may delay or suspend payment to you in the event of investigation of a potential fraud or other breach of this agreement. i. In the event that the vendor disputes any transaction or statement of account it must report its claim to Kibuga within three (3) weeks of the date of the relevant transaction, failing which such claim shall be deemed to be waived. Breaches of seller terms and conditions a.

**[44]** — `Sellers_Terms_and_Conditions.pdf`, page 1

> Sellers Terms and Conditions
> This will not affect any liability to pay commission that accrues before the new rates are posted or for services that have been previously paid. 5. VAT and other taxes a. All amounts stated on the marketplace are stated inclusive of VAT and any other taxes applicable to the transaction. The seller acknowledges that: ● Commissions shall be calculated as a percentage of the selling price (being the price set by the vendor at the time of the order) inclusive of VAT and any other taxes charged to the buyer. ● Commissions are inclusive of VAT and all other taxes thereon; and ● In the event of any upwards revision in the rate of VAT or any other applicable taxes, the amount of the commission shall be automatically adjusted to ensure that Kibuga’s net revenues remain constant. b. The seller shall be exclusively liable in respect of all taxes applicable to the transactions entered into on the marketplace with buyers, including VAT, and shall therefore be responsible for the reporting, filing and payment of the same. c. Should a competent tax authority determine that Kibuga is liable for payment of any taxes (including stamp, excise or customs duties) in respect of the transactions, notably, you hereby indemnify and hold harmless Kibuga in respect of the same. We may make tax-related deductions to payments processed by us on your behalf and remit such deducted amounts to the relevant government or tax authority. d. Promptly following receipt of a written request from us, you must supply to us any information and documentation that we may reasonably request in order to identify you or facilitate our compliance with our legal obligations relating to the taxation of payments made to us or processed by us. We may supply such information and/or documentation to relevant government and tax authorities. Remittances a.

**Retrieved chunk text (what the model actually saw):**

**[44]** — `Sellers_Terms_and_Conditions.pdf`, page 1

> Sellers Terms and Conditions
> This will not affect any liability to pay commission that accrues before the new rates are posted or for services that have been previously paid. 5. VAT and other taxes a. All amounts stated on the marketplace are stated inclusive of VAT and any other taxes applicable to the transaction. The seller acknowledges that: ● Commissions shall be calculated as a percentage of the selling price (being the price set by the vendor at the time of the order) inclusive of VAT and any other taxes charged to the buyer. ● Commissions are inclusive of VAT and all other taxes thereon; and ● In the event of any upwards revision in the rate of VAT or any other applicable taxes, the amount of the commission shall be automatically adjusted to ensure that Kibuga’s net revenues remain constant. b. The seller shall be exclusively liable in respect of all taxes applicable to the transactions entered into on the marketplace with buyers, including VAT, and shall therefore be responsible for the reporting, filing and payment of the same. c. Should a competent tax authority determine that Kibuga is liable for payment of any taxes (including stamp, excise or customs duties) in respect of the transactions, notably, you hereby indemnify and hold harmless Kibuga in respect of the same. We may make tax-related deductions to payments processed by us on your behalf and remit such deducted amounts to the relevant government or tax authority. d. Promptly following receipt of a written request from us, you must supply to us any information and documentation that we may reasonably request in order to identify you or facilitate our compliance with our legal obligations relating to the taxation of payments made to us or processed by us. We may supply such information and/or documentation to relevant government and tax authorities. Remittances a.

**[3]** — `General_Terms_for_Sellers_and_Buyers.pdf`, page 1

> 2. Registration and account
> ● We shall accept binding sales, on behalf of sellers, but Kibuga is not a party to the transaction between the seller and the buyer; and A contract for the sale and purchase of a product or products will come into force between the buyer and seller, and accordingly you commit to buying or selling the relevant product or products, upon the buyer’s confirmation of purchase via the marketplace. Subject to these general terms and conditions, the seller’s terms of business shall govern the contract for sale and purchase between the buyer and the seller. Notwithstanding this, the following provisions will be incorporated into the contract of sale and purchase between the buyer and the seller: ● The price for a product will be as stated in the relevant product listing. ● The price for the product must include all taxes and comply with applicable laws in force from time to time. Delivery charges, packaging charges, handling charges, administrative charges, insurance costs, other ancillary costs and charges, will only be payable by the buyer if this is expressly and clearly stated in the product listing. Products must be of satisfactory quality, fit and safe for any purpose specified in, and conform in all material respects to, the product listing and any other description of the products supplied or made available by the seller to the buyer; and The seller warrants that the seller has good title to, and is the sole legal and beneficial owner of, the products, and that the products are not subject to any third-party rights or restrictions including in respect of third-party intellectual property rights and/or any criminal, insolvency or tax investigation or proceedings.

**[46]** — `Sellers_Terms_and_Conditions.pdf`, page 1

> Sellers Terms and Conditions
> If we reasonably determine that you have breached these seller terms and conditions, our general terms and conditions, or any Kibuga codes, policies or guidelines, we may: 1. send you one or more formal warnings. b. suspend, prohibit or block your access to our marketplace as provided in the general terms and conditions. c. apply penalties for breach as provided in our Seller Penalty Policy; and/or d. commence legal action against you, whether for breach of contract or otherwise. 2. We may vary the amount of the penalties for breach from time to time by updating the Seller Penalty Policy, but this will not affect any liability to pay penalties that accrue before the new amounts are posted. Confidentiality and data privacy All information and documents concerning the conduct of business pursuant to these general terms and conditions, including information relating to business methods, procedures, policies and sales information, is strictly confidential unless it is already in the public domain. You shall not use Kibuga’s confidential information for any purpose other than to perform your obligations under this Agreement and you shall not disclose Kibuga’s confidential information without our prior written consent. Sellers may not send advertising or promotional communications to buyers on the marketplace without the prior written consent of Kibuga and shall be directly responsible to marketplace users for any misuse of their personal data. If Kibuga is sued, fined, or otherwise incurs expenses because of the seller’s handling of personal data obtained through the marketplace, the seller shall indemnify Kibuga in respect of the same.

**Model's answer (verbatim):**

> Kibuga may make tax-related deductions to payments processed by us on your behalf and remit such deducted amounts to the relevant government or tax authority. Therefore, taxes applicable to the transactions entered into on the marketplace with buyers, including VAT, are handled by Kibuga through these deductions. The amount of the commission is automatically adjusted in case of any upwards revision in the rate of VAT or other applicable taxes, ensuring that Kibuga's net revenues remain constant.

**Human verdict:**

```
  [x] CORRECT      — answer is accurate and supported by the passages shown
  [ ] UNGROUNDED   — plausible but not supported by the passages the model saw
  [ ] WRONG        — contradicts the passages, or is factually incorrect
  [ ] LABEL ISSUE  — answer is fine, but the gold label is wrong/incomplete
  Notes: ______________________________________________
```

### Q38 — multi_chunk

**Question:** Walk me through everything I need to know to return an item and get my money back.

**Layer A verdict:** PASS  
**Layer A reason:** gold-overlap ratio 0.79 (92/117 distinctive toks)

**Gold chunks:** [36, 37, 38]  
**Retrieved chunks:** [37, 36, 38]  
**Gold chunk in context: YES**

**Gold chunk text:**

**[36]** — `Return_Policy.pdf`, page 1

> Return Policy
> Return Policy What are the conditions for returning an item? Two (2) days free returns policy, subject to Terms and conditions. Requirement for a valid procedure • Proof of purchase – the document handed over to you together with the product, on delivery. • Original packaging – the manufacturer packaging • Any free promotional items – gifts or accessories delivered with the purchased item • Valid return reason i.e. If Item is Faulty Please Note: We do not accept returns for the items below. For such purchases, please inspect the item carefully upon delivery or pick up and if necessary, reject it on the spot: • Innerwear, swimsuits, gym wear, sleep wear • Perfumes, jewelry, health & wellness products, adult toys • For missing items and damaged products especially, broken screens please check with our riders during delivery and reject on the spot. How do I return an item/ What happens once I have returned an item? For any return request please contact our Customer Service Call Center at 0742511381/0742511394. and fill the form. What happens once I have returned an item? • We will perform a careful quality check. • If the claim is valid, we will refund you according to your requested refund method. • The process may take up to 2 days from when your return request was submitted. • If the claim is invalid the item will be sent back to you. • We keep track of all return requests and use the data to improve our product quality and service, as well as for customer profiling. Customers with unjustified/invalid returns may be denied the right to return items or even shop on Kibuga in the future. How much time do I have to return a product to Kibuga? • All items sold on Kibuga if faulty, can be returned within a period of 2 days from delivery date.

**[37]** — `Return_Policy.pdf`, page 1

> Return Policy
> NOTE: You have 2 days to notify us of your return by calling Customer Service, from the day you received your purchase. For defective items, we also advise you to contact the manufacturer if the product has a warranty. How do I send my product to Kibuga? • We will make 3 attempts within 2 working days to pick-up the returning item after you submit the return request .Note that You can also drop your return item at our offices/Warehouse. However, after 3 pick-up attempts, we will cancel the return procedure and you will not be able to return your product to us anymore. Please ensure that the package of the returning item is in good condition for the return; any package found to be damaged will be rejected by the rider during collection or sent back after quality check is done. How do I track my return status? • We will keep you updated by email and SMS about the status of your return. For any inquiries contact our Customer Service Call Center at 0742511381 / 0742511394.. Is my product under warranty? • We advise you to check our warranty page to get more information about our warranty policy. If my returned product is not validated for refund, how do I get informed? • If your return is invalid, then we will call you to explain the issue and send the item(s) back to you. We will arrange the delivery of the item."Note that we will make two (2) attempts to return the product to you at no cost. However, after two (2) failed attempts, we will cancel the return process and store the product at our warehouse for up to seven (7) days awaiting your collection. If you do not collect the product within these seven (7) days, it will be deemed as forfeited and we will dispose off in accordance with the Ugandan law I received something I didn't order.

**[38]** — `Return_Policy.pdf`, page 1

> Return Policy
> What now? • On delivery, kindly ensure to verify that the item delivered is in good condition and reject if it does not match your order. Can I return my items after the timeline to return has expired? • Sorry, returns are not possible after the 2-day return period. Do I have to return the gift when I return a product? • Yes, any gift must also be returned. Do I have to pay for shipping charges when I return a product? • There are no charges for shipping a product back to Kibuga.

**Retrieved chunk text (what the model actually saw):**

**[37]** — `Return_Policy.pdf`, page 1

> Return Policy
> NOTE: You have 2 days to notify us of your return by calling Customer Service, from the day you received your purchase. For defective items, we also advise you to contact the manufacturer if the product has a warranty. How do I send my product to Kibuga? • We will make 3 attempts within 2 working days to pick-up the returning item after you submit the return request .Note that You can also drop your return item at our offices/Warehouse. However, after 3 pick-up attempts, we will cancel the return procedure and you will not be able to return your product to us anymore. Please ensure that the package of the returning item is in good condition for the return; any package found to be damaged will be rejected by the rider during collection or sent back after quality check is done. How do I track my return status? • We will keep you updated by email and SMS about the status of your return. For any inquiries contact our Customer Service Call Center at 0742511381 / 0742511394.. Is my product under warranty? • We advise you to check our warranty page to get more information about our warranty policy. If my returned product is not validated for refund, how do I get informed? • If your return is invalid, then we will call you to explain the issue and send the item(s) back to you. We will arrange the delivery of the item."Note that we will make two (2) attempts to return the product to you at no cost. However, after two (2) failed attempts, we will cancel the return process and store the product at our warehouse for up to seven (7) days awaiting your collection. If you do not collect the product within these seven (7) days, it will be deemed as forfeited and we will dispose off in accordance with the Ugandan law I received something I didn't order.

**[36]** — `Return_Policy.pdf`, page 1

> Return Policy
> Return Policy What are the conditions for returning an item? Two (2) days free returns policy, subject to Terms and conditions. Requirement for a valid procedure • Proof of purchase – the document handed over to you together with the product, on delivery. • Original packaging – the manufacturer packaging • Any free promotional items – gifts or accessories delivered with the purchased item • Valid return reason i.e. If Item is Faulty Please Note: We do not accept returns for the items below. For such purchases, please inspect the item carefully upon delivery or pick up and if necessary, reject it on the spot: • Innerwear, swimsuits, gym wear, sleep wear • Perfumes, jewelry, health & wellness products, adult toys • For missing items and damaged products especially, broken screens please check with our riders during delivery and reject on the spot. How do I return an item/ What happens once I have returned an item? For any return request please contact our Customer Service Call Center at 0742511381/0742511394. and fill the form. What happens once I have returned an item? • We will perform a careful quality check. • If the claim is valid, we will refund you according to your requested refund method. • The process may take up to 2 days from when your return request was submitted. • If the claim is invalid the item will be sent back to you. • We keep track of all return requests and use the data to improve our product quality and service, as well as for customer profiling. Customers with unjustified/invalid returns may be denied the right to return items or even shop on Kibuga in the future. How much time do I have to return a product to Kibuga? • All items sold on Kibuga if faulty, can be returned within a period of 2 days from delivery date.

**[38]** — `Return_Policy.pdf`, page 1

> Return Policy
> What now? • On delivery, kindly ensure to verify that the item delivered is in good condition and reject if it does not match your order. Can I return my items after the timeline to return has expired? • Sorry, returns are not possible after the 2-day return period. Do I have to return the gift when I return a product? • Yes, any gift must also be returned. Do I have to pay for shipping charges when I return a product? • There are no charges for shipping a product back to Kibuga.

**Model's answer (verbatim):**

> To initiate the return process, you must notify Customer Service within 2 days of receiving your purchase by calling them at either 0742511381 or 0742511394. You need to provide proof of purchase and original packaging for a valid procedure.
>
> For defective items, contact the manufacturer if there is a warranty. If you choose to send your item back, ensure it is in good condition as any damaged package will be rejected by the rider during collection or sent back after quality check is done. 
>
> Once you have submitted your return request and all necessary documents are provided, Kibuga will perform a careful quality check. If the claim is valid, you will receive a refund according to your requested method within 2 days from when your return was submitted. However, if the claim is invalid, the item will be sent back to you.
>
> Kibuga keeps track of all return requests for improvement and customer profiling purposes. Customers with unjustified or invalid returns may lose their right to return items in the future.
>
> If a product is not under warranty, Kibuga advises checking our warranty page for more information about our policy. For missing items or damaged products, especially broken screens, you should check with our riders during delivery and reject on the spot if necessary.
>
> There are no shipping charges when returning a product to Kibuga. If you have any gifts included in your purchase, they must also be returned.

**Human verdict:**

```
  [x] CORRECT      — answer is accurate and supported by the passages shown
  [ ] UNGROUNDED   — plausible but not supported by the passages the model saw
  [ ] WRONG        — contradicts the passages, or is factually incorrect
  [ ] LABEL ISSUE  — answer is fine, but the gold label is wrong/incomplete
  Notes: ______________________________________________
```

---

## Priority 3: Remaining prose — inference, not lookup

### Q15 — prose

**Question:** What kinds of content am I forbidden from posting?

**Layer A verdict:** PASS  
**Layer A reason:** gold-overlap ratio 0.72 (39/54 distinctive toks)

**Gold chunks:** [5]  
**Retrieved chunks:** [6, 5, 7]  
**Gold chunk in context: YES**

**Gold chunk text:**

**[5]** — `General_Terms_for_Sellers_and_Buyers.pdf`, page 3

> 5. Rules about your content
> In these general terms and conditions, "your content" means: All works and materials (including without limitation text, graphics, images, audio material, video material, audio-visual material, scripts, software and files) that you submit to us or our marketplace for storage or publication, processing by, or onward transmission; and ● All communications on the marketplace, including product reviews, feedback and comments. Your content, and the use of your content by us in accordance with these general terms and conditions, must be accurate, complete and truthful. Your content must be appropriate, civil and tasteful, and accord with generally accepted standards of etiquette and behavior on the internet, and must not: ● Be offensive, obscene, indecent, pornographic, lewd, suggestive or sexually explicit. Depict violence in an explicit, graphic or gratuitous manner; or ● Be blasphemous, in breach of racial or religious hatred or discrimination legislation. ● Be deceptive, fraudulent, threatening, abusive, harassing, anti-social, menacing, hateful, discriminatory or inflammatory. Cause annoyance, inconvenience or needless anxiety to any person; or Constitute spam. Your content must not be illegal or unlawful, infringe any person's legal rights, or be capable of giving rise to legal action against any person (in each case in any jurisdiction and under any applicable law). Your content must not infringe or breach: ● Any copyright, moral right, database right, trademark right, design right, right in passing off or other intellectual property right. ● Any right of confidence, right of privacy or right under data protection legislation. ● Any contractual obligation owed to any person; or ● Any court order.

**Retrieved chunk text (what the model actually saw):**

**[6]** — `General_Terms_for_Sellers_and_Buyers.pdf`, page 3

> 5. Rules about your content
> You must not use our marketplace to link to any website or web page consisting of or containing material that would, were it posted on our marketplace, breach the provisions of these general terms and conditions. ● You must not submit to our marketplace any material that is or has ever been the subject of any threatened or actual legal proceedings or other similar complaint. The review function on the marketplace may be used to facilitate buyer reviews on products. You shall not use the review function or any other form of communication to provide inaccurate, inauthentic or fake reviews. You must not interfere with a transaction by: (i) contacting another user to buy or sell an item listed on the marketplace outside of the marketplace; or (ii) communicating with a user involved in an active or completed transaction to warn them away from a particular buyer, seller or item; or (iii) contacting another user with the intent to collect any payments. You acknowledge that all users of the marketplace are solely responsible for interactions with other users, and you shall exercise caution and good judgment in your communication with users. You shall not send them personal information including credit card details. ● We may periodically review your content and we reserve the right to remove any content in our discretion for any reason whatsoever. activity that breaches these general terms and conditions, you may inform us by contacting us. Our rights to use your content You grant us a non-exclusive, royalty-free license to use, reproduce, store, adapt, publish, translate and distribute your content across our marketing channels and any existing or future media. ● You grant us the right to sub-license the rights licensed. ● You grant to us the right to bring an action for infringement of the rights licensed under section 7.1.

**[5]** — `General_Terms_for_Sellers_and_Buyers.pdf`, page 3

> 5. Rules about your content
> In these general terms and conditions, "your content" means: All works and materials (including without limitation text, graphics, images, audio material, video material, audio-visual material, scripts, software and files) that you submit to us or our marketplace for storage or publication, processing by, or onward transmission; and ● All communications on the marketplace, including product reviews, feedback and comments. Your content, and the use of your content by us in accordance with these general terms and conditions, must be accurate, complete and truthful. Your content must be appropriate, civil and tasteful, and accord with generally accepted standards of etiquette and behavior on the internet, and must not: ● Be offensive, obscene, indecent, pornographic, lewd, suggestive or sexually explicit. Depict violence in an explicit, graphic or gratuitous manner; or ● Be blasphemous, in breach of racial or religious hatred or discrimination legislation. ● Be deceptive, fraudulent, threatening, abusive, harassing, anti-social, menacing, hateful, discriminatory or inflammatory. Cause annoyance, inconvenience or needless anxiety to any person; or Constitute spam. Your content must not be illegal or unlawful, infringe any person's legal rights, or be capable of giving rise to legal action against any person (in each case in any jurisdiction and under any applicable law). Your content must not infringe or breach: ● Any copyright, moral right, database right, trademark right, design right, right in passing off or other intellectual property right. ● Any right of confidence, right of privacy or right under data protection legislation. ● Any contractual obligation owed to any person; or ● Any court order.

**[7]** — `General_Terms_for_Sellers_and_Buyers.pdf`, page 3

> 5. Rules about your content
> You hereby waive all your moral rights in your content to the maximum extent permitted by applicable law; and you warrant and represent that all other moral rights in your content have been waived to the maximum extent permitted by applicable law. Without prejudice to our other rights under these general terms and conditions, if you breach our rules on content in any way, or if we reasonably suspect that you have breached our rules on content, we may delete, unpublish or edit any or all your content.

**Model's answer (verbatim):**

> You are forbidden from posting offensive, obscene, indecent, pornographic, lewd, suggestive, sexually explicit, violent in an explicit, graphic or gratuitous manner, blasphemous, racially or religiously discriminatory, deceptive, fraudulent, threatening, abusive, harassing, anti-social, hateful, discriminatory, inflammatory, annoying, causing inconvenience or needless anxiety, spam, illegal, infringing on copyrights, moral rights, database rights, trademark rights, design rights, right in passing off, or any other intellectual property right, breaching contractual obligations, or giving rise to legal action.

**Human verdict:**

```
  [x] CORRECT      — answer is accurate and supported by the passages shown
  [ ] UNGROUNDED   — plausible but not supported by the passages the model saw
  [ ] WRONG        — contradicts the passages, or is factually incorrect
  [ ] LABEL ISSUE  — answer is fine, but the gold label is wrong/incomplete
  Notes: ______________________________________________
```

### Q32 — prose

**Question:** What can Kibuga do to me if I break the rules?

**Layer A verdict:** PASS  
**Layer A reason:** gold-overlap ratio 0.66 (27/41 distinctive toks)

**Gold chunks:** [15]  
**Retrieved chunks:** [10, 46, 23]  
**Gold chunk in context: NO**

**Gold chunk text:**

**[15]** — `General_Terms_for_Sellers_and_Buyers.pdf`, page 8

> 1. Limitations and exclusions of liability
> If you breach these general terms and conditions, or if we reasonably suspect that you have breached these general terms and conditions or any Kibuga codes, policies or guidelines in any way we may: 1. temporarily suspend your access to our marketplace. 2. permanently prohibit you from accessing our marketplace. ● Block computers using your IP address from accessing our marketplace. ● Contact any or all your internet service providers and request that they block your access to our marketplace. ● Suspend or delete your account on our marketplace; and/or ● Commence legal action against you, whether for breach of contract or otherwise. Where we suspend, prohibit or block your access to our marketplace or a part of our marketplace you must not take any action to circumvent such suspension or prohibition or blocking (including without limitation creating and/or using a different account).

**Retrieved chunk text (what the model actually saw):**

**[10]** — `General_Terms_for_Sellers_and_Buyers.pdf`, page 5

> 2. Use of website and mobile applications
> Use data collected from our website for any direct marketing activity (including without limitation email marketing, SMS marketing, telemarketing and direct mailing); or ● Do anything that interferes with the normal use of our website. 3. Copyright and trademarks ● Subject to the express provisions of these general terms and conditions: we, together with our licensors, own and control all the copyright and other intellectual property rights in our website and the material on our website; and ● All the copyright and other intellectual property rights in our website and the material on our website are reserved. Kibuga’s logos and our other registered and unregistered trademarks are trademarks belonging to us; we give no permission for the use of these trademarks, and such use may constitute an infringement of our rights. The third party registered and unregistered trademarks or service marks on our website are the property of their respective owners and we do not endorse and are not affiliated with any of the holders of any such rights and as such we cannot grant any license to exercise such rights.

**[46]** — `Sellers_Terms_and_Conditions.pdf`, page 1

> Sellers Terms and Conditions
> If we reasonably determine that you have breached these seller terms and conditions, our general terms and conditions, or any Kibuga codes, policies or guidelines, we may: 1. send you one or more formal warnings. b. suspend, prohibit or block your access to our marketplace as provided in the general terms and conditions. c. apply penalties for breach as provided in our Seller Penalty Policy; and/or d. commence legal action against you, whether for breach of contract or otherwise. 2. We may vary the amount of the penalties for breach from time to time by updating the Seller Penalty Policy, but this will not affect any liability to pay penalties that accrue before the new amounts are posted. Confidentiality and data privacy All information and documents concerning the conduct of business pursuant to these general terms and conditions, including information relating to business methods, procedures, policies and sales information, is strictly confidential unless it is already in the public domain. You shall not use Kibuga’s confidential information for any purpose other than to perform your obligations under this Agreement and you shall not disclose Kibuga’s confidential information without our prior written consent. Sellers may not send advertising or promotional communications to buyers on the marketplace without the prior written consent of Kibuga and shall be directly responsible to marketplace users for any misuse of their personal data. If Kibuga is sued, fined, or otherwise incurs expenses because of the seller’s handling of personal data obtained through the marketplace, the seller shall indemnify Kibuga in respect of the same.

**[23]** — `Privacy_Policy.pdf`, page 1

> 1. About this
> Notice This Privacy Notice provides information on how Kibuga collects and processes your personal data when you visit our website or mobile applications. It outlines what we do with your personal data, how we keep it secure, and explains the rights you have regarding your personal data.

**Model's answer (verbatim):**

> If you reasonably determine that you have breached these seller terms and conditions, our general terms and conditions, or any Kibuga codes, policies or guidelines, Kibuga may send you one or more formal warnings. They may also suspend, prohibit or block your access to our marketplace as provided in the general terms and conditions. Additionally, they can apply penalties for breach as provided in our Seller Penalty Policy; and/or commence legal action against you, whether for breach of contract or otherwise.

**Human verdict:**

```
  [x] CORRECT      — answer is accurate and supported by the passages shown
  [ ] UNGROUNDED   — plausible but not supported by the passages the model saw
  [ ] WRONG        — contradicts the passages, or is factually incorrect
  [ ] LABEL ISSUE  — answer is fine, but the gold label is wrong/incomplete
  Notes: ______________________________________________
```

### Q33 — prose

**Question:** Which outside parties might see my personal data?

**Layer A verdict:** PASS  
**Layer A reason:** gold-overlap ratio 0.62 (23/37 distinctive toks)

**Gold chunks:** [29]  
**Retrieved chunks:** [29, 32, 25]  
**Gold chunk in context: YES**

**Gold chunk text:**

**[29]** — `Privacy_Policy.pdf`, page 2

> 7. How
> We Share Your Personal Data Third-party sharing: ● Product and service delivery: Sharing data with third-party sellers. ● Service providers: Engaging third parties for functions like order fulfillment, payment processing, and marketing assistance. ● Business transfers: Customer information may be transferred in business transactions. Fraud detection: Sharing data for fraud protection and compliance with the law. We ensure that third parties use your data per this Privacy Notice and applicable laws and only for specified purposes.

**Retrieved chunk text (what the model actually saw):**

**[29]** — `Privacy_Policy.pdf`, page 2

> 7. How
> We Share Your Personal Data Third-party sharing: ● Product and service delivery: Sharing data with third-party sellers. ● Service providers: Engaging third parties for functions like order fulfillment, payment processing, and marketing assistance. ● Business transfers: Customer information may be transferred in business transactions. Fraud detection: Sharing data for fraud protection and compliance with the law. We ensure that third parties use your data per this Privacy Notice and applicable laws and only for specified purposes.

**[32]** — `Privacy_Policy.pdf`, page 3

> 10. Data
> Security We have implemented security measures to prevent unauthorized access, use, alteration, or disclosure of your personal data. Access is limited to employees, agents, contractors, and third parties who need it for business purposes and are bound by confidentiality.

**[25]** — `Privacy_Policy.pdf`, page 1

> 3. The
> Data We Collect About You Personal data refers to information that can identify a specific individual, either directly or indirectly. We collect personal data to provide tailored products and services and to continuously improve them. We may collect, use, store, and transfer various types of personal data for marketing and optimization purposes. Kibuga also uses Google Digital Marketing for targeted offers. Data you provide: ● Contact details: Name, postal addresses, phone numbers, email addresses. ● Demographic information: Date of birth, age, gender. ● Online registration information: Passwords, authentication information. ● Payment information: Credit card information, billing address. ● Survey responses: Customer satisfaction surveys, market research. ● Competition entries and submissions. ● Marketing preferences. Automatically collected data or data from third parties: ● Device information: PC, tablet, mobile device, operating system, browser, IP address. ● Usage information: Searches, views, downloads, purchases, web pages visited. ● User-generated content: Blogs, social media postings. ● Social media data: Username or ID, profile photo, followers. We provide options for managing your personal data, including opting out of personalized experiences and targeted advertising. You can close your account or adjust preferences by contacting us at uganda.legal@Kibuga.com.

**Model's answer (verbatim):**

> Third-party sellers, service providers for functions like order fulfillment, payment processing, and marketing assistance, as well as business transfers in transactions, may see your personal data. Additionally, there is a possibility that fraud detection entities might access your data to ensure compliance with laws and protect against fraud.

**Human verdict:**

```
  [x] CORRECT      — answer is accurate and supported by the passages shown
  [ ] UNGROUNDED   — plausible but not supported by the passages the model saw
  [ ] WRONG        — contradicts the passages, or is factually incorrect
  [ ] LABEL ISSUE  — answer is fine, but the gold label is wrong/incomplete
  Notes: ______________________________________________
```

### Q34 — prose

**Question:** Does Kibuga use my data for advertising?

**Layer A verdict:** PASS  
**Layer A reason:** gold-overlap ratio 0.70 (23/33 distinctive toks)

**Gold chunks:** [25]  
**Retrieved chunks:** [25, 10, 46]  
**Gold chunk in context: YES**

**Gold chunk text:**

**[25]** — `Privacy_Policy.pdf`, page 1

> 3. The
> Data We Collect About You Personal data refers to information that can identify a specific individual, either directly or indirectly. We collect personal data to provide tailored products and services and to continuously improve them. We may collect, use, store, and transfer various types of personal data for marketing and optimization purposes. Kibuga also uses Google Digital Marketing for targeted offers. Data you provide: ● Contact details: Name, postal addresses, phone numbers, email addresses. ● Demographic information: Date of birth, age, gender. ● Online registration information: Passwords, authentication information. ● Payment information: Credit card information, billing address. ● Survey responses: Customer satisfaction surveys, market research. ● Competition entries and submissions. ● Marketing preferences. Automatically collected data or data from third parties: ● Device information: PC, tablet, mobile device, operating system, browser, IP address. ● Usage information: Searches, views, downloads, purchases, web pages visited. ● User-generated content: Blogs, social media postings. ● Social media data: Username or ID, profile photo, followers. We provide options for managing your personal data, including opting out of personalized experiences and targeted advertising. You can close your account or adjust preferences by contacting us at uganda.legal@Kibuga.com.

**Retrieved chunk text (what the model actually saw):**

**[25]** — `Privacy_Policy.pdf`, page 1

> 3. The
> Data We Collect About You Personal data refers to information that can identify a specific individual, either directly or indirectly. We collect personal data to provide tailored products and services and to continuously improve them. We may collect, use, store, and transfer various types of personal data for marketing and optimization purposes. Kibuga also uses Google Digital Marketing for targeted offers. Data you provide: ● Contact details: Name, postal addresses, phone numbers, email addresses. ● Demographic information: Date of birth, age, gender. ● Online registration information: Passwords, authentication information. ● Payment information: Credit card information, billing address. ● Survey responses: Customer satisfaction surveys, market research. ● Competition entries and submissions. ● Marketing preferences. Automatically collected data or data from third parties: ● Device information: PC, tablet, mobile device, operating system, browser, IP address. ● Usage information: Searches, views, downloads, purchases, web pages visited. ● User-generated content: Blogs, social media postings. ● Social media data: Username or ID, profile photo, followers. We provide options for managing your personal data, including opting out of personalized experiences and targeted advertising. You can close your account or adjust preferences by contacting us at uganda.legal@Kibuga.com.

**[10]** — `General_Terms_for_Sellers_and_Buyers.pdf`, page 5

> 2. Use of website and mobile applications
> Use data collected from our website for any direct marketing activity (including without limitation email marketing, SMS marketing, telemarketing and direct mailing); or ● Do anything that interferes with the normal use of our website. 3. Copyright and trademarks ● Subject to the express provisions of these general terms and conditions: we, together with our licensors, own and control all the copyright and other intellectual property rights in our website and the material on our website; and ● All the copyright and other intellectual property rights in our website and the material on our website are reserved. Kibuga’s logos and our other registered and unregistered trademarks are trademarks belonging to us; we give no permission for the use of these trademarks, and such use may constitute an infringement of our rights. The third party registered and unregistered trademarks or service marks on our website are the property of their respective owners and we do not endorse and are not affiliated with any of the holders of any such rights and as such we cannot grant any license to exercise such rights.

**[46]** — `Sellers_Terms_and_Conditions.pdf`, page 1

> Sellers Terms and Conditions
> If we reasonably determine that you have breached these seller terms and conditions, our general terms and conditions, or any Kibuga codes, policies or guidelines, we may: 1. send you one or more formal warnings. b. suspend, prohibit or block your access to our marketplace as provided in the general terms and conditions. c. apply penalties for breach as provided in our Seller Penalty Policy; and/or d. commence legal action against you, whether for breach of contract or otherwise. 2. We may vary the amount of the penalties for breach from time to time by updating the Seller Penalty Policy, but this will not affect any liability to pay penalties that accrue before the new amounts are posted. Confidentiality and data privacy All information and documents concerning the conduct of business pursuant to these general terms and conditions, including information relating to business methods, procedures, policies and sales information, is strictly confidential unless it is already in the public domain. You shall not use Kibuga’s confidential information for any purpose other than to perform your obligations under this Agreement and you shall not disclose Kibuga’s confidential information without our prior written consent. Sellers may not send advertising or promotional communications to buyers on the marketplace without the prior written consent of Kibuga and shall be directly responsible to marketplace users for any misuse of their personal data. If Kibuga is sued, fined, or otherwise incurs expenses because of the seller’s handling of personal data obtained through the marketplace, the seller shall indemnify Kibuga in respect of the same.

**Model's answer (verbatim):**

> Yes, Kibuga uses your data for advertising purposes as stated in the document which mentions they may collect and use various types of personal data including payment information, survey responses, marketing preferences, and automatically collected data from third parties for targeted offers through Google Digital Marketing.

**Human verdict:**

```
  [x] CORRECT      — answer is accurate and supported by the passages shown
  [ ] UNGROUNDED   — plausible but not supported by the passages the model saw
  [ ] WRONG        — contradicts the passages, or is factually incorrect
  [ ] LABEL ISSUE  — answer is fine, but the gold label is wrong/incomplete
  Notes: ______________________________________________
```

---

## Priority 4: exact_fact controls — should be unambiguous; if these fail, the problem is bigger

### Q01 — exact_fact

**Question:** What is Kibuga's returns window?

**Layer A verdict:** PASS  
**Layer A reason:** gold-overlap ratio 0.88 (7/8 distinctive toks)

**Gold chunks:** [36]  
**Retrieved chunks:** [36, 4, 38]  
**Gold chunk in context: YES**

**Gold chunk text:**

**[36]** — `Return_Policy.pdf`, page 1

> Return Policy
> Return Policy What are the conditions for returning an item? Two (2) days free returns policy, subject to Terms and conditions. Requirement for a valid procedure • Proof of purchase – the document handed over to you together with the product, on delivery. • Original packaging – the manufacturer packaging • Any free promotional items – gifts or accessories delivered with the purchased item • Valid return reason i.e. If Item is Faulty Please Note: We do not accept returns for the items below. For such purchases, please inspect the item carefully upon delivery or pick up and if necessary, reject it on the spot: • Innerwear, swimsuits, gym wear, sleep wear • Perfumes, jewelry, health & wellness products, adult toys • For missing items and damaged products especially, broken screens please check with our riders during delivery and reject on the spot. How do I return an item/ What happens once I have returned an item? For any return request please contact our Customer Service Call Center at 0742511381/0742511394. and fill the form. What happens once I have returned an item? • We will perform a careful quality check. • If the claim is valid, we will refund you according to your requested refund method. • The process may take up to 2 days from when your return request was submitted. • If the claim is invalid the item will be sent back to you. • We keep track of all return requests and use the data to improve our product quality and service, as well as for customer profiling. Customers with unjustified/invalid returns may be denied the right to return items or even shop on Kibuga in the future. How much time do I have to return a product to Kibuga? • All items sold on Kibuga if faulty, can be returned within a period of 2 days from delivery date.

**Retrieved chunk text (what the model actually saw):**

**[36]** — `Return_Policy.pdf`, page 1

> Return Policy
> Return Policy What are the conditions for returning an item? Two (2) days free returns policy, subject to Terms and conditions. Requirement for a valid procedure • Proof of purchase – the document handed over to you together with the product, on delivery. • Original packaging – the manufacturer packaging • Any free promotional items – gifts or accessories delivered with the purchased item • Valid return reason i.e. If Item is Faulty Please Note: We do not accept returns for the items below. For such purchases, please inspect the item carefully upon delivery or pick up and if necessary, reject it on the spot: • Innerwear, swimsuits, gym wear, sleep wear • Perfumes, jewelry, health & wellness products, adult toys • For missing items and damaged products especially, broken screens please check with our riders during delivery and reject on the spot. How do I return an item/ What happens once I have returned an item? For any return request please contact our Customer Service Call Center at 0742511381/0742511394. and fill the form. What happens once I have returned an item? • We will perform a careful quality check. • If the claim is valid, we will refund you according to your requested refund method. • The process may take up to 2 days from when your return request was submitted. • If the claim is invalid the item will be sent back to you. • We keep track of all return requests and use the data to improve our product quality and service, as well as for customer profiling. Customers with unjustified/invalid returns may be denied the right to return items or even shop on Kibuga in the future. How much time do I have to return a product to Kibuga? • All items sold on Kibuga if faulty, can be returned within a period of 2 days from delivery date.

**[4]** — `General_Terms_for_Sellers_and_Buyers.pdf`, page 2

> 4. Returns and refunds
> Returns of products by buyers and acceptance of returned products by sellers shall be managed by us in accordance with the returns page on the marketplace, as may be amended from time to time. Acceptance of returns shall be in our discretion, subject to compliance with applicable laws of the territory. Refunds in respect of returned products shall be managed in accordance with the refunds page on the marketplace, as may be amended from time to time. Our rules on refunds shall be exercised in our discretion, subject to applicable laws of the territory. We may offer refunds, in our discretion: Payments In respect of the product price. Shipping fees (as stated on the refunds page); and ● By way of store credits, wallet refunds, vouchers, mobile money transfer, bank transfers or such other method as we may determine from time to time. Returned products shall be accepted and refunds issued by Kibuga, for and on behalf of the seller.

**[38]** — `Return_Policy.pdf`, page 1

> Return Policy
> What now? • On delivery, kindly ensure to verify that the item delivered is in good condition and reject if it does not match your order. Can I return my items after the timeline to return has expired? • Sorry, returns are not possible after the 2-day return period. Do I have to return the gift when I return a product? • Yes, any gift must also be returned. Do I have to pay for shipping charges when I return a product? • There are no charges for shipping a product back to Kibuga.

**Model's answer (verbatim):**

> Kibuga's returns window is 2 days from the delivery date.

**Human verdict:**

```
  [x] CORRECT      — answer is accurate and supported by the passages shown
  [ ] UNGROUNDED   — plausible but not supported by the passages the model saw
  [ ] WRONG        — contradicts the passages, or is factually incorrect
  [ ] LABEL ISSUE  — answer is fine, but the gold label is wrong/incomplete
  Notes: ______________________________________________
```

### Q05 — exact_fact

**Question:** What is the customer support email address?

**Layer A verdict:** PASS  
**Layer A reason:** gold-overlap ratio 0.50 (3/6 distinctive toks)

**Gold chunks:** [39]  
**Retrieved chunks:** [39, 25, 34]  
**Gold chunk in context: YES**

**Gold chunk text:**

**[39]** — `Seek_Support.pdf`, page 1

> Seek Support
> Seek Support Headquarters: Muganzirwazza Commercial Plaza, Lubiri Road, Plot 1446 Bulange - Mengo, P.O BOX 163315, Kampala, Uganda Customer Support: Email: support@kibuga.com Phone: +256200959991 Phone: +256740063330 Social Media: Follow us on Facebook, Twitter, and Instagram @KibugaOnlineShop Business Hours: Monday to Friday: 08:00 AM - 05:00 PM Saturday: 08:00 AM - 02:00 PM Sunday: Closed For any inquiries, feedback, or support, please contact us through the provided details. Our team is dedicated to assisting you with any questions or concerns you may have.

**Retrieved chunk text (what the model actually saw):**

**[39]** — `Seek_Support.pdf`, page 1

> Seek Support
> Seek Support Headquarters: Muganzirwazza Commercial Plaza, Lubiri Road, Plot 1446 Bulange - Mengo, P.O BOX 163315, Kampala, Uganda Customer Support: Email: support@kibuga.com Phone: +256200959991 Phone: +256740063330 Social Media: Follow us on Facebook, Twitter, and Instagram @KibugaOnlineShop Business Hours: Monday to Friday: 08:00 AM - 05:00 PM Saturday: 08:00 AM - 02:00 PM Sunday: Closed For any inquiries, feedback, or support, please contact us through the provided details. Our team is dedicated to assisting you with any questions or concerns you may have.

**[25]** — `Privacy_Policy.pdf`, page 1

> 3. The
> Data We Collect About You Personal data refers to information that can identify a specific individual, either directly or indirectly. We collect personal data to provide tailored products and services and to continuously improve them. We may collect, use, store, and transfer various types of personal data for marketing and optimization purposes. Kibuga also uses Google Digital Marketing for targeted offers. Data you provide: ● Contact details: Name, postal addresses, phone numbers, email addresses. ● Demographic information: Date of birth, age, gender. ● Online registration information: Passwords, authentication information. ● Payment information: Credit card information, billing address. ● Survey responses: Customer satisfaction surveys, market research. ● Competition entries and submissions. ● Marketing preferences. Automatically collected data or data from third parties: ● Device information: PC, tablet, mobile device, operating system, browser, IP address. ● Usage information: Searches, views, downloads, purchases, web pages visited. ● User-generated content: Blogs, social media postings. ● Social media data: Username or ID, profile photo, followers. We provide options for managing your personal data, including opting out of personalized experiences and targeted advertising. You can close your account or adjust preferences by contacting us at uganda.legal@Kibuga.com.

**[34]** — `Privacy_Policy.pdf`, page 3

> 12. Data
> Controllers & Contact For questions, concerns, or to exercise your rights, contact our Data Privacy Officer at support@kibuga.com. We will respond to complaints within prescribed timelines.

**Model's answer (verbatim):**

> The customer support email address for Kibuga is support@kibuga.com.

**Human verdict:**

```
  [x] CORRECT      — answer is accurate and supported by the passages shown
  [ ] UNGROUNDED   — plausible but not supported by the passages the model saw
  [ ] WRONG        — contradicts the passages, or is factually incorrect
  [ ] LABEL ISSUE  — answer is fine, but the gold label is wrong/incomplete
  Notes: ______________________________________________
```

---

## Priority 5: The 3 WEAK cases — borderline, excluded from the 25, cheap to include

### Q07 — paraphrase

**Question:** How long do I have to send something back?

**Layer A verdict:** WEAK  
**Layer A reason:** gold-overlap ratio 0.44 (16/36 distinctive toks)

**Gold chunks:** [36]  
**Retrieved chunks:** [37, 38, 36]  
**Gold chunk in context: YES**

**Gold chunk text:**

**[36]** — `Return_Policy.pdf`, page 1

> Return Policy
> Return Policy What are the conditions for returning an item? Two (2) days free returns policy, subject to Terms and conditions. Requirement for a valid procedure • Proof of purchase – the document handed over to you together with the product, on delivery. • Original packaging – the manufacturer packaging • Any free promotional items – gifts or accessories delivered with the purchased item • Valid return reason i.e. If Item is Faulty Please Note: We do not accept returns for the items below. For such purchases, please inspect the item carefully upon delivery or pick up and if necessary, reject it on the spot: • Innerwear, swimsuits, gym wear, sleep wear • Perfumes, jewelry, health & wellness products, adult toys • For missing items and damaged products especially, broken screens please check with our riders during delivery and reject on the spot. How do I return an item/ What happens once I have returned an item? For any return request please contact our Customer Service Call Center at 0742511381/0742511394. and fill the form. What happens once I have returned an item? • We will perform a careful quality check. • If the claim is valid, we will refund you according to your requested refund method. • The process may take up to 2 days from when your return request was submitted. • If the claim is invalid the item will be sent back to you. • We keep track of all return requests and use the data to improve our product quality and service, as well as for customer profiling. Customers with unjustified/invalid returns may be denied the right to return items or even shop on Kibuga in the future. How much time do I have to return a product to Kibuga? • All items sold on Kibuga if faulty, can be returned within a period of 2 days from delivery date.

**Retrieved chunk text (what the model actually saw):**

**[37]** — `Return_Policy.pdf`, page 1

> Return Policy
> NOTE: You have 2 days to notify us of your return by calling Customer Service, from the day you received your purchase. For defective items, we also advise you to contact the manufacturer if the product has a warranty. How do I send my product to Kibuga? • We will make 3 attempts within 2 working days to pick-up the returning item after you submit the return request .Note that You can also drop your return item at our offices/Warehouse. However, after 3 pick-up attempts, we will cancel the return procedure and you will not be able to return your product to us anymore. Please ensure that the package of the returning item is in good condition for the return; any package found to be damaged will be rejected by the rider during collection or sent back after quality check is done. How do I track my return status? • We will keep you updated by email and SMS about the status of your return. For any inquiries contact our Customer Service Call Center at 0742511381 / 0742511394.. Is my product under warranty? • We advise you to check our warranty page to get more information about our warranty policy. If my returned product is not validated for refund, how do I get informed? • If your return is invalid, then we will call you to explain the issue and send the item(s) back to you. We will arrange the delivery of the item."Note that we will make two (2) attempts to return the product to you at no cost. However, after two (2) failed attempts, we will cancel the return process and store the product at our warehouse for up to seven (7) days awaiting your collection. If you do not collect the product within these seven (7) days, it will be deemed as forfeited and we will dispose off in accordance with the Ugandan law I received something I didn't order.

**[38]** — `Return_Policy.pdf`, page 1

> Return Policy
> What now? • On delivery, kindly ensure to verify that the item delivered is in good condition and reject if it does not match your order. Can I return my items after the timeline to return has expired? • Sorry, returns are not possible after the 2-day return period. Do I have to return the gift when I return a product? • Yes, any gift must also be returned. Do I have to pay for shipping charges when I return a product? • There are no charges for shipping a product back to Kibuga.

**[36]** — `Return_Policy.pdf`, page 1

> Return Policy
> Return Policy What are the conditions for returning an item? Two (2) days free returns policy, subject to Terms and conditions. Requirement for a valid procedure • Proof of purchase – the document handed over to you together with the product, on delivery. • Original packaging – the manufacturer packaging • Any free promotional items – gifts or accessories delivered with the purchased item • Valid return reason i.e. If Item is Faulty Please Note: We do not accept returns for the items below. For such purchases, please inspect the item carefully upon delivery or pick up and if necessary, reject it on the spot: • Innerwear, swimsuits, gym wear, sleep wear • Perfumes, jewelry, health & wellness products, adult toys • For missing items and damaged products especially, broken screens please check with our riders during delivery and reject on the spot. How do I return an item/ What happens once I have returned an item? For any return request please contact our Customer Service Call Center at 0742511381/0742511394. and fill the form. What happens once I have returned an item? • We will perform a careful quality check. • If the claim is valid, we will refund you according to your requested refund method. • The process may take up to 2 days from when your return request was submitted. • If the claim is invalid the item will be sent back to you. • We keep track of all return requests and use the data to improve our product quality and service, as well as for customer profiling. Customers with unjustified/invalid returns may be denied the right to return items or even shop on Kibuga in the future. How much time do I have to return a product to Kibuga? • All items sold on Kibuga if faulty, can be returned within a period of 2 days from delivery date.

**Model's answer (verbatim):**

> You have 2 days to notify us of your return by calling Customer Service, from the day you received your purchase. If the product has a warranty, you should also contact the manufacturer. After that, we will make 3 attempts within 2 working days to pick-up the returning item. If after these attempts it is not picked up, the return procedure will be canceled and the product cannot be returned anymore.

**Human verdict:**

```
  [x] CORRECT      — answer is accurate and supported by the passages shown
  [ ] UNGROUNDED   — plausible but not supported by the passages the model saw
  [ ] WRONG        — contradicts the passages, or is factually incorrect
  [ ] LABEL ISSUE  — answer is fine, but the gold label is wrong/incomplete
  Notes: ______________________________________________
```

### Q14 — near_miss

**Question:** What happens if my return claim is rejected?

**Layer A verdict:** WEAK  
**Layer A reason:** gold-overlap ratio 0.39 (17/44 distinctive toks)

**Gold chunks:** [36]  
**Retrieved chunks:** [36, 37, 38]  
**Gold chunk in context: YES**

**Gold chunk text:**

**[36]** — `Return_Policy.pdf`, page 1

> Return Policy
> Return Policy What are the conditions for returning an item? Two (2) days free returns policy, subject to Terms and conditions. Requirement for a valid procedure • Proof of purchase – the document handed over to you together with the product, on delivery. • Original packaging – the manufacturer packaging • Any free promotional items – gifts or accessories delivered with the purchased item • Valid return reason i.e. If Item is Faulty Please Note: We do not accept returns for the items below. For such purchases, please inspect the item carefully upon delivery or pick up and if necessary, reject it on the spot: • Innerwear, swimsuits, gym wear, sleep wear • Perfumes, jewelry, health & wellness products, adult toys • For missing items and damaged products especially, broken screens please check with our riders during delivery and reject on the spot. How do I return an item/ What happens once I have returned an item? For any return request please contact our Customer Service Call Center at 0742511381/0742511394. and fill the form. What happens once I have returned an item? • We will perform a careful quality check. • If the claim is valid, we will refund you according to your requested refund method. • The process may take up to 2 days from when your return request was submitted. • If the claim is invalid the item will be sent back to you. • We keep track of all return requests and use the data to improve our product quality and service, as well as for customer profiling. Customers with unjustified/invalid returns may be denied the right to return items or even shop on Kibuga in the future. How much time do I have to return a product to Kibuga? • All items sold on Kibuga if faulty, can be returned within a period of 2 days from delivery date.

**Retrieved chunk text (what the model actually saw):**

**[36]** — `Return_Policy.pdf`, page 1

> Return Policy
> Return Policy What are the conditions for returning an item? Two (2) days free returns policy, subject to Terms and conditions. Requirement for a valid procedure • Proof of purchase – the document handed over to you together with the product, on delivery. • Original packaging – the manufacturer packaging • Any free promotional items – gifts or accessories delivered with the purchased item • Valid return reason i.e. If Item is Faulty Please Note: We do not accept returns for the items below. For such purchases, please inspect the item carefully upon delivery or pick up and if necessary, reject it on the spot: • Innerwear, swimsuits, gym wear, sleep wear • Perfumes, jewelry, health & wellness products, adult toys • For missing items and damaged products especially, broken screens please check with our riders during delivery and reject on the spot. How do I return an item/ What happens once I have returned an item? For any return request please contact our Customer Service Call Center at 0742511381/0742511394. and fill the form. What happens once I have returned an item? • We will perform a careful quality check. • If the claim is valid, we will refund you according to your requested refund method. • The process may take up to 2 days from when your return request was submitted. • If the claim is invalid the item will be sent back to you. • We keep track of all return requests and use the data to improve our product quality and service, as well as for customer profiling. Customers with unjustified/invalid returns may be denied the right to return items or even shop on Kibuga in the future. How much time do I have to return a product to Kibuga? • All items sold on Kibuga if faulty, can be returned within a period of 2 days from delivery date.

**[37]** — `Return_Policy.pdf`, page 1

> Return Policy
> NOTE: You have 2 days to notify us of your return by calling Customer Service, from the day you received your purchase. For defective items, we also advise you to contact the manufacturer if the product has a warranty. How do I send my product to Kibuga? • We will make 3 attempts within 2 working days to pick-up the returning item after you submit the return request .Note that You can also drop your return item at our offices/Warehouse. However, after 3 pick-up attempts, we will cancel the return procedure and you will not be able to return your product to us anymore. Please ensure that the package of the returning item is in good condition for the return; any package found to be damaged will be rejected by the rider during collection or sent back after quality check is done. How do I track my return status? • We will keep you updated by email and SMS about the status of your return. For any inquiries contact our Customer Service Call Center at 0742511381 / 0742511394.. Is my product under warranty? • We advise you to check our warranty page to get more information about our warranty policy. If my returned product is not validated for refund, how do I get informed? • If your return is invalid, then we will call you to explain the issue and send the item(s) back to you. We will arrange the delivery of the item."Note that we will make two (2) attempts to return the product to you at no cost. However, after two (2) failed attempts, we will cancel the return process and store the product at our warehouse for up to seven (7) days awaiting your collection. If you do not collect the product within these seven (7) days, it will be deemed as forfeited and we will dispose off in accordance with the Ugandan law I received something I didn't order.

**[38]** — `Return_Policy.pdf`, page 1

> Return Policy
> What now? • On delivery, kindly ensure to verify that the item delivered is in good condition and reject if it does not match your order. Can I return my items after the timeline to return has expired? • Sorry, returns are not possible after the 2-day return period. Do I have to return the gift when I return a product? • Yes, any gift must also be returned. Do I have to pay for shipping charges when I return a product? • There are no charges for shipping a product back to Kibuga.

**Model's answer (verbatim):**

> If your return claim is invalid, we will call you to explain the issue and send the item(s) back to you. We will arrange the delivery of the item. Note that we will make two (2) attempts to return the product to you at no cost. However, after two (2) failed attempts, we will cancel the return process and store the product at our warehouse for up to seven (7) days awaiting your collection. If you do not collect the product within these seven (7) days, it will be deemed as forfeited and we will dispose off in accordance with the Ugandan law.

**Human verdict:**

```
  [x] CORRECT      — answer is accurate and supported by the passages shown
  [ ] UNGROUNDED   — plausible but not supported by the passages the model saw
  [ ] WRONG        — contradicts the passages, or is factually incorrect
  [ ] LABEL ISSUE  — answer is fine, but the gold label is wrong/incomplete
  Notes: ______________________________________________
```

### Q21 — multi_chunk

**Question:** What is the full returns procedure from request to refund?

**Layer A verdict:** WEAK  
**Layer A reason:** gold-overlap ratio 0.40 (56/140 distinctive toks)

**Gold chunks:** [37]  
**Retrieved chunks:** [36, 4, 37]  
**Gold chunk in context: YES**

**Gold chunk text:**

**[37]** — `Return_Policy.pdf`, page 1

> Return Policy
> NOTE: You have 2 days to notify us of your return by calling Customer Service, from the day you received your purchase. For defective items, we also advise you to contact the manufacturer if the product has a warranty. How do I send my product to Kibuga? • We will make 3 attempts within 2 working days to pick-up the returning item after you submit the return request .Note that You can also drop your return item at our offices/Warehouse. However, after 3 pick-up attempts, we will cancel the return procedure and you will not be able to return your product to us anymore. Please ensure that the package of the returning item is in good condition for the return; any package found to be damaged will be rejected by the rider during collection or sent back after quality check is done. How do I track my return status? • We will keep you updated by email and SMS about the status of your return. For any inquiries contact our Customer Service Call Center at 0742511381 / 0742511394.. Is my product under warranty? • We advise you to check our warranty page to get more information about our warranty policy. If my returned product is not validated for refund, how do I get informed? • If your return is invalid, then we will call you to explain the issue and send the item(s) back to you. We will arrange the delivery of the item."Note that we will make two (2) attempts to return the product to you at no cost. However, after two (2) failed attempts, we will cancel the return process and store the product at our warehouse for up to seven (7) days awaiting your collection. If you do not collect the product within these seven (7) days, it will be deemed as forfeited and we will dispose off in accordance with the Ugandan law I received something I didn't order.

**Retrieved chunk text (what the model actually saw):**

**[36]** — `Return_Policy.pdf`, page 1

> Return Policy
> Return Policy What are the conditions for returning an item? Two (2) days free returns policy, subject to Terms and conditions. Requirement for a valid procedure • Proof of purchase – the document handed over to you together with the product, on delivery. • Original packaging – the manufacturer packaging • Any free promotional items – gifts or accessories delivered with the purchased item • Valid return reason i.e. If Item is Faulty Please Note: We do not accept returns for the items below. For such purchases, please inspect the item carefully upon delivery or pick up and if necessary, reject it on the spot: • Innerwear, swimsuits, gym wear, sleep wear • Perfumes, jewelry, health & wellness products, adult toys • For missing items and damaged products especially, broken screens please check with our riders during delivery and reject on the spot. How do I return an item/ What happens once I have returned an item? For any return request please contact our Customer Service Call Center at 0742511381/0742511394. and fill the form. What happens once I have returned an item? • We will perform a careful quality check. • If the claim is valid, we will refund you according to your requested refund method. • The process may take up to 2 days from when your return request was submitted. • If the claim is invalid the item will be sent back to you. • We keep track of all return requests and use the data to improve our product quality and service, as well as for customer profiling. Customers with unjustified/invalid returns may be denied the right to return items or even shop on Kibuga in the future. How much time do I have to return a product to Kibuga? • All items sold on Kibuga if faulty, can be returned within a period of 2 days from delivery date.

**[4]** — `General_Terms_for_Sellers_and_Buyers.pdf`, page 2

> 4. Returns and refunds
> Returns of products by buyers and acceptance of returned products by sellers shall be managed by us in accordance with the returns page on the marketplace, as may be amended from time to time. Acceptance of returns shall be in our discretion, subject to compliance with applicable laws of the territory. Refunds in respect of returned products shall be managed in accordance with the refunds page on the marketplace, as may be amended from time to time. Our rules on refunds shall be exercised in our discretion, subject to applicable laws of the territory. We may offer refunds, in our discretion: Payments In respect of the product price. Shipping fees (as stated on the refunds page); and ● By way of store credits, wallet refunds, vouchers, mobile money transfer, bank transfers or such other method as we may determine from time to time. Returned products shall be accepted and refunds issued by Kibuga, for and on behalf of the seller.

**[37]** — `Return_Policy.pdf`, page 1

> Return Policy
> NOTE: You have 2 days to notify us of your return by calling Customer Service, from the day you received your purchase. For defective items, we also advise you to contact the manufacturer if the product has a warranty. How do I send my product to Kibuga? • We will make 3 attempts within 2 working days to pick-up the returning item after you submit the return request .Note that You can also drop your return item at our offices/Warehouse. However, after 3 pick-up attempts, we will cancel the return procedure and you will not be able to return your product to us anymore. Please ensure that the package of the returning item is in good condition for the return; any package found to be damaged will be rejected by the rider during collection or sent back after quality check is done. How do I track my return status? • We will keep you updated by email and SMS about the status of your return. For any inquiries contact our Customer Service Call Center at 0742511381 / 0742511394.. Is my product under warranty? • We advise you to check our warranty page to get more information about our warranty policy. If my returned product is not validated for refund, how do I get informed? • If your return is invalid, then we will call you to explain the issue and send the item(s) back to you. We will arrange the delivery of the item."Note that we will make two (2) attempts to return the product to you at no cost. However, after two (2) failed attempts, we will cancel the return process and store the product at our warehouse for up to seven (7) days awaiting your collection. If you do not collect the product within these seven (7) days, it will be deemed as forfeited and we will dispose off in accordance with the Ugandan law I received something I didn't order.

**Model's answer (verbatim):**

> The full returns procedure from request to refund involves several steps:
>
> 1. **Notification**: Notify Kibuga within 2 days of receiving the purchase by calling Customer Service at 0742511381/0742511394.
>
> 2. **Return Request Submission**: Submit a return request through the notification process, which includes providing proof of purchase (document handed over to you together with the product on delivery), original packaging, and any free promotional items delivered with the purchased item.
>
> 3. **Quality Check**: Kibuga will perform a quality check on the returned item(s).
>
> 4. **Validation of Claim**: If the claim is valid, Kibuga will issue a refund according to the requested method (store credits, wallet refunds, vouchers, mobile money transfer, bank transfers, or other methods as determined by Kibuga from time to time). The process may take up to 2 days.
>
> 5. **Invalid Claims**: If the claim is invalid, the item(s) will be sent back to you. Kibuga keeps track of all return requests for improvement and customer profiling purposes.
>
> 6. **Warranty Check**: For defective items, advise contacting the manufacturer if the product has a warranty.
>
> 7. **Shipping**: Returned products are accepted by Kibuga on behalf of the seller. Shipping fees (as stated on the refunds page) will be managed in accordance with the marketplace's refund policies.
>
> 8. **Tracking Status**: Customers can track their return status through updates via email and SMS, or contact Customer Service Call Center at 0742511381/0742511394 for inquiries.
>
> 9. **Warranty Information**: Check the warranty page for more information about Kibuga's warranty policy.
>
> 10. **Invalid Returns Handling**: If a return is invalid, Kibuga will call to explain and send the item back at no cost. After two attempts, if not collected within seven days, the product will be disposed of in accordance with Ugandan law.

**Human verdict:**

```
  [x] CORRECT      — answer is accurate and supported by the passages shown
  [ ] UNGROUNDED   — plausible but not supported by the passages the model saw
  [ ] WRONG        — contradicts the passages, or is factually incorrect
  [ ] LABEL ISSUE  — answer is fine, but the gold label is wrong/incomplete
  Notes: ______________________________________________
```
