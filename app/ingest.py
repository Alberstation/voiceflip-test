"""
Ingestion CLI: load DOCX/HTML, chunk, embed, store in Qdrant.
Run inside container: docker compose run --rm app python -m app.ingest
"""
from pathlib import Path

from app.chunking import chunk_content, get_doc_chunking_from_xlsx
from app.config import settings
from app.constants import CHUNKING_OVERLAP, SUPPORTED_DOC_EXTENSIONS
from app.loaders import load_document
from app.vectorstore import chunks_to_langchain_docs, ensure_collection, get_vector_store


def discover_supported_files(docs_dir: Path) -> list[Path]:
    """Find all DOCX/HTML files under docs_dir."""
    return sorted(
        f for f in docs_dir.rglob("*")
        if f.is_file() and f.suffix.lower() in SUPPORTED_DOC_EXTENSIONS
    )


def load_and_chunk_files(files: list[Path], chunking_map: dict) -> list[tuple[str, dict]]:
    """Load each file, apply chunking strategy, return flat list of (text, metadata) chunks."""
    all_chunks: list[tuple[str, dict]] = []
    for path in files:
        try:
            blocks = load_document(path)
            if not blocks:
                continue
            strategy = chunking_map.get(path.name) or chunking_map.get(path.stem) or CHUNKING_OVERLAP
            chunks = chunk_content(blocks, strategy=strategy)
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"Skip {path}: {e}")
    return all_chunks


def main() -> None:
    docs_dir = settings.docs_path()
    xlsx_path = settings.metadata_xlsx_path()
    if not docs_dir.exists():
        print(f"Docs dir not found: {docs_dir}")
        return

    chunking_map = get_doc_chunking_from_xlsx(xlsx_path) if xlsx_path.exists() else {}
    files = discover_supported_files(docs_dir)
    if not files:
        print(f"No DOCX/HTML files in {docs_dir}")
        return

    all_chunks = load_and_chunk_files(files, chunking_map)
    if not all_chunks:
        print("No chunks produced.")
        return

    ensure_collection()
    docs = chunks_to_langchain_docs(all_chunks)
    store = get_vector_store()
    store.add_documents(docs)
    print(f"Ingested {len(docs)} chunks from {len(files)} files.")


if __name__ == "__main__":
    main()
