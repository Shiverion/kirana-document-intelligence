from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

import pytest
import pymupdf


def _make_second_pdf(path: Path) -> None:
    document = pymupdf.open()
    page_one = document.new_page(width=612, height=792)
    page_one.insert_text((72, 72), "Aurora Parcel Lab — independent test document")
    page_one.insert_text((72, 102), "Its Bluebird depot operated 73 electric vans in 2025.")
    page_two = document.new_page(width=612, height=792)
    page_two.insert_text((72, 72), "North Pier facility opened in 2024.")
    page_two.insert_text((72, 102), "The facility uses chilled storage for medicines.")
    page_two.insert_text((72, 132), "Mina Example served as Chief Executive Officer at year-end 2025.")
    page_two.insert_text((72, 162), "Planned capital expenditure for 2026 was THB 1,050 million.")
    page_two.insert_text((72, 192), "Actual capital expenditure in 2025 was THB 905 million.")
    document.save(path)
    document.close()


def _make_one_page_pdf(path: Path, text: str) -> None:
    document = pymupdf.open()
    page = document.new_page(width=612, height=792)
    page.insert_text((72, 72), text)
    document.save(path)
    document.close()


def _mock_answer_from_retrieved_quote(qa, question: str, answer: str, monkeypatch) -> dict:
    hits = qa.retrieve(question, top_k=5, strategy="structured")
    assert hits
    response = {
        "status": "answered",
        "answer": answer,
        "citations": [{"id": hits[0]["id"], "quote": hits[0]["quote"]}],
    }
    monkeypatch.setattr(
        qa,
        "_ollama_request",
        lambda payload, endpoint="/api/generate": {"response": json.dumps(response)},
    )
    return qa.ask(question, top_k=5, strategy="structured")


def _temporary_directory():
    return TemporaryDirectory(prefix=".a1-test-", dir=Path(__file__).resolve().parents[1])


def test_new_pdf_loads_and_retrieval_uses_unique_one_based_pages() -> None:
    try:
        from kirana_qa import DocumentQA
    except ImportError as exc:
        pytest.fail(f"A1 app must expose kirana_qa.DocumentQA: {exc}")

    with _temporary_directory() as temp_dir:
        pdf = Path(temp_dir) / "independent_second_document.pdf"
        _make_second_pdf(pdf)
        qa = DocumentQA.from_pdf(pdf)
        results = qa.retrieve(
            "How many electric vans operated at Bluebird depot in 2025?",
            top_k=5,
            strategy="structured",
        )

        assert isinstance(results, list) and results
        pages = [row["page"] for row in results]
        assert all(isinstance(page, int) and page in (1, 2) for page in pages)
        assert len(pages) == len(set(pages))
        assert pages[0] == 1

        answer = qa.ask(
            "How many electric vans operated at Bluebird depot in 2025?",
            top_k=5,
            strategy="structured",
        )
        assert answer["status"] == "answered"
        assert answer["citations"]
        citation_pages = [citation["page"] for citation in answer["citations"]]
        assert all(isinstance(page, int) and page in (1, 2) for page in citation_pages)
        assert len(citation_pages) == len(set(citation_pages))
        assert all(citation.get("quote", "").strip() for citation in answer["citations"])


def test_new_pdf_safely_abstains_when_requested_fact_is_absent() -> None:
    try:
        from kirana_qa import DocumentQA
    except ImportError as exc:
        pytest.fail(f"A1 app must expose kirana_qa.DocumentQA: {exc}")

    with _temporary_directory() as temp_dir:
        pdf = Path(temp_dir) / "independent_second_document.pdf"
        _make_second_pdf(pdf)
        qa = DocumentQA.from_pdf(pdf)
        answer = qa.ask(
            "What percentage discount does Schedule C give for 500 pallets?",
            top_k=5,
            strategy="structured",
        )
        assert answer["status"] == "abstained"
        assert not answer.get("citations")


@pytest.mark.parametrize(
    "question",
    [
        "Who was the Chief Financial Officer at the end of 2025?",
        "How much capital expenditure did the company actually incur in full-year 2026?",
    ],
)
def test_new_pdf_rejects_close_but_unsupported_facts(question: str) -> None:
    try:
        from kirana_qa import DocumentQA
    except ImportError as exc:
        pytest.fail(f"A1 app must expose kirana_qa.DocumentQA: {exc}")

    with _temporary_directory() as temp_dir:
        pdf = Path(temp_dir) / "independent_second_document.pdf"
        _make_second_pdf(pdf)
        qa = DocumentQA.from_pdf(pdf)
        answer = qa.ask(question, top_k=5, strategy="structured")
        assert answer["status"] == "abstained"
        assert not answer.get("citations")


def test_scope_two_question_cannot_use_scope_one_excerpt() -> None:
    try:
        from kirana_qa import DocumentQA
    except ImportError as exc:
        pytest.fail(f"A1 app must expose kirana_qa.DocumentQA: {exc}")

    with _temporary_directory() as temp_dir:
        pdf = Path(temp_dir) / "scope-number-regression.pdf"
        document = pymupdf.open()
        page = document.new_page(width=612, height=792)
        page.insert_text((72, 72), "Scope 1 greenhouse gas emissions in 2025 were 24,600 tCO2e.")
        page.insert_text((72, 102), "Scope 2 greenhouse gas emissions in 2025 were 12,100 tCO2e.")
        document.save(pdf)
        document.close()

        qa = DocumentQA.from_pdf(pdf)
        answer = qa.ask(
            "What were Scope 2 greenhouse gas emissions in 2025?",
            top_k=5,
            strategy="structured",
        )
        if answer["status"] == "answered":
            quote = answer["citations"][0]["quote"]
            assert "Scope 2" in quote
            assert "12,100" in quote
            assert "24,600" not in quote
        else:
            assert answer["status"] == "abstained"
            assert not answer.get("citations")


def test_chart_specific_question_rejects_annual_revenue_prose(monkeypatch) -> None:
    try:
        from kirana_qa import DocumentQA
    except ImportError as exc:
        pytest.fail(f"A1 app must expose kirana_qa.DocumentQA: {exc}")

    with _temporary_directory() as temp_dir:
        pdf = Path(temp_dir) / "annual-prose-only.pdf"
        _make_one_page_pdf(
            pdf,
            "Annual revenue was THB 8,420 million in 2025, and Q4 was the strongest quarter.",
        )
        qa = DocumentQA.from_pdf(pdf, model_config={"provider": "ollama", "model": "offline-test-stub"})
        question = "According to the quarterly revenue chart, what was Q4 2025 revenue in THB million?"
        answer = _mock_answer_from_retrieved_quote(
            qa,
            question,
            "Q4 2025 revenue was THB 8,420 million.",
            monkeypatch,
        )
        assert answer["status"] == "abstained"
        assert not answer.get("citations")


def test_indonesia_count_rejects_unscoped_global_fleet_total(monkeypatch) -> None:
    try:
        from kirana_qa import DocumentQA
    except ImportError as exc:
        pytest.fail(f"A1 app must expose kirana_qa.DocumentQA: {exc}")

    with _temporary_directory() as temp_dir:
        pdf = Path(temp_dir) / "global-fleet-only.pdf"
        _make_one_page_pdf(
            pdf,
            "At 31 December 2025, the global electric fleet totaled 218 vehicles.",
        )
        qa = DocumentQA.from_pdf(pdf, model_config={"provider": "ollama", "model": "offline-test-stub"})
        question = "For Indonesia, how many electric light trucks were in the fleet at the end of 2025?"
        answer = _mock_answer_from_retrieved_quote(
            qa,
            question,
            "Indonesia had 218 electric light trucks at year-end 2025.",
            monkeypatch,
        )
        assert answer["status"] == "abstained"
        assert not answer.get("citations")


def test_cli_accepts_a_new_pdf_through_the_normal_entrypoint() -> None:
    project_root = Path(__file__).resolve().parents[1]
    with _temporary_directory() as temp_dir:
        pdf = Path(temp_dir) / "independent_second_document.pdf"
        _make_second_pdf(pdf)
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "kirana_qa",
                "ask",
                "--pdf",
                str(pdf),
                "--question",
                "How many electric vans operated at Bluebird depot in 2025?",
                "--json",
            ],
            cwd=project_root,
            env=os.environ.copy(),
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert completed.returncode == 0, completed.stderr
        answer = json.loads(completed.stdout)
        assert answer["status"] == "answered"
        assert answer["citations"]
        assert all(citation["page"] in (1, 2) for citation in answer["citations"])


@pytest.mark.parametrize("bad_response", ["invented_quote", "blank_answer", "blank_refusal"])
def test_model_contract_rejects_unverifiable_responses(bad_response: str, monkeypatch) -> None:
    try:
        from kirana_qa import DocumentQA
    except ImportError as exc:
        pytest.fail(f"A1 app must expose kirana_qa.DocumentQA: {exc}")

    with _temporary_directory() as temp_dir:
        pdf = Path(temp_dir) / "independent_second_document.pdf"
        _make_second_pdf(pdf)
        qa = DocumentQA.from_pdf(pdf, model_config={"provider": "ollama", "model": "offline-test-stub"})
        question = "How many electric vans operated at Bluebird depot in 2025?"
        hit = qa.retrieve(question, top_k=5, strategy="structured")[0]
        model_response = {
            "status": "answered",
            "answer": "There were 999 electric vans.",
            "citations": [{"id": hit["id"], "quote": "Invented evidence not present in the PDF."}],
        }
        if bad_response == "blank_answer":
            model_response["answer"] = ""
            model_response["citations"][0]["quote"] = hit["evidence"]
        elif bad_response == "blank_refusal":
            model_response = {"status": "abstained", "answer": "", "citations": []}
        monkeypatch.setattr(
            qa,
            "_ollama_request",
            lambda payload, endpoint="/api/generate": {
                "response": json.dumps(model_response)
            },
        )
        result = qa.ask(question, top_k=5, strategy="structured")
        assert result["status"] == "abstained"
        assert result["answer"].strip()
        assert not result.get("citations")


def test_second_pdf_ruled_table_keeps_year_header_with_value() -> None:
    try:
        from kirana_qa import DocumentQA
    except ImportError as exc:
        pytest.fail(f"A1 app must expose kirana_qa.DocumentQA: {exc}")

    with _temporary_directory() as temp_dir:
        pdf = Path(temp_dir) / "independent_table_document.pdf"
        document = pymupdf.open()
        page = document.new_page(width=612, height=792)
        x_edges = [50, 250, 330, 410]
        y_edges = [50, 90, 130]
        for x in x_edges:
            page.draw_line((x, y_edges[0]), (x, y_edges[-1]), color=(0, 0, 0), width=1)
        for y in y_edges:
            page.draw_line((x_edges[0], y), (x_edges[-1], y), color=(0, 0, 0), width=1)
        page.insert_text((60, 76), "Metric")
        page.insert_text((265, 76), "2024")
        page.insert_text((345, 76), "2025")
        page.insert_text((60, 116), "Capital expenditure")
        page.insert_text((265, 116), "742")
        page.insert_text((345, 116), "905")
        document.save(pdf)
        document.close()

        qa = DocumentQA.from_pdf(pdf)
        rows = qa.retrieve("What was capital expenditure in 2025?", top_k=5, strategy="structured")
        evidence = "\n".join(str(row.get("evidence", "")) for row in rows).casefold()
        assert "capital expenditure" in evidence
        assert "2025=905" in "".join(evidence.split())

