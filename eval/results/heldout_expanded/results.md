## Retrieval results (9 non-trap questions)

| Setup | hit@1 | hit@3 | all@3 | hit@5 | all@5 | MRR | avg ms |
|---|---|---|---|---|---|---|---|
| section+hybrid | 0.89 | 1.00 | 0.89 | 1.00 | 0.89 | 0.94 | 28 |
| section+hybrid_rerank | 0.89 | 1.00 | 0.89 | 1.00 | 0.89 | 0.94 | 624 |
| section+dense | 0.56 | 1.00 | 0.89 | 1.00 | 0.89 | 0.78 | 24 |
| fixed+dense | 1.00 | 1.00 | 0.78 | 1.00 | 0.89 | 1.00 | 23 |
| fixed+hybrid_rerank | 0.89 | 0.89 | 0.78 | 1.00 | 0.78 | 0.92 | 601 |
| fixed+hybrid | 0.78 | 1.00 | 0.78 | 1.00 | 0.89 | 0.87 | 27 |

## all@3 by question type

| Setup | interaction |
|---|---|
| section+hybrid | 0.89 |
| section+hybrid_rerank | 0.89 |
| section+dense | 0.89 |
| fixed+dense | 0.78 |
| fixed+hybrid_rerank | 0.78 |
| fixed+hybrid | 0.78 |
