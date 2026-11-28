"""Tests the search wiring with a tiny stand-in embedder (no model download).

The stand-in turns words into a hashed bag-of-words vector, which is enough to
check that indexing, dense search, keyword search, fusion and reranking all
connect correctly. Real search quality is measured in Step 7, not here.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import chromadb
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from index import build_collection, collection_name  # noqa: E402
from retrieval import SETUPS, Retriever, detect_drugs, rrf_fuse  # noqa: E402

DIM = 256


class HashEmbedder:
    def __call__(self, input):
        vectors = []
        for text in input:
            v = np.zeros(DIM, dtype=np.float32)
            for word in re.findall(r"[a-z0-9]+", text.lower()):
                v[int(hashlib.md5(word.encode()).hexdigest(), 16) % DIM] += 1.0
            norm = np.linalg.norm(v)
            vectors.append(v / norm if norm else v)
        return vectors

    @staticmethod
    def name():
        return "hash-embedder"

    def get_config(self):
        return {}

    @staticmethod
    def build_from_config(config):
        return HashEmbedder()

    def embed_query(self, input):
        return self(input)


class FakeReranker:
    """Scores by how many question words appear in the chunk."""

    def predict(self, pairs):
        return [len(set(q.lower().split()) & set(t.lower().split())) for q, t in pairs]


def make_chunks(style):
    texts = {
        ("metformin", "Contraindications"): "Metformin is contraindicated in severe renal impairment and metabolic acidosis.",
        ("warfarin", "Drug Interactions"): "Warfarin interacts with NSAIDs such as ibuprofen which increase bleeding risk.",
        ("ibuprofen", "Adverse Reactions"): "Ibuprofen common adverse reactions include nausea heartburn and headache.",
        ("sertraline", "Indications and Usage"): "Sertraline is indicated for major depressive disorder and panic disorder.",
    }
    return [
        {"id": f"{drug}|{section}|0|{style}", "text": text, "drug": drug, "section": section,
         "source_url": f"https://example.org/{drug}", "chunk_style": style}
        for (drug, section), text in texts.items()
    ]


@pytest.fixture()
def retriever(tmp_path):
    client = chromadb.PersistentClient(path=str(tmp_path / "db"))
    embedder = HashEmbedder()
    chunk_dir = tmp_path / "chunks"
    chunk_dir.mkdir()
    for style in ("section", "fixed"):
        chunks = make_chunks(style)
        (chunk_dir / f"chunks_{style}.json").write_text(json.dumps(chunks))
        build_collection(client, style, chunks, embedder)
        collection = client.get_collection(
            collection_name(style),
            embedding_function=embedder,  # type: ignore[arg-type]  (editor typing quirk, runs fine)
        )
        assert collection.count() == 4
    return Retriever(
        client=client,
        embedding_function=embedder,  # type: ignore[arg-type]
        chunk_dir=chunk_dir,
        reranker=FakeReranker(),
    )


def test_rrf_prefers_items_high_in_both_lists():
    fused = rrf_fuse([["a", "b", "c"], ["b", "a", "d"]])
    assert [i for i, _ in fused[:2]] in (["a", "b"], ["b", "a"])
    assert fused[-1][0] in ("c", "d")


@pytest.mark.parametrize("setup", SETUPS)
def test_every_setup_finds_the_right_chunk(retriever, setup):
    results = retriever.retrieve("warfarin ibuprofen bleeding interaction", setup, k=2)
    assert results, f"{setup} returned nothing"
    assert results[0]["drug"] == "warfarin"
    assert results[0]["section"] == "Drug Interactions"
    assert set(results[0]) >= {"id", "text", "drug", "section", "source_url", "score"}


def test_unknown_setup_raises(retriever):
    with pytest.raises(ValueError):
        retriever.retrieve("anything", "nope+dense")


def test_detect_drugs_order_and_word_boundaries():
    assert detect_drugs("Is it safe to take warfarin together with ibuprofen?") == ["warfarin", "ibuprofen"]
    assert detect_drugs("What are the side effects of insulin glargine?") == ["insulin glargine"]
    assert detect_drugs("What is the capital of France?") == []
    assert detect_drugs("Can I stop taking sertralines?") == []   # whole words only


@pytest.mark.parametrize("setup", SETUPS)
def test_drug_filter_limits_results_to_that_drug(retriever, setup):
    results = retriever.retrieve("bleeding nausea depression kidney", setup, k=4, drug="ibuprofen")
    assert results and {r["drug"] for r in results} == {"ibuprofen"}


@pytest.mark.parametrize("setup", SETUPS)
def test_routed_two_drug_question_covers_both_drugs(retriever, setup):
    results = retriever.retrieve_routed("warfarin ibuprofen bleeding interaction", setup, k=2)
    assert {r["drug"] for r in results} == {"warfarin", "ibuprofen"}


@pytest.mark.parametrize("setup", SETUPS)
def test_routed_without_drug_name_behaves_like_normal_search(retriever, setup):
    question = "renal impairment and metabolic acidosis"
    routed = retriever.retrieve_routed(question, setup, k=3)
    plain = retriever.retrieve(question, setup, k=3)
    assert [r["id"] for r in routed] == [r["id"] for r in plain]