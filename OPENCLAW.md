# Phase 6 — OpenClaw Integration

This document describes how the VoiceFlip RAG system is connected to [OpenClaw](https://openclaw.ai/) and how to reproduce the integration.

## Objective

- Run OpenClaw using Docker (standalone from the main stack).
- Connect OpenClaw to the RAG system via a **custom skill** that calls the RAG API.
- Define a functional flow: **user instruction → OpenClaw → RAG query → result**.
- Optional: interact with OpenClaw from the React frontend (send message to OpenClaw).

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  User (WebChat / Telegram / WhatsApp / …)                        │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  OpenClaw Gateway (Docker)                                       │
│  - Main session, tools, skills                                  │
│  - Skill: rag-query → exec → query-rag.sh → HTTP to RAG API     │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                │  HTTP POST /query
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  VoiceFlip RAG API (Docker)                                     │
│  - /query, /chat, /retrieve, /documents                          │
│  - Qdrant + LangChain + LangGraph                               │
└─────────────────────────────────────────────────────────────────┘
                                ▲
                                │  POST /openclaw/send (optional)
┌───────────────────────────────┴─────────────────────────────────┐
│  React Frontend                                                  │
│  - OpenClaw tab: link to WebChat + “Send to OpenClaw”            │
└─────────────────────────────────────────────────────────────────┘
```

### Integration mechanism

- **RAG → OpenClaw**: OpenClaw does not call the RAG API directly. We provide a **skill** (`openclaw-skill-rag/`) that the agent can invoke. When the user asks a question that should use the knowledge base, the agent uses the skill, which runs a shell script. The script calls the RAG API (`POST /query`) and returns the answer. So the connection is **skill → exec → curl → RAG API**.
- **Frontend → OpenClaw**: The React app has an “OpenClaw” tab. It can send a message to OpenClaw’s main session via our backend: the frontend calls `POST /openclaw/send`; the backend forwards to OpenClaw’s **Tools Invoke API** (`POST /tools/invoke` with tool `sessions_send`). This requires OpenClaw to allowlist `sessions_send` over HTTP (see below).

### Why this design

- **Skill instead of MCP**: A custom skill with a small script keeps the integration simple and avoids running an extra MCP server. The agent already has `exec`; we only need to teach it when and how to call the RAG (via SKILL.md) and provide a script that does the HTTP call.
- **OpenClaw in main Compose**: OpenClaw gateway and CLI are defined in `docker-compose.yml` (same network `voiceflip-net`), so a single `docker compose up -d` starts the full stack including OpenClaw.
- **Frontend proxy**: The frontend cannot call OpenClaw’s Tools Invoke API from the browser (CORS and token). So the backend exposes `/openclaw/send`, which forwards to OpenClaw when `OPENCLAW_GATEWAY_URL` and `OPENCLAW_GATEWAY_TOKEN` are set.

## Deliverables

| Deliverable | Location |
|------------|----------|
| Docker configuration for OpenClaw | `docker-compose.yml` (services `openclaw-gateway`, `openclaw-cli`) |
| RAG skill (SKILL.md + script) | `openclaw-skill-rag/` |
| Backend proxy for “Send to OpenClaw” | `POST /openclaw/send` in `app/main.py` |
| Frontend OpenClaw tab | `frontend/src/App.tsx` (tab + send form) |
| This documentation | `docs/OPENCLAW.md` |

## How to run

### Prerequisites

- Docker and Docker Compose v2.
- Main RAG stack running (app + vectordb).
- For “Send to OpenClaw” from the frontend: OpenClaw gateway URL and token (see below).

### 1. Start the RAG stack and create the shared network

From the project root:

```bash
docker compose up -d app vectordb
```

This starts the API and Qdrant and creates the network `voiceflip-net` (see `docker-compose.yml`).

### 2. Start OpenClaw (optional)

OpenClaw is part of the main stack. Start everything with:

```bash
mkdir -p .openclaw-config .openclaw-workspace
docker compose up -d
```

- OpenClaw gateway starts with app, vectordb, and frontend.
- The RAG skill is mounted from `./openclaw-skill-rag` into the container.
- Inside the container, `RAG_API_URL` is set to `http://app:8000`.

First-time only — run the onboarding wizard (model, channels, etc.):

```bash
docker compose --profile tools run --rm openclaw-cli onboard
```

After that, the gateway can use the RAG skill. For a **research → document → RAG** flow: use the frontend OpenClaw tab to send a research request, paste the reply into “Generate document from research text”, download PDF or DOCX, then upload the DOCX in the Upload tab to add it to the RAG context.

### 3. Functional flow: instruction → RAG query → result

1. Open OpenClaw WebChat (or any connected channel): **http://localhost:18789** (or the URL shown by the gateway).
2. Send a message that should trigger the RAG skill, for example:
   - “Use the RAG skill to answer: What tax credits exist for home buyers?”
   - “Query the document knowledge base: What are the main eligibility criteria?”
3. The agent should invoke the `rag-query` skill, which runs `query-rag.sh` with your question. The script calls `POST http://app:8000/query` and returns the answer.
4. OpenClaw then shows that answer in the chat.

If the RAG API or vectordb is not ready, ingest documents first:

```bash
docker compose run --rm -v ./docs:/app/docs -v ./Real_Estate_RAG_Documents.xlsx:/app/Real_Estate_RAG_Documents.xlsx app python -m app.ingest
```

### 4. Interact with OpenClaw from the frontend

1. **Configure the backend** so it can forward messages to OpenClaw. In `.env` (or in the environment of the `app` service):

   - When OpenClaw runs in the main stack (`docker compose up -d`):
     - `OPENCLAW_GATEWAY_URL=http://openclaw-gateway:18789`
   - When OpenClaw runs on the host (e.g. `openclaw gateway`):
     - On Windows/Mac: `OPENCLAW_GATEWAY_URL=http://host.docker.internal:18789`
     - On Linux: use the host’s IP or ensure the app can reach the host port.

   And set:

   - `OPENCLAW_GATEWAY_TOKEN=<your-gateway-token>`

   Restart the RAG app so it picks up the new env vars.

2. **Allowlist `sessions_send`** in OpenClaw for HTTP Tools Invoke. In your OpenClaw config (e.g. under `~/.openclaw/openclaw.json` or the mounted config), add or adjust:

   ```json5
   {
     gateway: {
       tools: {
         allow: ["sessions_send"],
         deny: []   // or omit deny; default deny list includes sessions_send
       }
     }
   }
   ```

   Then restart the OpenClaw gateway.

3. Open the **React frontend** (e.g. http://localhost:5173), go to the **OpenClaw** tab, and use “Send to OpenClaw” with a message like: “Use the RAG skill to answer: What tax credits exist for home buyers?”. The reply will appear in OpenClaw (WebChat or your connected channel), not in the frontend.

## Evidence of execution

- **Skill**: `openclaw-skill-rag/SKILL.md` and `openclaw-skill-rag/query-rag.sh` are in the repo; the script is executable and uses `RAG_API_URL` and `curl`.
- **Docker**: `docker-compose.yml` defines `openclaw-gateway` and `openclaw-cli` (profile `tools`) with the skill volume and `voiceflip-net`.
- **Flow**: After starting both stacks and onboarding OpenClaw, sending “Use the RAG skill to answer: …” in WebChat produces an answer from the RAG API (visible in OpenClaw logs and chat).
- **Frontend**: The OpenClaw tab shows the WebChat link and “Send to OpenClaw”; if the backend is configured and `sessions_send` is allowlisted, the message is delivered and the reply appears in OpenClaw.

## Files reference

- `openclaw-skill-rag/SKILL.md` — Skill manifest and instructions for the agent.
- `openclaw-skill-rag/query-rag.sh` — Script that calls the RAG API (uses `RAG_API_URL`, default `http://app:8000`).
- `docker-compose.yml` — Main stack (app, vectordb, frontend, openclaw-gateway, openclaw-cli); defines network `voiceflip-net`.
- `app/main.py` — Endpoint `POST /openclaw/send`.
- `app/config.py` — `openclaw_gateway_url`, `openclaw_gateway_token`.
- `frontend/src/App.tsx` — OpenClaw tab and send form.
- `.env.example` — Optional `OPENCLAW_GATEWAY_URL`, `OPENCLAW_GATEWAY_TOKEN`.

## Optional: .gitignore

Add to `.gitignore` so local OpenClaw config/workspace are not committed:

```
.openclaw-config/
.openclaw-workspace/
```
