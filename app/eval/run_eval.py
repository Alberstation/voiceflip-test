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


def run_rag_for_eval(questions: list[dict]) -> tuple[list[dict], list[float]]:
    """Run RAG for each question; return samples with answer, contexts, latency per query."""
    store = get_vector_store()
    samples: list[dict] = []
    latencies: list[float] = []
    for qa in questions:
        q = qa["question"]
        gt = qa.get("ground_truth", "")
        t0 = time.perf_counter()
        docs, scores, _ = retrieval_with_scores(store, q, technique="top_k")
        contexts = [d.page_content for d in docs]
        out = query_rag(q, retrieval_technique="top_k")
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


def run_evaluation(questions_path: Path, report_path: Path | None = None) -> dict:
    """
    Run RAGAS evaluation on questions from the given path. Returns report dict.
    If report_path is set, also writes the report JSON to that file.
    """
    questions = load_questions(questions_path)
    if len(questions) < 1:
        raise ValueError(f"No questions loaded from {questions_path}")
    if len(questions) < 15:
        raise ValueError(f"Need >= 15 questions for RAGAS; found {len(questions)}")

    samples, latencies = run_rag_for_eval(questions)

    data = {
        "question": [s["question"] for s in samples],
        "answer": [s["answer"] for s in samples],
        "contexts": [s["contexts"] for s in samples],
        "ground_truth": [s["ground_truth"] for s in samples],
    }
    dataset = Dataset.from_dict(data)

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

    from langchain_huggingface import HuggingFaceEndpointEmbeddings
    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddingsWrapper

    from app.llm import get_llm

    chat_llm = get_llm()
    embeddings = HuggingFaceEndpointEmbeddings(
        model=settings.embedding_model,
        huggingfacehub_api_token=settings.huggingfacehub_api_token or None,
        task="feature-extraction",
    )
    ragas_llm = LangchainLLMWrapper(chat_llm)
    ragas_embeddings = LangchainEmbeddingsWrapper(embeddings)

    has_gt = sum(1 for s in samples if s["ground_truth"])
    metrics_list = [faithfulness, answer_relevancy, context_precision]
    if has_gt > 0:
        metrics_list.append(context_recall)

    result = evaluate(
        dataset,
        metrics=metrics_list,
        llm=ragas_llm,
        embeddings=ragas_embeddings,
        show_progress=False,
    )

    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    max_latency = max(latencies) if latencies else 0

    scores = {}
    if hasattr(result, "to_pandas"):
        df = result.to_pandas()
        for col in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
            if col in df.columns:
                vals = df[col].dropna()
                scores[col] = round(float(vals.mean()), 4) if len(vals) > 0 else "N/A"
    else:
        for k in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
            scores[k] = getattr(result, k, "N/A")
            if isinstance(scores[k], (int, float)):
                scores[k] = round(float(scores[k]), 4)

    faithfulness_val = scores.get("faithfulness")
    if isinstance(faithfulness_val, (int, float)):
        hallucination_score = round(1.0 - float(faithfulness_val), 4)
    else:
        hallucination_score = "N/A"

    report = {
        "num_questions": len(questions),
        "metrics": {
            **scores,
            "hallucination_score": hallucination_score,
            "latency_avg_seconds": round(avg_latency, 2),
            "latency_max_seconds": round(max_latency, 2),
        },
        "tool": "RAGAS",
        "llm_judge": settings.llm_model,
        "limitations": "Small models (1.5B-7B) as judges have known limitations in evaluation quality.",
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
