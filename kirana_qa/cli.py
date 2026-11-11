from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .core import DocumentQA


def _model_config(args: argparse.Namespace) -> dict[str, Any] | None:
    if not getattr(args, "model", None):
        return None
    return {
        "provider": "ollama",
        "model": args.model,
        "base_url": args.base_url,
        "timeout": args.timeout,
        "num_ctx": args.num_ctx,
        "num_predict": args.num_predict,
        "num_gpu": args.num_gpu,
    }


def _json_print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kirana-qa", description="Ask citation-grounded questions about a PDF")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ask = subparsers.add_parser("ask", help="Ask one question about a PDF")
    ask.add_argument("--pdf", required=True, type=Path)
    ask.add_argument("--question", required=True)
    ask.add_argument("--top-k", type=int, default=5)
    ask.add_argument("--strategy", choices=("structured", "baseline"), default="structured")
    ask.add_argument("--model", help="Optional installed Ollama model (e.g. qwen3.5:4b)")
    ask.add_argument("--base-url", default="http://localhost:11434")
    ask.add_argument("--timeout", type=float, default=90)
    ask.add_argument("--num-ctx", type=int, default=3072, help="Ollama context window")
    ask.add_argument("--num-predict", type=int, default=512, help="Ollama output token limit")
    ask.add_argument("--num-gpu", type=int, help="Optional number of layers to place on the GPU")
    ask.add_argument("--ocr", action="store_true", help="Use the configured Ollama vision model to transcribe placed images")
    ask.add_argument("--json", action="store_true", dest="as_json", help="Print a machine-readable answer")

    inspect = subparsers.add_parser("inspect", help="Report extraction coverage for every PDF page")
    inspect.add_argument("--pdf", required=True, type=Path)
    inspect.add_argument("--model", help="Optional Ollama vision model for image OCR")
    inspect.add_argument("--base-url", default="http://localhost:11434")
    inspect.add_argument("--timeout", type=float, default=90)
    inspect.add_argument("--num-ctx", type=int, default=3072)
    inspect.add_argument("--num-predict", type=int, default=512)
    inspect.add_argument("--num-gpu", type=int)
    inspect.add_argument("--ocr", action="store_true", help="Transcribe placed images with the configured model")
    inspect.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        qa = DocumentQA.from_pdf(
            args.pdf,
            model_config=_model_config(args),
            ocr_visuals=bool(args.ocr),
        )
        if args.command == "inspect":
            report = qa.coverage_report()
            if args.as_json:
                _json_print(report)
            else:
                print(f"PDF: {report['pdf']} ({report['page_count']} pages)")
                print(f"Evidence available on {report['pages_with_evidence']} pages")
                for page in report["pages"]:
                    limitation = ""
                    if page["status"] == "text_extracted_visuals_not_ocr":
                        limitation = "; placed visuals were not OCRed"
                    elif page["status"] == "text_plus_ocr_visuals_unverified":
                        limitation = "; OCR output is machine transcribed and unverified"
                    elif page["status"] == "no_body_text_detected":
                        limitation = "; no body text extracted"
                    print(
                        f"Page {page['page']:>3}: {page['status']}; {page['body_chars']} text chars, "
                        f"{page['image_count']} image(s), {page['unit_count']} evidence unit(s){limitation}"
                    )
            return 0

        result = qa.ask(args.question, top_k=args.top_k, strategy=args.strategy)
        if args.as_json:
            _json_print(result)
        else:
            print(result["answer"])
            if result.get("citations"):
                print("\nCitations:")
                for citation in result["citations"]:
                    print(f"  p. {citation['page']}: {citation['quote']}")
            if result.get("diagnostics", {}).get("model_error"):
                print(f"\nModel unavailable; used extractive evidence. {result['diagnostics']['model_error']}", file=sys.stderr)
        return 0
    except Exception as exc:
        print(f"kirana-qa: {exc}", file=sys.stderr)
        return 2
