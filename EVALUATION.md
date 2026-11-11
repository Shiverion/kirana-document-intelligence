# Kirana QA evaluation

## Setup and scoring

The benchmark uses the supplied 13-page Kirana report and [20 source-annotated questions](data/a1_gold.json). Sixteen questions are answerable. Four require abstention. Gold evidence is recorded per required fact, with multiple eligible pages when the same fact appears more than once. The report and gold hashes are in the run metadata.

Retrieval is evaluated on answerable questions. Evidence-group Recall@5 gives credit when any eligible page for a required fact is in the top five unique pages. All Evidence@5 requires all groups. nDCG@5 uses binary relevance on the union of annotated pages and rewards placing them earlier. Page-level retrieval can succeed even when the model receives an incomplete row or chart transcription.

The automatic answer scorer requires all required fact aliases for a strict answer pass. Its grounded strict score also requires citation page coverage, and counts correct abstentions across the four unanswerable cases. Cite-page precision and completeness are page-hit proxies. The source audit checks additional details that those proxies miss, including row and column alignment, corrected values, units, and claims added in an explanation. The [implementation plan](PLAN_A1.md) links each metric to its research source and documents the local adaptations.

## First run and diagnosis

The first model run used Qwen3.5 4B via Ollama, RapidOCR, five retrieved pages, and the initial evidence formatting. Retrieval found all required page groups for 16 of 16 answerable cases. The model passed only 4 of 16 answerable cases under the strict alias rubric, abstained on all four unanswerable questions, and passed 8 of 20 under the grounded strict proxy. [Raw initial results](results/ollama-initial/report.json)

| Observed case | What went wrong | Revision to evaluate |
| --- | --- | --- |
| K01 total revenue and K02 Q4 disruption | The lexical guard blocked questions with the gold page already ranked first. | Let the model examine retrieved evidence and decide whether it supports an answer. |
| K04 EBITDA, K06 Cibitung, K07 Da Nang, K08 Indonesian fleet, K10 emissions, K12 staff and fleet | Native rows reached the model without reliable field labels. The model confused an opening year with a reporting period, and an all-country total with a country-specific count. | Read individual PDF table cells and attach the column label to the value, with the physical source page. |
| K14 Q4 chart and K15 scanned tariff | The assistant quoted the correct page but paired the question with another value on that page. | Preserve OCR layout, so the model can associate values with the right labels before citing. |
| K19 2026 actual capital expenditure | The assistant refused the unsupported request but incorrectly described the 2025 actual as a 2024 value in its explanation. | Keep refusals concise and require evidence for any additional factual detail. |

## Second run and source audit

With native table cell bindings and OCR geometry enabled, the model passed 11 of 16 answerable cases on the automated rubric and 15 of 20 across all cases on the grounded proxy. The benchmark refused all four unsupported cases. The same configuration scored 0.938 Evidence-group Recall@5 and 0.800 nDCG@5, compared with 0.875 and 0.768 for full-page BM25. These retrieval numbers compare two pipelines, since the candidate also indexes OCR. [Full second-run results](results/ollama-final/report.json)

Source review found 12 correct answers out of the 16 answerable cases. K01 was correct against the financial table on page 4. The lexical matcher missed the valid wording “8,420 THB million”. The gold set stayed fixed between full runs. The errata case returned 82 and identified 96 as the original figure. The Indonesia comparison combined 2,240 employees from page 10 with 44 electric light trucks from page 9.

| Remaining case | Source audit and diagnosis |
| --- | --- |
| K07 · Da Nang and watch list | The two required pages ranked first and second. The prompt included the watch-list rule and a flattened Da Nang row, but dropped the labeled row that separates 2025 utilisation from the 2023 opening year. |
| K13 · NPS card | The OCR evidence for 52 and 47 was indexed on page 3, but page 3 fell outside the five retrieved pages. This was a ranking failure. |
| K14 · Quarterly revenue | Page 5 was retrieved. The model abstained in the second run. The source chart labels Q4 at THB 2,305 million. The first run paired Q4 with Q1's value of 1,962. |
| K15 · Scanned tariff | Page 13 was retrieved, but the flattened excerpt paired the cold-chain label with THB 1,150, the frozen-storage rate. Cold-chain is THB 780. This is a wrong answer with a relevant page and illustrates the limit of the citation page-hit proxy. |
| K17–K20 · Unsupported requests | All four were marked abstained, but the model often returned an empty message. A deterministic refusal message is needed for the CLI. |

## Third full run

The next build retained the selected labeled row in the model context, corrected scan skew before grouping OCR fragments, ranked OCR transcriptions without coordinate tokens, and ensured an abstention displayed a message. The run used Qwen3.5 4B via Ollama, RapidOCR, five unique pages, and the same PDF and gold hashes. [Per-case report](results/ollama-verified/report.md) · [Raw results](results/ollama-verified/report.json)

| Metric | Result |
| --- | ---: |
| Evidence-group Recall@5, full-page BM25 → structured with OCR | 87.5% → 100% |
| All Evidence@5, full-page BM25 → structured with OCR | 14/16 → 16/16 |
| nDCG@5, full-page BM25 → structured with OCR | 0.768 → 0.826 |
| Strict answer pass, lexical rubric | 11/16 |
| Correct answer, reviewed against the source pages | 13/16 |
| Grounded strict pass, automated page and alias proxy | 15/20 |
| Correct abstention on unsupported requests | 4/4 |
| Page coverage with extractable evidence | 13/13 |
| Ask latency, median / p95 on the 4 GB GTX 1650 profile | 21.1 s / 26.2 s |

The lexical rubric missed two valid phrases. K01 answered “8,420 Thai baht million”. K02 said the floods were “closing sections of the main southern highway”. The gold set stayed fixed and those two corrections are reported separately from the automated score. The source review checks the answer against the cited pages. It does not require each short excerpt to independently reproduce the entire table header.

K07 combined Da Nang's 62% utilisation from page 8 and the watch-list rule from page 7. K15 correctly cited the scan row with the cold-chain rate of THB 780 per pallet per month. K13's infographic page returned to the top five, but the assistant still abstained. K12 regressed from the correct Indonesia fleet count of 44 to the group-wide 218. K14 answered with annual revenue of THB 8,420 million where the chart shows Q4 revenue of THB 2,305 million. Both errors used real excerpts with the wrong scope.

## Final scope checks

The final application checks explicitly requested visuals and named-entity numeric requests against the cited evidence. I replayed the checks over all 20 recorded answers with generation and retrieval held fixed. Only K12 and K14 changed, from incorrect answers to abstentions. The 13 source-verified answers and the four correct abstentions were preserved. Answer coverage fell from 15/20 to 13/20. The automatic strict scores stayed at 11/16 for answerable cases and 15/20 overall. Citation page precision rose from 0.833 to 0.950, while the evidence completeness proxy fell from 0.833 to 0.792. This is the cost of withholding an answer whose remaining cited evidence is insufficient. [Replay and live checks](results/scope-guard-check/report.json)

I also ran K12 and K14 live through Ollama with the final code. Both were refused by the scope checks. K12, K13 and K14 remain answerable questions that the evaluated configuration did not solve. The replay isolates the effect of the final checks. It does not measure variation across a fresh 20-answer generation.

The full regression suite passed 22 tests, including a new PDF through the API and CLI, a year-labeled table, an empty refusal, an invalid source quote, and both scope failures.

These runs use one report and one fixed question set to diagnose changes. The figures are specific to this sample. A separate synthetic PDF exercised the same API and CLI, including ruled tables, unsupported facts and citation validation. The recruiter's second Kirana document remains a future evaluation.
