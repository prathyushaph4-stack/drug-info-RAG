## Retrieval results (9 non-trap questions)

| Setup | hit@1 | hit@3 | all@3 | hit@5 | all@5 | MRR | avg ms |
|---|---|---|---|---|---|---|---|
| section+hybrid | 0.89 | 0.89 | 0.78 | 1.00 | 0.89 | 0.92 | 25 |
| fixed+hybrid_rerank | 0.89 | 0.89 | 0.78 | 0.89 | 0.78 | 0.89 | 652 |
| fixed+hybrid | 0.78 | 0.89 | 0.78 | 1.00 | 0.89 | 0.86 | 26 |
| section+dense | 0.89 | 1.00 | 0.67 | 1.00 | 0.89 | 0.93 | 26 |
| section+hybrid_rerank | 0.78 | 0.89 | 0.67 | 0.89 | 0.78 | 0.83 | 701 |
| fixed+dense | 0.89 | 0.89 | 0.56 | 1.00 | 0.67 | 0.91 | 25 |

## all@3 by question type

| Setup | interaction |
|---|---|
| section+hybrid | 0.78 |
| fixed+hybrid_rerank | 0.78 |
| fixed+hybrid | 0.78 |
| section+dense | 0.67 |
| section+hybrid_rerank | 0.67 |
| fixed+dense | 0.56 |
