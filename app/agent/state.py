"""
LangGraph agent state. TypedDict for type-safe state passing.
"""
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """State for the LangGraph agent. All fields optional to support partial updates."""

    messages: Annotated[list[BaseMessage], add_messages]
    query: str
    route: Literal["rag", "web_search", "general"]
    context_docs: list
    context_str: str
    rag_answer: str
    citations: list[dict]
    relevance_score: float
    is_relevant: bool
    hallucination_score: float
    is_hallucination: bool
    web_search_results: str
    final_answer: str
    session_id: str
