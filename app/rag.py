"""
RAG pipeline: retrieval + structured prompt (answer with citations only).
Edge case: if all retrieval scores below threshold, respond with NOT_ENOUGH_CONTEXT_MSG.
"""
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

from app.constants import NOT_ENOUGH_CONTEXT_MSG
from app.llm import get_llm
from app.prompts import SYSTEM_PROMPT, USER_PROMPT
from app.retrieval import retrieval_with_scores
from app.vectorstore import get_vector_store


def format_context(docs: list[Document]) -> str:
    """Format retrieved documents for the LLM prompt."""
    parts = []
    for i, d in enumerate(docs, 1):
        doc_id = d.metadata.get("doc_id") or d.metadata.get("source") or "unknown"
        page_para = d.metadata.get("page_or_para") or d.metadata.get("row_range") or "—"
        parts.append(f"[{i}] (doc_id: {doc_id}, page/para: {page_para})\n{d.page_content}")
    return "\n\n".join(parts)


def build_citations(docs: list[Document]) -> list[dict]:
    """Extract citation metadata from retrieved documents."""
    return [
        {
            "doc_id": d.metadata.get("doc_id") or d.metadata.get("source"),
            "page_or_para": d.metadata.get("page_or_para") or d.metadata.get("row_range"),
        }
        for d in docs
    ]


def query_rag(question: str, retrieval_technique: str = "top_k", *, eval_mode: bool = False) -> dict:
    """
    Run RAG: retrieve, then generate answer with citations.
    retrieval_technique: "top_k" or "mmr"
    eval_mode: if True, retrieval uses unfiltered chunks and eval_retrieval_top_k (for evaluation runs).
    Returns dict with keys: answer, citations, below_threshold, context_used.
    """
    store = get_vector_store()
    docs, scores, below_threshold = retrieval_with_scores(
        store, question, technique=retrieval_technique, eval_mode=eval_mode
    )

    if below_threshold or not docs:
        return {
            "answer": NOT_ENOUGH_CONTEXT_MSG,
            "citations": [],
            "below_threshold": True,
            "context_used": [],
        }

    context_str = format_context(docs)
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", USER_PROMPT),
    ])
    chain = prompt | get_llm()
    response = chain.invoke({"context": context_str, "question": question})
    text = response.content if hasattr(response, "content") else str(response)

    return {
        "answer": text,
        "citations": build_citations(docs),
        "below_threshold": False,
        "context_used": [{"content": d.page_content[:200], "metadata": d.metadata} for d in docs],
    }
