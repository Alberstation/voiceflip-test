"""
Phase 4 — RAG System Evaluation.
Executable script: run inside Docker with RAG ingested.
Usage: docker compose run --rm -v ./question_list.docx:/app/question_list.docx app python -m app.eval.run_eval
"""
import json
import os
import sys
import time
from pathlib import Path

from datasets import Dataset

from app.config import settings
from app.eval.dataset import load_questions
from app.rag import query_rag
from app.retrieval import retrieval_with_scores
from app.vectorstore import get_vector_store

EVAL_QUESTION_PATH = Path(os.environ.get("EVAL_DATASET_PATH", "/app/question_list.pdf"))
EVAL_REPORT_PATH = Path(os.environ.get("EVAL_REPORT_PATH", "/app/eval_report.json"))
EVAL_DEBUG = os.environ.get("EVAL_DEBUG", "").lower() in ("1", "true", "yes")


def run_rag_for_eval(questions: list[dict]) -> tuple[list[dict], list[float]]:
    """Run RAG for each question; return samples with answer, contexts, latency per query.
    Uses eval_mode=True so retrieval is unfiltered (no min chunk length/words) and eval_retrieval_top_k
    for better RAGAS metrics (more relevant short chunks, more context per question).
    """
    store = get_vector_store()
    eval_mode = getattr(settings, "eval_use_unfiltered_retrieval", True)
    samples: list[dict] = []
    latencies: list[float] = []
    for qa in questions:
        q = qa["question"]
        gt = qa.get("ground_truth", "")
        t0 = time.perf_counter()
        docs, scores, _ = retrieval_with_scores(store, q, technique="top_k", eval_mode=eval_mode)
        contexts = [d.page_content for d in docs]
        out = query_rag(q, retrieval_technique="top_k", eval_mode=eval_mode)
        answer = out["answer"]
        t1 = time.perf_counter()
        latencies.append(t1 - t0)
        samples.append({
            "question": q,
            "answer": answer,
            "contexts": contexts,
            "ground_truth": gt or "",
        })
    return samples, latencies


def run_evaluation(
    questions_path: Path,
    report_path: Path | None = None,
    max_questions: int | None = None,
) -> dict:
    """
    Run RAGAS evaluation on questions from the given path. Returns report dict.
    If report_path is set, also writes the report JSON to that file.
    max_questions: cap on how many questions to use (reduces token usage / free-tier usage). Default from settings.eval_max_questions.
    """
    all_questions = load_questions(questions_path)
    if len(all_questions) < 1:
        raise ValueError(f"No questions loaded from {questions_path}")
    if len(all_questions) < 15:
        raise ValueError(f"Need >= 15 questions for RAGAS; found {len(all_questions)}")

    cap = max_questions if max_questions is not None else settings.eval_max_questions
    cap = min(cap, len(all_questions))  # Use all questions up to cap (default 20)
    questions = all_questions[:cap]
    if cap < len(all_questions):
        import structlog
        structlog.get_logger().info("eval_capped_questions", total=len(all_questions), used=cap, reason="eval_max_questions / token limit")

    samples, latencies = run_rag_for_eval(questions)

    # Sanity checks: ensure contexts are present (RAGAS needs them)
    empty_ctx = sum(1 for s in samples if not s["contexts"])
    if empty_ctx > 0:
        print(f"Warning: {empty_ctx}/{len(samples)} samples have empty contexts.", file=sys.stderr)

    if EVAL_DEBUG:
        for i, s in enumerate(samples[:3]):
            ctx_preview = (s["contexts"][0][:150] + "...") if s["contexts"] else "(none)"
            print(f"[DEBUG] Sample {i}: q={s['question'][:60]}... ctx_cnt={len(s['contexts'])} first_ctx={ctx_preview}", file=sys.stderr)

    # RAGAS v0.2+ expects: user_input, retrieved_contexts, response, reference (or legacy: question, answer, contexts, ground_truth)
    data = {
        "question": [s["question"] for s in samples],
        "answer": [s["answer"] for s in samples],
        "contexts": [s["contexts"] for s in samples],
        "ground_truth": [s["ground_truth"] for s in samples],
    }
    hf_dataset = Dataset.from_dict(data)

    try:
        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
    except ImportError:
        try:
            from ragas import evaluate
            from ragas.metrics.ragas import faithfulness
            from ragas.metrics import answer_relevancy, context_precision, context_recall
        except ImportError as e:
            raise RuntimeError("RAGAS not installed. pip install ragas") from e

    # RAGAS v0.2+ expects user_input, response, retrieved_contexts, reference
    column_map = {
        "user_input": "question",
        "response": "answer",
        "retrieved_contexts": "contexts",
        "reference": "ground_truth",
    }

    # Use HF Dataset; evaluate() will remap columns via column_map
    dataset = hf_dataset

    from langchain_huggingface import HuggingFaceEndpointEmbeddings
    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddingsWrapper

    from app.llm import get_llm

    # Use dedicated eval LLM if set; higher max_tokens to avoid LLMDidNotFinishException
    if settings.eval_llm_model:
        chat_llm = get_llm(model=settings.eval_llm_model, max_new_tokens=settings.eval_llm_max_new_tokens)
    else:
        chat_llm = get_llm()
    embeddings = HuggingFaceEndpointEmbeddings(
        model=settings.embedding_model,
        huggingfacehub_api_token=settings.huggingfacehub_api_token or None,
        task="feature-extraction",
    )
    ragas_llm = LangchainLLMWrapper(chat_llm)
    ragas_embeddings = LangchainEmbeddingsWrapper(embeddings)

    has_gt = sum(1 for s in samples if s["ground_truth"])
    metrics_list = [faithfulness, answer_relevancy]
    if not getattr(settings, "eval_skip_context_precision", False):
        metrics_list.append(context_precision)
    if has_gt > 0:
        metrics_list.append(context_recall)

    result = evaluate(
        dataset,
        metrics=metrics_list,
        llm=ragas_llm,
        embeddings=ragas_embeddings,
        column_map=column_map,
        show_progress=False,
    )

    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    max_latency = max(latencies) if latencies else 0

    scores = {}
    metric_keys = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]

    def _find_col(df, key: str):
        if key in df.columns:
            return key
        low = key.lower()
        for c in df.columns:
            if c and c.lower() == low:
                return c
        return None

    if hasattr(result, "to_pandas") and callable(getattr(result, "to_pandas")):
        df = result.to_pandas()
        for col in metric_keys:
            c = _find_col(df, col)
            if c is not None:
                vals = df[c].dropna()
                scores[col] = round(float(vals.mean()), 4) if len(vals) > 0 else "N/A"
    if hasattr(result, "scores") and result.scores:
        # RAGAS v0.2+ returns result.scores as list of dicts; use to fill any missing
        import numpy as np

        def _get_metric(row: dict, key: str):
            v = row.get(key)
            if v is not None:
                return v
            for rk, rv in row.items():
                if rk and rk.lower() == key.lower():
                    return rv
            return None

        for k in metric_keys:
            if k in scores:
                continue
            vals = [_get_metric(r, k) for r in result.scores if isinstance(r, dict)]
            vals = [v for v in vals if v is not None and isinstance(v, (int, float)) and not (isinstance(v, float) and np.isnan(v))]
            if vals:
                scores[k] = round(float(np.mean(vals)), 4)
    for k in metric_keys:
        if k not in scores:
            v = getattr(result, k, "N/A")
            scores[k] = round(float(v), 4) if isinstance(v, (int, float)) else "N/A"

    faithfulness_val = scores.get("faithfulness")
    if isinstance(faithfulness_val, (int, float)):
        hallucination_score = round(1.0 - float(faithfulness_val), 4)
    else:
        hallucination_score = "N/A"

    llm_judge = settings.eval_llm_model or settings.llm_model
    report = {
        "num_questions": len(questions),
        "metrics": {
            **scores,
            "hallucination_score": hallucination_score,
            "latency_avg_seconds": round(avg_latency, 2),
            "latency_max_seconds": round(max_latency, 2),
        },
        "tool": "RAGAS",
        "llm_judge": llm_judge,
        "limitations": "Small models (1.5B-7B) as judges have known limitations. Set EVAL_LLM_MODEL to a 7B+ model for more reliable scores.",
    }

    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

    return report


def main() -> int:
    """Run evaluation and print aggregated report."""
    path = EVAL_QUESTION_PATH
    if not path.exists():
        print(f"Evaluation dataset not found: {path}", file=sys.stderr)
        print("Mount question_list.pdf or question_list.docx: -v ./question_list.pdf:/app/question_list.pdf", file=sys.stderr)
        return 1

    try:
        report = run_evaluation(path, report_path=EVAL_REPORT_PATH)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 1

    print("\n" + "=" * 60)
    print("RAG EVALUATION REPORT")
    print("=" * 60)
    print(json.dumps(report, indent=2))
    print("=" * 60)
    print(f"Report saved to {EVAL_REPORT_PATH}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
