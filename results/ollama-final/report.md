# Document QA evaluation

Cases: 20 total, 16 answerable, 4 unanswerable. Retrieval cutoff: k=5.

PDF SHA256: `109f0c113b5d8184ff720b87d69d3d9c7c236cf3be4aff5cd02b50addea43605`.
Gold SHA256: `f3f0b5b59b3256bd61812512d89765d3ad954b4577d9edc3df96d3f9b11d6c09`.
Strategy: `structured`; visual OCR requested: `True`; page coverage: 13/13 pages with evidence; statuses: `{'text_plus_ocr_visuals_unverified': 7, 'text_extracted': 6}`.

## Retrieval strategy comparison

| Strategy | Evidence-group Recall@k | All Evidence@k | nDCG@k |
|---|---:|---:|---:|
| baseline | 0.875 | 0.875 | 0.768 |
| structured | 0.938 | 0.938 | 0.800 |

| Metric | Score |
|---|---:|
| Evidence-group Recall@k | 0.938 |
| Evidence-group Recall@k (micro pooled) | 0.917 |
| All Evidence@k | 0.938 |
| nDCG@k | 0.800 |
| Atomic answer fact recall (lexical proxy) | 0.667 |
| Citation page support precision (page-hit proxy) | 0.938 |
| Citation evidence completeness | 0.750 |
| Strict answer pass rate (answerable cases) | 0.688 (11/16) |
| Grounded strict pass rate (all cases) | 0.750 (15/20) |
| Abstention recall | 1.000 |
| False abstention rate | 0.188 |
| Coverage | 0.650 |
| Selective error rate | 0.154 |
| Latency retrieve (mean / median / p95 ms) | 15.2 / 14.3 / 16.4 |
| Latency ask_including_internal_retrieval (mean / median / p95 ms) | 19317.4 / 19768.2 / 25413.0 |
| Latency case_total (mean / median / p95 ms) | 19332.6 / 19783.1 / 25426.8 |

Definitions: Evidence Recall@k is the macro average, by answerable case, of required evidence groups covered; a group is covered if any accepted gold page is retrieved. The micro pooled rate is also shown. All Evidence@k is the fraction of answerable cases with all groups covered. nDCG@k uses binary relevance over the union of distinct gold support pages. Atomic answer recall matches any listed alias as a case-insensitive token-bounded phrase; this is a lexical proxy, not semantic judging. Strict answer pass is answerable cases answered with every required alias present, over answerable cases only. Grounded strict pass adds citation page completeness for answerable cases and correct abstention for unanswerable cases, over all cases. Citation precision and completeness use cited page IDs against gold support pages; quote text is not judged for entailment. Coverage is the share of all cases answered; selective error is the error share among answered cases.

## Per-case results

| ID | Type / category | Status | Retrieval evidence | Answer facts | Citation evidence | Answer strict | Grounded strict | Retrieved pages | Mode | Diagnosis |
|---|---|---|---:|---:|---:|---|---|---|---|---|
| K01 | answerable / prose | answered | 2/2 | 1/2 | 2/2 | FAIL | FAIL | [4, 12, 11, 9, 1] | ollama | answer_generation_miss |
| K02 | answerable / prose | answered | 2/2 | 2/2 | 2/2 | PASS | PASS | [6, 2, 5, 12, 1] | ollama | pass |
| K03 | answerable / prose | answered | 1/1 | 1/1 | 1/1 | PASS | PASS | [6, 1, 10, 12, 2] | ollama | pass |
| K04 | answerable / table | answered | 1/1 | 1/1 | 1/1 | PASS | PASS | [4, 2, 10, 9, 8] | ollama | pass |
| K05 | answerable / table | answered | 1/1 | 1/1 | 1/1 | PASS | PASS | [4, 11, 1, 2, 12] | ollama | pass |
| K06 | answerable / table | answered | 1/1 | 1/1 | 1/1 | PASS | PASS | [8, 7, 10, 4, 2] | ollama | pass |
| K07 | answerable / cross_page | abstained | 3/3 | 0/3 | 0/3 | FAIL | FAIL | [7, 8, 1, 4, 6] | ollama | answer_generation_miss |
| K08 | answerable / table | answered | 1/1 | 1/1 | 1/1 | PASS | PASS | [9, 11, 12, 2, 1] | ollama | pass |
| K09 | answerable / errata | answered | 3/3 | 3/3 | 3/3 | PASS | PASS | [12, 11, 2, 9, 3] | ollama | pass |
| K10 | answerable / table | answered | 1/1 | 1/1 | 1/1 | PASS | PASS | [9, 1, 2, 12, 7] | ollama | pass |
| K11 | answerable / glossary | answered | 1/1 | 1/1 | 1/1 | PASS | PASS | [12, 4, 7, 8, 9] | ollama | pass |
| K12 | answerable / cross_page | answered | 2/2 | 2/2 | 2/2 | PASS | PASS | [9, 10, 11, 12, 3] | ollama | pass |
| K13 | answerable / infographic | abstained | 0/2 | 0/2 | 0/2 | FAIL | FAIL | [12, 2, 4, 1, 11] | ollama | retrieval_rank_miss |
| K14 | answerable / chart | abstained | 1/1 | 0/1 | 0/1 | FAIL | FAIL | [4, 2, 11, 5, 6] | ollama | answer_generation_miss |
| K15 | answerable / scanned_table | answered | 1/1 | 0/1 | 1/1 | FAIL | FAIL | [2, 8, 7, 10, 13] | ollama | answer_generation_miss |
| K16 | answerable / prose | answered | 1/1 | 1/1 | 1/1 | PASS | PASS | [11, 4, 1, 2, 7] | ollama | pass |
| K17 | unanswerable / unsupported | abstained | 0/0 | 0/0 | 0/0 | — | PASS | [2, 12, 1, 10, 4] | ollama | correct_abstention |
| K18 | unanswerable / missing_attachment | abstained | 0/0 | 0/0 | 0/0 | — | PASS | [8, 7, 12, 4, 5] | ollama | correct_abstention |
| K19 | unanswerable / unsupported_actual | abstained | 0/0 | 0/0 | 0/0 | — | PASS | [11, 4, 12, 1, 7] | ollama | correct_abstention |
| K20 | unanswerable / unsupported_detail | abstained | 0/0 | 0/0 | 0/0 | — | PASS | [11, 2, 1, 4, 5] | ollama | correct_abstention |

## Strict-pass failures

- **K01** — What was Kirana's total revenue for 2025, and in what currency is it reported? (status: answered)
- **K07** — What was Da Nang's 2025 warehouse utilisation, and what is the company's rule for putting a site on the consolidation watch list? (status: abstained)
- **K13** — What customer Net Promoter Score (NPS) did Kirana report for 2025 and for 2024? (status: abstained)
- **K14** — According to the quarterly revenue chart, what was Q4 2025 revenue in THB million? (status: abstained)
- **K15** — Under the standard 2026 tariff, what is the cold-chain pallet storage rate per pallet per month? (status: answered)

## Answer and citation detail

### K01 · ollama
Answer: Kirana's total revenue for 2025 was 8,420 THB million.
- p.4: “Revenue 6,910 7,655 8,420”
- p.4: “THB million 2023 2024 2025”
Latency: retrieve 13.4 ms, ask 29190.9 ms.

### K02 · ollama
Answer: Kirana's on-time delivery dipped in Q4 2025 due to severe flooding in southern Thailand, which closed sections of the main southern highway and forced line-haul traffic to Hat Yai to be rerouted through slower inland roads. Service recovered in December once the highway reopened.
- p.6: “Performance dipped in the fourth quarter. Flooding in southern Thailand closed sections of the main southern highway, and line-haul to Hat Yai was rerouted through slower inland roads. Service recovered in December once the highway reopened.”
- p.2: “The fourth quarter tested our network. Severe flooding in southern Thailand closed sections of the main southern highway for several weeks and forced us to reroute line-haul traffic. Our teams kept customers informed and service recovered by December.”
Latency: retrieve 13.8 ms, ask 25413.0 ms.

### K03 · ollama
Answer: Kirana delivered 41.6 million parcels in 2025.
- p.6: “We delivered 41.6 million parcels in 2025.”
Latency: retrieve 15.0 ms, ask 18396.9 ms.

### K04 · ollama
Answer: EBITDA in 2024 was 1,186 THB million.
- p.4: “EBITDA 1,036 1,186 1,347”
Latency: retrieve 14.9 ms, ask 20209.3 ms.

### K05 · ollama
Answer: Kirana reported capital expenditure of THB 905 million for 2025.
- p.4: “Capital expenditure 610 742 905”
Latency: retrieve 13.4 ms, ask 19669.4 ms.

### K06 · ollama
Answer: The 2025 utilisation rate at the Cibitung cold-chain facility in Bekasi was 96%.
- p.8: “ID-CBT Cibitung, Bekasi Indonesia Cold chain 21,000 96% 2019”
Latency: retrieve 14.3 ms, ask 19387.0 ms.

### K07 · ollama
Answer: (empty)
Citations: none.
Latency: retrieve 30.3 ms, ask 21679.2 ms.

### K08 · ollama
Answer: Kirana's Indonesian electric light truck fleet consisted of 44 vehicles at the end of 2025.
- p.9: “Electric light truck 132 44 18 24 218”
Latency: retrieve 13.8 ms, ask 19319.5 ms.

### K09 · ollama
Answer: The original figure stated in the CEO letter was 96 electric trucks added in 2025. The corrected number, as reported in the errata and Fleet and sustainability section, is 82.
- p.12: “The Letter from the Chief Executive Officer states that 96 electric trucks were added in 2025. The correct figure is 82, as reported in the Fleet and sustainability section.”
Latency: retrieve 16.4 ms, ask 19867.1 ms.

### K10 · ollama
Answer: Kirana's Scope 2 greenhouse gas emissions in 2025 were 12,100 tCO2e.
- p.9: “Scope 2 (tCO2e) 14,300 13,900 12,100”
Latency: retrieve 15.3 ms, ask 20748.3 ms.

### K11 · ollama
Answer: FTL stands for full truckload.
- p.12: “• FTL: full truckload.”
Latency: retrieve 13.9 ms, ask 4368.7 ms.

### K12 · ollama
Answer: Kirana's year-end 2025 employee headcount for Indonesia was 2,240, and the number of electric light trucks was 44.
- p.10: “Indonesia 1,960 2,240”
- p.9: “Electric light truck 132 44 18 24 218”
Latency: retrieve 14.3 ms, ask 21863.6 ms.

### K13 · ollama
Answer: The provided evidence does not contain the customer Net Promoter Score (NPS) for Kirana for 2024 or 2025. While Evidence [P12-B3-4] defines NPS as 'Net Promoter Score, from our biannual customer survey,' no specific numerical values or scores for any year are reported in the supplied text.
Citations: none.
Latency: retrieve 15.2 ms, ask 21183.1 ms.

### K14 · ollama
Answer: (empty)
Citations: none.
Latency: retrieve 14.7 ms, ask 21429.5 ms.

### K15 · ollama
Answer: Under the standard 2026 tariff, the cold-chain pallet storage rate is 1,150.00 THB per pallet per month.
- p.13: “Cold-chainpalletstorage(2-8C) perpalletpermonth 1,150.00”
Latency: retrieve 15.5 ms, ask 21480.7 ms.

### K16 · ollama
Answer: Kirana plans capital expenditure of approximately THB 1,050 million for 2026.
- p.11: “Planned capital expenditure is approximately THB 1,050 million.”
Latency: retrieve 14.4 ms, ask 18147.2 ms.

### K17 · ollama
Answer: (empty)
Citations: none.
Latency: retrieve 15.0 ms, ask 15066.0 ms.

### K18 · ollama
Answer: (empty)
Citations: none.
Latency: retrieve 12.9 ms, ask 16637.9 ms.

### K19 · ollama
Answer: (empty)
Citations: none.
Latency: retrieve 14.2 ms, ask 16524.2 ms.

### K20 · ollama
Answer: (empty)
Citations: none.
Latency: retrieve 13.8 ms, ask 15766.6 ms.

