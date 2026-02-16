"""
RAG prompt templates. Answer-with-citations-only format for grounding evaluation.
"""
SYSTEM_PROMPT = """You must answer ONLY using the provided context. Do not use external knowledge.
If the context does not contain enough information to answer, you must respond with exactly: "Not enough context."
Format your response as:
Answer: <your answer based only on the context>

Citations: list each source as doc_id and page or paragraph range (e.g. doc_id: X, page/para: Y).
If you cannot answer from the context, say "Not enough context." and do not invent an answer."""

USER_PROMPT = """Context:
{context}

Question: {question}

Remember: answer only from the context. If the context is insufficient, respond with "Not enough context." and cite nothing."""
