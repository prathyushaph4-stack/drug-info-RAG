"""Step 3: clean the labels and cut them into chunks, in two different ways.

Style A, "section": one chunk per label section (long sections are split on
        paragraph/sentence boundaries so no chunk gets huge).
Style B, "fixed":   the whole label as one stream of words, cut every
        FIXED_WORDS words with FIXED_OVERLAP words of overlap.

Every chunk carries metadata (drug, section, source link) so answers can cite it.

Run from the project root:
    python src/chunking.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
CHUNK_DIR = ROOT / "data" / "chunks"

FIXED_WORDS = 250
FIXED_OVERLAP = 40
SECTION_MAX_WORDS = 250


def clean_text(text: str) -> str:
    """Remove label numbering and extra whitespace."""
    text = re.sub(r"^\s*\d+(\.\d+)*\s+[A-Z][A-Z &,/-]{4,}\s+", "", text)  # "1 INDICATIONS AND USAGE"
    text = re.sub(r"\[\s*see[^\]]*\]", "", text, flags=re.IGNORECASE)      # "[see Warnings (5.1)]"
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_long(text: str, max_words: int) -> list[str]:
    """Split text into pieces of at most max_words, breaking at sentence ends."""
    if len(text.split()) <= max_words:
        return [text]
    sentences = re.split(r"(?<=[.!?])\s+", text)
    pieces, current = [], []
    for sentence in sentences:
        if current and len(" ".join(current + [sentence]).split()) > max_words:
            pieces.append(" ".join(current))
            current = []
        current.append(sentence)
    if current:
        pieces.append(" ".join(current))
    return pieces


def section_chunks(record: dict) -> list[dict]:
    chunks = []
    for section, raw in record["sections"].items():
        text = clean_text(raw)
        if not text:
            continue
        for part, piece in enumerate(split_long(text, SECTION_MAX_WORDS)):
            chunks.append({
                "id": f"{record['drug']}|{section}|{part}|section",
                "text": piece,
                "drug": record["drug"],
                "section": section,
                "source_url": record["source_url"],
                "chunk_style": "section",
            })
    return chunks


def fixed_chunks(record: dict, size: int = FIXED_WORDS, overlap: int = FIXED_OVERLAP) -> list[dict]:
    # Build one word stream, remembering which section each word came from.
    words, word_sections = [], []
    for section, raw in record["sections"].items():
        for w in clean_text(raw).split():
            words.append(w)
            word_sections.append(section)
    chunks, start, idx = [], 0, 0
    step = size - overlap
    while start < len(words):
        end = min(start + size, len(words))
        chunks.append({
            "id": f"{record['drug']}|fixed|{idx}",
            "text": " ".join(words[start:end]),
            "drug": record["drug"],
            "section": word_sections[start],  # section where this chunk starts
            "source_url": record["source_url"],
            "chunk_style": "fixed",
        })
        if end == len(words):
            break
        start += step
        idx += 1
    return chunks


def build_all() -> dict[str, list[dict]]:
    out = {"section": [], "fixed": []}
    for path in sorted(RAW_DIR.glob("*.json")):
        record = json.loads(path.read_text())
        out["section"].extend(section_chunks(record))
        out["fixed"].extend(fixed_chunks(record))
    return out


def main() -> None:
    CHUNK_DIR.mkdir(parents=True, exist_ok=True)
    result = build_all()
    for style, chunks in result.items():
        (CHUNK_DIR / f"chunks_{style}.json").write_text(json.dumps(chunks, indent=2))
        print(f"{style}: {len(chunks)} chunks")
    if not any(result.values()):
        print("No raw labels found. Run src/fetch_labels.py first.")


if __name__ == "__main__":
    main()
