# RAG AI Engineer — VoiceFlip Technical Test

Retrieval-Augmented Generation pipeline with Docker-based environment, Qdrant vector store, and LangChain.

## Requirements

- **Docker** and **Docker Compose** (v2)
- **Git**
- **Python 3.11+** (optional; runtime is fully containerized)

---

## Environment variables

Copy `.env.example` to `.env` and set values as needed. All parameters are documented in [.env.example](.env.example).

| Variable | Required for | Description |
|----------|--------------|-------------|
| `HUGGINGFACEHUB_API_TOKEN` | **app** (RAG/agent) | [Hugging Face token](https://huggingface.co/settings/tokens) for embeddings and LLM |
| `OPENCLAW_GATEWAY_TOKEN` | OpenClaw (optional) | Gateway token from OpenClaw setup |
| `OPENCLAW_GATEWAY_URL` | **app** (OpenClaw tab) | e.g. `http://openclaw-gateway:18789` when OpenClaw runs in Docker |
| `OPENCLAW_CONFIG_DIR` | OpenClaw | Default `./.openclaw-config` |
| `OPENCLAW_WORKSPACE_DIR` | OpenClaw | Default `./.openclaw-workspace` |
| `OPENCLAW_GATEWAY_PORT` | OpenClaw | Default `18789` |

```bash
cp .env.example .env
# Edit .env: at minimum set HUGGINGFACEHUB_API_TOKEN for RAG/chat
```

---

## Running the services

All services use **healthchecks**. The table below lists how to run each service and how to verify it is healthy.

### Services overview

| Service | Compose file | Port(s) | Health check | Depends on |
|---------|--------------|---------|--------------|------------|
| **vectordb** | `docker-compose.yml` | 6333, 6334 | TCP 6333 | — |
| **app** | `docker-compose.yml` | 8000 | `GET http://localhost:8000/health` | vectordb (healthy) |
| **frontend** | `docker-compose.yml` | 5173 | `GET http://localhost:5173/` | app (healthy) |
| **openclaw-gateway** | `docker-compose.openclaw.yml` | 18789, 18790 | `node dist/index.js health --token $OPENCLAW_GATEWAY_TOKEN` | network `voiceflip-net` (app running) |
| **openclaw-cli** | `docker-compose.openclaw.yml` | — | (one-off for onboard) | — |

### Health checks (verify manually)

| Service | Check |
|---------|--------|
| **app** | `curl -f http://localhost:8000/health` → `{"status":"ok"}` |
| **vectordb** | `curl -f http://localhost:6333/readyz` or open http://localhost:6333/dashboard |
| **frontend** | Open http://localhost:5173/ in a browser |
| **openclaw-gateway** | `curl -f http://localhost:18789/` (or use OpenClaw’s health command with token) |

Docker Compose runs healthchecks automatically; `depends_on` with `condition: service_healthy` waits for dependencies before starting.

---

## Quick start (full stack: app + vectordb + frontend)

1. **Clone and set env**

   ```bash
   git clone <repo-url>
   cd voiceflip-test
   cp .env.example .env
   # Set HUGGINGFACEHUB_API_TOKEN in .env
   ```

2. **Start all main services**

   ```bash
   docker compose up --build -d
   ```

3. **Wait for health** (optional; Compose already waits for app/vectordb)

   ```bash
   docker compose ps
   # All services should show "healthy" (or "running" for frontend once ready)
   curl -s http://localhost:8000/health
   curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/
   ```

4. **Use the app**

   - **API** — http://localhost:8000  
   - **OpenAPI docs** — http://localhost:8000/docs  
   - **Frontend** — http://localhost:5173  

---

## Running only the backend (app + vectordb)

```bash
cp .env.example .env
# Set HUGGINGFACEHUB_API_TOKEN
docker compose up -d app vectordb
```

- **Health**: `curl http://localhost:8000/health` and `curl http://localhost:6333/readyz`
- **API**: http://localhost:8000 and http://localhost:8000/docs

---

## Running the frontend (with backend)

The frontend is in the main compose; it starts after **app** is healthy.

```bash
docker compose up -d
# Frontend: http://localhost:5173 (healthcheck: curl http://localhost:5173/)
```

**Frontend locally (dev)** while backend runs in Docker:

```bash
# Terminal 1
docker compose up -d app vectordb

# Terminal 2
cd frontend && npm install && npm run dev
# Open http://localhost:5173 (Vite may use a different port if 5173 is busy)
```

---

## Running OpenClaw (optional, Phase 6)

OpenClaw uses a **separate** compose file and the shared network `voiceflip-net` so it can reach the RAG API at `http://app:8000`.

1. **Start the main stack first** (so `voiceflip-net` exists and `app` is reachable)

   ```bash
   docker compose up -d app vectordb
   ```

2. **Set OpenClaw env** in `.env`

   - `OPENCLAW_GATEWAY_TOKEN` (generate or use token from OpenClaw setup)
   - Optional: `OPENCLAW_CONFIG_DIR`, `OPENCLAW_WORKSPACE_DIR` (defaults: `./.openclaw-config`, `./.openclaw-workspace`)

3. **Create config/workspace dirs** (if not present)

   ```bash
   mkdir -p .openclaw-config .openclaw-workspace
   ```

4. **Start OpenClaw**

   ```bash
   docker compose -f docker-compose.openclaw.yml up -d
   ```

5. **Onboard once** (model, channels, etc.)

   ```bash
   docker compose -f docker-compose.openclaw.yml run --rm openclaw-cli onboard
   ```

6. **Health**: OpenClaw gateway healthcheck runs inside the container (`node dist/index.js health --token $OPENCLAW_GATEWAY_TOKEN`). From the host: open http://localhost:18789 or use the dashboard link from the CLI.

Full details: [docs/OPENCLAW.md](docs/OPENCLAW.md).

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

## Phase 3 — LangGraph Agent

**LangGraph agent** with query routing, RAG, relevance evaluation, hallucination detection, and web search fallback.

### API Endpoints (FastAPI)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/query` | RAG query (top_k or MMR) |
| POST | `/chat` | Chat with agent (conversational memory) |
| POST | `/documents` | Add DOCX/HTML documents to RAG |
| POST | `/retrieve` | Retrieve docs with top_k or MMR (for frontend) |
| POST | `/openclaw/send` | Forward message to OpenClaw main session (optional; Phase 6) |

### Example: Chat (conversational memory)

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What tax credits exist for home buyers?", "session_id": "user-123"}'
```

`session_id` is optional; a new UUID is generated if omitted.

### Example: Add documents

```bash
curl -X POST http://localhost:8000/documents \
  -F "files=@document1.docx" \
  -F "files=@document2.html"
```

### Example: Retrieve (top_k or mmr)

```bash
curl -X POST http://localhost:8000/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "homebuyer tax credits", "technique": "top_k"}'
```

---

## Phase 4 — RAG System Evaluation

**RAGAS** (open-source) for systematic RAG evaluation. See [docs/EVALUATION.md](docs/EVALUATION.md).

### Run evaluation

Requires `question_list.docx` with ≥15 questions (one per paragraph). Optional Q/A pairs with "Q:" / "A:" for context recall.

```bash
docker compose run --rm \
  -v ./question_list.docx:/app/question_list.docx \
  -v ./eval_output:/app/eval_output \
  -e EVAL_REPORT_PATH=/app/eval_output/eval_report.json \
  app python -m app.eval.run_eval
```

Report at `./eval_output/eval_report.json`.

---

## Phase 5 — Frontend (React)

**React** demo: Chat, Upload Documents, Retrieval, OpenClaw tab. See [Running the frontend](#running-the-frontend-with-backend) for how to run it.

| Tab | Description |
|-----|-------------|
| **Chat** | LangGraph agent (RAG, relevance, web search). Session-based memory. |
| **Upload Documents** | Add DOCX/HTML to the RAG vector store. |
| **Retrieval** | Query vector store with **top_k** or **MMR**. |
| **OpenClaw** | Link to OpenClaw WebChat and “Send to OpenClaw” (when configured). |

---

## Phase 6 — OpenClaw Integration (Bonus)

See [Running OpenClaw](#running-openclaw-optional-phase-6) and [docs/OPENCLAW.md](docs/OPENCLAW.md) for setup, RAG skill, and flow.

---

## Project layout

```
.
├── app/
│   ├── api/                 # API layer (modular)
│   │   ├── routers/         # health, rag, chat, documents, retrieval, openclaw
│   │   ├── schemas.py       # Pydantic request/response models
│   │   └── __init__.py
│   ├── agent/               # LangGraph agent
│   ├── config.py            # Settings from .env
│   ├── constants.py
│   ├── main.py              # FastAPI app: CORS + router
│   ├── openclaw_client.py   # OpenClaw Tools Invoke client
│   ├── services.py          # Agent, ingestion, retrieval
│   ├── rag.py, retrieval.py, vectorstore.py, loaders.py, ...
│   └── eval/
├── frontend/                # React (Vite) UI
├── openclaw-skill-rag/      # OpenClaw RAG skill
├── docker-compose.yml       # app, vectordb, frontend (all with healthchecks)
├── docker-compose.openclaw.yml
├── docs/OPENCLAW.md, EVALUATION.md
├── .env.example
└── requirements.txt
```

---

## Code conventions

- **Comments and docstrings**: English only.
- **Modularity**: Single responsibility; routers and schemas in `app/api/`; business logic in services/rag/retrieval.
- **Constants**: `app/constants.py`.
- **Config**: `.env` / `.env.example`.
- **Type hints**: For function signatures and public APIs.

## Architecture

- **API**: `app/main.py` mounts `app.api` routers; each router in `app/api/routers/` handles one domain (health, rag, chat, documents, retrieval, openclaw).
- **RAG**: Loaders → cleaning → chunking → vectorstore → retrieval (top_k / MMR) → LLM → response. See `app/rag.py`, `app/retrieval.py`, `app/vectorstore.py`.
- **Agent**: LangGraph StateGraph (routing, RAG, relevance, hallucination, web search). Conversational memory via MemorySaver.

## Git and commits

- **Conventional Commits**: `feat:`, `fix:`, `docs:`, `chore:`.
- **Atomic commits**, descriptive messages.

## License

MIT — see [LICENSE](LICENSE).

---

**VoiceFlip Technologies** — Technical Test v1.3 (February 2026)
