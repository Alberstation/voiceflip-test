# Voiceflip AI Engineer test

Retrieval-Augmented Generation (RAG) pipeline with Docker-based environment: Qdrant vector store, LangChain, LangGraph agent, OpenClaw integration, document generation, and RAGAS evaluation dashboard.

## Requirements

- **Docker** and **Docker Compose** (v2)
- **Git**
- **Python 3.11+** (optional; runtime is fully containerized)

---

## Environment variables

Copy `.env.example` to `.env` and set values as needed. All parameters are documented in [.env.example](.env.example).

| Variable | Required for | Description |
|----------|--------------|-------------|
| `HUGGINGFACEHUB_API_TOKEN` | **app** (RAG/agent) | [Hugging Face token](https://huggingface.co/settings/tokens) for embeddings and LLM. If you see **402 Payment Required**, the free tier limit may be reached — check [billing](https://huggingface.co/settings/billing); the app will automatically try fallback models. |
| `LLM_MODEL` | **app** (optional) | Primary chat model (default: `Qwen/Qwen2.5-1.5B-Instruct`). On 402, the app tries fallbacks. |
| `LLM_FALLBACK_MODELS` | **app** (optional) | Comma-separated fallback models (default: `mistralai/Mistral-7B-Instruct-v0.2,HuggingFaceH4/zephyr-7b-beta`). Used when the primary returns 402. |
| `OPENCLAW_GATEWAY_TOKEN` | OpenClaw (optional) | Gateway token from OpenClaw setup |
| `OPENCLAW_GATEWAY_URL` | **app** (OpenClaw tab) | e.g. `http://openclaw-gateway:18789` when OpenClaw runs in Docker |
| `OPENCLAW_CONFIG_DIR` | OpenClaw | Default `./.openclaw-config` (created automatically by init-dirs) |
| `OPENCLAW_WORKSPACE_DIR` | OpenClaw | Default `./.openclaw-workspace` (created automatically by init-dirs) |
| `OPENCLAW_GATEWAY_PORT` | OpenClaw | Default `18789` |

```bash
cp .env.example .env
# At minimum set HUGGINGFACEHUB_API_TOKEN
# For OpenClaw tab + WebChat set OPENCLAW_GATEWAY_TOKEN and OPENCLAW_GATEWAY_URL
```

---

## Running the services

### What starts with `docker compose up`

| Service | Port(s) | Description |
|---------|---------|-------------|
| **init-dirs** | — | One-off: creates `.openclaw-config`, `.openclaw-workspace`, `docs/` on the host, then exits. |
| **vectordb** | 6333, 6334 | Qdrant vector database. |
| **app** | 8000 | FastAPI: RAG, chat, documents, retrieval, OpenClaw proxy, eval API. |
| **frontend** | 5173 | React UI (Chat, Upload, Retrieval, OpenClaw, RAGAS Dashboard). |
| **openclaw-gateway** | 18789, 18790 | OpenClaw gateway; **starts automatically** — no separate command needed. |

**openclaw-cli** is **not** started by `up`. Use it only for the one-time onboarding:  
`docker compose --profile tools run --rm openclaw-cli onboard`

### Health checks (optional)

| Service | Check |
|---------|--------|
| app | `curl -f http://localhost:8000/health` → `{"status":"ok"}` |
| vectordb | `curl -f http://localhost:6333/readyz` or http://localhost:6333/dashboard |
| frontend | http://localhost:5173 |
| openclaw-gateway | http://localhost:18789 |

Docker Compose runs healthchecks automatically; services wait for dependencies (e.g. app waits for vectordb, openclaw-gateway waits for app).

---

## Quick start — one command starts everything

A single command starts the full stack: **app**, **vectordb**, **frontend**, and **OpenClaw**. OpenClaw does **not** require a separate compose file or another `up` command.

1. **Clone and set environment**

   ```bash
   git clone <repo-url>
   cd voiceflip-test
   cp .env.example .env
   ```

2. **Configure `.env`** (minimum for RAG/chat: set `HUGGINGFACEHUB_API_TOKEN`; optional: OpenClaw variables — see [Environment variables](#environment-variables)).

3. **Start all services**

   ```bash
   docker compose up --build -d
   ```

   This starts: **init-dirs** (creates `.openclaw-config`, `.openclaw-workspace`, `docs/` on the host, then exits), **vectordb**, **app**, **frontend**, and **openclaw-gateway**. **OpenClaw starts automatically** with the rest of the stack.

4. **First-time OpenClaw only** — run onboarding once (model, channels)

   ```bash
   docker compose --profile tools run --rm openclaw-cli onboard
   ```

   After that, OpenClaw WebChat and the frontend “Send to OpenClaw” work without running this again.

5. **Open the app**

   | What | URL |
   |------|-----|
   | Frontend | http://localhost:5173 |
   | API | http://localhost:8000 |
   | OpenAPI docs | http://localhost:8000/docs |
   | OpenClaw WebChat | http://localhost:18789 |  

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

## Running OpenClaw (Phase 6 — research → document → RAG)

OpenClaw is part of the main stack. **It starts automatically** with `docker compose up --build -d`; you do **not** need a different compose file or another `up` command.

**Flow**: Ask OpenClaw for US housing research (e.g. in WebChat or via the frontend “Send to OpenClaw”) → copy the reply → in the frontend OpenClaw tab paste the text and **Generate document** (PDF or DOCX) → download → in **Upload Documents** upload the file to add it to the RAG context (DOCX supported for ingestion).

**First-time setup**: Set in `.env`: `OPENCLAW_GATEWAY_TOKEN`, `OPENCLAW_GATEWAY_URL`. Start the stack with `docker compose up -d`. Then run onboarding once: `docker compose --profile tools run --rm openclaw-cli onboard`. OpenClaw WebChat: http://localhost:18789

Full details: [OPENCLAW.md](OPENCLAW.md).

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
| POST | `/documents/generate` | Generate PDF or DOCX from title + content (for research → document flow) |
| GET | `/eval/report` | Return last saved RAGAS evaluation report (for dashboard) |
| POST | `/eval/run` | Run RAGAS evaluation; optional file (question list PDF/DOCX). Returns report. |

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

## Phase 4 — RAG System Evaluation (RAGAS)

**RAGAS** (open-source) for systematic RAG evaluation. Metrics: Faithfulness, Answer Relevancy, Context Precision, Context Recall, Hallucination Score, Latency. See [EVALUATION.md](EVALUATION.md).

### Question list (PDF or DOCX)

Use **question_list.pdf** (or DOCX) with ≥15 questions — one question per paragraph. Optional Q/A pairs with "Q:" / "A:" for context recall. Default path in the app: `/app/question_list.pdf`.

### Run evaluation (CLI)

```bash
docker compose run --rm \
  -v ./question_list.pdf:/app/question_list.pdf \
  -v ./eval_output:/app/eval_output \
  -e EVAL_DATASET_PATH=/app/question_list.pdf \
  -e EVAL_REPORT_PATH=/app/eval_output/eval_report.json \
  app python -m app.eval.run_eval
```

Report at `./eval_output/eval_report.json`.

### RAGAS Dashboard (frontend)

In the frontend, open the **RAGAS Dashboard** tab. You can **Load last report** (from the last run) or **Run evaluation** (optionally upload a question list PDF/DOCX). The dashboard shows: question count, Faithfulness, Answer Relevancy, Context Precision, Context Recall, Hallucination Score, and Latency (avg/max).

---

## Phase 5 — Frontend (React)

**React** UI on **port 5173**; started with the stack via `docker compose up -d`.

| Tab | Description |
|-----|-------------|
| **Chat** | LangGraph agent (RAG, relevance, web search). Session-based memory. |
| **Upload Documents** | Add DOCX/HTML to the RAG vector store. |
| **Retrieval** | Query vector store with **top_k** or **MMR**. |
| **OpenClaw** | OpenClaw WebChat link, Send to OpenClaw, and Generate document from research text (PDF/DOCX). |
| **RAGAS Dashboard** | Evaluation metrics (Faithfulness, Answer Relevancy, Context Precision, Context Recall, Hallucination Score, Latency) and question count. Load last report or run evaluation (upload question list PDF/DOCX). |

---

## Phase 6 — OpenClaw Integration

See [OpenClaw — research → document → RAG](#openclaw--research--document--rag-phase-6) and [OPENCLAW.md](OPENCLAW.md) for setup, RAG skill, and flow. OpenClaw **starts automatically** with `docker compose up`; only the first-time onboarding uses a separate command.

---

## Project layout

```
.
├── app/
│   ├── api/                 # API layer (modular)
│   │   ├── routers/         # health, rag, chat, documents, retrieval, openclaw, eval
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
├── docker-compose.yml       # app, vectordb, frontend, openclaw-gateway (+ openclaw-cli profile)
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

- **API**: `app/main.py` mounts `app.api` routers; each router in `app/api/routers/` handles one domain (health, rag, chat, documents, retrieval, openclaw, eval).
- **RAG**: Loaders → cleaning → chunking → vectorstore → retrieval (top_k / MMR) → LLM → response. See `app/rag.py`, `app/retrieval.py`, `app/vectorstore.py`.
- **Agent**: LangGraph StateGraph (routing, RAG, relevance, hallucination, web search). Conversational memory via MemorySaver.

## Git and commits

- **Conventional Commits**: `feat:`, `fix:`, `docs:`, `chore:`.
- **Atomic commits**, descriptive messages.

## License

MIT — see [LICENSE](LICENSE).

---

**VoiceFlip Technologies** — Technical Test v1.3 (February 2026)
