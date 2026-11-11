# Kirana Document Intelligence

A local PDF question-answering assistant for Kirana Logistics Group’s investor relations team. It returns an answer with the physical PDF page and a source excerpt, or explains why the report lacks sufficient evidence.

## Run the demo

Use Python 3.11 or later, uv and Ollama. Download the [supplied annual report](https://drive.google.com/file/d/1KY4C1tE8ao0pV0784qgUp8r-PZW5lBxB/view) into `data/Kirana_Logistics_Annual_Report_2025.pdf`, or use the path to another PDF. Start Ollama with `ollama serve` in a separate terminal if it is not already running.

```powershell
uv sync --extra ocr
ollama pull qwen3.5:4b
uv run --extra ocr python -m kirana_qa ask --pdf data/Kirana_Logistics_Annual_Report_2025.pdf --ocr --model qwen3.5:4b --num-gpu 24 --question "The CEO letter and the errata give different figures for electric trucks added in 2025. What was the original figure, and which corrected number should an analyst use?"
```

Swap `--pdf` to process a new document. Add `--json` to inspect the returned status, retrieval and citation metadata. Run `inspect` instead of `ask` and omit `--question` for page-by-page extraction coverage. The program has an extractive path when run without `--model`. The demo uses partial GPU offload for a 4 GB GPU. Change `--num-gpu` to `0` for CPU, or omit it for automatic offload on a device with sufficient memory.

## Architecture

1. **Ingest.** PyMuPDF enumerates physical pages and extracts native text. For ruled tables, cell rectangles preserve field and value pairs such as a year and its corresponding EBITDA. RapidOCR transcribes placed images. The app corrects scan skew before grouping OCR fragments into rows and retains their coordinates. The manifest records gaps by page.
2. **Retrieve.** A full-page BM25 baseline measures how often native PDF text locates the evidence. The structured strategy ranks individual evidence units, favors labeled table rows and aggregates results to unique pages. The model context prioritizes the selected unit from each retrieved page before adding more.
3. **Answer.** The optional Ollama model receives the retrieved evidence. It can abstain or respond with cited excerpts. Code resolves citation IDs against the context and checks the normalized excerpts. Explicit visual and entity-specific questions also receive scope checks. Citations identify physical PDF pages and the source type, with a region when available.
4. **Inspect.** A coverage report exposes which pages had native text or image evidence, and where processing was incomplete. The evaluation harness compares retrieval independently from answer scoring.

Local processing makes the demo reproducible without a model API key. Page-level citations make the source easy to verify. OCR is useful for text in a scan or figure. It can misread digits or lose a relationship between a label and a value, so visual results merit direct inspection. The visual path reads printed labels and numbers. It cannot infer values reliably from unlabelled marks, and complex borderless tables may require a different parser. A validated excerpt establishes provenance. The evaluation separately checks whether the evidence supports the answer.

## Evaluation

The [20-question gold set](data/a1_gold.json) covers prose, tables, questions requiring more than one page, an erratum, an infographic, a chart, a scanned tariff and four unsupported requests. The gold set specifies required facts and acceptable evidence pages. The [evaluation report](EVALUATION.md) explains the results and failures. The [detailed plan](PLAN_A1.md) describes the research and the local adaptations used in the metrics.

```powershell
uv run --extra ocr python -m evals.run --ocr-visuals --compare-baseline --diagnose-retrieval --model-config configs/ollama-4gb.json --output-dir results/reproduced
uv run --with pytest python -m pytest -q
```

To isolate the final scope checks, replay the recorded answers. Add `--live K12 K14` to run those two questions again through Ollama.

```powershell
uv run --extra ocr python -m evals.replay_scope_guards --run results/ollama-verified/report.json --output results/scope-guard-reproduced/report.json
```

## Next week

Validate the system on the second Kirana PDF and reports from other issuers. Add precise visual region citations where OCR mispairs chart labels and values. Review difficult refusal and contradiction cases with investor relations before tuning the answer policy on a separate development set. Recheck those changes on a held-out set.

## Use of AI tools

Codex helped plan the solution, implement the application and evaluation harness, and review benchmark output. Separate Luna agents worked on implementation and testing. Gold facts and supporting pages were checked against the source PDF, including visual inspection of the infographic, chart and scanned tariff. The local application uses Ollama for optional answer generation.
