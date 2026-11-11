"""Deterministic metrics for evidence retrieval and answer evaluation.

Answer matching uses case-insensitive, token-boundary alias matching. It is a
lexical proxy; it does not establish semantic equivalence or entailment.
Citation support is likewise a page-hit proxy against human-labeled gold pages.
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any


def _squash_whitespace(value: str) -> str:
    return " ".join(value.casefold().split())


def alias_in_text(alias: str, text: str) -> bool:
    """Return whether *alias* occurs as a case-insensitive token-bounded phrase.

    Punctuation inside aliases is kept literal. Numeric aliases therefore
    distinguish values such as ``5.2`` and ``5.20`` instead of matching a
    numeric prefix. Whitespace differences are ignored.
    """
    needle = _squash_whitespace(alias)
    haystack = _squash_whitespace(text)
    if not needle:
        return False
    pattern = re.compile(
        rf"{_alias_boundary_pattern(needle)}",
        flags=re.IGNORECASE,
    )
    return pattern.search(haystack) is not None


def _alias_boundary_pattern(needle: str) -> str:
    escaped = re.escape(needle)
    # Sentence punctuation around a value is harmless (for example, ``82.``).
    # A comma or decimal point next to another digit, however, is part of a
    # larger number and must not make a shorter alias match inside it.
    if re.fullmatch(r"\d[\d.,]*", needle):
        return rf"(?<!\w)(?<!\d,)(?<!\d\.){escaped}(?!\w)(?![,.]\d)"
    return rf"(?<!\w){escaped}(?!\w)"


def fact_is_present(fact: Mapping[str, Any], text: str) -> bool:
    aliases = fact.get("aliases", [])
    return any(alias_in_text(str(alias), text) for alias in aliases)


def unique_ranked_pages(retrieved: Sequence[Any], top_k: int) -> list[int]:
    """Read and deduplicate 1-based page IDs while preserving ranking order."""
    pages: list[int] = []
    seen: set[int] = set()
    for row in retrieved:
        if isinstance(row, Mapping):
            page = row.get("page")
        else:
            page = getattr(row, "page", None)
        if isinstance(page, bool) or not isinstance(page, int) or page < 1:
            continue
        if page not in seen:
            seen.add(page)
            pages.append(page)
        if len(pages) >= top_k:
            break
    return pages


def _group_hit(fact: Mapping[str, Any], pages: Iterable[int]) -> bool:
    return bool(set(fact.get("pages", [])) & set(pages))


def _ndcg_at_k(ranked_pages: Sequence[int], relevant_pages: set[int], k: int) -> float:
    if not relevant_pages:
        return 0.0
    dcg = sum(
        1.0 / math.log2(rank + 2)
        for rank, page in enumerate(ranked_pages[:k])
        if page in relevant_pages
    )
    ideal_hits = min(len(relevant_pages), k)
    idcg = sum(1.0 / math.log2(rank + 2) for rank in range(ideal_hits))
    return dcg / idcg if idcg else 0.0


def evaluate_cases(
    gold_cases: Sequence[Mapping[str, Any]],
    predictions: Mapping[str, Mapping[str, Any]],
    *,
    top_k: int = 5,
    diagnosis: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Score predictions keyed by gold case ID and return JSON-ready details.

    Retrieval metrics use only answerable cases with one or more required fact
    groups. Evidence Recall@k is macro evidence-group coverage per answerable
    case; the micro pooled rate is reported separately. All Evidence@k is the
    share of answerable cases whose every group is covered. nDCG@k uses binary
    relevance on the union of distinct gold support pages per answerable case.
    """
    if top_k < 1:
        raise ValueError("top_k must be positive")

    answerable_cases = [c for c in gold_cases if c["answerable"]]
    unanswerable_cases = [c for c in gold_cases if not c["answerable"]]
    details: list[dict[str, Any]] = []
    evidence_group_hits = 0
    evidence_group_total = 0
    case_recalls: list[float] = []
    all_evidence_hits = 0
    ndcgs: list[float] = []
    answer_fact_hits = 0
    answer_fact_total = 0
    cited_supported = 0
    cited_total = 0
    citation_group_hits = 0
    citation_group_total = 0
    answer_strict_passes = 0
    grounded_strict_passes = 0
    false_abstentions = 0
    abstention_hits = 0
    answered_total = 0
    selective_errors = 0

    for case in gold_cases:
        case_id = str(case["id"])
        if case_id not in predictions:
            raise ValueError(f"Missing prediction for case {case_id!r}")
        prediction = predictions[case_id]
        status = str(prediction.get("status", "")).casefold()
        if status not in {"answered", "abstained"}:
            raise ValueError(f"Case {case_id!r}: status must be answered or abstained")
        facts = list(case.get("required_facts", []))
        retrieved = unique_ranked_pages(prediction.get("retrieval", []), top_k)
        cited_rows = prediction.get("citations", []) or []
        if not isinstance(cited_rows, list):
            cited_rows = []
        cited_pages: list[int] = []
        for citation in cited_rows:
            page = citation.get("page") if isinstance(citation, Mapping) else None
            if isinstance(page, int) and not isinstance(page, bool) and page >= 1:
                cited_pages.append(page)
        cited_page_set = set(cited_pages)
        relevant_pages = {
            int(page)
            for fact in facts
            for page in fact.get("pages", [])
            if isinstance(page, int) and not isinstance(page, bool) and page >= 1
        }
        retrieved_group_hits = sum(_group_hit(fact, retrieved) for fact in facts)
        citation_group_hits_case = sum(_group_hit(fact, cited_page_set) for fact in facts)
        answer_text = str(prediction.get("answer", ""))
        fact_answer_hits = (
            sum(fact_is_present(fact, answer_text) for fact in facts)
            if status == "answered"
            else 0
        )

        if case["answerable"]:
            if not facts:
                raise ValueError(f"Answerable case {case_id!r} must have required_facts")
            evidence_group_hits += retrieved_group_hits
            evidence_group_total += len(facts)
            case_recalls.append(retrieved_group_hits / len(facts))
            all_evidence_hits += retrieved_group_hits == len(facts)
            ndcgs.append(_ndcg_at_k(retrieved, relevant_pages, top_k))
            answer_fact_hits += fact_answer_hits
            answer_fact_total += len(facts)
            citation_group_hits += citation_group_hits_case
            citation_group_total += len(facts)
            cited_supported += sum(page in relevant_pages for page in cited_pages)
            cited_total += len(cited_rows)
            if status == "abstained":
                false_abstentions += 1
            if status == "answered":
                answered_total += 1
                if fact_answer_hits != len(facts):
                    selective_errors += 1
            citation_complete = citation_group_hits_case == len(facts)
            answer_strict_pass = (
                status == "answered"
                and fact_answer_hits == len(facts)
            )
            grounded_strict_pass = answer_strict_pass and citation_complete
            answer_strict_passes += answer_strict_pass
        else:
            if facts:
                raise ValueError(f"Unanswerable case {case_id!r} must have no required_facts")
            citation_complete = not cited_rows
            answer_strict_pass = None
            grounded_strict_pass = status == "abstained" and citation_complete
            # A citation on an unanswerable question cannot be supported by
            # the gold report, so include it as a false positive in precision.
            cited_total += len(cited_rows)
            if status == "abstained":
                abstention_hits += 1
            else:
                answered_total += 1
                selective_errors += 1

        grounded_strict_passes += grounded_strict_pass
        row = {
            "id": case_id,
            "question": case.get("question", ""),
            "category": case.get("category", ""),
            "answerable": bool(case["answerable"]),
            "status": status,
            "retrieved_pages_at_k": retrieved,
            "retrieved_evidence_groups": retrieved_group_hits,
            "required_evidence_groups": len(facts),
            "answer_fact_hits": fact_answer_hits,
            "answer_fact_total": len(facts),
            "citation_pages": cited_pages,
            "citation_evidence_groups": citation_group_hits_case,
            "citation_complete": citation_complete,
            "answer_strict_pass": answer_strict_pass,
            "grounded_strict_pass": grounded_strict_pass,
            "answer": answer_text,
            "citations": cited_rows,
            "mode": prediction.get("mode"),
            "diagnostics": prediction.get("diagnostics"),
            "timing_ms": prediction.get("timing_ms"),
        }
        if diagnosis and case_id in diagnosis:
            row["retrieval_diagnosis"] = diagnosis[case_id]
        details.append(row)

    total_cases = len(gold_cases)
    metrics = {
        "case_count": total_cases,
        "answerable_count": len(answerable_cases),
        "unanswerable_count": len(unanswerable_cases),
        "top_k": top_k,
        "retrieval_recall_at_k": (
            sum(case_recalls) / len(case_recalls) if case_recalls else None
        ),
        "retrieval_recall_micro_at_k": (
            evidence_group_hits / evidence_group_total if evidence_group_total else None
        ),
        "all_evidence_at_k": (
            all_evidence_hits / len(answerable_cases) if answerable_cases else None
        ),
        "ndcg_at_k": sum(ndcgs) / len(ndcgs) if ndcgs else None,
        "atomic_answer_fact_recall": (
            answer_fact_hits / answer_fact_total if answer_fact_total else None
        ),
        "citation_page_support_precision_proxy": (
            cited_supported / cited_total if cited_total else None
        ),
        "citation_evidence_completeness": (
            citation_group_hits / citation_group_total if citation_group_total else None
        ),
        "strict_answer_pass_rate": (
            answer_strict_passes / len(answerable_cases) if answerable_cases else None
        ),
        "strict_answer_pass_count": answer_strict_passes,
        "strict_answer_failure_count": len(answerable_cases) - answer_strict_passes,
        "strict_answer_denominator": len(answerable_cases),
        "grounded_strict_pass_rate": (
            grounded_strict_passes / total_cases if total_cases else None
        ),
        "grounded_strict_pass_count": grounded_strict_passes,
        "grounded_strict_failure_count": total_cases - grounded_strict_passes,
        "grounded_strict_denominator": total_cases,
        "abstention_recall": (
            abstention_hits / len(unanswerable_cases) if unanswerable_cases else None
        ),
        "false_abstention_rate": (
            false_abstentions / len(answerable_cases) if answerable_cases else None
        ),
        "coverage": answered_total / total_cases if total_cases else None,
        "selective_error_rate": (
            selective_errors / answered_total if answered_total else None
        ),
    }
    latency_values: dict[str, list[float]] = {}
    for case in details:
        for name, value in (case.get("timing_ms") or {}).items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                latency_values.setdefault(str(name), []).append(float(value))
    if latency_values:
        import statistics

        latency_summary: dict[str, dict[str, float]] = {}
        for name, values in latency_values.items():
            ordered = sorted(values)
            p95_index = max(0, math.ceil(0.95 * len(ordered)) - 1)
            latency_summary[name] = {
                "mean_ms": statistics.fmean(values),
                "median_ms": statistics.median(values),
                "p95_ms": ordered[p95_index],
            }
        metrics["latency"] = latency_summary
    return {"metrics": metrics, "cases": details}


def render_markdown(report: Mapping[str, Any]) -> str:
    """Render a compact human-readable report with definitions and failures."""
    metrics = report["metrics"]
    metadata = report.get("metadata", {})
    lines = [
        "# Document QA evaluation",
        "",
        f"Cases: {metrics['case_count']} total, {metrics['answerable_count']} answerable, "
        f"{metrics['unanswerable_count']} unanswerable. Retrieval cutoff: k={metrics['top_k']}.",
        "",
    ]
    if metadata:
        coverage = metadata.get("coverage_summary", {})
        lines.extend(
            [
                f"PDF SHA256: `{metadata.get('pdf_sha256', 'unknown')}`.",
                f"Gold SHA256: `{metadata.get('gold_sha256', 'unknown')}`.",
                f"Strategy: `{metadata.get('strategy', 'unknown')}`; visual OCR requested: "
                f"`{metadata.get('ocr_visuals_requested', False)}`; page coverage: "
                f"{coverage.get('pages_with_evidence', 'unknown')}/{coverage.get('page_count', 'unknown')} pages with evidence; "
                f"statuses: `{coverage.get('page_status_counts', {})}`.",
                "",
            ]
        )
    if "retrieval_comparison" in report:
        comparison = report["retrieval_comparison"]
        lines.extend(
            [
                "## Retrieval strategy comparison",
                "",
                "| Strategy | Evidence-group Recall@k | All Evidence@k | nDCG@k |",
                "|---|---:|---:|---:|",
            ]
        )
        for strategy, values in comparison.items():
            lines.append(
                f"| {strategy} | {_fmt_metric(values.get('retrieval_recall_at_k'))} | "
                f"{_fmt_metric(values.get('all_evidence_at_k'))} | "
                f"{_fmt_metric(values.get('ndcg_at_k'))} |"
            )
        lines.append("")
    lines.extend(
        [
        "| Metric | Score |",
        "|---|---:|",
        ]
    )
    labels = [
        ("Evidence-group Recall@k", "retrieval_recall_at_k"),
        ("Evidence-group Recall@k (micro pooled)", "retrieval_recall_micro_at_k"),
        ("All Evidence@k", "all_evidence_at_k"),
        ("nDCG@k", "ndcg_at_k"),
        ("Atomic answer fact recall (lexical proxy)", "atomic_answer_fact_recall"),
        ("Citation page support precision (page-hit proxy)", "citation_page_support_precision_proxy"),
        ("Citation evidence completeness", "citation_evidence_completeness"),
        ("Strict answer pass rate (answerable cases)", "strict_answer_pass_rate"),
        ("Grounded strict pass rate (all cases)", "grounded_strict_pass_rate"),
        ("Abstention recall", "abstention_recall"),
        ("False abstention rate", "false_abstention_rate"),
        ("Coverage", "coverage"),
        ("Selective error rate", "selective_error_rate"),
    ]
    for label, key in labels:
        score = _fmt_metric(metrics.get(key))
        if key == "strict_answer_pass_rate":
            score += f" ({metrics['strict_answer_pass_count']}/{metrics['strict_answer_denominator']})"
        elif key == "grounded_strict_pass_rate":
            score += f" ({metrics['grounded_strict_pass_count']}/{metrics['grounded_strict_denominator']})"
        lines.append(f"| {label} | {score} |")
    for name, summary in metrics.get("latency", {}).items():
        lines.append(
            f"| Latency {name} (mean / median / p95 ms) | "
            f"{summary['mean_ms']:.1f} / {summary['median_ms']:.1f} / {summary['p95_ms']:.1f} |"
        )
    lines.extend(
        [
            "",
            "Definitions: Evidence Recall@k is the macro average, by answerable case, of required evidence groups covered; a group is covered if any accepted gold page is retrieved. The micro pooled rate is also shown. All Evidence@k is the fraction of answerable cases with all groups covered. nDCG@k uses binary relevance over the union of distinct gold support pages. Atomic answer recall matches any listed alias as a case-insensitive token-bounded phrase; this is a lexical proxy, not semantic judging. Strict answer pass is answerable cases answered with every required alias present, over answerable cases only. Grounded strict pass adds citation page completeness for answerable cases and correct abstention for unanswerable cases, over all cases. Citation precision and completeness use cited page IDs against gold support pages; quote text is not judged for entailment. Coverage is the share of all cases answered; selective error is the error share among answered cases.",
            "",
            "## Per-case results",
            "",
        "| ID | Type / category | Status | Retrieval evidence | Answer facts | Citation evidence | Answer strict | Grounded strict | Retrieved pages | Mode | Diagnosis |",
        "|---|---|---|---:|---:|---:|---|---|---|---|---|",
        ]
    )
    for case in report["cases"]:
        kind = "answerable" if case["answerable"] else "unanswerable"
        case_type = f"{kind} / {case.get('category', '')}"
        diagnosis = case.get("retrieval_diagnosis", {}).get("label", "")
        lines.append(
            f"| {case['id']} | {case_type} | {case['status']} | "
            f"{case['retrieved_evidence_groups']}/{case['required_evidence_groups']} | "
            f"{case['answer_fact_hits']}/{case['answer_fact_total']} | "
            f"{case['citation_evidence_groups']}/{case['required_evidence_groups']} | "
            f"{'—' if case['answer_strict_pass'] is None else ('PASS' if case['answer_strict_pass'] else 'FAIL')} | "
            f"{'PASS' if case['grounded_strict_pass'] else 'FAIL'} | "
            f"{case['retrieved_pages_at_k']} | {case.get('mode') or ''} | {diagnosis} |"
        )
    failed = [case for case in report["cases"] if not case["grounded_strict_pass"]]
    lines.extend(["", "## Strict-pass failures", ""])
    if not failed:
        lines.append("None.")
    else:
        for case in failed:
            lines.append(f"- **{case['id']}** — {case['question']} (status: {case['status']})")
    lines.extend(["", "## Answer and citation detail", ""])
    for case in report["cases"]:
        lines.append(f"### {case['id']} · {case.get('mode') or 'unknown mode'}")
        answer = str(case.get("answer", "")).replace("\n", " ").strip()
        lines.append(f"Answer: {answer or '(empty)'}")
        citations = case.get("citations", []) or []
        if citations:
            for citation in citations:
                if isinstance(citation, Mapping):
                    lines.append(
                        f"- p.{citation.get('page', '?')}: “{str(citation.get('quote', '')).replace(chr(10), ' ').strip()}”"
                    )
        else:
            lines.append("Citations: none.")
        if case.get("diagnostics"):
            lines.append(f"Diagnostics: `{case['diagnostics']}`")
        if case.get("timing_ms"):
            timing = case["timing_ms"]
            lines.append(
                f"Latency: retrieve {timing.get('retrieve', 0):.1f} ms, "
                f"ask {timing.get('ask_including_internal_retrieval', 0):.1f} ms."
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def _fmt_metric(value: Any) -> str:
    return "n/a" if value is None else f"{float(value):.3f}"

