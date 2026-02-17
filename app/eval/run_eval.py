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


def main() -> int:
    """Run evaluation and print aggregated report."""
    path = EVAL_QUESTION_PATH
    if not path.exists():
        print(f"Evaluation dataset not found: {path}", file=sys.stderr)
        print("Mount question_list.pdf or question_list.docx: -v ./question_list.pdf:/app/question_list.pdf", file=sys.stderr)
        return 1

    questions = load_questions(path)
    if len(questions) < 15:
        print(f"Need >= 15 questions; found {len(questions)} in {path}", file=sys.stderr)
        return 1

    print(f"Running RAG for {len(questions)} questions...")
    samples, latencies = run_rag_for_eval(questions)

    # Build HuggingFace Dataset for RAGAS
    data = {
        "question": [s["question"] for s in samples],
        "answer": [s["answer"] for s in samples],
        "contexts": [s["contexts"] for s in samples],
        "ground_truth": [s["ground_truth"] for s in samples],
    }
    dataset = Dataset.from_dict(data)

    # RAGAS: faithfulness, answer_relevancy, context_precision, context_recall (if ground_truth)
    try:
        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
    except ImportError:
        try:
            from ragas import evaluate
            from ragas.metrics.ragas import faithfulness
            from ragas.metrics import answer_relevancy, context_precision, context_recall
        except ImportError:
            print("RAGAS not installed. pip install ragas", file=sys.stderr)
            return 1

    from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
    from langchain_huggingface import HuggingFaceEndpointEmbeddings
    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddingsWrapper

    llm = HuggingFaceEndpoint(
        repo_id=settings.llm_model,
        task="text-generation",
        huggingfacehub_api_token=settings.huggingfacehub_api_token or None,
        max_new_tokens=settings.llm_max_new_tokens,
        temperature=settings.llm_temperature,
        top_p=settings.llm_top_p,
    )
    chat_llm = ChatHuggingFace(llm=llm)
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

    print("Running RAGAS evaluation...")
    result = evaluate(
        dataset,
        metrics=metrics_list,
        llm=ragas_llm,
        embeddings=ragas_embeddings,
        show_progress=True,
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

    print("\n" + "=" * 60)
    print("RAG EVALUATION REPORT")
    print("=" * 60)
    print(json.dumps(report, indent=2))
    print("=" * 60)

    out_path = EVAL_REPORT_PATH
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Report saved to {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
