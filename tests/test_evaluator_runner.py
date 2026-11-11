from __future__ import annotations

from pathlib import Path
from typing import Any

from evals.run import _factory, build_parser


def test_model_config_and_ocr_flag_are_passed_to_document_factory() -> None:
    captured: dict[str, Any] = {}

    class FakeQA:
        @classmethod
        def from_pdf(cls, path: str, *, model_config=None, ocr_visuals=False):
            captured.update(path=path, model_config=model_config, ocr_visuals=ocr_visuals)
            return object()

    config = {"provider": "ollama", "model": "qwen3.5:4b", "num_gpu": 12}
    _factory(FakeQA, Path("second.pdf"), config, ocr_visuals=True)
    assert captured == {
        "path": "second.pdf",
        "model_config": config,
        "ocr_visuals": True,
    }


def test_cli_parser_accepts_inline_model_config() -> None:
    args = build_parser().parse_args(
        ["--pdf", "report.pdf", "--gold", "gold.json", "--model-config", '{"model":"qwen3.5:4b"}']
    )
    assert args.model_config == {"model": "qwen3.5:4b"}

