# Drug-Information RAG Assistant (with an evaluated retrieval pipeline)

A question-answering assistant over official FDA drug labels. It answers with
citations, refuses out-of-scope or personal medical-advice questions, and,
the main point of this project, **measures which retrieval setup works best**.

> **Not medical advice.** This is a portfolio project. Always consult a doctor
> or pharmacist about medicines.

## Status

- [x] Step 1: project setup
- [x] Step 2: label download script (`src/fetch_labels.py`)
- [x] Step 3: cleaning + two chunking styles (`src/chunking.py`, tested)
- [x] Step 4: embeddings + ChromaDB index (`src/index.py`)
- [x] Step 5: three retrieval setups (`src/retrieval.py`: dense, hybrid, hybrid + reranker)
- [x] Step 6: gold test set, 44 questions (`eval/gold_set.json`, checked by `eval/validate_gold.py`); pharmacist review pending
- [x] Step 7: retrieval evaluation script (`eval/evaluate_retrieval.py`: hit@k, all@3, MRR, speed)
- [ ] Step 8: answer generation, query routing, guardrails
- [ ] Step 9: error analysis (before/after)
- [ ] Step 10: FastAPI + Docker + final write-up

## Data

Official drug labels from the US FDA via [openFDA](https://open.fda.gov/apis/drug/label/)
for 40 common drugs (list in `src/drugs.py`). Sections kept: Indications and
Usage, Dosage and Administration, Contraindications, Warnings, Adverse
Reactions, Drug Interactions.

## Setup (macOS / Linux)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python src/fetch_labels.py   # Step 2: downloads about 40 labels into data/raw/ (takes ~1-2 min)
python src/chunking.py       # Step 3: writes data/chunks/chunks_section.json and chunks_fixed.json
python src/index.py          # Step 4: embeds chunks into ChromaDB (first run downloads a ~130 MB model)
python src/retrieval.py      # Step 5: compares all 6 setups on one sample question
python eval/validate_gold.py       # checks the 44 gold questions against the real label text
python eval/evaluate_retrieval.py  # Step 7: scores all 6 setups, writes eval/results/
python -m pytest tests             # chunking, label-picking, retrieval and scoring tests
```

## Design notes

- **Chunk size:** about 250 words (about 350-400 tokens), chosen to fit inside the 512-token window of the
  embedding model (`BAAI/bge-small-en-v1.5`). Longer chunks would be silently truncated before embedding.
- **Six setups compared:** {section chunks, fixed chunks} x {dense, hybrid, hybrid + reranker}.
- **Hybrid** merges embedding search and BM25 keyword search with Reciprocal Rank Fusion; drug names and
  doses are exact words, which keyword search handles well.
- **Reranker:** `cross-encoder/ms-marco-MiniLM-L-6-v2` re-orders the top 20 hybrid candidates.
- **Data note:** over-the-counter labels (aspirin, acetaminophen, cetirizine, loratadine) have only 3 of the
  6 sections in openFDA, so some questions about them cannot be answered from the labels.

## Results

_To be filled in after Steps 7 and 9 (results table, before/after error-analysis numbers, limitations)._