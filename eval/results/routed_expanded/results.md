## Retrieval results (36 non-trap questions)

| Setup | hit@1 | hit@3 | all@3 | hit@5 | all@5 | MRR | avg ms |
|---|---|---|---|---|---|---|---|
| fixed+dense | 0.83 | 0.94 | 0.89 | 1.00 | 0.97 | 0.89 | 15 |
| fixed+hybrid | 0.69 | 0.94 | 0.89 | 0.97 | 0.92 | 0.82 | 17 |
| section+hybrid_rerank | 0.67 | 0.92 | 0.89 | 0.92 | 0.92 | 0.79 | 388 |
| section+dense | 0.78 | 0.92 | 0.86 | 0.94 | 0.92 | 0.86 | 16 |
| section+hybrid | 0.72 | 0.89 | 0.83 | 0.92 | 0.89 | 0.80 | 17 |
| fixed+hybrid_rerank | 0.69 | 0.86 | 0.78 | 0.97 | 0.94 | 0.79 | 381 |

## all@3 by question type

| Setup | contraindication | dosage | indication | interaction | side_effect | warning |
|---|---|---|---|---|---|---|
| fixed+dense | 1.00 | 1.00 | 1.00 | 0.70 | 1.00 | 0.75 |
| fixed+hybrid | 1.00 | 1.00 | 1.00 | 0.80 | 0.67 | 1.00 |
| section+hybrid_rerank | 1.00 | 1.00 | 1.00 | 0.90 | 0.50 | 1.00 |
| section+dense | 1.00 | 1.00 | 1.00 | 0.70 | 0.83 | 0.75 |
| section+hybrid | 1.00 | 0.83 | 1.00 | 0.80 | 0.67 | 0.75 |
| fixed+hybrid_rerank | 1.00 | 1.00 | 0.83 | 0.70 | 0.50 | 0.75 |
