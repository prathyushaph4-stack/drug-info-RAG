"""Checks eval/gold_set.json before it is used for evaluation.

Run from the project root:
    python eval/validate_gold.py

It checks the format, and (the useful part) that every evidence phrase really
appears in that drug's label text in data/raw/, so typos are caught early.

How a retrieved chunk is judged relevant later (Step 7):
    chunk.drug == relevant.drug  AND  one of the evidence phrases appears in chunk.text
This does not depend on where chunk boundaries fall, so both chunking styles
are compared fairly.
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from chunking import clean_text  # noqa: E402
from drugs import DRUGS  # noqa: E402

TYPES = {"dosage", "indication", "side_effect", "warning", "contraindication", "interaction", "trap"}
BEHAVIORS = {"answer", "refuse", "not_found"}


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def load_label_text(raw_dir: Path) -> dict[str, str]:
    """drug name -> all its cleaned label text, lowercase."""
    labels = {}
    for path in raw_dir.glob("*.json"):
        record = json.loads(path.read_text())
        text = " ".join(clean_text(t) for t in record["sections"].values())
        labels[record["drug"]] = normalize(text)
    return labels


def validate(questions: list[dict], labels: dict[str, str] | None) -> list[str]:
    errors = []
    seen_ids = set()
    for i, q in enumerate(questions, start=1):
        tag = q.get("id", f"#{i}")
        for field in ("id", "type", "question", "relevant", "answer_points", "expected_behavior"):
            if field not in q:
                errors.append(f"{tag}: missing field '{field}'")
        if q.get("id") in seen_ids:
            errors.append(f"{tag}: duplicate id")
        seen_ids.add(q.get("id"))
        if q.get("type") not in TYPES:
            errors.append(f"{tag}: type must be one of {sorted(TYPES)}")
        if q.get("expected_behavior") not in BEHAVIORS:
            errors.append(f"{tag}: expected_behavior must be one of {sorted(BEHAVIORS)}")
        if not str(q.get("question", "")).strip():
            errors.append(f"{tag}: question is empty")
        if not q.get("answer_points"):
            errors.append(f"{tag}: answer_points is empty")

        relevant = q.get("relevant", [])
        if q.get("type") == "trap":
            if q.get("expected_behavior") == "answer":
                errors.append(f"{tag}: a trap question should expect 'refuse' or 'not_found'")
            continue
        if q.get("expected_behavior") != "answer":
            errors.append(f"{tag}: non-trap questions should expect 'answer'")
        if not relevant:
            errors.append(f"{tag}: 'relevant' is empty (only trap questions may leave it empty)")
        if q.get("type") == "interaction" and len({r.get("drug") for r in relevant}) < 2:
            errors.append(f"{tag}: interaction questions should list both drugs in 'relevant'")
        for r in relevant:
            drug, evidence = r.get("drug"), r.get("evidence", [])
            if drug not in DRUGS:
                errors.append(f"{tag}: drug '{drug}' is not in src/drugs.py")
                continue
            if not evidence:
                errors.append(f"{tag}: {drug} has no evidence phrases")
            for phrase in evidence:
                if labels is not None and normalize(phrase) not in labels.get(drug, ""):
                    errors.append(f"{tag}: evidence '{phrase}' not found in the {drug} label")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", default=str(ROOT / "eval" / "gold_set.json"))
    parser.add_argument("--raw-dir", default=str(ROOT / "data" / "raw"))
    args = parser.parse_args()

    questions = json.loads(Path(args.gold).read_text())
    raw_dir = Path(args.raw_dir)
    labels = load_label_text(raw_dir) if any(raw_dir.glob("*.json")) else None
    if labels is None:
        print("(No labels in data/raw/, so evidence phrases were NOT checked against the label text.)")

    errors = validate(questions, labels)
    counts = Counter(q.get("type") for q in questions)
    print(f"{len(questions)} questions: " + ", ".join(f"{t}={n}" for t, n in sorted(counts.items())))
    if errors:
        print(f"\n{len(errors)} problem(s) found:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("All questions look good.")


if __name__ == "__main__":
    main()