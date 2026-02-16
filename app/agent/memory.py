"""
Conversational memory for the agent. In-memory per session (no Redis).
Uses LangGraph's MemorySaver checkpointer via thread_id.
"""
