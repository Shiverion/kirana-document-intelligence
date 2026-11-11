from __future__ import annotations

import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from evals.metrics import alias_in_text, evaluate_cases, render_markdown, unique_ranked_pages
from evals.run import _load_gold


def _temporary_directory():
    return TemporaryDirectory(prefix=".a1-test-", dir=Path(__file__).resolve().parents[1])


def test_alias_match_uses_token_boundaries_and_numeric_precision() -> None:
    assert alias_in_text("41.6 million", "We delivered 41.6 million parcels.")
    assert alias_in_text("THB", "Revenue: thb 8,420 million")
    assert alias_in_text("82", "The errata gives the corrected value as 82.")
    assert alias_in_text("corrected", "The corrected. number is 82.")
    assert not alias_in_text("44", "Fleet total: 144 trucks")
    assert not alias_in_text("186", "THB 1,186 million")
    assert alias_in_text("1,186", "THB 1,186 million")
    assert not alias_in_text("5.2", "The reading was 5.20")
    assert not alias_in_text("15%", "The discount is 15 percent")


def test_page_ranking_deduplicates_and_keeps_first_rank() -> None:
    rows = [{"page": 2}, {"page": 2}, {"page": 3}, {"page": 1}]
    assert unique_ranked_pages(rows, 3) == [2, 3, 1]


def test_metrics_report_expected_denominators_and_proxies() -> None:
    gold = [
        {
            "id": "A",
            "question": "What happened?",
            "category": "cross_page",
            "answerable": True,
            "required_facts": [
                {"id": "f1", "aliases": ["alpha 1"], "pages": [2, 3]},
                {"id": "f2", "aliases": ["beta 2"], "pages": [4]},
            ],
        },
        {
            "id": "B",
            "question": "Who is the CFO?",
            "category": "unsupported",
            "answerable": False,
            "required_facts": [],
        },
    ]
    predictions = {
        "A": {
            "status": "answered",
            "answer": "alpha 1 and beta 2",
            "retrieval": [{"page": 1}, {"page": 2}, {"page": 2}, {"page": 4}],
            "citations": [{"page": 2, "quote": "alpha"}, {"page": 9, "quote": "other"}],
        },
        "B": {"status": "abstained", "answer": "", "retrieval": [], "citations": []},
    }
    report = evaluate_cases(gold, predictions, top_k=3)
    metrics = report["metrics"]
    assert metrics["retrieval_recall_at_k"] == 1.0
    assert metrics["all_evidence_at_k"] == 1.0
    assert metrics["atomic_answer_fact_recall"] == 1.0
    assert metrics["citation_page_support_precision_proxy"] == 0.5
    assert metrics["citation_evidence_completeness"] == 0.5
    assert metrics["citation_page_support_precision_proxy"] == 0.5
    assert metrics["strict_answer_pass_rate"] == 1.0
    assert metrics["strict_answer_pass_count"] == 1
    assert metrics["strict_answer_denominator"] == 1
    assert metrics["grounded_strict_pass_rate"] == 0.5
    assert metrics["grounded_strict_pass_count"] == 1
    assert metrics["abstention_recall"] == 1.0
    assert metrics["false_abstention_rate"] == 0.0
    assert metrics["coverage"] == 0.5
    assert metrics["selective_error_rate"] == 0.0
    expected_ndcg = (1 / math.log2(3) + 1 / math.log2(4)) / (
        1 + 1 / math.log2(3) + 1 / math.log2(4)
    )
    assert metrics["ndcg_at_k"] == pytest.approx(expected_ndcg)
    assert "page-hit proxy" in render_markdown(report)


def test_gold_file_has_twenty_cases_and_four_refusals() -> None:
    project_root = Path(__file__).resolve().parents[1]
    cases = _load_gold(project_root / "data" / "a1_gold.json", None)
    assert len(cases) == 20
    assert sum(not case["answerable"] for case in cases) == 4
    assert cases[0]["id"] == "K01"
    assert cases[-1]["id"] == "K20"


def test_gold_schema_rejects_empty_aliases_and_duplicate_ids() -> None:
    with _temporary_directory() as temp_dir:
        path = Path(temp_dir) / "gold.json"
        _test_invalid_gold(path)


def _test_invalid_gold(path: Path) -> None:
    invalid = [
        {
            "id": "A",
            "question": "Question?",
            "category": "table",
            "answerable": True,
            "required_facts": [{"id": "f", "aliases": [], "pages": [1]}],
        }
    ]
    path.write_text(json.dumps(invalid), encoding="utf-8")
    with pytest.raises(ValueError, match="aliases"):
        _load_gold(path, None)


def test_answerable_prediction_requires_every_fact_group() -> None:
    gold = [
        {
            "id": "A",
            "question": "Q",
            "category": "table",
            "answerable": True,
            "required_facts": [
                {"id": "x", "aliases": ["x"], "pages": [1]},
                {"id": "y", "aliases": ["y"], "pages": [2]},
            ],
        }
    ]
    report = evaluate_cases(
        gold,
        {"A": {"status": "answered", "answer": "x", "retrieval": [], "citations": []}},
    )
    assert report["cases"][0]["answer_strict_pass"] is False
    assert report["cases"][0]["grounded_strict_pass"] is False
    assert report["metrics"]["atomic_answer_fact_recall"] == 0.5


def test_citations_on_unanswerable_cases_count_as_unsupported() -> None:
    gold = [
        {
            "id": "A",
            "question": "Who was the CFO?",
            "category": "unsupported",
            "answerable": False,
            "required_facts": [],
        }
    ]
    report = evaluate_cases(
        gold,
        {"A": {"status": "answered", "answer": "CEO", "retrieval": [], "citations": [{"page": 2, "quote": "CEO"}]}},
    )
    assert report["metrics"]["citation_page_support_precision_proxy"] == 0.0
    assert report["metrics"]["grounded_strict_pass_rate"] == 0.0


def test_abstention_text_does_not_receive_answer_fact_credit() -> None:
    gold = [
        {
            "id": "A",
            "question": "What was the figure?",
            "category": "table",
            "answerable": True,
            "required_facts": [{"id": "figure", "aliases": ["96"], "pages": [1]}],
        }
    ]
    report = evaluate_cases(
        gold,
        {
            "A": {
                "status": "abstained",
                "answer": "I cannot answer, though a nearby number is 96.",
                "retrieval": [{"page": 1}],
                "citations": [],
            }
        },
    )
    assert report["metrics"]["atomic_answer_fact_recall"] == 0.0
    assert report["cases"][0]["answer_fact_hits"] == 0

