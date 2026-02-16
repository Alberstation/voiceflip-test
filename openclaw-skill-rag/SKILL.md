---
name: rag-query
description: Query the VoiceFlip RAG API to get answers from ingested documents (real estate, tax credits, policies). Use when the user asks about document content or wants a RAG-backed answer.
metadata: {"openclaw":{"always":true}}
---

# RAG Query (VoiceFlip)

## What it does

Sends a natural-language question to the VoiceFlip RAG service and returns the answer with citations. The RAG system uses a vector store (Qdrant) and an LLM to answer from ingested DOCX/HTML documents.

## When to use

- User asks about real estate, tax credits, home buyers, or document content.
- User explicitly asks to "query RAG", "search documents", or "ask the knowledge base".

## How to use (exec)

Run the script with the user's question as a single argument. The script calls the RAG API and prints the answer.

```bash
bash "{baseDir}/query-rag.sh" "USER_QUESTION_HERE"
```

Replace `USER_QUESTION_HERE` with the exact question (properly escaped for the shell). Use `top_k` retrieval unless the user asks for diversity, then use `mmr`.

## Inputs

- **Question** (required): Natural language question to answer from the document store.

## Output

The script prints the RAG answer (and optionally citations). Return that text to the user.

## Guardrails

- Do not expose internal URLs or API keys in the reply.
- If the script fails (e.g. connection refused), tell the user the RAG service may be offline and suggest checking that the VoiceFlip stack is running.
