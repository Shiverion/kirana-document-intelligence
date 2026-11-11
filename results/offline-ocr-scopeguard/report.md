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
| Atomic answer fact recall (lexical proxy) | 0.167 |
| Citation page support precision (page-hit proxy) | 1.000 |
| Citation evidence completeness | 0.167 |
| Strict answer pass rate (answerable cases) | 0.250 (4/16) |
| Grounded strict pass rate (all cases) | 0.400 (8/20) |
| Abstention recall | 1.000 |
| False abstention rate | 0.750 |
| Coverage | 0.200 |
| Selective error rate | 0.000 |
| Latency retrieve (mean / median / p95 ms) | 11.2 / 11.1 / 13.4 |
| Latency ask_including_internal_retrieval (mean / median / p95 ms) | 11.3 / 10.8 / 12.9 |
| Latency case_total (mean / median / p95 ms) | 22.5 / 21.4 / 26.0 |

Definitions: Evidence Recall@k is the macro average, by answerable case, of required evidence groups covered; a group is covered if any accepted gold page is retrieved. The micro pooled rate is also shown. All Evidence@k is the fraction of answerable cases with all groups covered. nDCG@k uses binary relevance over the union of distinct gold support pages. Atomic answer recall matches any listed alias as a case-insensitive token-bounded phrase; this is a lexical proxy, not semantic judging. Strict answer pass is answerable cases answered with every required alias present, over answerable cases only. Grounded strict pass adds citation page completeness for answerable cases and correct abstention for unanswerable cases, over all cases. Citation precision and completeness use cited page IDs against gold support pages; quote text is not judged for entailment. Coverage is the share of all cases answered; selective error is the error share among answered cases.

## Per-case results

| ID | Type / category | Status | Retrieval evidence | Answer facts | Citation evidence | Answer strict | Grounded strict | Retrieved pages | Mode | Diagnosis |
|---|---|---|---:|---:|---:|---|---|---|---|---|
| K01 | answerable / prose | abstained | 2/2 | 0/2 | 0/2 | FAIL | FAIL | [4, 12, 11, 9, 1] | extractive_guard | answer_generation_miss |
| K02 | answerable / prose | abstained | 2/2 | 0/2 | 0/2 | FAIL | FAIL | [6, 2, 5, 12, 1] | extractive_guard | answer_generation_miss |
| K03 | answerable / prose | answered | 1/1 | 1/1 | 1/1 | PASS | PASS | [6, 1, 10, 12, 2] | extractive | pass |
| K04 | answerable / table | answered | 1/1 | 1/1 | 1/1 | PASS | PASS | [4, 2, 10, 9, 8] | extractive | pass |
| K05 | answerable / table | answered | 1/1 | 1/1 | 1/1 | PASS | PASS | [4, 11, 1, 2, 12] | extractive | pass |
| K06 | answerable / table | abstained | 1/1 | 0/1 | 0/1 | FAIL | FAIL | [8, 7, 10, 4, 2] | extractive_guard | answer_generation_miss |
| K07 | answerable / cross_page | abstained | 3/3 | 0/3 | 0/3 | FAIL | FAIL | [7, 8, 1, 4, 6] | extractive_guard | answer_generation_miss |
| K08 | answerable / table | abstained | 1/1 | 0/1 | 0/1 | FAIL | FAIL | [9, 11, 12, 2, 1] | extractive_guard | answer_generation_miss |
| K09 | answerable / errata | abstained | 3/3 | 0/3 | 0/3 | FAIL | FAIL | [12, 11, 2, 9, 3] | extractive_guard | answer_generation_miss |
| K10 | answerable / table | abstained | 1/1 | 0/1 | 0/1 | FAIL | FAIL | [9, 1, 2, 12, 7] | extractive_guard | answer_generation_miss |
| K11 | answerable / glossary | abstained | 1/1 | 0/1 | 0/1 | FAIL | FAIL | [12, 4, 7, 8, 9] | extractive_guard | answer_generation_miss |
| K12 | answerable / cross_page | abstained | 2/2 | 0/2 | 0/2 | FAIL | FAIL | [9, 10, 11, 12, 3] | extractive_guard | answer_generation_miss |
| K13 | answerable / infographic | abstained | 0/2 | 0/2 | 0/2 | FAIL | FAIL | [12, 2, 4, 1, 11] | extractive_guard | retrieval_rank_miss |
| K14 | answerable / chart | abstained | 1/1 | 0/1 | 0/1 | FAIL | FAIL | [4, 2, 11, 5, 6] | extractive_guard | answer_generation_miss |
| K15 | answerable / scanned_table | abstained | 1/1 | 0/1 | 0/1 | FAIL | FAIL | [2, 8, 7, 10, 13] | extractive_guard | answer_generation_miss |
| K16 | answerable / prose | answered | 1/1 | 1/1 | 1/1 | PASS | PASS | [11, 4, 1, 2, 7] | extractive | pass |
| K17 | unanswerable / unsupported | abstained | 0/0 | 0/0 | 0/0 | — | PASS | [2, 12, 1, 10, 4] | extractive_guard | correct_abstention |
| K18 | unanswerable / missing_attachment | abstained | 0/0 | 0/0 | 0/0 | — | PASS | [8, 7, 12, 4, 5] | extractive_guard | correct_abstention |
| K19 | unanswerable / unsupported_actual | abstained | 0/0 | 0/0 | 0/0 | — | PASS | [11, 4, 12, 1, 7] | extractive_guard | correct_abstention |
| K20 | unanswerable / unsupported_detail | abstained | 0/0 | 0/0 | 0/0 | — | PASS | [11, 2, 1, 4, 5] | extractive_guard | correct_abstention |

## Strict-pass failures

- **K01** — What was Kirana's total revenue for 2025, and in what currency is it reported? (status: abstained)
- **K02** — What disruption caused Kirana's on-time delivery to dip in Q4 2025, and how did it affect the main southern highway? (status: abstained)
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

## Answer and citation detail

### K01 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 4, 'evidence': 'Revenue figures are reported in Thai baht. Indonesian, Vietnamese and Malaysian revenues are translated at average exchange rates for the year.', 'quote': 'Revenue figures are reported in Thai baht. Indonesian, Vietnamese and Malaysian revenues are translated at average exchange rates for the year.', 'source': 'text', 'evidence_id': 'P4-B11-12'}, {'page': 12, 'evidence': 'The Letter from the Chief Executive Officer states that 96 electric trucks were added in 2025. The correct figure is 82, as reported in the Fleet and sustainability section. The electric fleet was 218 vehicles at 31 December 2025.', 'quote': 'The Letter from the Chief Executive Officer states that 96 electric trucks were added in 2025. The correct figure is 82, as reported in the Fleet and sustainability section. The electric fleet was 218 vehicles at 31 December 2025.', 'source': 'text', 'evidence_id': 'P12-B7-8'}, {'page': 11, 'evidence': '• Currency. A weaker Indonesian rupiah reduces the baht value of our Indonesian earnings.', 'quote': '• Currency. A weaker Indonesian rupiah reduces the baht value of our Indonesian earnings.', 'source': 'text', 'evidence_id': 'P11-B3-4'}]}`
Latency: retrieve 16.0 ms, ask 14.6 ms.

### K02 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 6, 'evidence': 'Performance dipped in the fourth quarter. Flooding in southern Thailand closed sections of the main southern highway, and line-haul to Hat Yai was rerouted through slower inland roads. Service recovered in December once the highway reopened.', 'quote': 'Performance dipped in the fourth quarter. Flooding in southern Thailand closed sections of the main southern highway, and line-haul to Hat Yai was rerouted through slower inland roads. Service recovered in December once the highway reopened.', 'source': 'text', 'evidence_id': 'P6-B2-3'}, {'page': 2, 'evidence': 'The fourth quarter tested our network. Severe flooding in southern Thailand closed sections of the main southern highway for several weeks and forced us to reroute line-haul traffic. Our teams kept customers informed and service recovered by December. I want to thank every colleague who worked through those weeks.', 'quote': 'The fourth quarter tested our network. Severe flooding in southern Thailand closed sections of the main southern highway for several weeks and forced us to reroute line-haul traffic. Our teams kept customers informed and service recovered by December. I want to thank every colleague who worked through those weeks.', 'source': 'text', 'evidence_id': 'P2-B4-5'}, {'page': 5, 'evidence': 'Revenue built steadily through the year. The fourth quarter was the strongest, driven by peak-season e-commerce volume, despite the flood disruption in southern Thailand.', 'quote': 'Revenue built steadily through the year. The fourth quarter was the strongest, driven by peak-season e-commerce volume, despite the flood disruption in southern Thailand.', 'source': 'text', 'evidence_id': 'P5-B1-2'}]}`
Latency: retrieve 13.4 ms, ask 12.6 ms.

### K03 · extractive
Answer: The document states: “We delivered 41.6 million parcels in 2025. Full-year on-time delivery (OTD) was 94.0%, measured as the share of shipments delivered within the committed window.”
- p.6: “We delivered 41.6 million parcels in 2025. Full-year on-time delivery (OTD) was 94.0%, measured as the share of shipments delivered within the committed window.”
Latency: retrieve 13.0 ms, ask 10.8 ms.

### K04 · extractive
Answer: The document states: “Table 1. Five-line financial summary | Table row: THB million=EBITDA | 2023=1,036 | 2024=1,186 | 2025=1,347” Table header: “Table 1. Five-line financial summary | Table columns: THB million | 2023 | 2024 | 2025”
- p.4: “EBITDA 1,036 1,186 1,347”
- p.4: “THB million 2023 2024 2025”
Latency: retrieve 11.5 ms, ask 11.9 ms.

### K05 · extractive
Answer: The document states: “Capital expenditure 610 742 905”
- p.4: “Capital expenditure 610 742 905”
Latency: retrieve 11.6 ms, ask 11.8 ms.

### K06 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 8, 'evidence': 'Table row: Code=ID-CBT | Location=Cibitung, Bekasi | Country=Indonesia | Type=Cold chain | Area (sqm)=21,000 | Utilisation 2025=96% | Opened=2019', 'quote': 'ID-CBT Cibitung, Bekasi Indonesia Cold chain 21,000 96% 2019', 'source': 'table_row', 'evidence_id': 'P8-T1-R1'}, {'page': 7, 'evidence': 'Table 2. Major facilities at 31 December 2025 | Table row: Code=TH-RYG | Location=Rayong | Country=Thailand | Type=Cold chain | Area (sqm)=9,600 | Utilisation 2025=82% | Opened=2021', 'quote': 'TH-RYG Rayong Thailand Cold chain 9,600 82% 2021', 'source': 'table_row', 'evidence_id': 'P7-T1-R8'}, {'page': 10, 'evidence': 'Our lost-time injury frequency rate (LTIFR) improved to 0.42 per million hours worked, from 0.55 in 2024. There were no work-related fatalities. Forklift pedestrian separation was completed at all major facilities.', 'quote': 'Our lost-time injury frequency rate (LTIFR) improved to 0.42 per million hours worked, from 0.55 in 2024. There were no work-related fatalities. Forklift pedestrian separation was completed at all major facilities.', 'source': 'text', 'evidence_id': 'P10-B9-10'}]}`
Latency: retrieve 11.6 ms, ask 9.8 ms.

### K07 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 7, 'evidence': 'We review utilisation monthly. Sites that remain below 65% for two consecutive quarters are placed on a consolidation watch list, while sites above 92% trigger an expansion study.', 'quote': 'We review utilisation monthly. Sites that remain below 65% for two consecutive quarters are placed on a consolidation watch list, while sites above 92% trigger an expansion study.', 'source': 'text', 'evidence_id': 'P7-B3-4'}, {'page': 8, 'evidence': 'Table row: Code=VN-DNG | Location=Da Nang | Country=Vietnam | Type=Cross-dock | Area (sqm)=8,400 | Utilisation 2025=62% | Opened=2023', 'quote': 'VN-DNG Da Nang Vietnam Cross-dock 8,400 62% 2023', 'source': 'table_row', 'evidence_id': 'P8-T1-R10'}, {'page': 1, 'evidence': 'This is a fictional company and document created by DevXLabs for candidate assessment. Any resemblance to a real company is coincidental.', 'quote': 'This is a fictional company and document created by DevXLabs for candidate assessment. Any resemblance to a real company is coincidental.', 'source': 'text', 'evidence_id': 'P1-B3-4'}]}`
Latency: retrieve 11.7 ms, ask 12.4 ms.

### K08 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 9, 'evidence': 'Our electric fleet grew from 136 vehicles at the end of 2024 to 218 at the end of 2025, an increase of 82. Electric vehicles now make up 18% of the fleet. All new light trucks ordered for urban routes in Thailand and Malaysia are electric.', 'quote': 'Our electric fleet grew from 136 vehicles at the end of 2024 to 218 at the end of 2025, an increase of 82. Electric vehicles now make up 18% of the fleet. All new light trucks ordered for urban routes in Thailand and Malaysia are electric.', 'source': 'text', 'evidence_id': 'P9-B7-8'}, {'page': 11, 'evidence': '• Add 120 electric light trucks, bringing the electric share of the fleet above 25%.', 'quote': '• Add 120 electric light trucks, bringing the electric share of the fleet above 25%.', 'source': 'text', 'evidence_id': 'P11-B10-11'}, {'page': 12, 'evidence': 'The Letter from the Chief Executive Officer states that 96 electric trucks were added in 2025. The correct figure is 82, as reported in the Fleet and sustainability section. The electric fleet was 218 vehicles at 31 December 2025.', 'quote': 'The Letter from the Chief Executive Officer states that 96 electric trucks were added in 2025. The correct figure is 82, as reported in the Fleet and sustainability section. The electric fleet was 218 vehicles at 31 December 2025.', 'source': 'text', 'evidence_id': 'P12-B7-8'}]}`
Latency: retrieve 10.2 ms, ask 10.5 ms.

### K09 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 12, 'evidence': 'The Letter from the Chief Executive Officer states that 96 electric trucks were added in 2025. The correct figure is 82, as reported in the Fleet and sustainability section. The electric fleet was 218 vehicles at 31 December 2025.', 'quote': 'The Letter from the Chief Executive Officer states that 96 electric trucks were added in 2025. The correct figure is 82, as reported in the Fleet and sustainability section. The electric fleet was 218 vehicles at 31 December 2025.', 'source': 'text', 'evidence_id': 'P12-B7-8'}, {'page': 11, 'evidence': '• Add 120 electric light trucks, bringing the electric share of the fleet above 25%.', 'quote': '• Add 120 electric light trucks, bringing the electric share of the fleet above 25%.', 'source': 'text', 'evidence_id': 'P11-B10-11'}, {'page': 2, 'evidence': 'Our fleet transition accelerated. We added 96 electric trucks during the year, mostly in Bangkok and the Klang Valley, and installed rooftop solar at six more facilities.', 'quote': 'Our fleet transition accelerated. We added 96 electric trucks during the year, mostly in Bangkok and the Klang Valley, and installed rooftop solar at six more facilities.', 'source': 'text', 'evidence_id': 'P2-B3-4'}]}`
Latency: retrieve 9.8 ms, ask 10.2 ms.

### K10 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 9, 'evidence': 'Table 4. Greenhouse gas emissions | Table row: Scope 1 (tCO2e) | 2023=98,400 | 2024=101,200 | 2025=99,700', 'quote': 'Scope 1 (tCO2e) 98,400 101,200 99,700', 'source': 'table_row', 'evidence_id': 'P9-T2-R1'}, {'page': 1, 'evidence': 'Kirana Logistics Group', 'quote': 'Kirana Logistics Group', 'source': 'text', 'evidence_id': 'P1-B0-1'}, {'page': 2, 'evidence': '2025 was a year of disciplined growth for Kirana. Revenue rose 10.0% to THB 8,420 million and net profit reached THB 531 million. We expanded our cold-chain capacity in Indonesia, where demand from grocery and pharmaceutical customers continues to outpace supply.', 'quote': '2025 was a year of disciplined growth for Kirana. Revenue rose 10.0% to THB 8,420 million and net profit reached THB 531 million. We expanded our cold-chain capacity in Indonesia, where demand from grocery and pharmaceutical customers continues to outpace supply.', 'source': 'text', 'evidence_id': 'P2-B2-3'}]}`
Latency: retrieve 9.8 ms, ask 9.8 ms.

### K11 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 12, 'evidence': '• FTL: full truckload.', 'quote': '• FTL: full truckload.', 'source': 'text', 'evidence_id': 'P12-B4-5'}, {'page': 4, 'evidence': 'Table 1. Five-line financial summary | Table row: THB million=Revenue | 2023=6,910 | 2024=7,655 | 2025=8,420', 'quote': 'Revenue 6,910 7,655 8,420', 'source': 'table_row', 'evidence_id': 'P4-T1-R1'}, {'page': 7, 'evidence': 'Table 2. Major facilities at 31 December 2025 | Table row: Code=TH-LKB | Location=Lat Krabang, Bangkok | Country=Thailand | Type=Ambient + cross-dock | Area (sqm)=62,000 | Utilisation 2025=91% | Opened=2011', 'quote': 'TH-LKB Lat Krabang, Bangkok Thailand Ambient + cross-dock 62,000 91% 2011', 'source': 'table_row', 'evidence_id': 'P7-T1-R1'}]}`
Latency: retrieve 11.7 ms, ask 12.2 ms.

### K12 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 9, 'evidence': 'Our electric fleet grew from 136 vehicles at the end of 2024 to 218 at the end of 2025, an increase of 82. Electric vehicles now make up 18% of the fleet. All new light trucks ordered for urban routes in Thailand and Malaysia are electric.', 'quote': 'Our electric fleet grew from 136 vehicles at the end of 2024 to 218 at the end of 2025, an increase of 82. Electric vehicles now make up 18% of the fleet. All new light trucks ordered for urban routes in Thailand and Malaysia are electric.', 'source': 'text', 'evidence_id': 'P9-B7-8'}, {'page': 10, 'evidence': 'Table 5. Employees by country at year end | Table row: Country=Indonesia | Employees 2024=1,960 | Employees 2025=2,240', 'quote': 'Indonesia 1,960 2,240', 'source': 'table_row', 'evidence_id': 'P10-T1-R2'}, {'page': 11, 'evidence': '• Add 120 electric light trucks, bringing the electric share of the fleet above 25%.', 'quote': '• Add 120 electric light trucks, bringing the electric share of the fleet above 25%.', 'source': 'text', 'evidence_id': 'P11-B10-11'}]}`
Latency: retrieve 11.5 ms, ask 12.9 ms.

### K13 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 12, 'evidence': '• NPS: Net Promoter Score, from our biannual customer survey.', 'quote': '• NPS: Net Promoter Score, from our biannual customer survey.', 'source': 'text', 'evidence_id': 'P12-B3-4'}, {'page': 2, 'evidence': '2025 was a year of disciplined growth for Kirana. Revenue rose 10.0% to THB 8,420 million and net profit reached THB 531 million. We expanded our cold-chain capacity in Indonesia, where demand from grocery and pharmaceutical customers continues to outpace supply.', 'quote': '2025 was a year of disciplined growth for Kirana. Revenue rose 10.0% to THB 8,420 million and net profit reached THB 531 million. We expanded our cold-chain capacity in Indonesia, where demand from grocery and pharmaceutical customers continues to outpace supply.', 'source': 'text', 'evidence_id': 'P2-B2-3'}, {'page': 4, 'evidence': 'Table 1. Five-line financial summary | Table row: THB million=Net profit | 2023=412 | 2024=468 | 2025=531', 'quote': 'Net profit 412 468 531', 'source': 'table_row', 'evidence_id': 'P4-T1-R4'}]}`
Latency: retrieve 10.2 ms, ask 10.3 ms.

### K14 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 4, 'evidence': 'Table 1. Five-line financial summary | Table row: THB million=Revenue | 2023=6,910 | 2024=7,655 | 2025=8,420', 'quote': 'Revenue 6,910 7,655 8,420', 'source': 'table_row', 'evidence_id': 'P4-T1-R1'}, {'page': 2, 'evidence': '2025 was a year of disciplined growth for Kirana. Revenue rose 10.0% to THB 8,420 million and net profit reached THB 531 million. We expanded our cold-chain capacity in Indonesia, where demand from grocery and pharmaceutical customers continues to outpace supply.', 'quote': '2025 was a year of disciplined growth for Kirana. Revenue rose 10.0% to THB 8,420 million and net profit reached THB 531 million. We expanded our cold-chain capacity in Indonesia, where demand from grocery and pharmaceutical customers continues to outpace supply.', 'source': 'text', 'evidence_id': 'P2-B2-3'}, {'page': 11, 'evidence': 'We expect revenue growth of 11% to 13% in 2026. Planned capital expenditure is approximately THB 1,050 million.', 'quote': 'We expect revenue growth of 11% to 13% in 2026. Planned capital expenditure is approximately THB 1,050 million.', 'source': 'text', 'evidence_id': 'P11-B8-9'}]}`
Latency: retrieve 10.5 ms, ask 10.5 ms.

### K15 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 2, 'evidence': '2025 at a glance · Financial review · Revenue analysis · Operations · Facilities and network · Fleet and sustainability · People and safety · Risks and outlook · Appendix A: Glossary and errata · Appendix B: Standard contract tariff 2026', 'quote': '2025 at a glance · Financial review · Revenue analysis · Operations · Facilities and network · Fleet and sustainability · People and safety · Risks and outlook · Appendix A: Glossary and errata · Appendix B: Standard contract tariff 2026', 'source': 'text', 'evidence_id': 'P2-B8-9'}, {'page': 8, 'evidence': 'Table row: Code=MY-JHB | Location=Johor Bahru | Country=Malaysia | Type=Cold chain | Area (sqm)=9,200 | Utilisation 2025=85% | Opened=2022', 'quote': 'MY-JHB Johor Bahru Malaysia Cold chain 9,200 85% 2022', 'source': 'table_row', 'evidence_id': 'P8-T1-R13'}, {'page': 7, 'evidence': 'TH-RYG Rayong Thailand Cold chain 9,600 82% 2021', 'quote': 'TH-RYG Rayong Thailand Cold chain 9,600 82% 2021', 'source': 'text', 'evidence_id': 'P7-B15-16'}]}`
Latency: retrieve 10.3 ms, ask 11.1 ms.

### K16 · extractive
Answer: The document states: “We expect revenue growth of 11% to 13% in 2026. Planned capital expenditure is approximately THB 1,050 million.”
- p.11: “We expect revenue growth of 11% to 13% in 2026. Planned capital expenditure is approximately THB 1,050 million.”
Latency: retrieve 10.8 ms, ask 9.7 ms.

### K17 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 2, 'evidence': 'Letter from the Chief Executive Officer', 'quote': 'Letter from the Chief Executive Officer', 'source': 'text', 'evidence_id': 'P2-B0-1'}, {'page': 12, 'evidence': 'The Letter from the Chief Executive Officer states that 96 electric trucks were added in 2025. The correct figure is 82, as reported in the Fleet and sustainability section. The electric fleet was 218 vehicles at 31 December 2025.', 'quote': 'The Letter from the Chief Executive Officer states that 96 electric trucks were added in 2025. The correct figure is 82, as reported in the Fleet and sustainability section. The electric fleet was 218 vehicles at 31 December 2025.', 'source': 'text', 'evidence_id': 'P12-B7-8'}, {'page': 1, 'evidence': 'Kirana Logistics Group', 'quote': 'Kirana Logistics Group', 'source': 'text', 'evidence_id': 'P1-B0-1'}]}`
Latency: retrieve 9.6 ms, ask 10.6 ms.

### K18 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 8, 'evidence': 'Table row: Code=MY-JHB | Location=Johor Bahru | Country=Malaysia | Type=Cold chain | Area (sqm)=9,200 | Utilisation 2025=85% | Opened=2022', 'quote': 'MY-JHB Johor Bahru Malaysia Cold chain 9,200 85% 2022', 'source': 'table_row', 'evidence_id': 'P8-T1-R13'}, {'page': 7, 'evidence': 'TH-RYG Rayong Thailand Cold chain 9,600 82% 2021', 'quote': 'TH-RYG Rayong Thailand Cold chain 9,600 82% 2021', 'source': 'text', 'evidence_id': 'P7-B15-16'}, {'page': 12, 'evidence': '• Utilisation: average share of usable pallet positions occupied.', 'quote': '• Utilisation: average share of usable pallet positions occupied.', 'source': 'text', 'evidence_id': 'P12-B5-6'}]}`
Latency: retrieve 10.1 ms, ask 10.3 ms.

### K19 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 11, 'evidence': 'We expect revenue growth of 11% to 13% in 2026. Planned capital expenditure is approximately THB 1,050 million.', 'quote': 'We expect revenue growth of 11% to 13% in 2026. Planned capital expenditure is approximately THB 1,050 million.', 'source': 'text', 'evidence_id': 'P11-B8-9'}, {'page': 4, 'evidence': 'Capital expenditure 610 742 905', 'quote': 'Capital expenditure 610 742 905', 'source': 'text', 'evidence_id': 'P4-B8-9'}, {'page': 12, 'evidence': '• FTL: full truckload.', 'quote': '• FTL: full truckload.', 'source': 'text', 'evidence_id': 'P12-B4-5'}]}`
Latency: retrieve 11.4 ms, ask 12.5 ms.

### K20 · extractive_guard
Answer: I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.
Citations: none.
Diagnostics: `{'reason': 'No single excerpt contains the requested topic and any explicit time or role constraints.', 'candidate_evidence': [{'page': 11, 'evidence': '• Customer concentration. Our ten largest customers generated 41% of revenue.', 'quote': '• Customer concentration. Our ten largest customers generated 41% of revenue.', 'source': 'text', 'evidence_id': 'P11-B2-3'}, {'page': 2, 'evidence': '2025 was a year of disciplined growth for Kirana. Revenue rose 10.0% to THB 8,420 million and net profit reached THB 531 million. We expanded our cold-chain capacity in Indonesia, where demand from grocery and pharmaceutical customers continues to outpace supply.', 'quote': '2025 was a year of disciplined growth for Kirana. Revenue rose 10.0% to THB 8,420 million and net profit reached THB 531 million. We expanded our cold-chain capacity in Indonesia, where demand from grocery and pharmaceutical customers continues to outpace supply.', 'source': 'text', 'evidence_id': 'P2-B2-3'}, {'page': 1, 'evidence': 'Kirana Logistics Group', 'quote': 'Kirana Logistics Group', 'source': 'text', 'evidence_id': 'P1-B0-1'}]}`
Latency: retrieve 10.1 ms, ask 10.7 ms.

