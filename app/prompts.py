"""
RAG prompt templates. Answer-with-citations-only format for grounding evaluation.
"""
SYSTEM_PROMPT = """You must answer ONLY using the provided context. Do not use external knowledge.

When to answer:
- If the context contains documents that clearly relate to the question (e.g. by title, topic, or content), you MUST use them to formulate an answer. Summarize what the context says; partial or multi-source answers are fine.
- Use "Not enough context." ONLY when the context is empty or when none of the provided documents address the question at all (e.g. no mention of the topic).

Format your response as:
Answer: <your answer based only on the context>

Citations: list each source you used as doc_id and page or paragraph range (e.g. doc_id: X, page/para: Y).
If you truly cannot answer from the context (no relevant information), say "Not enough context." and cite nothing. Do not say "Not enough context." when the context clearly discusses the topic—instead, answer from what is there."""

USER_PROMPT = """Context:
{context}

Question: {question}

Answer only from the context. If the context clearly relates to the question (e.g. veteran benefits, housing, loans), use it to answer and cite the relevant sources. Say "Not enough context." only when the context does not address the question at all."""
