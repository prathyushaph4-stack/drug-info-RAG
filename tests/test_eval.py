import json
import sys
from pathlib import Path

import chromadb
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "eval"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from evaluate_retrieval import evaluate, is_relevant, score_question, summarize, to_markdown  # noqa: E402
from index import build_collection  # noqa: E402
from retrieval import SETUPS, Retriever  # noqa: E402
from test_retrieval import FakeReranker, HashEmbedder, make_chunks  # noqa: E402


def chunk(drug, text):
    return {"drug": drug, "section": "Drug Interactions", "text": text}


REQ_WARFARIN = {"drug": "warfarin", "evidence": ["Nonsteroidal Anti-Inflammatory"]}
REQ_IBUPROFEN = {"drug": "ibuprofen", "evidence": ["warfarin"]}


def test_is_relevant_needs_right_drug_and_phrase():
    assert is_relevant(chunk("warfarin", "includes nonsteroidal   anti-inflammatory agents"), REQ_WARFARIN)
    assert not is_relevant(chunk("naproxen", "nonsteroidal anti-inflammatory"), REQ_WARFARIN)   # wrong drug
    assert not is_relevant(chunk("warfarin", "unrelated text"), REQ_WARFARIN)                    # wrong text


def test_score_two_drug_question():
    results = [chunk("warfarin", "nonsteroidal anti-inflammatory"), chunk("tramadol", "x"),
               chunk("ibuprofen", "interacts with warfarin")]
    s = score_question(results, [REQ_WARFARIN, REQ_IBUPROFEN])
    assert s["first_rank"] == 1 and s["mrr"] == 1.0
    assert s["hit@1"] == 1 and s["all@1"] == 0      # only one of two drugs at rank 1
    assert s["all@3"] == 1                           # both found by rank 3


def test_score_miss():
    s = score_question([chunk("tramadol", "x")] * 3, [REQ_WARFARIN])
    assert s["first_rank"] is None and s["mrr"] == 0.0 and s["hit@5"] == 0 and s["all@3"] == 0


def test_evaluate_skips_traps_and_records_failures():
    questions = [
        {"id": "a", "type": "interaction", "question": "q1", "relevant": [REQ_WARFARIN]},
        {"id": "b", "type": "trap", "question": "q2", "relevant": []},
    ]
    good = [chunk("warfarin", "nonsteroidal anti-inflammatory")]
    bad = [chunk("tramadol", "nothing")]
    scored, failures = evaluate(lambda q, setup, k: good if setup == "good" else bad, questions, ["good", "bad"])
    assert [len(v) for v in scored.values()] == [1, 1]          # trap skipped
    assert [f["setup"] for f in failures] == ["bad"]
    summary = summarize(scored)
    assert summary["good"]["all@3"] == 1.0 and summary["bad"]["all@3"] == 0.0
    assert "| good |" in to_markdown(summary, 1)


def test_full_pipeline_with_stand_in_models(tmp_path):
    client = chromadb.PersistentClient(path=str(tmp_path / "db"))
    embedder = HashEmbedder()
    chunk_dir = tmp_path / "chunks"
    chunk_dir.mkdir()
    for style in ("section", "fixed"):
        chunks = make_chunks(style)
        (chunk_dir / f"chunks_{style}.json").write_text(json.dumps(chunks))
        build_collection(client, style, chunks, embedder)
    retriever = Retriever(client=client, embedding_function=embedder,  # type: ignore[arg-type]
                          chunk_dir=chunk_dir, reranker=FakeReranker())
    questions = [{
        "id": "q1", "type": "interaction", "question": "warfarin ibuprofen bleeding interaction",
        "relevant": [{"drug": "warfarin", "evidence": ["nsaids"]}, {"drug": "ibuprofen", "evidence": ["adverse reactions"]}],
    }]
    scored, _ = evaluate(lambda q, s, k: retriever.retrieve(q, s, k), questions, list(SETUPS))
    assert set(scored) == set(SETUPS)
    assert all(rows[0]["hit@3"] == 1 for rows in scored.values())