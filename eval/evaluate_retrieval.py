"""Step 7: score all 6 retrieval setups on the gold question set.

Run from the project root (after index.py and a passing validate_gold.py):
    python eval/evaluate_retrieval.py

A retrieved chunk is RELEVANT to one requirement when:
    chunk.drug == requirement.drug  AND  one evidence phrase appears in chunk.text
Trap questions are skipped here (they test the answer step, not retrieval).

Metrics (averaged over the non-trap questions):
    hit@k   at least one relevant chunk is in the top k
    all@k   EVERY required drug has a relevant chunk in the top k
            (same as hit@k for one-drug questions; stricter for interactions)
    MRR     mean of 1 / (rank of the first relevant chunk), looking at the top 10
    avg_ms  average search time per question (models already loaded)

Outputs go to eval/results/: results.md, results.json, failures.json
"""
import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "eval"))

from validate_gold import normalize  # noqa: E402

KS = (1, 3, 5)
MAX_RANK = 10


def is_relevant(chunk: dict, requirement: dict) -> bool:
    if chunk["drug"] != requirement["drug"]:
        return False
    text = normalize(chunk["text"])
    return any(normalize(phrase) in text for phrase in requirement["evidence"])


def score_question(results: list[dict], requirements: list[dict]) -> dict:
    """Score one question's ranked results against its requirements."""
    ranks = []
    for requirement in requirements:
        rank = None
        for position, chunk in enumerate(results[:MAX_RANK], start=1):
            if is_relevant(chunk, requirement):
                rank = position
                break
        ranks.append(rank)
    found = [r for r in ranks if r is not None]
    first = min(found) if found else None
    scores = {"first_rank": first, "mrr": (1.0 / first) if first else 0.0}
    for k in KS:
        scores[f"hit@{k}"] = int(first is not None and first <= k)
        scores[f"all@{k}"] = int(all(r is not None and r <= k for r in ranks))
    return scores


def evaluate(retrieve, questions: list[dict], setups: list[str]):
    """retrieve(question_text, setup, k) -> list of result dicts."""
    scored: dict[str, list[dict]] = {s: [] for s in setups}
    failures = []
    questions = [q for q in questions if q["type"] != "trap"]
    for setup in setups:
        retrieve(questions[0]["question"], setup, 3)   # warm-up: loads models, not timed
        for q in questions:
            start = time.perf_counter()
            results = retrieve(q["question"], setup, MAX_RANK)
            elapsed_ms = (time.perf_counter() - start) * 1000
            scores = score_question(results, q["relevant"])
            scores.update(id=q["id"], type=q["type"], ms=elapsed_ms)
            scored[setup].append(scores)
            if not scores["all@3"]:
                failures.append({
                    "setup": setup,
                    "id": q["id"],
                    "type": q["type"],
                    "question": q["question"],
                    "needed": q["relevant"],
                    "top3": [f"{r['drug']} / {r['section']}" for r in results[:3]],
                    "first_relevant_rank": scores["first_rank"],
                })
    return scored, failures


def mean(values) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def summarize(scored: dict[str, list[dict]]) -> dict:
    summary = {}
    for setup, rows in scored.items():
        by_type = defaultdict(list)
        for row in rows:
            by_type[row["type"]].append(row["all@3"])
        summary[setup] = {
            "n": len(rows),
            **{f"hit@{k}": mean(r[f"hit@{k}"] for r in rows) for k in KS},
            "all@3": mean(r["all@3"] for r in rows),
            "mrr": mean(r["mrr"] for r in rows),
            "avg_ms": mean(r["ms"] for r in rows),
            "all@3_by_type": {t: mean(v) for t, v in sorted(by_type.items())},
        }
    return summary


def to_markdown(summary: dict, n_questions: int) -> str:
    lines = [
        f"## Retrieval results ({n_questions} non-trap questions)",
        "",
        "| Setup | hit@1 | hit@3 | all@3 | hit@5 | MRR | avg ms |",
        "|---|---|---|---|---|---|---|",
    ]
    ranked = sorted(summary.items(), key=lambda kv: (kv[1]["all@3"], kv[1]["mrr"]), reverse=True)
    for setup, m in ranked:
        lines.append(
            f"| {setup} | {m['hit@1']:.2f} | {m['hit@3']:.2f} | {m['all@3']:.2f} | "
            f"{m['hit@5']:.2f} | {m['mrr']:.2f} | {m['avg_ms']:.0f} |"
        )
    types = sorted({t for m in summary.values() for t in m["all@3_by_type"]})
    lines += ["", "## all@3 by question type", "", "| Setup | " + " | ".join(types) + " |",
              "|---|" + "---|" * len(types)]
    for setup, m in ranked:
        cells = " | ".join(f"{m['all@3_by_type'].get(t, 0):.2f}" for t in types)
        lines.append(f"| {setup} | {cells} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", default=str(ROOT / "eval" / "gold_set.json"))
    parser.add_argument("--out-dir", default=str(ROOT / "eval" / "results"))
    args = parser.parse_args()

    from retrieval import SETUPS, Retriever  # imported here so tests don't load models

    questions = json.loads(Path(args.gold).read_text())
    retriever = Retriever()
    scored, failures = evaluate(
        lambda text, setup, k: retriever.retrieve(text, setup, k), questions, list(SETUPS)
    )
    summary = summarize(scored)
    n_questions = len(next(iter(scored.values())))

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    markdown = to_markdown(summary, n_questions)
    (out_dir / "results.md").write_text(markdown)
    (out_dir / "results.json").write_text(json.dumps({"summary": summary, "per_question": scored}, indent=2))
    (out_dir / "failures.json").write_text(json.dumps(failures, indent=2))
    print(markdown)
    print(f"{len(failures)} failed (question, setup) pairs saved to {out_dir / 'failures.json'}")


if __name__ == "__main__":
    main()