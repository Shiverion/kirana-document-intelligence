"""Apply final scope checks to recorded answers and optionally retest selected questions."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from evals.metrics import evaluate_cases
from kirana_qa import DocumentQA, validate_answer_constraints


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True, help="Full run report.json to replay")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--live", nargs="*", default=[], metavar="CASE_ID")
    args = parser.parse_args()

    recorded = read_json(args.run)
    meta = recorded["metadata"]
    pdf = Path(meta["pdf"])
    gold = Path(meta["gold"])
    for path, key in ((pdf, "pdf_sha256"), (gold, "gold_sha256")):
        if hashlib.sha256(path.read_bytes()).hexdigest() != meta[key]:
            parser.error(f"{path} differs from the recorded input")
    cases = read_json(gold)
    recorded_cases = {case["id"]: case for case in recorded["cases"]}
    cases = [case for case in cases if case["id"] in recorded_cases]
    top_k = recorded["metrics"]["top_k"]
    strategy = meta["strategy"]
    qa = DocumentQA.from_pdf(pdf, model_config=meta["model_config"], ocr_visuals=meta["ocr_visuals_requested"])
    predictions = {}
    changed = []
    live = {}
    for case in cases:
        case_id = case["id"]
        question = case["question"]
        row = recorded_cases[case_id]
        hits = qa.retrieve(question, top_k=top_k, strategy=strategy)
        if [hit["page"] for hit in hits] != row["retrieved_pages_at_k"]:
            parser.error(f"Retrieval changed for {case_id}; run a new full benchmark")
        evidence = qa.answer_evidence(question, top_k=top_k, strategy=strategy)
        previous = {key: row[key] for key in ("status", "answer", "citations")}
        result = validate_answer_constraints(question, previous, evidence)
        predictions[case_id] = {**result, "retrieval": hits}
        if result != previous:
            changed.append({"id": case_id, "previous": previous, "guarded": result})
        if case_id in args.live:
            live[case_id] = qa.ask(question, top_k=top_k, strategy=strategy)
            print(f"{case_id} live: {live[case_id]['status']} ({live[case_id].get('mode', 'unknown')})", flush=True)

    report = {
        "source_run": str(args.run),
        "method": "Deterministic post-validation replay; model responses and retrieval held fixed.",
        "changed": changed,
        "replay": evaluate_cases(cases, predictions, top_k=top_k),
        "live": live,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Replay changed {len(changed)} of {len(cases)} cases. Report: {args.output}")


if __name__ == "__main__":
    main()
