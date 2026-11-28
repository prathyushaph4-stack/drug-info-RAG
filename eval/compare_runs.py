"""Before/after table: plain retrieval versus drug-aware (routed) retrieval.

Run from the project root, after BOTH of these have been run:
    python eval/evaluate_retrieval.py            # baseline  -> eval/results/
    python eval/evaluate_retrieval.py --routed   # routed    -> eval/results/routed/
    python eval/compare_runs.py
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing {path}. Run evaluate_retrieval.py (with and without --routed) first.")
    summary = json.loads(path.read_text())["summary"]
    if any("all@5" not in metrics for metrics in summary.values()):
        raise SystemExit(f"{path} was made by an older evaluate_retrieval.py. Re-run it (with and without --routed).")
    return summary


def arrow(before: float, after: float) -> str:
    return f"{before:.2f} -> {after:.2f}"


def compare(before: dict, after: dict) -> str:
    lines = [
        "## Before vs after",
        "",
        "| Setup | all@3 | all@5 | interaction all@3 | hit@3 | MRR | avg ms |",
        "|---|---|---|---|---|---|---|",
    ]
    for setup in sorted(before, key=lambda s: after[s]["all@3"], reverse=True):
        b, a = before[setup], after[setup]
        lines.append(
            f"| {setup} | {arrow(b['all@3'], a['all@3'])} | {arrow(b['all@5'], a['all@5'])} | "
            f"{arrow(b['all@3_by_type'].get('interaction', 0), a['all@3_by_type'].get('interaction', 0))} | "
            f"{arrow(b['hit@3'], a['hit@3'])} | {arrow(b['mrr'], a['mrr'])} | "
            f"{b['avg_ms']:.0f} -> {a['avg_ms']:.0f} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two evaluation runs (folders with results.json).")
    parser.add_argument("--before", default=str(ROOT / "eval" / "results"))
    parser.add_argument("--after", default=str(ROOT / "eval" / "results" / "routed"))
    args = parser.parse_args()
    before_dir, after_dir = Path(args.before), Path(args.after)
    table = compare(load(before_dir / "results.json"), load(after_dir / "results.json"))
    (after_dir / "comparison.md").write_text(table)
    print(table)


if __name__ == "__main__":
    main()