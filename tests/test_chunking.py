import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from chunking import clean_text, fixed_chunks, section_chunks, split_long  # noqa: E402

SAMPLE = {
    "drug": "testdrug",
    "source_url": "https://example.org/label",
    "sections": {
        "Indications and Usage": "1 INDICATIONS AND USAGE Used for testing. [see Warnings (5.1)] Second sentence.",
        "Contraindications": " ".join(f"word{i}" for i in range(1200)),
    },
}


def test_clean_text_removes_numbering_and_refs():
    cleaned = clean_text(SAMPLE["sections"]["Indications and Usage"])
    assert not cleaned.startswith("1 INDICATIONS")
    assert "[see" not in cleaned
    assert "  " not in cleaned


def test_split_long_respects_limit():
    text = " ".join(["This is a sentence."] * 400)
    pieces = split_long(text, 100)
    assert len(pieces) > 1
    assert all(len(p.split()) <= 100 for p in pieces)


def test_section_chunks_have_metadata():
    chunks = section_chunks(SAMPLE)
    assert {c["section"] for c in chunks} == {"Indications and Usage", "Contraindications"}
    assert all(c["drug"] == "testdrug" and c["source_url"] for c in chunks)
    assert len({c["id"] for c in chunks}) == len(chunks)  # ids are unique


def test_fixed_chunks_size_and_overlap():
    chunks = fixed_chunks(SAMPLE, size=500, overlap=50)
    assert all(len(c["text"].split()) <= 500 for c in chunks)
    first_tail = chunks[0]["text"].split()[-50:]
    second_head = chunks[1]["text"].split()[:50]
    assert first_tail == second_head  # overlap is exactly 50 words
    assert len({c["id"] for c in chunks}) == len(chunks)
