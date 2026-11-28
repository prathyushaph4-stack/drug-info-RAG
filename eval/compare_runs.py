"""Before/after table: plain retrieval versus drug-aware (routed) retrieval.

Run from the project root, after BOTH of these have been run:
    python eval/evaluate_retrieval.py            # baseline  -> eval/results/
    python eval/evaluate_retrieval.py --routed   # routed    -> eval/results/routed/
    python eval/compare_runs.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BEFORE = ROOT / "eval" / "results" / "results.json"
AFTER = ROOT / "eval" / "results" / "routed" / "results.json"


def load(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing {path}. Run evaluate_retrieval.py (with and without --routed) first.")
    return json.loads(path.read_text())["summary"]


def arrow(before: float, after: float) -> str:
    return f"{before:.2f} -> {after:.2f}"


def compare(before: dict, after: dict) -> str:
    lines = [
        "## Plain vs drug-aware retrieval",
        "",
        "| Setup | all@3 | interaction all@3 | hit@3 | MRR | avg ms |",
        "|---|---|---|---|---|---|",
    ]
    for setup in sorted(before, key=lambda s: after[s]["all@3"], reverse=True):
        b, a = before[setup], after[setup]
        lines.append(
            f"| {setup} | {arrow(b['all@3'], a['all@3'])} | "
            f"{arrow(b['all@3_by_type'].get('interaction', 0), a['all@3_by_type'].get('interaction', 0))} | "
            f"{arrow(b['hit@3'], a['hit@3'])} | {arrow(b['mrr'], a['mrr'])} | "
            f"{b['avg_ms']:.0f} -> {a['avg_ms']:.0f} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    table = compare(load(BEFORE), load(AFTER))
    (AFTER.parent / "comparison.md").write_text(table)
    print(table)


if __name__ == "__main__":
    main()