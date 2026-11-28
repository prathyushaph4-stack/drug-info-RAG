"""Step 5: three ways to search the drug-label chunks, for both chunking styles.

    dense           search by meaning (embeddings in ChromaDB)
    hybrid          meaning search + keyword search (BM25), merged with
                    Reciprocal Rank Fusion (RRF)
    hybrid_rerank   hybrid, then a second model re-orders the top candidates

2 chunking styles x 3 modes = 6 setups, named like "section+dense".

Usage:
    from retrieval import Retriever
    r = Retriever()
    results = r.retrieve("What are the contraindications of warfarin?", "fixed+hybrid", k=3)
"""
import re
from pathlib import Path

import chromadb

from drug_classes import DRUG_CLASSES
from drugs import DRUGS
from index import CHROMA_PATH, CHUNK_DIR, STYLES, collection_name, default_embedding_function, load_chunks

MODES = ("dense", "hybrid", "hybrid_rerank")
SETUPS = [f"{style}+{mode}" for style in STYLES for mode in MODES]

RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
CANDIDATES = 20   # how many results each search contributes before fusing / reranking
RRF_K = 60        # standard RRF constant


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def detect_drugs(question: str) -> list[str]:
    """Drugs from our list that the question names, in the order they appear."""
    text = question.lower()
    found = []
    for drug in DRUGS:
        match = re.search(rf"\b{re.escape(drug)}\b", text)
        if match:
            found.append((match.start(), drug))
    return [drug for _, drug in sorted(found)]


def rrf_fuse(rankings: list[list[str]], k: int = RRF_K) -> list[tuple[str, float]]:
    """Merge several ranked lists of ids. An id near the top of many lists wins.

    score(id) = sum over lists of 1 / (k + rank), rank starting at 1.
    """
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, item_id in enumerate(ranking, start=1):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda pair: pair[1], reverse=True)


def default_reranker():
    from sentence_transformers import CrossEncoder

    return CrossEncoder(RERANK_MODEL)


class Retriever:
    def __init__(self, client=None, embedding_function=None, chunk_dir: Path = CHUNK_DIR, reranker=None):
        self._client = client
        self._embedder = embedding_function
        self._chunk_dir = chunk_dir
        self._reranker = reranker
        self._collections: dict = {}
        self._chunks: dict[str, dict[str, dict]] = {}     # style -> {id: chunk}
        self._bm25: dict = {}                              # style -> (BM25Okapi, [ids])

    # ---------- lazy setup ----------
    def _get_collection(self, style: str):
        if style not in self._collections:
            if self._client is None:
                self._client = chromadb.PersistentClient(path=CHROMA_PATH)
            if self._embedder is None:
                self._embedder = default_embedding_function()
            self._collections[style] = self._client.get_collection(
                collection_name(style),
                embedding_function=self._embedder,  # type: ignore[arg-type]  (editor typing quirk, runs fine)
            )
        return self._collections[style]

    def _get_chunks(self, style: str) -> dict[str, dict]:
        if style not in self._chunks:
            self._chunks[style] = {c["id"]: c for c in load_chunks(style, self._chunk_dir)}
        return self._chunks[style]

    def _get_bm25(self, style: str):
        if style not in self._bm25:
            from rank_bm25 import BM25Okapi

            chunks = self._get_chunks(style)
            ids = list(chunks)
            corpus = [tokenize(chunks[i]["text"] + " " + chunks[i]["drug"]) for i in ids]
            self._bm25[style] = (BM25Okapi(corpus), ids)
        return self._bm25[style]

    def _as_result(self, style: str, chunk_id: str, score: float) -> dict:
        chunk = self._get_chunks(style)[chunk_id]
        return {
            "id": chunk_id,
            "text": chunk["text"],
            "drug": chunk["drug"],
            "section": chunk["section"],
            "source_url": chunk["source_url"],
            "score": float(score),
        }

    # ---------- the three searches ----------
    def dense_search(self, style: str, question: str, n: int = CANDIDATES, drug: str | None = None) -> list[dict]:
        hits = self._get_collection(style).query(
            query_texts=[question], n_results=n, where={"drug": drug} if drug else None
        )
        ids = hits["ids"][0]
        distances = (hits["distances"] or [[1.0] * len(ids)])[0]
        return [
            self._as_result(style, chunk_id, 1.0 - dist)   # cosine distance -> similarity
            for chunk_id, dist in zip(ids, distances)
        ]

    def keyword_search(self, style: str, question: str, n: int = CANDIDATES, drug: str | None = None) -> list[dict]:
        bm25, ids = self._get_bm25(style)
        scores = bm25.get_scores(tokenize(question))
        chunks = self._get_chunks(style)
        allowed = [i for i in range(len(ids)) if drug is None or chunks[ids[i]]["drug"] == drug]
        top = sorted(allowed, key=lambda i: scores[i], reverse=True)[:n]
        return [self._as_result(style, ids[i], scores[i]) for i in top if scores[i] > 0]

    def hybrid_search(self, style: str, question: str, n: int = CANDIDATES, drug: str | None = None) -> list[dict]:
        dense = self.dense_search(style, question, n, drug)
        keyword = self.keyword_search(style, question, n, drug)
        fused = rrf_fuse([[r["id"] for r in dense], [r["id"] for r in keyword]])
        return [self._as_result(style, chunk_id, score) for chunk_id, score in fused[:n]]

    def rerank(self, question: str, candidates: list[dict]) -> list[dict]:
        if self._reranker is None:
            self._reranker = default_reranker()
        scores = self._reranker.predict([(question, c["text"]) for c in candidates])
        reranked = [dict(c, score=float(s)) for c, s in zip(candidates, scores)]
        return sorted(reranked, key=lambda r: r["score"], reverse=True)

    # ---------- the one function everything else calls ----------
    def retrieve(self, question: str, setup: str, k: int = 3, drug: str | None = None) -> list[dict]:
        """setup is one of SETUPS, e.g. 'section+dense' or 'fixed+hybrid_rerank'.

        If drug is given, only that drug's chunks are searched.
        """
        if setup not in SETUPS:
            raise ValueError(f"Unknown setup '{setup}'. Choose from {SETUPS}")
        style, mode = setup.split("+")
        if mode == "dense":
            results = self.dense_search(style, question, drug=drug)
        elif mode == "hybrid":
            results = self.hybrid_search(style, question, drug=drug)
        else:
            results = self.rerank(question, self.hybrid_search(style, question, drug=drug))
        return results[:k]

    def retrieve_routed(self, question: str, setup: str, k: int = 3, expand_classes: bool = False) -> list[dict]:
        """Drug-aware retrieval.

        Finds the drugs the question names, searches each drug's chunks separately,
        then interleaves the lists (drug A #1, drug B #1, drug A #2, ...), so a
        two-drug question can never be crowded out by one drug. With one drug named,
        the search is limited to that drug. With none named, it is a normal search.
        """
        drugs = detect_drugs(question)
        if not drugs:
            return self.retrieve(question, setup, k)
        per_drug = []
        for drug in drugs:
            query = question
            if expand_classes and len(drugs) > 1:
                # labels often name the partner's CLASS (NSAIDs, benzodiazepines...), not the drug
                partners = [p for p in drugs if p != drug]
                extra = " ".join(term for p in partners for term in DRUG_CLASSES.get(p, []))
                query = f"{question} {extra}".strip()
            per_drug.append(self.retrieve(query, setup, k, drug=drug))
        merged, seen = [], set()
        for rank in range(k):
            for results in per_drug:
                if rank < len(results) and results[rank]["id"] not in seen:
                    merged.append(results[rank])
                    seen.add(results[rank]["id"])
        return merged[:k]


if __name__ == "__main__":
    retriever = Retriever()
    question = "Can I take warfarin with ibuprofen?"
    for setup in SETUPS:
        top = retriever.retrieve(question, setup, k=3)
        print(f"\n{setup}")
        for r in top:
            print(f"  {r['drug']:<14} {r['section']:<26} score={r['score']:.3f}")