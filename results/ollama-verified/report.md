# Document QA evaluation

Cases: 20 total, 16 answerable, 4 unanswerable. Retrieval cutoff: k=5.

PDF SHA256: `109f0c113b5d8184ff720b87d69d3d9c7c236cf3be4aff5cd02b50addea43605`.
Gold SHA256: `f3f0b5b59b3256bd61812512d89765d3ad954b4577d9edc3df96d3f9b11d6c09`.
Strategy: `structured`; visual OCR requested: `True`; page coverage: 13/13 pages with evidence; statuses: `{'text_plus_ocr_visuals_unverified': 7, 'text_extracted': 6}`.

## Retrieval strategy comparison

| Strategy | Evidence-group Recall@k | All Evidence@k | nDCG@k |
|---|---:|---:|---:|
| baseline | 0.875 | 0.875 | 0.768 |
| structured | 1.000 | 1.000 | 0.826 |

| Metric | Score |
|---|---:|
| Evidence-group Recall@k | 1.000 |
| Evidence-group Recall@k (micro pooled) | 1.000 |
| All Evidence@k | 1.000 |
| nDCG@k | 0.826 |
| Atomic answer fact recall (lexical proxy) | 0.750 |
| Citation page support precision (page-hit proxy) | 0.833 |
| Citation evidence completeness | 0.833 |
| Strict answer pass rate (answerable cases) | 0.688 (11/16) |
| Grounded strict pass rate (all cases) | 0.750 (15/20) |
| Abstention recall | 1.000 |
| False abstention rate | 0.062 |
| Coverage | 0.750 |
| Selective error rate | 0.267 |
| Latency retrieve (mean / median / p95 ms) | 20.6 / 20.3 / 23.0 |
| Latency ask_including_internal_retrieval (mean / median / p95 ms) | 21354.7 / 21107.0 / 26222.3 |
| Latency case_total (mean / median / p95 ms) | 21375.3 / 21129.8 / 26244.5 |

Definitions: Evidence Recall@k is the macro average, by answerable case, of required evidence groups covered; a group is covered if any accepted gold page is retrieved. The micro pooled rate is also shown. All Evidence@k is the fraction of answerable cases with all groups covered. nDCG@k uses binary relevance over the union of distinct gold support pages. Atomic answer recall matches any listed alias as a case-insensitive token-bounded phrase; this is a lexical proxy, not semantic judging. Strict answer pass is answerable cases answered with every required alias present, over answerable cases only. Grounded strict pass adds citation page completeness for answerable cases and correct abstention for unanswerable cases, over all cases. Citation precision and completeness use cited page IDs against gold support pages; quote text is not judged for entailment. Coverage is the share of all cases answered; selective error is the error share among answered cases.

## Per-case results

| ID | Type / category | Status | Retrieval evidence | Answer facts | Citation evidence | Answer strict | Grounded strict | Retrieved pages | Mode | Diagnosis |
|---|---|---|---:|---:|---:|---|---|---|---|---|
| K01 | answerable / prose | answered | 2/2 | 1/2 | 2/2 | FAIL | FAIL | [5, 4, 13, 1, 12] | ollama | answer_generation_miss |
| K02 | answerable / prose | answered | 2/2 | 1/2 | 2/2 | FAIL | FAIL | [6, 5, 13, 12, 2] | ollama | answer_generation_miss |
| K03 | answerable / prose | answered | 1/1 | 1/1 | 1/1 | PASS | PASS | [9, 3, 6, 13, 1] | ollama | pass |
| K04 | answerable / table | answered | 1/1 | 1/1 | 1/1 | PASS | PASS | [4, 3, 9, 2, 10] | ollama | pass |
| K05 | answerable / table | answered | 1/1 | 1/1 | 1/1 | PASS | PASS | [4, 13, 11, 1, 2] | ollama | pass |
| K06 | answerable / table | answered | 1/1 | 1/1 | 1/1 | PASS | PASS | [8, 7, 13, 2, 10] | ollama | pass |
| K07 | answerable / cross_page | answered | 3/3 | 3/3 | 3/3 | PASS | PASS | [7, 8, 13, 1, 3] | ollama | pass |
| K08 | answerable / table | answered | 1/1 | 1/1 | 1/1 | PASS | PASS | [11, 9, 12, 13, 2] | ollama | pass |
| K09 | answerable / errata | answered | 3/3 | 3/3 | 3/3 | PASS | PASS | [12, 11, 2, 6, 5] | ollama | pass |
| K10 | answerable / table | answered | 1/1 | 1/1 | 1/1 | PASS | PASS | [9, 13, 1, 2, 12] | ollama | pass |
| K11 | answerable / glossary | answered | 1/1 | 1/1 | 1/1 | PASS | PASS | [13, 12, 4, 7, 8] | ollama | pass |
| K12 | answerable / cross_page | answered | 2/2 | 1/2 | 1/2 | FAIL | FAIL | [10, 9, 11, 13, 12] | ollama | answer_generation_miss |
| K13 | answerable / infographic | abstained | 2/2 | 0/2 | 0/2 | FAIL | FAIL | [12, 3, 13, 4, 2] | ollama | answer_generation_miss |
| K14 | answerable / chart | answered | 1/1 | 0/1 | 0/1 | FAIL | FAIL | [5, 4, 3, 11, 2] | ollama | answer_generation_miss |
| K15 | answerable / scanned_table | answered | 1/1 | 1/1 | 1/1 | PASS | PASS | [13, 2, 6, 7, 8] | ollama | pass |
| K16 | answerable / prose | answered | 1/1 | 1/1 | 1/1 | PASS | PASS | [4, 11, 13, 1, 2] | ollama | pass |
| K17 | unanswerable / unsupported | abstained | 0/0 | 0/0 | 0/0 | — | PASS | [2, 12, 13, 1, 10] | ollama | correct_abstention |
| K18 | unanswerable / missing_attachment | abstained | 0/0 | 0/0 | 0/0 | — | PASS | [13, 5, 7, 8, 12] | ollama | correct_abstention |
| K19 | unanswerable / unsupported_actual | abstained | 0/0 | 0/0 | 0/0 | — | PASS | [4, 11, 13, 12, 1] | ollama | correct_abstention |
| K20 | unanswerable / unsupported_detail | abstained | 0/0 | 0/0 | 0/0 | — | PASS | [11, 13, 9, 5, 2] | ollama | correct_abstention |

## Strict-pass failures

- **K01** — What was Kirana's total revenue for 2025, and in what currency is it reported? (status: answered)
- **K02** — What disruption caused Kirana's on-time delivery to dip in Q4 2025, and how did it affect the main southern highway? (status: answered)
- **K12** — For Indonesia, what were Kirana's year-end 2025 employee headcount and number of electric light trucks? (status: answered)
- **K13** — What customer Net Promoter Score (NPS) did Kirana report for 2025 and for 2024? (status: abstained)
- **K14** — According to the quarterly revenue chart, what was Q4 2025 revenue in THB million? (status: answered)

## Answer and citation detail

### K01 · ollama
Answer: Kirana's total revenue for 2025 was 8,420 Thai baht million.
- p.4: “THB million 2023 2024 2025”
- p.4: “Revenue 6,910 7,655 8,420”
Latency: retrieve 19.6 ms, ask 28454.6 ms.

### K02 · ollama
Answer: Severe flooding in southern Thailand caused the disruption, closing sections of the main southern highway and forcing line-haul traffic to be rerouted through slower inland roads. Service recovered by December once the highway reopened.
- p.2: “The fourth quarter tested our network. Severe flooding in southern Thailand closed sections of the main southern highway for several weeks and forced us to reroute line-haul traffic. Our teams kept customers informed and service recovered by December. I want to thank every colleague who worked through those weeks.”
- p.6: “Performance dipped in the fourth quarter. Flooding in southern Thailand closed sections of the main southern highway, and line-haul to Hat Yai was rerouted through slower inland roads. Service recovered in December once the highway reopened.”
Latency: retrieve 22.2 ms, ask 26222.3 ms.

### K03 · ollama
Answer: Kirana delivered 41.6 million parcels in 2025.
- p.6: “We delivered 41.6 million parcels in 2025.”
Latency: retrieve 19.1 ms, ask 19853.4 ms.

### K04 · ollama
Answer: EBITDA in 2024 was 1,186 THB million.
- p.4: “EBITDA 1,036 1,186 1,347”
Latency: retrieve 20.4 ms, ask 21679.5 ms.

### K05 · ollama
Answer: Kirana reported capital expenditure of THB 905 million for 2025.
- p.4: “Capital expenditure 610 742 905”
Latency: retrieve 20.3 ms, ask 22186.3 ms.

### K06 · ollama
Answer: The 2025 utilisation rate at the Cibitung cold-chain facility in Bekasi was 96%.
- p.8: “ID-CBT Cibitung, Bekasi Indonesia Cold chain 21,000 96% 2019”
- p.8: “ID-CBT Cibitung, Bekasi Indonesia Cold chain 21,000 96% 2019”
Latency: retrieve 17.8 ms, ask 22119.8 ms.

### K07 · ollama
Answer: Da Nang's 2025 warehouse utilisation was 62%. The company places a site on the consolidation watch list if it remains below 65% for two consecutive quarters.
- p.8: “VN-DNG Da Nang Vietnam Cross-dock 8,400 62% 2023”
- p.7: “We review utilisation monthly. Sites that remain below 65% for two consecutive quarters are placed on a consolidation watch list, while sites above 92% trigger an expansion study.”
Latency: retrieve 21.3 ms, ask 24091.5 ms.

### K08 · ollama
Answer: Kirana had 44 electric light trucks in its Indonesian fleet at the end of 2025.
- p.9: “Electric light truck 132 44 18 24 218”
- p.9: “Electric light truck 132 44 18 24 218”
Latency: retrieve 20.7 ms, ask 20957.5 ms.

### K09 · ollama
Answer: The original figure stated in the CEO letter was 96 electric trucks added in 2025. The corrected number, as reported in the errata and Fleet and sustainability section, is 82.
- p.12: “The Letter from the Chief Executive Officer states that 96 electric trucks were added in 2025. The correct figure is 82, as reported in the Fleet and sustainability section.”
Latency: retrieve 24.9 ms, ask 21204.3 ms.

### K10 · ollama
Answer: Kirana's Scope 2 greenhouse gas emissions in 2025 were 12,100 tCO2e.
- p.9: “Scope 2 (tCO2e) 14,300 13,900 12,100”
- p.9: “Scope 2 (tCO2e) 14,300 13,900 12,100”
Latency: retrieve 19.1 ms, ask 24164.1 ms.

### K11 · ollama
Answer: FTL stands for full truckload.
- p.12: “• FTL: full truckload.”
Latency: retrieve 22.4 ms, ask 15372.7 ms.

### K12 · ollama
Answer: Kirana's year-end 2025 employee headcount was 2,240 and the number of electric light trucks was 218.
- p.10: “Indonesia 1,960 2,240”
- p.12: “The electric fleet was 218 vehicles at 31 December 2025.”
Latency: retrieve 20.7 ms, ask 21009.7 ms.

### K13 · ollama
Answer: I could not find enough evidence in the retrieved excerpts to answer.
Citations: none.
Latency: retrieve 20.1 ms, ask 20269.1 ms.

### K14 · ollama
Answer: Q4 2025 revenue was THB 8,420 million.
- p.2: “Revenue rose 10.0% to THB 8,420 million”
- p.4: “Revenue 6,910 7,655 8,420”
Latency: retrieve 20.5 ms, ask 22302.2 ms.

### K15 · ollama
Answer: Under the standard 2026 tariff, the cold-chain pallet storage rate for temperatures between 2-8°C is 780.00 THB per pallet per month.
- p.13: “Cold-chainpalletstorage(2-8C) | per palletper month | 780.00”
- p.13: “Rates exclude 7% VAT. Effective 1 January 2026.”
Latency: retrieve 21.1 ms, ask 25799.1 ms.

### K16 · ollama
Answer: Kirana plans capital expenditure of approximately THB 1,050 million for 2026.
- p.11: “We expect revenue growth of 11% to 13% in 2026. Planned capital expenditure is approximately THB 1,050 million.”
Latency: retrieve 18.9 ms, ask 19553.0 ms.

### K17 · ollama
Answer: I could not find enough evidence in the retrieved excerpts to answer.
Citations: none.
Latency: retrieve 20.1 ms, ask 16208.9 ms.

### K18 · ollama
Answer: I could not find enough evidence in the retrieved excerpts to answer.
Citations: none.
Latency: retrieve 19.0 ms, ask 19482.6 ms.

### K19 · ollama
Answer: I could not find enough evidence in the retrieved excerpts to answer.
Citations: none.
Latency: retrieve 23.0 ms, ask 18793.8 ms.

### K20 · ollama
Answer: I could not find enough evidence in the retrieved excerpts to answer.
Citations: none.
Latency: retrieve 20.0 ms, ask 17370.7 ms.

