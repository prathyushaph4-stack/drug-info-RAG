"""Helper for fixing gold-set evidence phrases.

Shows where a word or phrase appears in a drug's real label, with the
surrounding text, so you can copy the exact wording into eval/gold_set.json.

Run from the project root:
    python eval/find_evidence.py metformin "maximum"
    python eval/find_evidence.py warfarin "nsaid" --width 150
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from chunking import clean_text  # noqa: E402


def find(drug: str, phrase: str, raw_dir: Path, width: int, limit: int) -> None:
    path = raw_dir / f"{drug.replace(' ', '_')}.json"
    if not path.exists():
        sys.exit(f"No label file for '{drug}' in {raw_dir}")
    record = json.loads(path.read_text())
    shown = 0
    for section, raw in record["sections"].items():
        text = clean_text(raw)
        for match in re.finditer(re.escape(phrase), text, flags=re.IGNORECASE):
            start, end = max(0, match.start() - width), min(len(text), match.end() + width)
            print(f"[{section}] ...{text[start:end]}...\n")
            shown += 1
            if shown >= limit:
                return
    if shown == 0:
        print(f"'{phrase}' not found in the {drug} label.")
        print("Sections available:", ", ".join(record["sections"]))


def count_sections(drug: str, phrase: str, raw_dir: Path) -> None:
    """One line: in which sections of the label does the phrase appear, and how often."""
    path = raw_dir / f"{drug.replace(' ', '_')}.json"
    if not path.exists():
        sys.exit(f"No label file for '{drug}' in {raw_dir}")
    record = json.loads(path.read_text())
    counts = {
        section: len(re.findall(re.escape(phrase), clean_text(text), flags=re.IGNORECASE))
        for section, text in record["sections"].items()
    }
    hits = ", ".join(f"{section}={n}" for section, n in counts.items() if n)
    print(f"{drug} / '{phrase}': {hits or 'not found'}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("drug")
    parser.add_argument("phrase")
    parser.add_argument("--width", type=int, default=100, help="characters of context on each side")
    parser.add_argument("--limit", type=int, default=5, help="maximum matches to show")
    parser.add_argument("--raw-dir", default=str(ROOT / "data" / "raw"))
    parser.add_argument("--count", action="store_true", help="only list which sections contain the phrase")
    args = parser.parse_args()
    if args.count:
        count_sections(args.drug, args.phrase, Path(args.raw_dir))
    else:
        find(args.drug, args.phrase, Path(args.raw_dir), args.width, args.limit)


if __name__ == "__main__":
    main()