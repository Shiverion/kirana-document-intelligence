"""Run retrieval and answer evaluation for the Kirana document QA app."""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

from evals.metrics import evaluate_cases, render_markdown


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _read_json_arg(value: str) -> dict[str, Any]:
    stripped = value.strip()
    if stripped.startswith("{"):
        raw = stripped
    else:
        candidate = Path(value)
        raw = candidate.read_text(encoding="utf-8") if candidate.is_file() else value
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(
            "model config must be inline JSON or a path to a JSON file"
        ) from exc
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("model config JSON must be an object")
    return parsed


def _load_gold(path: Path, limit: int | None) -> list[dict[str, Any]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid gold JSON at {path}: {exc}") from exc
    if isinstance(value, dict) and "cases" in value:
        value = value["cases"]
    if not isinstance(value, list):
        raise ValueError("Gold data must be an array or an object with a 'cases' array")

    seen_ids: set[str] = set()
    for index, case in enumerate(value, start=1):
        prefix = f"gold case #{index}"
        if not isinstance(case, dict):
            raise ValueError(f"{prefix} must be an object")
        for field in ("id", "question", "category", "answerable", "required_facts"):
            if field not in case:
                raise ValueError(f"{prefix} is missing {field!r}")
        case_id = str(case["id"])
        if not case_id or case_id in seen_ids:
            raise ValueError(f"{prefix} has a blank or duplicate id: {case_id!r}")
        seen_ids.add(case_id)
        if not isinstance(case["question"], str) or not case["question"].strip():
            raise ValueError(f"Case {case_id!r} question must be nonempty text")
        if not isinstance(case["answerable"], bool):
            raise ValueError(f"Case {case_id!r} answerable must be boolean")
        facts = case["required_facts"]
        if not isinstance(facts, list):
            raise ValueError(f"Case {case_id!r} required_facts must be an array")
        if case["answerable"] and not facts:
            raise ValueError(f"Answerable case {case_id!r} needs required_facts")
        if not case["answerable"] and facts:
            raise ValueError(f"Unanswerable case {case_id!r} must have empty required_facts")
        fact_ids: set[str] = set()
        for fact_index, fact in enumerate(facts, start=1):
            if not isinstance(fact, dict):
                raise ValueError(f"Case {case_id!r} fact #{fact_index} must be an object")
            for field in ("id", "aliases", "pages"):
                if field not in fact:
                    raise ValueError(f"Case {case_id!r} fact #{fact_index} missing {field!r}")
            fact_id = str(fact["id"])
            if not fact_id or fact_id in fact_ids:
                raise ValueError(f"Case {case_id!r} has a blank or duplicate fact id")
            fact_ids.add(fact_id)
            aliases, pages = fact["aliases"], fact["pages"]
            if not isinstance(aliases, list) or not aliases or any(
                not isinstance(alias, str) or not alias.strip() for alias in aliases
            ):
                raise ValueError(f"Case {case_id!r} fact {fact_id!r} needs nonempty aliases")
            if not isinstance(pages, list) or not pages or any(
                isinstance(page, bool) or not isinstance(page, int) or page < 1
                for page in pages
            ):
                raise ValueError(f"Case {case_id!r} fact {fact_id!r} needs positive page IDs")
    if limit is not None:
        value = value[:limit]
    return value


def _factory(
    qa_type: Any,
    pdf_path: Path,
    model_config: dict[str, Any] | None,
    *,
    ocr_visuals: bool,
) -> Any:
    factory = qa_type.from_pdf
    kwargs: dict[str, Any] = {}
    if model_config is not None:
        signature = inspect.signature(factory)
        if "model_config" not in signature.parameters and not any(
            item.kind == inspect.Parameter.VAR_KEYWORD
            for item in signature.parameters.values()
        ):
            raise RuntimeError(
                "--model-config was provided, but DocumentQA.from_pdf does not accept "
                "model_config"
            )
        kwargs["model_config"] = model_config
    if ocr_visuals:
        signature = inspect.signature(factory)
        if "ocr_visuals" not in signature.parameters and not any(
            item.kind == inspect.Parameter.VAR_KEYWORD
            for item in signature.parameters.values()
        ):
            raise RuntimeError(
                "--ocr-visuals was provided, but DocumentQA.from_pdf does not accept "
                "ocr_visuals"
            )
        kwargs["ocr_visuals"] = True
    return factory(str(pdf_path), **kwargs)


def _infer_page_count(qa: Any) -> int | None:
    for name in ("page_count", "num_pages", "n_pages"):
        value = getattr(qa, name, None)
        if isinstance(value, int) and not isinstance(value, bool) and value > 0:
            return value
    for name in ("pages", "page_texts", "page_contents"):
        value = getattr(qa, name, None)
        try:
            count = len(value)
        except (TypeError, AttributeError):
            continue
        if count > 0:
            return count
    return None


def _diagnose_case(
    case: dict[str, Any],
    prediction: dict[str, Any],
    full_retrieval: list[dict[str, Any]] | None,
    page_count: int | None,
    qa: Any,
) -> dict[str, Any]:
    if not case["answerable"]:
        return {"label": "correct_abstention" if prediction["status"] == "abstained" else "unsafe_answer"}
    facts = case["required_facts"]
    ranked = {row["page"] for row in prediction["retrieval"] if isinstance(row, dict) and isinstance(row.get("page"), int)}
    missing_groups = [fact for fact in facts if not ranked.intersection(fact["pages"])]
    if missing_groups:
        out_of_range = [
            int(page)
            for fact in missing_groups
            for page in fact["pages"]
            if page_count is not None and page > page_count
        ]
        if out_of_range:
            return {"label": "gold_page_out_of_range", "pages": sorted(set(out_of_range))}
        if full_retrieval is None:
            return {"label": "retrieval_miss; ingestion coverage unknown"}
        full_set = {row.get("page") for row in full_retrieval if isinstance(row, dict)}
        ingested_units = getattr(qa, "units", None)
        if isinstance(ingested_units, list):
            unavailable_facts: list[dict[str, Any]] = []
            for fact in missing_groups:
                has_gold_alias = any(
                    getattr(unit, "page", None) in fact["pages"]
                    and any(_alias_hit(str(alias), str(getattr(unit, "text", ""))) for alias in fact["aliases"])
                    for unit in ingested_units
                )
                if not has_gold_alias:
                    unavailable_facts.append(fact)
            if unavailable_facts:
                return {
                    "label": "ingestion_coverage_gap",
                    "fact_ids": [fact["id"] for fact in unavailable_facts],
                }
        if all(full_set.intersection(fact["pages"]) for fact in facts):
            return {"label": "retrieval_rank_miss"}
        return {"label": "retrieval_miss"}

    answer_hits = sum(
        any(_alias_hit(str(alias), prediction.get("answer", "")) for alias in fact["aliases"])
        for fact in facts
    )
    citation_pages = {
        citation.get("page")
        for citation in prediction["citations"]
        if isinstance(citation, dict) and isinstance(citation.get("page"), int)
    }
    citation_complete = all(citation_pages.intersection(fact["pages"]) for fact in facts)
    if prediction["status"] == "abstained" or answer_hits < len(facts):
        return {"label": "answer_generation_miss"}
    if not citation_complete:
        return {"label": "citation_miss"}
    return {"label": "pass"}


def _alias_hit(alias: str, text: str) -> bool:
    from evals.metrics import alias_in_text

    return alias_in_text(alias, text)


def run_evaluation(args: argparse.Namespace) -> dict[str, Any]:
    gold_cases = _load_gold(args.gold, args.limit)
    if not gold_cases:
        raise ValueError("Gold data has no selected cases")
    sys.path.insert(0, str(PROJECT_ROOT))
    from kirana_qa import DocumentQA

    qa = _factory(
        DocumentQA,
        args.pdf,
        args.model_config,
        ocr_visuals=args.ocr_visuals,
    )
    page_count = _infer_page_count(qa)
    predictions: dict[str, dict[str, Any]] = {}
    baseline_predictions: dict[str, dict[str, Any]] = {}
    diagnosis: dict[str, dict[str, Any]] = {}

    for case in gold_cases:
        question = case["question"]
        case_started = time.perf_counter()
        retrieval_started = time.perf_counter()
        retrieved = qa.retrieve(question, top_k=args.top_k, strategy=args.strategy)
        retrieval_ms = (time.perf_counter() - retrieval_started) * 1000
        answer_started = time.perf_counter()
        answer = qa.ask(question, top_k=args.top_k, strategy=args.strategy)
        ask_ms = (time.perf_counter() - answer_started) * 1000
        total_ms = (time.perf_counter() - case_started) * 1000
        if not isinstance(answer, dict):
            raise TypeError(f"ask() must return a dict; got {type(answer).__name__}")
        status = str(answer.get("status", "")).casefold()
        if status not in {"answered", "abstained"}:
            raise ValueError(f"Case {case['id']!r}: unexpected ask() status {status!r}")
        citations = answer.get("citations", [])
        if not isinstance(citations, list):
            citations = []
        predictions[str(case["id"])] = {
            "status": status,
            "answer": str(answer.get("answer", "")),
            "citations": citations,
            "retrieval": retrieved if isinstance(retrieved, list) else [],
            "retrieved_pages_reported_by_ask": answer.get("retrieved_pages", []),
            "mode": answer.get("mode"),
            "diagnostics": answer.get("diagnostics"),
            "timing_ms": {
                "retrieve": retrieval_ms,
                "ask_including_internal_retrieval": ask_ms,
                "case_total": total_ms,
            },
        }
        if args.compare_baseline:
            baseline = qa.retrieve(question, top_k=args.top_k, strategy="baseline")
            baseline_predictions[str(case["id"])] = {
                "status": "answered",
                "answer": "",
                "citations": [],
                "retrieval": baseline if isinstance(baseline, list) else [],
            }

        if args.diagnose_retrieval:
            if case["answerable"]:
                all_support_pages = [
                    page for fact in case["required_facts"] for page in fact["pages"]
                ]
                full_retrieval = None
                if page_count is not None:
                    full_k = page_count
                else:
                    full_k = max(all_support_pages, default=args.top_k)
                if full_k > args.top_k:
                    rows = qa.retrieve(question, top_k=full_k, strategy=args.strategy)
                    full_retrieval = rows if isinstance(rows, list) else []
                diagnosis[str(case["id"])] = _diagnose_case(
                    case, predictions[str(case["id"])], full_retrieval, page_count, qa
                )
            else:
                diagnosis[str(case["id"])] = {
                    "label": (
                        "correct_abstention"
                        if predictions[str(case["id"])]["status"] == "abstained"
                        else "false_answer"
                    )
                }
        if args.progress:
            print(
                f"[{case['id']}] {answer.get('mode', 'unknown')}/{status} "
                f"{total_ms:.1f} ms",
                file=sys.stderr,
                flush=True,
            )

    report = evaluate_cases(gold_cases, predictions, top_k=args.top_k, diagnosis=diagnosis)
    if args.compare_baseline:
        base_report = evaluate_cases(gold_cases, baseline_predictions, top_k=args.top_k)
        report["retrieval_comparison"] = {
            "baseline": {
                key: base_report["metrics"][key]
                for key in ("retrieval_recall_at_k", "all_evidence_at_k", "ndcg_at_k")
            },
            args.strategy: {
                key: report["metrics"][key]
                for key in ("retrieval_recall_at_k", "all_evidence_at_k", "ndcg_at_k")
            },
        }
    coverage = None
    coverage_method = getattr(qa, "coverage_report", None)
    if callable(coverage_method):
        coverage = coverage_method()
        if isinstance(coverage, dict) and coverage.get("pdf"):
            coverage["pdf"] = _display_path(Path(str(coverage["pdf"])))
    coverage_pages = coverage.get("pages", []) if isinstance(coverage, dict) else []
    coverage_summary = {
        "page_count": page_count,
        "pages_with_evidence": (
            coverage.get("pages_with_evidence") if isinstance(coverage, dict) else None
        ),
        "pages_without_evidence": (
            coverage.get("pages_without_evidence") if isinstance(coverage, dict) else None
        ),
        "page_status_counts": dict(
            Counter(str(row.get("status", "unknown")) for row in coverage_pages if isinstance(row, dict))
        ),
    }
    pdf_sha256 = hashlib.sha256(args.pdf.read_bytes()).hexdigest()
    gold_sha256 = hashlib.sha256(args.gold.read_bytes()).hexdigest()
    report["metadata"] = {
        "pdf": _display_path(args.pdf),
        "pdf_sha256": pdf_sha256,
        "gold": _display_path(args.gold),
        "gold_sha256": gold_sha256,
        "strategy": args.strategy,
        "model_config": args.model_config,
        "ocr_visuals_requested": args.ocr_visuals,
        "page_count_inferred": page_count,
        "coverage_summary": coverage_summary,
        "coverage_report": coverage,
        "answer_matching": "case-insensitive token-bounded aliases; lexical proxy only",
        "citation_matching": "citation page IDs checked against human gold pages; quote entailment not automated",
    }
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=PROJECT_ROOT / "data" / "Kirana_Logistics_Annual_Report_2025.pdf")
    parser.add_argument("--gold", type=Path, default=PROJECT_ROOT / "data" / "a1_gold.json")
    parser.add_argument("--limit", type=int, default=None, help="evaluate the first N gold cases")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--strategy", choices=("structured", "baseline"), default="structured")
    parser.add_argument("--model-config", type=_read_json_arg, default=None, help="inline JSON or JSON file passed to DocumentQA.from_pdf")
    parser.add_argument("--ocr-visuals", action="store_true", help="enable the app's optional visual OCR during ingestion")
    parser.add_argument("--compare-baseline", action="store_true", help="compare baseline and chosen strategy for retrieval metrics only")
    parser.add_argument("--diagnose-retrieval", action="store_true", help="perform extra full-depth retrieval to distinguish rank misses from coverage misses")
    parser.add_argument("--progress", action="store_true", help="print each completed case and elapsed time to stderr")
    parser.add_argument("--output-dir", type=Path, default=None, help="write report.json and report.md here")
    parser.add_argument("--json", action="store_true", help="print JSON instead of Markdown")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.top_k < 1 or (args.limit is not None and args.limit < 1):
        parser.error("--top-k and --limit must be positive")
    for path, label in ((args.pdf, "PDF"), (args.gold, "gold file")):
        if not path.is_file():
            parser.error(f"{label} does not exist: {path}")
    report = run_evaluation(args)
    markdown = render_markdown(report)
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (args.output_dir / "report.md").write_text(markdown, encoding="utf-8")
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

