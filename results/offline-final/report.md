# Document QA evaluation

Cases: 20 total, 16 answerable, 4 unanswerable. Retrieval cutoff: k=5.

PDF SHA256: `109f0c113b5d8184ff720b87d69d3d9c7c236cf3be4aff5cd02b50addea43605`.
Gold SHA256: `f3f0b5b59b3256bd61812512d89765d3ad954b4577d9edc3df96d3f9b11d6c09`.
Strategy: `structured`; visual OCR requested: `False`; page coverage: 12/13 pages with evidence; statuses: `{'text_extracted_visuals_not_ocr': 7, 'text_extracted': 6}`.

## Retrieval strategy comparison

| Strategy | Evidence-group Recall@k | All Evidence@k | nDCG@k |
|---|---:|---:|---:|
| baseline | 0.875 | 0.875 | 0.768 |
| structured | 0.875 | 0.875 | 0.748 |

| Metric | Score |
|---|---:|
| Evidence-group Recall@k | 0.875 |
| Evidence-group Recall@k (micro pooled) | 0.875 |
| All Evidence@k | 0.875 |
| nDCG@k | 0.748 |
| Atomic answer fact recall (lexical proxy) | 0.083 |
| Citation page support precision (page-hit proxy) | 1.000 |
| Citation evidence completeness | 0.083 |
| Strict answer pass rate (answerable cases) | 0.125 (2/16) |
| Grounded strict pass rate (all cases) | 0.300 (6/20) |
| Abstention recall | 1.000 |
| False abstention rate | 0.875 |
| Coverage | 0.100 |
| Selective error rate | 0.000 |
| Latency retrieve (mean / median / p95 ms) | 5.0 / 4.8 / 6.1 |
| Latency ask_including_internal_retrieval (mean / median / p95 ms) | 4.9 / 4.8 / 5.8 |
| Latency case_total (mean / median / p95 ms) | 9.9 / 9.6 / 11.2 |

Definitions: Evidence Recall@k is the macro average, by answerable case, of required evidence groups covered; a group is covered if any accepted gold page is retrieved. The micro pooled rate is also shown. All Evidence@k is the fraction of answerable cases with all groups covered. nDCG@k uses binary relevance over the union of distinct gold support pages. Atomic answer recall matches any listed alias as a case-insensitive token-bounded phrase; this is a lexical proxy, not semantic judging. Strict answer pass is answerable cases answered with every required alias present, over answerable cases only. Grounded strict pass adds citation page completeness for answerable cases and correct abstention for unanswerable cases, over all cases. Citation precision and completeness use cited page IDs against gold support pages; quote text is not judged for entailment. Coverage is the share of all cases answered; selective error is the error share among answered cases.

## Per-case results

| ID | Type | Status | Retrieval evidence | Answer facts | Citation evidence | Answer strict | Grounded strict | Retrieved pages | Mode | Diagnosis |
|---|---|---|---:|---:|---:|---|---|---|---|---|
| K01 | answerable | abstained | 2/2 | 0/2 | 0/2 | FAIL | FAIL | [4, 12, 1, 10, 11] | extractive_guard | answer_generation_miss |
| K02 | answerable | abstained | 2/2 | 0/2 | 0/2 | FAIL | FAIL | [6, 12, 2, 5, 1] | extractive_guard | answer_generation_miss |
| K03 | answerable | answered | 1/1 | 1/1 | 1/1 | PASS | PASS | [6, 1, 10, 12, 2] | extractive | pass |
| K04 | answerable | abstained | 1/1 | 0/1 | 0/1 | FAIL | FAIL | [4, 9, 2, 10, 8] | extractive_guard | answer_generation_miss |
| K05 | answerable | answered | 1/1 | 1/1 | 1/1 | PASS | PASS | [4, 11, 1, 12, 2] | extractive | pass |
| K06 | answerable | abstained | 1/1 | 0/1 | 0/1 | FAIL | FAIL | [8, 7, 2, 11, 10] | extractive_guard | answer_generation_miss |
| K07 | answerable | abstained | 3/3 | 0/3 | 0/3 | FAIL | FAIL | [7, 8, 1, 4, 12] | extractive_guard | answer_generation_miss |
| K08 | answerable | abstained | 1/1 | 0/1 | 0/1 | FAIL | FAIL | [9, 11, 12, 2, 1] | extractive_guard | answer_generation_miss |
| K09 | answerable | abstained | 3/3 | 0/3 | 0/3 | FAIL | FAIL | [12, 11, 2, 9, 3] | extractive_guard | answer_generation_miss |
| K10 | answerable | abstained | 1/1 | 0/1 | 0/1 | FAIL | FAIL | [9, 1, 12, 2, 3] | extractive_guard | answer_generation_miss |
| K11 | answerable | abstained | 1/1 | 0/1 | 0/1 | FAIL | FAIL | [12] | extractive_guard | answer_generation_miss |
| K12 | answerable | abstained | 2/2 | 0/2 | 0/2 | FAIL | FAIL | [9, 11, 10, 12, 3] | extractive_guard | answer_generation_miss |
| K13 | answerable | abstained | 0/2 | 0/2 | 0/2 | FAIL | FAIL | [12, 9, 2, 4, 10] | extractive_guard | ingestion_coverage_gap |
| K14 | answerable | abstained | 1/1 | 0/1 | 0/1 | FAIL | FAIL | [4, 2, 11, 5, 6] | extractive_guard | answer_generation_miss |
| K15 | answerable | abstained | 0/1 | 0/1 | 0/1 | FAIL | FAIL | [2, 7, 8, 11, 12] | extractive_guard | ingestion_coverage_gap |
| K16 | answerable | abstained | 1/1 | 0/1 | 0/1 | FAIL | FAIL | [4, 11, 1, 2, 7] | extractive_guard | answer_generation_miss |
| K17 | unanswerable | abstained | 0/0 | 0/0 | 0/0 | — | PASS | [2, 12, 4, 1, 10] | extractive_guard | correct_abstention |
| K18 | unanswerable | abstained | 0/0 | 0/0 | 0/0 | — | PASS | [7, 8, 12, 4, 5] | extractive_guard | correct_abstention |
| K19 | unanswerable | abstained | 0/0 | 0/0 | 0/0 | — | PASS | [4, 11, 1, 12, 2] | extractive_guard | correct_abstention |
| K20 | unanswerable | abstained | 0/0 | 0/0 | 0/0 | — | PASS | [11, 2, 1, 5, 4] | extractive_guard | correct_abstention |

## Strict-pass failures

- **K01** — What was Kirana's total revenue for 2025, and in what currency is it reported? (status: abstained)
- **K02** — What disruption caused Kirana's on-time delivery to dip in Q4 2025, and how did it affect the main southern highway? (status: abstained)
- **K04** — What was EBITDA in 2024 according to the financial summary? (status: abstained)
- **K06** — What was the 2025 utilisation rate at the Cibitung cold-chain facility in Bekasi? (status: abstained)
- **K07** — What was Da Nang's 2025 warehouse utilisation, and what is the company's rule for putting a site on the consolidation watch list? (status: abstained)
- **K08** — How many electric light trucks were in Kirana's Indonesian fleet at the end of 2025? (status: abstained)
- **K09** — The CEO letter and the errata give different figures for electric trucks added in 2025. What was the original figure, and which corrected number should an analyst use? (status: abstained)
- **K10** — What were Kirana's Scope 2 greenhouse gas emissions in 2025? (status: abstained)
- **K11** — What does FTL stand for in this report? (status: abstained)
- **K12** — For Indonesia, what were Kirana's year-end 2025 employee headcount and number of electric light trucks? (status: abstained)
- **K13** — What customer Net Promoter Score (NPS) did Kirana report for 2025 and for 2024? (status: abstained)
- **K14** — According to the quarterly revenue chart, what was Q4 2025 revenue in THB million? (status: abstained)
- **K15** — Under the standard 2026 tariff, what is the cold-chain pallet storage rate per pallet per month? (status: abstained)
- **K16** — What capital expenditure does Kirana plan for 2026? (status: abstained)

## Answer and citation detail

### K01 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 4, 'evidence': 'Revenue figures are reported in Thai baht. Indonesian, Vietnamese and Malaysian revenues are translated at average exchange rates for the year.', 'source': 'text'}, {'page': 12, 'evidence': 'The Letter from the Chief Executive Officer states that 96 electric trucks were added in 2025. The correct figure is 82, as reported in the Fleet and sustainability section. The electric fleet was 218 vehicles at 31 December 2025.', 'source': 'text'}, {'page': 1, 'evidence': 'Kirana Logistics Group', 'source': 'text'}]}`
Latency: retrieve 6.1 ms, ask 5.1 ms.

### K02 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 6, 'evidence': 'Performance dipped in the fourth quarter. Flooding in southern Thailand closed sections of the main southern highway, and line-haul to Hat Yai was rerouted through slower inland roads. Service recovered in December once the highway reopened.', 'source': 'text'}, {'page': 12, 'evidence': '• OTD: on-time delivery, the share of shipments delivered within the committed window.', 'source': 'text'}, {'page': 2, 'evidence': 'The fourth quarter tested our network. Severe flooding in southern Thailand closed sections of the main southern highway for several weeks and forced us to reroute line-haul traffic. Our teams kept customers informed and service recovered by December. I want to thank every colleague who worked through those weeks.', 'source': 'text'}]}`
Latency: retrieve 4.8 ms, ask 4.9 ms.

### K03 · extractive
Answer: The document states: “We delivered 41.6 million parcels in 2025. Full-year on-time delivery (OTD) was 94.0%, measured as the share of shipments delivered within the committed window.”
- p.6: “We delivered 41.6 million parcels in 2025. Full-year on-time delivery (OTD) was 94.0%, measured as the share of shipments delivered within the committed window.”
Latency: retrieve 4.4 ms, ask 4.8 ms.

### K04 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 4, 'evidence': 'Table 1. Five-line financial summary', 'source': 'text'}, {'page': 9, 'evidence': '2023 2024 2025', 'source': 'text'}, {'page': 2, 'evidence': '2025 at a glance · Financial review · Revenue analysis · Operations · Facilities and network · Fleet and sustainability · People and safety · Risks and outlook · Appendix A: Glossary and errata · Appendix B: Standard contract tariff 2026', 'source': 'text'}]}`
Latency: retrieve 4.4 ms, ask 4.5 ms.

### K05 · extractive
Answer: The document states: “Capital expenditure 610 742 905”
- p.4: “Capital expenditure 610 742 905”
Latency: retrieve 4.5 ms, ask 4.4 ms.

### K06 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 8, 'evidence': 'ID-CBT Cibitung, Bekasi Indonesia Cold chain 21,000 96% 2019', 'source': 'text'}, {'page': 7, 'evidence': 'Our network strategy is to keep a large hub near each capital city, supported by cross-dock sites that shorten last-mile distances in secondary cities. Cold-chain capacity is the fastest-growing part of the network, and the Cibitung cold store in Bekasi operated close to full capacity for most of the year.', 'source': 'text'}, {'page': 2, 'evidence': '2025 at a glance · Financial review · Revenue analysis · Operations · Facilities and network · Fleet and sustainability · People and safety · Risks and outlook · Appendix A: Glossary and errata · Appendix B: Standard contract tariff 2026', 'source': 'text'}]}`
Latency: retrieve 5.2 ms, ask 4.7 ms.

### K07 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 7, 'evidence': 'We review utilisation monthly. Sites that remain below 65% for two consecutive quarters are placed on a consolidation watch list, while sites above 92% trigger an expansion study.', 'source': 'text'}, {'page': 8, 'evidence': 'VN-DNG Da Nang Vietnam Cross-dock 8,400 62% 2023', 'source': 'text'}, {'page': 1, 'evidence': 'This is a fictional company and document created by DevXLabs for candidate assessment. Any resemblance to a real company is coincidental.', 'source': 'text'}]}`
Latency: retrieve 4.8 ms, ask 4.8 ms.

### K08 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 9, 'evidence': 'Our electric fleet grew from 136 vehicles at the end of 2024 to 218 at the end of 2025, an increase of 82. Electric vehicles now make up 18% of the fleet. All new light trucks ordered for urban routes in Thailand and Malaysia are electric.', 'source': 'text'}, {'page': 11, 'evidence': '• Add 120 electric light trucks, bringing the electric share of the fleet above 25%.', 'source': 'text'}, {'page': 12, 'evidence': 'The Letter from the Chief Executive Officer states that 96 electric trucks were added in 2025. The correct figure is 82, as reported in the Fleet and sustainability section. The electric fleet was 218 vehicles at 31 December 2025.', 'source': 'text'}]}`
Latency: retrieve 4.6 ms, ask 4.6 ms.

### K09 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 12, 'evidence': 'The Letter from the Chief Executive Officer states that 96 electric trucks were added in 2025. The correct figure is 82, as reported in the Fleet and sustainability section. The electric fleet was 218 vehicles at 31 December 2025.', 'source': 'text'}, {'page': 11, 'evidence': '• Add 120 electric light trucks, bringing the electric share of the fleet above 25%.', 'source': 'text'}, {'page': 2, 'evidence': 'Our fleet transition accelerated. We added 96 electric trucks during the year, mostly in Bangkok and the Klang Valley, and installed rooftop solar at six more facilities.', 'source': 'text'}]}`
Latency: retrieve 4.6 ms, ask 5.8 ms.

### K10 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 9, 'evidence': 'Table 4. Greenhouse gas emissions', 'source': 'text'}, {'page': 1, 'evidence': 'Kirana Logistics Group', 'source': 'text'}, {'page': 12, 'evidence': 'The Letter from the Chief Executive Officer states that 96 electric trucks were added in 2025. The correct figure is 82, as reported in the Fleet and sustainability section. The electric fleet was 218 vehicles at 31 December 2025.', 'source': 'text'}]}`
Latency: retrieve 5.0 ms, ask 4.7 ms.

### K11 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 12, 'evidence': '• FTL: full truckload.', 'source': 'text'}]}`
Latency: retrieve 4.2 ms, ask 4.2 ms.

### K12 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 9, 'evidence': 'Our electric fleet grew from 136 vehicles at the end of 2024 to 218 at the end of 2025, an increase of 82. Electric vehicles now make up 18% of the fleet. All new light trucks ordered for urban routes in Thailand and Malaysia are electric.', 'source': 'text'}, {'page': 11, 'evidence': '• Add 120 electric light trucks, bringing the electric share of the fleet above 25%.', 'source': 'text'}, {'page': 10, 'evidence': 'Table 5. Employees by country at year end', 'source': 'text'}]}`
Latency: retrieve 5.1 ms, ask 4.9 ms.

### K13 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 12, 'evidence': '• NPS: Net Promoter Score, from our biannual customer survey.', 'source': 'text'}, {'page': 9, 'evidence': '2023 2024 2025', 'source': 'text'}, {'page': 2, 'evidence': '2025 was a year of disciplined growth for Kirana. Revenue rose 10.0% to THB 8,420 million and net profit reached THB 531 million. We expanded our cold-chain capacity in Indonesia, where demand from grocery and pharmaceutical customers continues to outpace supply.', 'source': 'text'}]}`
Latency: retrieve 4.8 ms, ask 4.7 ms.

### K14 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 4, 'evidence': 'THB million 2023 2024 2025', 'source': 'text'}, {'page': 2, 'evidence': '2025 was a year of disciplined growth for Kirana. Revenue rose 10.0% to THB 8,420 million and net profit reached THB 531 million. We expanded our cold-chain capacity in Indonesia, where demand from grocery and pharmaceutical customers continues to outpace supply.', 'source': 'text'}, {'page': 11, 'evidence': 'We expect revenue growth of 11% to 13% in 2026. Planned capital expenditure is approximately THB 1,050 million.', 'source': 'text'}]}`
Latency: retrieve 4.6 ms, ask 5.0 ms.

### K15 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 2, 'evidence': '2025 at a glance · Financial review · Revenue analysis · Operations · Facilities and network · Fleet and sustainability · People and safety · Risks and outlook · Appendix A: Glossary and errata · Appendix B: Standard contract tariff 2026', 'source': 'text'}, {'page': 7, 'evidence': 'TH-RYG Rayong Thailand Cold chain 9,600 82% 2021', 'source': 'text'}, {'page': 8, 'evidence': 'MY-JHB Johor Bahru Malaysia Cold chain 9,200 85% 2022', 'source': 'text'}]}`
Latency: retrieve 4.8 ms, ask 4.7 ms.

### K16 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 4, 'evidence': 'Capital expenditure 610 742 905', 'source': 'text'}, {'page': 11, 'evidence': 'We expect revenue growth of 11% to 13% in 2026. Planned capital expenditure is approximately THB 1,050 million.', 'source': 'text'}, {'page': 1, 'evidence': 'Kirana Logistics Group', 'source': 'text'}]}`
Latency: retrieve 4.5 ms, ask 4.4 ms.

### K17 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 2, 'evidence': 'Letter from the Chief Executive Officer', 'source': 'text'}, {'page': 12, 'evidence': 'The Letter from the Chief Executive Officer states that 96 electric trucks were added in 2025. The correct figure is 82, as reported in the Fleet and sustainability section. The electric fleet was 218 vehicles at 31 December 2025.', 'source': 'text'}, {'page': 4, 'evidence': 'Financial review', 'source': 'text'}]}`
Latency: retrieve 6.9 ms, ask 5.7 ms.

### K18 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 7, 'evidence': 'TH-RYG Rayong Thailand Cold chain 9,600 82% 2021', 'source': 'text'}, {'page': 8, 'evidence': 'MY-JHB Johor Bahru Malaysia Cold chain 9,200 85% 2022', 'source': 'text'}, {'page': 12, 'evidence': '• Utilisation: average share of usable pallet positions occupied.', 'source': 'text'}]}`
Latency: retrieve 5.9 ms, ask 5.3 ms.

### K19 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 4, 'evidence': 'Capital expenditure 610 742 905', 'source': 'text'}, {'page': 11, 'evidence': 'We expect revenue growth of 11% to 13% in 2026. Planned capital expenditure is approximately THB 1,050 million.', 'source': 'text'}, {'page': 1, 'evidence': 'Kirana Logistics Group', 'source': 'text'}]}`
Latency: retrieve 5.0 ms, ask 5.3 ms.

### K20 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 11, 'evidence': '• Customer concentration. Our ten largest customers generated 41% of revenue.', 'source': 'text'}, {'page': 2, 'evidence': '2025 was a year of disciplined growth for Kirana. Revenue rose 10.0% to THB 8,420 million and net profit reached THB 531 million. We expanded our cold-chain capacity in Indonesia, where demand from grocery and pharmaceutical customers continues to outpace supply.', 'source': 'text'}, {'page': 1, 'evidence': 'Kirana Logistics Group', 'source': 'text'}]}`
Latency: retrieve 5.1 ms, ask 5.9 ms.

