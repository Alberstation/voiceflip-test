"""
Service layer: agent invocation, document ingestion, retrieval.
"""
from pathlib import Path
from typing import Any

from app.chunking import chunk_content, get_doc_chunking_from_xlsx
from app.constants import CHUNKING_OVERLAP, RETRIEVAL_MMR, RETRIEVAL_TOP_K, SUPPORTED_DOC_EXTENSIONS
from app.loaders import load_document
from app.retrieval import retrieval_mmr, retrieval_similarity_top_k
from app.vectorstore import chunks_to_langchain_docs, ensure_collection, get_vector_store


def invoke_agent(message: str, session_id: str) -> dict[str, Any]:
    """Invoke the LangGraph agent with conversational memory."""
    from langchain_core.messages import HumanMessage

    from app.agent.graph import get_agent

    agent = get_agent()
    config = {"configurable": {"thread_id": session_id}}
    result = agent.invoke(
        {"messages": [HumanMessage(content=message)]},
        config=config,
    )
    messages = result.get("messages", [])
    last = messages[-1] if messages else None
    answer = last.content if last and hasattr(last, "content") else str(last) if last else ""
    return {"answer": answer, "messages": [{"role": "assistant", "content": answer}]}


def ingest_documents_from_files(files: list[tuple[str, bytes]], docs_dir: Path | None = None) -> dict[str, Any]:
    """
    Ingest uploaded files into RAG. Returns counts and any errors.
    files: list of (filename, content_bytes)
    """
    docs_dir = docs_dir or Path("/tmp/rag_uploads")
    docs_dir.mkdir(parents=True, exist_ok=True)
    chunking_map = {}
    xlsx_path = Path("/app/Real_Estate_RAG_Documents.xlsx")
    if xlsx_path.exists():
        chunking_map = get_doc_chunking_from_xlsx(xlsx_path)

    all_chunks: list[tuple[str, dict]] = []
    ingested: list[str] = []
    errors: list[str] = []

    for filename, content in files:
        name = Path(filename).name
        if Path(filename).suffix.lower() not in SUPPORTED_DOC_EXTENSIONS:
            errors.append(f"Unsupported format: {filename}")
            continue
        path = docs_dir / name
        try:
            path.write_bytes(content)
            blocks = load_document(path)
            if not blocks:
                errors.append(f"No content: {filename}")
                path.unlink(missing_ok=True)
                continue
            strategy = chunking_map.get(name) or chunking_map.get(Path(name).stem) or CHUNKING_OVERLAP
            chunks = chunk_content(blocks, strategy=strategy)
            all_chunks.extend(chunks)
            ingested.append(name)
            path.unlink(missing_ok=True)
        except Exception as e:
            errors.append(f"{filename}: {e}")

    if not all_chunks:
        return {"ingested": 0, "chunks": 0, "files": ingested, "errors": errors}

    ensure_collection()
    docs = chunks_to_langchain_docs(all_chunks)
    store = get_vector_store()
    store.add_documents(docs)
    return {"ingested": len(ingested), "chunks": len(docs), "files": ingested, "errors": errors}


def retrieve(query: str, technique: str) -> dict[str, Any]:
    """Retrieve documents using top_k or MMR. Returns docs with content and metadata."""
    store = get_vector_store()
    if technique == RETRIEVAL_MMR:
        docs = retrieval_mmr(store, query)
    else:
        docs = retrieval_similarity_top_k(store, query)
    return {
        "query": query,
        "technique": technique,
        "count": len(docs),
        "documents": [
            {"content": d.page_content, "metadata": d.metadata}
            for d in docs
        ],
    }
