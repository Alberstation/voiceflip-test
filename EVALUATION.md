# Phase 4 — RAG System Evaluation

## Tool choice: RAGAS

**RAGAS** (Retrieval Augmented Generation Assessment) is the chosen evaluation tool.

### Justification

- **Open-source** and actively maintained.
- **Reference-free** metrics for faithfulness and answer relevancy (no ground truth required).
- **Standard RAG metrics**: Faithfulness, Answer Relevancy, Context Precision, Context Recall.
- **HuggingFace compatible**: Supports LangChain LLMs and embeddings via `LangchainLLMWrapper` and `LangchainEmbeddingsWrapper`.
- **Aligned with Phase 2**: Uses the same remote LLM (Qwen/Qwen2.5-1.5B-Instruct) as judge.

### Alternatives considered

- **DeepEval**: Similar capabilities; less mature ecosystem.
- **LangSmith**: Proprietary; not fully open-source for self-hosted use.

## Metrics evaluated

| Metric | Description |
|--------|-------------|
| **Faithfulness** | Proportion of answer claims supported by the retrieved context (0–1) |
| **Answer Relevancy** | Relevance of the answer to the question (0–1) |
| **Context Precision** | Quality of retrieval: relevant chunks ranked higher (0–1) |
| **Context Recall** | How much of the ground truth is covered by the retrieved context (requires ground truth) |
| **Latency** | Average and max time per RAG query (custom metric) |

## Dataset

- **Source**: `question_list.docx`
- **Format**: One question per paragraph; optional Q/A pairs via "Q:" / "A:" or "Question:" / "Answer:" prefixes
- **Size**: ≥15 question/answer pairs

## Limitations of small models as judges

Small models (1.5B–7B parameters) used as LLM judges have known limitations:

1. **Faithfulness / hallucination**: May misclassify subtle hallucinations or over-penalize safe responses.
2. **Answer relevancy**: May favor literal overlap over semantic relevance.
3. **Context recall**: Often less accurate than larger models when judging coverage of ground truth.
4. **Consistency**: Scores can vary between runs; temperature and prompt sensitivity are higher.

**Mitigation**: Results are documented as indicative; production-grade evaluation should use larger judge models (e.g. 70B+) or human evaluation when feasible.

## Documented improvement (based on results)

**Suggested improvement**: If **Context Precision** is low, retrieval may be returning noisy chunks. Recommended actions:

1. **Increase similarity threshold** (`RETRIEVAL_SIMILARITY_THRESHOLD`) to filter weak matches.
2. **Use MMR** instead of pure top-k for more diverse, less redundant contexts.
3. **Adjust chunking** (chunk size, overlap) so chunks better match query granularity.
4. **Re-evaluate** after changes and compare `eval_report.json` between runs.

## Running the evaluation

```bash
# 1. Ingest documents (if not already done)
docker compose run --rm -v ./docs:/app/docs -v ./Real_Estate_RAG_Documents.xlsx:/app/Real_Estate_RAG_Documents.xlsx app python -m app.ingest

# 2. Run evaluation (mount question_list.pdf or .docx)
docker compose run --rm -v ./question_list.pdf:/app/question_list.pdf -v ./eval_output:/app/eval_output -e EVAL_REPORT_PATH=/app/eval_output/eval_report.json app python -m app.eval.run_eval
```

### Environment options

| Variable | Description |
|----------|-------------|
| `EVAL_DATASET_PATH` | Path to question list (PDF/DOCX). Default: `/app/question_list.pdf` |
| `EVAL_REPORT_PATH` | Output JSON path. Default: `/app/eval_report.json` |
| `EVAL_DEBUG` | Set to `1` or `true` to print sample Q/A/context previews to stderr |
| `EVAL_LLM_MODEL` | Override LLM for RAGAS judge (e.g. `mistralai/Mistral-7B-Instruct-v0.2`). Small models (1.5B) produce unreliable scores. |
| `EVAL_USE_UNFILTERED_RETRIEVAL` | If `true` (default), eval uses unfiltered retrieval (no min chunk length/words) so short relevant chunks are kept; improves Faithfulness and Context Precision. |
| `EVAL_RETRIEVAL_TOP_K` | Number of chunks per question during eval (default `12`). Set to `0` to use `RETRIEVAL_TOP_K`. Slightly higher k can improve metrics. |

Report will be at `./eval_output/eval_report.json` when using the mount above.
