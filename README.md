# RAG AI Engineer — VoiceFlip Technical Test

Repository for the VoiceFlip Technologies RAG AI Engineer technical test (Phase 1 and beyond). The system is a Retrieval-Augmented Generation pipeline with Docker-based environment, Qdrant vector store, and (in later phases) LangChain/LangGraph agent.

## Requirements

- **Docker** and **Docker Compose** (v2)
- **Git**
- **Python 3.11+** (for local development only; runtime is containerized)

## Quick start

1. **Clone the repository** (if not already):

   ```bash
   git clone <repo-url>
   cd voiceflip-test
   ```

2. **Optional — environment variables**  
   For Phase 1 you can run as-is. For Phase 2+ (embeddings, LLM), copy the example env and add your [Hugging Face token](https://huggingface.co/settings/tokens):

   ```bash
   cp .env.example .env
   # Edit .env and set HUGGINGFACEHUB_API_TOKEN=
   ```

3. **Start all services**:

   ```bash
   docker compose up --build
   ```

   This builds the app image and starts:

   - **app** — main application (FastAPI) at `http://localhost:8000`
   - **vectordb** — Qdrant at `http://localhost:6333` (API) and `6334` (gRPC)

4. **Check health**:

   - App: [http://localhost:8000/health](http://localhost:8000/health)
   - Qdrant: [http://localhost:6333/readyz](http://localhost:6333/readyz)

## Project layout (Phase 1)

```
.
├── app/
│   ├── __init__.py
│   └── main.py          # FastAPI app, /health endpoint
├── docker-compose.yml   # app + vectordb (Qdrant)
├── Dockerfile           # Multi-stage (build + runtime)
├── .env.example         # Example environment variables
├── .gitignore
├── requirements.txt
├── README.md
└── TECHNICAL_TEST_CANDIDATE.md
```

## Services

| Service   | Image / Build     | Ports   | Description                    |
|----------|-------------------|---------|--------------------------------|
| **app**  | Build from repo   | 8000    | Main application (FastAPI)     |
| **vectordb** | `qdrant/qdrant` | 6333, 6334 | Qdrant vector database |

- **Persistent storage**: Qdrant data is stored in the `qdrant_storage` Docker volume.
- **Health checks**: Both services define health checks; Compose waits for vectordb to be healthy before starting the app.

## Git and commits

This project uses **Conventional Commits** (e.g. `feat:`, `fix:`, `docs:`, `chore:`). Commits are atomic and descriptive.

## License

MIT — see [LICENSE](LICENSE).

---

**VoiceFlip Technologies** — Technical Test v1.3 (February 2026)
