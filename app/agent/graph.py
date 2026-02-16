"""
LangGraph StateGraph: query routing, RAG, relevance, hallucination, web search.
"""
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from app.agent.nodes import (
    finalize_node,
    general_node,
    hallucination_node,
    query_router_node,
    rag_node,
    relevance_node,
    web_search_node,
)
from app.agent.state import AgentState


def route_after_relevance(state: AgentState) -> str:
    """After relevance: hallucination if relevant, else web search fallback."""
    return "hallucination" if state.get("is_relevant", False) else "web_search"


def route_from_router(state: AgentState) -> str:
    """Route from router to RAG, web search, or general chat."""
    return state.get("route", "general")


def build_agent_graph() -> StateGraph:
    """Build the LangGraph agent with StateGraph and TypedDict state."""
    graph = StateGraph(AgentState)

    graph.add_node("router", query_router_node)
    graph.add_node("rag", rag_node)
    graph.add_node("relevance", relevance_node)
    graph.add_node("hallucination", hallucination_node)
    graph.add_node("web_search", web_search_node)
    graph.add_node("general", general_node)
    graph.add_node("finalize", finalize_node)

    graph.set_entry_point("router")
    graph.add_conditional_edges("router", route_from_router, {
        "rag": "rag",
        "web_search": "web_search",
        "general": "general",
    })

    graph.add_edge("rag", "relevance")
    graph.add_conditional_edges("relevance", route_after_relevance, {
        "hallucination": "hallucination",
        "web_search": "web_search",
    })
    graph.add_edge("hallucination", "finalize")
    graph.add_edge("web_search", "finalize")
    graph.add_edge("general", "finalize")
    graph.add_edge("finalize", END)

    return graph


def get_agent():
    """Return compiled agent with in-memory checkpointer for conversational memory."""
    checkpointer = MemorySaver()
    return build_agent_graph().compile(checkpointer=checkpointer)
