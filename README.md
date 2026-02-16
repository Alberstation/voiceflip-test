# RAG AI Engineer — VoiceFlip Technical Test

Retrieval-Augmented Generation pipeline with Docker-based environment, Qdrant vector store, and LangChain.

## Requirements

- **Docker** and **Docker Compose** (v2)
- **Git**
- **Python 3.11+** (optional; runtime is fully containerized)

## Quick Start

1. **Clone the repository**:

   ```bash
   git clone <repo-url>
   cd voiceflip-test
   ```

2. **Environment variables**  
   For Phase 1, run as-is. For Phase 2+ (RAG), copy `.env.example` to `.env` and set your [Hugging Face token](https://huggingface.co/settings/tokens):

   ```bash
   cp .env.example .env
   # Edit .env and set HUGGINGFACEHUB_API_TOKEN
   ```

3. **Start services**:

   ```bash
   docker compose up --build
   ```

   - **app** — FastAPI at `http://localhost:8000`
   - **vectordb** — Qdrant at `http://localhost:6333` (API) and `6334` (gRPC)

4. **Health checks**:

   - [http://localhost:8000/health](http://localhost:8000/health)
   - [http://localhost:6333/readyz](http://localhost:6333/readyz)

---

## Phase 2 — RAG (Docker-only)

**No local Python/pip.** All commands run inside the container.

**Ingest documents** (DOCX/HTML from `docs/`, chunking from `Real_Estate_RAG_Documents.xlsx`):

```bash
docker compose run --rm -v ./docs:/app/docs -v ./Real_Estate_RAG_Documents.xlsx:/app/Real_Estate_RAG_Documents.xlsx app python -m app.ingest
```

**Run unit tests**:

```bash
docker compose run --rm app pytest tests/ -v
```

**Query RAG** (after ingest, with services up):

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What tax credits exist for home buyers?", "retrieval_technique": "top_k"}'
```

Use `retrieval_technique`: `"top_k"` or `"mmr"`.

---

## Project Layout

```
.
├── app/
│   ├── constants.py     # Magic strings, supported formats
│   ├── config.py        # Settings from .env
│   ├── prompts.py       # RAG prompt templates
│   ├── metadata.py      # Excel chunking strategy parsing
│   ├── cleaning.py      # Text normalization
│   ├── loaders.py       # DOCX, HTML loaders
│   ├── chunking.py      # Overlap + row-based chunking
│   ├── embeddings.py    # HuggingFace embeddings
│   ├── vectorstore.py   # Qdrant
│   ├── retrieval.py     # Top-k + MMR, dedupe
│   ├── llm.py           # HuggingFace LLM
│   ├── rag.py           # RAG pipeline
│   ├── ingest.py        # CLI ingest
│   └── main.py          # FastAPI: /health, /query
├── tests/               # Unit tests (run in container)
├── docker-compose.yml
├── Dockerfile
├── .env.example         # All parameters documented
├── pytest.ini
└── requirements.txt
```

---

## Code Conventions

- **Comments and docstrings**: English only.
- **Modularity**: Single responsibility; no scripts > ~80 lines; extract helpers into separate modules.
- **Constants**: Centralized in `app/constants.py`; avoid magic strings.
- **Config**: All tunable parameters via `.env`; see `.env.example`.
- **Type hints**: Use for function signatures and public APIs.
- **Imports**: Group stdlib, third-party, local; alphabetical within groups.

## Architecture

- **Loaders** (`loaders.py`): DOCX, HTML → (text, metadata) blocks.
- **Cleaning** (`cleaning.py`): Conservative text normalization (NFKC, whitespace collapse).
- **Chunking** (`chunking.py`): Overlap or row-based; strategy per doc from Excel (`metadata.py`).
- **Vector Store** (`vectorstore.py`): Qdrant with cosine similarity.
- **Retrieval** (`retrieval.py`): Top-k or MMR; dedupe by (doc_id, page/para).
- **RAG** (`rag.py`): Retrieval → LLM (answer-with-citations-only prompt) → response.
- **Prompts** (`prompts.py`): Structured templates; edge case: "Not enough context" when scores below threshold.

## Services

| Service   | Image / Build   | Ports      | Description          |
|-----------|-----------------|------------|----------------------|
| **app**   | Build from repo | 8000       | FastAPI + RAG        |
| **vectordb** | `qdrant/qdrant` | 6333, 6334 | Qdrant vector DB     |

- **Persistent storage**: Qdrant data in `qdrant_storage` volume.
- **Health checks**: Both services use health checks; app waits for vectordb to be healthy.

## Git and Commits

- **Conventional Commits**: `feat:`, `fix:`, `docs:`, `chore:` prefixes.
- **Atomic commits**: One logical change per commit.
- **Descriptive messages**: Clear, concise subject lines.

## License

MIT — see [LICENSE](LICENSE).

---

**VoiceFlip Technologies** — Technical Test v1.3 (February 2026)
