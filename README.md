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
- [x] Step 8a: drug-aware retrieval routing (`retrieve_routed` in `src/retrieval.py`), motivated by error analysis
- [x] Step 8a': drug-class query expansion for two-drug questions (`src/drug_classes.py`; pharmacist review pending), tested on a separate held-out set (`eval/gold_heldout.json`)
- [ ] Step 8b: answer generation, refusal routing, guardrails
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

## Results (retrieval)

**Data:** 40 single-ingredient FDA drug labels (941 section chunks, 926 fixed-size chunks).
**Test sets:** a 36-question development set (`eval/gold_set.json`, non-trap questions) and a separate
9-question held-out set of two-drug interaction questions (`eval/gold_heldout.json`).
A retrieved chunk counts as correct if it is from the right drug and contains a phrase copied from that
drug's label. **all@k** means every drug the question needs has a correct chunk in the top k
(strict for two-drug questions). all@5 was added after the first results were seen; all@3 was the planned main measure.

### Final configurations: drug-aware routing + drug-class query expansion (36 questions)

| Setup | hit@1 | hit@3 | all@3 | hit@5 | all@5 | MRR | avg ms |
|---|---|---|---|---|---|---|---|
| fixed+dense | 0.83 | 0.94 | 0.89 | 1.00 | 0.97 | 0.89 | 15 |
| fixed+hybrid | 0.69 | 0.94 | 0.89 | 0.97 | 0.92 | 0.82 | 17 |
| section+hybrid_rerank | 0.67 | 0.92 | 0.89 | 0.92 | 0.92 | 0.79 | 388 |
| section+dense | 0.78 | 0.92 | 0.86 | 0.94 | 0.92 | 0.86 | 16 |
| section+hybrid | 0.72 | 0.89 | 0.83 | 0.92 | 0.89 | 0.80 | 17 |
| fixed+hybrid_rerank | 0.69 | 0.86 | 0.78 | 0.97 | 0.94 | 0.79 | 381 |

### What each improvement added (fixed+dense, 36 questions)

| Version | all@3 | all@5 | interaction all@3 | hit@1 | MRR |
|---|---|---|---|---|---|
| Plain retrieval | 0.75 | 0.81 | 0.30 | 0.78 | 0.85 |
| + drug-aware routing | 0.83 | 0.94 | 0.50 | 0.81 | 0.87 |
| + drug-class query expansion | 0.89 | 0.97 | 0.70 | 0.83 | 0.89 |

### Held-out interaction questions (9 questions): routing vs routing + class expansion

| Setup | all@3 | all@5 |
|---|---|---|
| section+dense | 0.67 -> 0.89 | 0.89 -> 0.89 |
| section+hybrid | 0.78 -> 0.89 | 0.89 -> 0.89 |
| section+hybrid_rerank | 0.67 -> 0.89 | 0.78 -> 0.89 |
| fixed+dense | 0.56 -> 0.78 | 0.67 -> 0.89 |
| fixed+hybrid | 0.78 -> 0.78 | 0.89 -> 0.89 |
| fixed+hybrid_rerank | 0.78 -> 0.78 | 0.78 -> 0.78 |

### Findings

- **No setup is clearly best.** Top configurations are within one or two questions of each other.
  fixed-size chunks with dense search is a good default: best hit@1, all@5 and MRR on the development set, and about 25x faster than the reranked setups.
- **The cross-encoder reranker did not help** (never leads on any measure, roughly 25x slower).
- **Hybrid (keyword + embedding) search** gave more complete coverage than dense search alone before routing was added; the gap mostly closed afterwards.
- **Class expansion generalised in direction:** on held-out questions it raised all@3 in 4 of 6 setups and lowered none,
  but one section+dense setup lost rank-1 precision (hit@1 0.89 -> 0.56). With 9 questions, one question moves a score by 0.11.

### Error analysis (what went wrong and how it was fixed)

1. **Wrong data:** the first download returned combination products (e.g. a sitagliptin + metformin label stored as "metformin").
   Found while checking evidence phrases; fixed by accepting only single-ingredient labels and printing the product name for every drug.
2. **Crowding:** for two-drug questions, 26 of 35 interaction failures had only one drug in the top 3.
   Fixed with drug-aware routing: detect the drugs named in the question, search each drug's chunks separately, interleave the results.
3. **Vocabulary gap:** labels name the partner drug's class ("NSAIDs", "benzodiazepines", "serotonin reuptake inhibitors"), not the specific drug.
   Fixed by adding the partner's class terms to each drug's query (`src/drug_classes.py`).
4. **Still open:** side-effect and warning questions fail when the exact answer word is in a different piece of a long section
   (right drug, right section, different chunk). Not fixed; see limitations.

### Limitations

- Small, self-written test sets (36 + 9 questions); differences of one or two questions are not significant.
- The development set was used to design routing and expansion. The held-out set was written before expansion was run, but after the failure patterns were known.
- Correctness is judged by phrase matching against label text, not by reading the answers.
- Drug detection works on the 40 generic names in `src/drugs.py`; brand names, misspellings and unlisted drugs fall back to plain search.
- The drug-class vocabulary was drafted with AI assistance and still needs a pharmacist's review.
- US FDA labels only (not Indian labelling). Not medical advice.