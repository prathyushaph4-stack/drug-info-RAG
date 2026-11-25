"""Step 4: turn every chunk into an embedding and store it in ChromaDB.

Two collections are created, one per chunking style:
    drugs_section  and  drugs_fixed

Run from the project root (after fetch_labels.py and chunking.py):
    python src/index.py

The first run downloads the embedding model (about 130 MB) from Hugging Face,
so it needs internet access once. After that it works offline.
"""
import json
from pathlib import Path

import chromadb

ROOT = Path(__file__).resolve().parent.parent
CHUNK_DIR = ROOT / "data" / "chunks"
CHROMA_PATH = str(ROOT / "chroma_db")

EMBED_MODEL = "BAAI/bge-small-en-v1.5"   # small, free, runs on a laptop CPU
STYLES = ("section", "fixed")
BATCH_SIZE = 64


def collection_name(style: str) -> str:
    return f"drugs_{style}"


def load_chunks(style: str, chunk_dir: Path = CHUNK_DIR) -> list[dict]:
    path = chunk_dir / f"chunks_{style}.json"
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run src/chunking.py first.")
    return json.loads(path.read_text())


def default_embedding_function():
    """The real embedding model. Imported lazily so tests don't need it."""
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

    return SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)


def build_collection(client, style: str, chunks: list[dict], embedding_function):
    """(Re)create one collection and fill it with the chunks."""
    name = collection_name(style)
    try:
        client.delete_collection(name)   # start fresh so re-running never duplicates
    except Exception:
        pass
    collection = client.create_collection(
        name=name,
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"},
    )
    for start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[start:start + BATCH_SIZE]
        collection.add(
            ids=[c["id"] for c in batch],
            documents=[c["text"] for c in batch],
            metadatas=[
                {
                    "drug": c["drug"],
                    "section": c["section"],
                    "source_url": c["source_url"],
                    "chunk_style": c["chunk_style"],
                }
                for c in batch
            ],
        )
    return collection


def main() -> None:
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    embedder = default_embedding_function()
    for style in STYLES:
        chunks = load_chunks(style)
        collection = build_collection(client, style, chunks, embedder)
        print(f"{collection_name(style)}: {collection.count()} chunks indexed")

    # Quick sanity check: one question against each collection
    question = "metformin kidney warning"
    for style in STYLES:
        collection = client.get_collection(
            collection_name(style),
            embedding_function=embedder,  # type: ignore[arg-type]  (editor typing quirk, runs fine)
        )
        hit = collection.query(query_texts=[question], n_results=1)
        metadatas = hit["metadatas"]
        if metadatas and metadatas[0]:
            meta = metadatas[0][0]
            print(f"[{style}] '{question}' -> {meta['drug']} / {meta['section']}")
        else:
            print(f"[{style}] '{question}' -> no result")


if __name__ == "__main__":
    main()