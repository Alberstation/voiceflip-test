"""
LangGraph agent nodes: query routing, RAG, relevance, hallucination, web search.
"""
from typing import Literal

import structlog
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools import DuckDuckGoSearchRun

from app.agent.state import AgentState
from app.constants import NOT_ENOUGH_CONTEXT_MSG
from app.llm import get_llm
from app.rag import format_context, query_rag
from app.retrieval import retrieval_with_scores
from app.vectorstore import get_vector_store

logger = structlog.get_logger()

# Router prompt: classify query type
ROUTER_PROMPT = """Classify the user query into one of these categories:
- "rag": Question about housing, real estate, home loans, tax credits, mortgages, homebuyer guides, or documents in our knowledge base.
- "web_search": Current events, news, prices, or information that may not be in our documents.
- "general": Greetings, chitchat, thanks, or simple conversational messages.

Respond with exactly one word: rag, web_search, or general."""

RELEVANCE_PROMPT = """Evaluate if the retrieved context is relevant to answer the question.
Context: {context}
Question: {question}
Answer: {answer}

Respond with "yes" or "no" only."""

HALLUCINATION_PROMPT = """Does this answer contain information that is NOT supported by the provided context?
Context: {context}
Answer: {answer}

Respond with "yes" or "no" only. If the answer says "Not enough context", respond "no"."""


def query_router_node(state: AgentState) -> AgentState:
    """Route query to RAG, web search, or general chat."""
    messages = state.get("messages", [])
    if not messages:
        return {"route": "general", "query": ""}
    last = messages[-1]
    query = last.content if hasattr(last, "content") else str(last)
    query = str(query).strip()
    state["query"] = query

    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", ROUTER_PROMPT),
            ("human", "{query}"),
        ])
        llm = get_llm()
        resp = prompt | llm
        out = resp.invoke({"query": query})
        raw = (out.content if hasattr(out, "content") else str(out)).strip().lower()
        route: Literal["rag", "web_search", "general"] = "general"
        if "web" in raw or "search" in raw:
            route = "web_search"
        elif "rag" in raw or "doc" in raw or "knowledge" in raw:
            route = "rag"
        logger.info("query_routed", query=query[:80], route=route)
        return {"route": route, "query": query}
    except Exception as e:
        logger.warning("router_fallback", error=str(e), route="rag")
        return {"route": "rag", "query": query}


def rag_node(state: AgentState) -> AgentState:
    """Run RAG pipeline; store context, answer, and citations."""
    query = state.get("query", "")
    if not query:
        return {"rag_answer": "", "context_str": "", "context_docs": [], "citations": []}

    store = get_vector_store()
    docs, scores, below_threshold = retrieval_with_scores(store, query, technique="top_k")

    if below_threshold or not docs:
        logger.info("rag_below_threshold", query=query[:80])
        return {
            "rag_answer": NOT_ENOUGH_CONTEXT_MSG,
            "context_str": "",
            "context_docs": [],
            "citations": [],
            "is_relevant": False,
        }

    context_str = format_context(docs)
    out = query_rag(query, retrieval_technique="top_k")
    citations = out.get("citations", [])

    logger.info("rag_complete", query=query[:80], num_docs=len(docs), num_citations=len(citations))
    return {
        "rag_answer": out["answer"],
        "context_str": context_str,
        "context_docs": [{"content": d.page_content[:300], "metadata": d.metadata} for d in docs],
        "citations": citations,
        "relevance_score": float(sum(scores) / len(scores)) if scores else 0.0,
    }


def relevance_node(state: AgentState) -> AgentState:
    """Evaluate if retrieved context is relevant to the question."""
    query = state.get("query", "")
    context_str = state.get("context_str", "")
    rag_answer = state.get("rag_answer", "")

    if not context_str or not query:
        return {"is_relevant": False}

    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", RELEVANCE_PROMPT),
            ("human", ""),
        ])
        llm = get_llm()
        resp = prompt | llm
        out = resp.invoke({
            "context": context_str[:1500],
            "question": query,
            "answer": rag_answer[:500],
        })
        raw = (out.content if hasattr(out, "content") else str(out)).strip().lower()
        is_relevant = "yes" in raw
        logger.info("relevance_evaluated", query=query[:80], is_relevant=is_relevant)
        return {"is_relevant": is_relevant}
    except Exception as e:
        logger.warning("relevance_fallback", error=str(e), is_relevant=True)
        return {"is_relevant": True}


def hallucination_node(state: AgentState) -> AgentState:
    """Detect if answer may be hallucinated (not grounded in context)."""
    context_str = state.get("context_str", "")
    rag_answer = state.get("rag_answer", "")

    if NOT_ENOUGH_CONTEXT_MSG in rag_answer or not context_str:
        return {"is_hallucination": False}

    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", HALLUCINATION_PROMPT),
            ("human", ""),
        ])
        llm = get_llm()
        resp = prompt | llm
        out = resp.invoke({"context": context_str[:1500], "answer": rag_answer[:500]})
        raw = (out.content if hasattr(out, "content") else str(out)).strip().lower()
        is_hallucination = "yes" in raw
        logger.info("hallucination_checked", is_hallucination=is_hallucination)
        return {"is_hallucination": is_hallucination}
    except Exception as e:
        logger.warning("hallucination_fallback", error=str(e), is_hallucination=False)
        return {"is_hallucination": False}


def web_search_node(state: AgentState) -> AgentState:
    """Fallback: search the web when RAG insufficient or relevance low."""
    query = state.get("query", "")
    if not query:
        return {"web_search_results": "", "final_answer": ""}

    try:
        search = DuckDuckGoSearchRun()
        results = search.invoke(query)
        logger.info("web_search_done", query=query[:80], results_len=len(str(results)[:500]))
        # Summarize with LLM
        llm = get_llm()
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Summarize the following web search results for the user's question. Be concise."),
            ("human", "Question: {query}\n\nResults: {results}"),
        ])
        chain = prompt | llm
        out = chain.invoke({"query": query, "results": str(results)[:3000]})
        answer = out.content if hasattr(out, "content") else str(out)
        return {"web_search_results": str(results)[:1000], "final_answer": answer}
    except Exception as e:
        logger.error("web_search_failed", error=str(e))
        return {"web_search_results": "", "final_answer": f"Web search failed: {e}"}


def general_node(state: AgentState) -> AgentState:
    """Handle general chat (greetings, thanks, chitchat)."""
    query = state.get("query", "")
    if not query:
        return {"final_answer": "How can I help you today?"}

    try:
        llm = get_llm()
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful real estate assistant. Respond briefly and friendly to chitchat, greetings, or thanks."),
            ("human", "{query}"),
        ])
        chain = prompt | llm
        out = chain.invoke({"query": query})
        answer = out.content if hasattr(out, "content") else str(out)
        return {"final_answer": answer}
    except Exception as e:
        logger.error("general_node_failed", error=str(e))
        return {"final_answer": f"Sorry, I encountered an error: {e}"}


def finalize_node(state: AgentState) -> AgentState:
    """Produce final answer and update messages."""
    route = state.get("route", "general")
    final_answer = state.get("final_answer", "")
    rag_answer = state.get("rag_answer", "")
    citations = state.get("citations", [])

    # Prefer final_answer when set (web search or general); else use RAG answer
    if final_answer:
        answer = final_answer
    elif rag_answer:
        answer = rag_answer
        if citations:
            cits = ", ".join(f"{c.get('doc_id', '?')}: {c.get('page_or_para', '?')}" for c in citations)
            answer = f"{rag_answer}\n\nSources: {cits}"
    else:
        answer = "I couldn't generate an answer. Please try again."

    messages = state.get("messages", [])
    messages.append(AIMessage(content=answer))
    logger.info("finalized_answer", route=route, answer_len=len(answer))
    return {"messages": messages, "final_answer": answer}
