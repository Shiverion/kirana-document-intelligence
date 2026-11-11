# Document QA evaluation

Cases: 20 total, 16 answerable, 4 unanswerable. Retrieval cutoff: k=5.

PDF SHA256: `109f0c113b5d8184ff720b87d69d3d9c7c236cf3be4aff5cd02b50addea43605`.
Gold SHA256: `f3f0b5b59b3256bd61812512d89765d3ad954b4577d9edc3df96d3f9b11d6c09`.
Strategy: `structured`; visual OCR requested: `True`; page coverage: 13/13 pages with evidence; statuses: `{'text_plus_ocr_visuals_unverified': 7, 'text_extracted': 6}`.

| Metric | Score |
|---|---:|
| Evidence-group Recall@k | 1.000 |
| Evidence-group Recall@k (micro pooled) | 1.000 |
| All Evidence@k | 1.000 |
| nDCG@k | 0.847 |
| Atomic answer fact recall (lexical proxy) | 0.542 |
| Citation page support precision (page-hit proxy) | 0.818 |
| Citation evidence completeness | 0.417 |
| Strict answer pass rate (answerable cases) | 0.250 (4/16) |
| Grounded strict pass rate (all cases) | 0.400 (8/20) |
| Abstention recall | 1.000 |
| False abstention rate | 0.500 |
| Coverage | 0.400 |
| Selective error rate | 0.500 |
| Latency retrieve (mean / median / p95 ms) | 8.3 / 7.7 / 9.6 |
| Latency ask_including_internal_retrieval (mean / median / p95 ms) | 19792.7 / 20055.0 / 39513.0 |
| Latency case_total (mean / median / p95 ms) | 19801.0 / 20068.5 / 39520.2 |

Definitions: Evidence Recall@k is the macro average, by answerable case, of required evidence groups covered; a group is covered if any accepted gold page is retrieved. The micro pooled rate is also shown. All Evidence@k is the fraction of answerable cases with all groups covered. nDCG@k uses binary relevance over the union of distinct gold support pages. Atomic answer recall matches any listed alias as a case-insensitive token-bounded phrase; this is a lexical proxy, not semantic judging. Strict answer pass is answerable cases answered with every required alias present, over answerable cases only. Grounded strict pass adds citation page completeness for answerable cases and correct abstention for unanswerable cases, over all cases. Citation precision and completeness use cited page IDs against gold support pages; quote text is not judged for entailment. Coverage is the share of all cases answered; selective error is the error share among answered cases.

## Per-case results

| ID | Type | Status | Retrieval evidence | Answer facts | Citation evidence | Answer strict | Grounded strict | Retrieved pages | Mode | Diagnosis |
|---|---|---|---:|---:|---:|---|---|---|---|---|
| K01 | answerable | abstained | 2/2 | 0/2 | 0/2 | FAIL | FAIL | [4, 12, 10, 11, 1] | grounding_guard | answer_generation_miss |
| K02 | answerable | abstained | 2/2 | 0/2 | 0/2 | FAIL | FAIL | [6, 12, 2, 5, 1] | grounding_guard | answer_generation_miss |
| K03 | answerable | answered | 1/1 | 1/1 | 1/1 | PASS | PASS | [6, 1, 10, 12, 2] | ollama | pass |
| K04 | answerable | abstained | 1/1 | 1/1 | 0/1 | FAIL | FAIL | [4, 2, 9, 10, 8] | ollama | answer_generation_miss |
| K05 | answerable | abstained | 1/1 | 0/1 | 0/1 | FAIL | FAIL | [4, 11, 1, 12, 2] | ollama | answer_generation_miss |
| K06 | answerable | abstained | 1/1 | 1/1 | 0/1 | FAIL | FAIL | [8, 7, 2, 11, 10] | ollama | answer_generation_miss |
| K07 | answerable | abstained | 3/3 | 3/3 | 0/3 | FAIL | FAIL | [7, 8, 1, 4, 12] | ollama | answer_generation_miss |
| K08 | answerable | answered | 1/1 | 0/1 | 1/1 | FAIL | FAIL | [9, 11, 12, 2, 1] | ollama | answer_generation_miss |
| K09 | answerable | answered | 3/3 | 3/3 | 3/3 | PASS | PASS | [12, 11, 2, 9, 3] | ollama | pass |
| K10 | answerable | abstained | 1/1 | 1/1 | 0/1 | FAIL | FAIL | [9, 1, 12, 2, 3] | ollama | answer_generation_miss |
| K11 | answerable | answered | 1/1 | 1/1 | 1/1 | PASS | PASS | [12] | ollama | pass |
| K12 | answerable | answered | 2/2 | 0/2 | 1/2 | FAIL | FAIL | [9, 11, 10, 12, 3] | ollama | answer_generation_miss |
| K13 | answerable | abstained | 2/2 | 1/2 | 0/2 | FAIL | FAIL | [12, 3, 2, 9, 4] | ollama | answer_generation_miss |
| K14 | answerable | answered | 1/1 | 0/1 | 1/1 | FAIL | FAIL | [4, 2, 11, 3, 5] | ollama | answer_generation_miss |
| K15 | answerable | answered | 1/1 | 0/1 | 1/1 | FAIL | FAIL | [2, 13, 7, 8, 11] | ollama | answer_generation_miss |
| K16 | answerable | answered | 1/1 | 1/1 | 1/1 | PASS | PASS | [11, 4, 1, 2, 7] | ollama | pass |
| K17 | unanswerable | abstained | 0/0 | 0/0 | 0/0 | — | PASS | [2, 12, 4, 1, 10] | ollama |  |
| K18 | unanswerable | abstained | 0/0 | 0/0 | 0/0 | — | PASS | [7, 8, 13, 12, 4] | ollama |  |
| K19 | unanswerable | abstained | 0/0 | 0/0 | 0/0 | — | PASS | [11, 4, 12, 1, 2] | ollama |  |
| K20 | unanswerable | abstained | 0/0 | 0/0 | 0/0 | — | PASS | [11, 2, 1, 5, 3] | ollama |  |

## Strict-pass failures

- **K01** — What was Kirana's total revenue for 2025, and in what currency is it reported? (status: abstained)
- **K02** — What disruption caused Kirana's on-time delivery to dip in Q4 2025, and how did it affect the main southern highway? (status: abstained)
- **K04** — What was EBITDA in 2024 according to the financial summary? (status: abstained)
- **K05** — How much capital expenditure did Kirana report for 2025? (status: abstained)
- **K06** — What was the 2025 utilisation rate at the Cibitung cold-chain facility in Bekasi? (status: abstained)
- **K07** — What was Da Nang's 2025 warehouse utilisation, and what is the company's rule for putting a site on the consolidation watch list? (status: abstained)
- **K08** — How many electric light trucks were in Kirana's Indonesian fleet at the end of 2025? (status: answered)
- **K10** — What were Kirana's Scope 2 greenhouse gas emissions in 2025? (status: abstained)
- **K12** — For Indonesia, what were Kirana's year-end 2025 employee headcount and number of electric light trucks? (status: answered)
- **K13** — What customer Net Promoter Score (NPS) did Kirana report for 2025 and for 2024? (status: abstained)
- **K14** — According to the quarterly revenue chart, what was Q4 2025 revenue in THB million? (status: answered)
- **K15** — Under the standard 2026 tariff, what is the cold-chain pallet storage rate per pallet per month? (status: answered)
