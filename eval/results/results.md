## Retrieval results (36 non-trap questions)

| Setup | hit@1 | hit@3 | all@3 | hit@5 | all@5 | MRR | avg ms |
|---|---|---|---|---|---|---|---|
| fixed+hybrid | 0.69 | 0.92 | 0.81 | 0.94 | 0.89 | 0.82 | 12 |
| section+hybrid_rerank | 0.67 | 0.89 | 0.78 | 0.92 | 0.78 | 0.78 | 315 |
| fixed+dense | 0.78 | 0.89 | 0.75 | 0.97 | 0.81 | 0.85 | 11 |
| section+dense | 0.75 | 0.92 | 0.75 | 0.94 | 0.81 | 0.84 | 12 |
| section+hybrid | 0.67 | 0.86 | 0.72 | 0.94 | 0.86 | 0.76 | 12 |
| fixed+hybrid_rerank | 0.61 | 0.86 | 0.72 | 0.94 | 0.83 | 0.75 | 318 |

## all@3 by question type

| Setup | contraindication | dosage | indication | interaction | side_effect | warning |
|---|---|---|---|---|---|---|
| fixed+hybrid | 1.00 | 1.00 | 1.00 | 0.50 | 0.67 | 1.00 |
| section+hybrid_rerank | 1.00 | 1.00 | 1.00 | 0.50 | 0.50 | 1.00 |
| fixed+dense | 1.00 | 1.00 | 0.83 | 0.30 | 1.00 | 0.75 |
| section+dense | 1.00 | 1.00 | 1.00 | 0.30 | 0.83 | 0.75 |
| section+hybrid | 0.75 | 0.83 | 1.00 | 0.50 | 0.50 | 1.00 |
| fixed+hybrid_rerank | 1.00 | 1.00 | 0.83 | 0.40 | 0.67 | 0.75 |
