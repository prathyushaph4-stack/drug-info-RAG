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
- [ ] Step 4: embeddings + ChromaDB index
- [ ] Step 5: three retrieval setups (dense, hybrid, hybrid + reranker)
- [ ] Step 6: pharmacist-written gold test set (40-50 questions)
- [ ] Step 7: retrieval evaluation (hit rate@3, MRR)
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
python -m pytest tests       # chunking tests
```

## Results

_To be filled in after Steps 7 and 9 (results table, before/after error-analysis numbers, limitations)._
