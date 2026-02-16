"""
Custom tools for the LangGraph agent.
"""
from langchain_core.tools import tool

from app.rag import query_rag


@tool
def chatbot_rag_search(query: str) -> str:
    """
    Search the RAG knowledge base for answers about housing, real estate, and home loans.
    Use this when the user asks questions about documents in the corpus.
    Returns answer with citations or 'Not enough context.' if no relevant documents found.
    """
    out = query_rag(query, retrieval_technique="top_k")
    answer = out["answer"]
    citations = out.get("citations", [])
    if citations:
        cits = ", ".join(f"{c.get('doc_id', '?')}: {c.get('page_or_para', '?')}" for c in citations)
        return f"{answer}\n\nSources: {cits}"
    return answer


@tool
def chatbot_rag_search_mmr(query: str) -> str:
    """
    Search the RAG knowledge base using MMR (Max Marginal Relevance) for diverse results.
    Use when the user may benefit from varied sources on the same topic.
    Returns answer with citations or 'Not enough context.' if no relevant documents found.
    """
    out = query_rag(query, retrieval_technique="mmr")
    answer = out["answer"]
    citations = out.get("citations", [])
    if citations:
        cits = ", ".join(f"{c.get('doc_id', '?')}: {c.get('page_or_para', '?')}" for c in citations)
        return f"{answer}\n\nSources: {cits}"
    return answer
