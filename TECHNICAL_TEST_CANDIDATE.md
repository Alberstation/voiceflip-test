# Technical Test — RAG AI Engineer

**VoiceFlip Technologies**
Version 1.3 | February 2026

---

**Estimated duration:** 12–16 hours (can be completed across multiple sessions)

**Format:** Git repository with deliverables per phase

**Required stack:** Python 3.11+, Docker, Git, LangChain / LangGraph

**Submission:** Link to repository (GitHub / GitLab)

---

## Recommended setup (no cost, no local model execution)

All models run remotely via **Hugging Face Inference API** (free tier). Only a free token is needed. No GPU or local compute required.

| Resource | Details |
| --- | --- |
| **Hugging Face Token** | Free at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) |
| **Qdrant** | `docker run -d -p 6333:6333 -p 6334:6334 qdrant/qdrant` |
| **Embeddings** | `langchain-huggingface` → `HuggingFaceEndpointEmbeddings` |
| **LLM** | `langchain-huggingface` → `HuggingFaceEndpoint` + `ChatHuggingFace` |
| **Vector Store** | `langchain-qdrant` → `QdrantVectorStore` |

---

## 1. Introduction and Objectives

This technical test evaluates the competencies of a **RAG AI Engineer** in a realistic end-to-end scenario. The candidate must build a complete Retrieval-Augmented Generation system, from infrastructure to service exposure, demonstrating proficiency in:

- Containerization and DevOps best practices (Docker, Docker Compose)
- Version control with professional conventions (Conventional Commits)
- RAG pipeline design and implementation (ingestion, chunking, embeddings, retrieval)
- Agent orchestration with LangGraph (state graphs, routing, tools)
- Systematic quality evaluation of the system
- Agentic extensions and emerging protocols (bonus)

> **Note on AI usage:** Candidates are expected to use AI assistants (Copilot, Cursor, Claude, etc.) as productivity tools. However, they must demonstrate deep understanding of every technical decision during the oral defense. AI usage is evaluated positively when combined with sound technical judgment.

---

## 2. Phase 1 — Environment Setup (Docker + Git)

### Objective

Set up a reproducible and professional development environment using Docker and Git.

### Requirements

**A) Docker & Docker Compose**

- Multi-stage Dockerfile (build + runtime)
- `docker-compose.yml` with at least:
  - `app` (main application)
  - `vectordb` (Qdrant)
  - `redis` (optional, valued)
- Health checks for each service
- Environment variables with `.env.example`
- Persistent volume for the vector database

**B) Git & Conventional Commits**

- `.gitignore` appropriate for Python/Docker
- Mandatory use of **Conventional Commits**
- Atomic and descriptive commits
- `README.md` with clear instructions

The repository must be startable with:

```bash
docker compose up --build
```

---

## 3. Phase 2 — Basic RAG Pipeline

### Objective

Implement a functional RAG pipeline covering ingestion, processing, vector storage, retrieval, and generation.

### Data corpus

The candidate must choose a document corpus to feed the system and **justify the choice** in the README. It can be technical documentation, articles, papers, manuals, or any set of documents that demonstrates the pipeline's capabilities. A corpus of at least 10 documents is recommended.

### Requirements

- Loaders for at least 2 formats (PDF, HTML, Markdown, DOCX)
- Text cleaning and normalization
- At least 2 chunking strategies with justification
- Metadata preservation
- Open-source embeddings and LLM via Hugging Face Inference API (remote, no local compute)
- Storage in the configured vector database
- At least 2 retrieval techniques
- Structured prompt and edge case handling
- Unit tests for chunking and retrieval

### Verified models on the free tier

| Type | Available models |
| --- | --- |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` (384 dim), `BAAI/bge-small-en-v1.5` (384 dim) |
| **LLM** | `Qwen/Qwen2.5-1.5B-Instruct`, `mistralai/Mistral-7B-Instruct-v0.2`, `HuggingFaceH4/zephyr-7b-beta` |

> **Tips:**
> - Chat models use the `conversational` task in the Inference API. If using `langchain-huggingface`, check the documentation for `HuggingFaceEndpoint` and `ChatHuggingFace`.
> - The free tier has per-hour request limits. Models may take 20-60s to load on the first request (cold start).
> - Any other model available on the free tier can be used, as long as the choice is justified.

---

## 4. Phase 3 — Agent with LangGraph

### Objective

Evolve the RAG pipeline into an **agent** capable of making decisions using LangGraph.

### Requirements

- StateGraph with TypedDict
- Query routing node
- RAG node
- Relevance evaluation node
- Hallucination detection node
- Web search fallback
- At least 1 custom tool
- Conversational memory
- Structured logging

---

## 5. Phase 4 — RAG System Evaluation

### Objective

Systematically evaluate the quality of the RAG system using reproducible metrics.

### Requirements

- Evaluation dataset (>=15 question/answer pairs)
- Evaluation of at least 4 metrics from the following:
  - Faithfulness
  - Answer Relevancy
  - Context Precision
  - Context Recall
  - Hallucination Score
  - Latency
- Executable evaluation script
- Aggregated report with results
- At least 1 documented improvement based on results

### Tools

Use **open-source** tools for evaluation. Recommended options:

- **RAGAS** (recommended)
- **DeepEval**
- **LangSmith Evaluation**

The choice must be justified and documented.

> **Note:** If the tool requires an LLM as a "judge", it must use the same remote open-source LLM defined in Phase 2. Small models (1.5B-7B) as judges have known limitations in evaluation quality — **documenting these limitations is valued positively**.

---

## 6. Phase 5 — API / Frontend

### Objective

Expose the RAG system as a consumable service.

### Options (choose at least one)

- **REST API** with FastAPI (automatic OpenAPI documentation)
- **Frontend** with Streamlit, Gradio, or Chainlit
- **Both** (valued)

### Requirements

- Functional endpoint(s) for RAG queries
- Usage documentation (README or OpenAPI)
- Working demo example
- Appropriate error handling

---

## 7. Phase 6 — OpenClaw Integration (Bonus)

**This phase is optional and considered a differentiator.**

### Objective

Integrate the RAG system with [OpenClaw](https://openclaw.ai/) — an open-source autonomous agent — demonstrating the ability to creatively connect systems.

### Context

OpenClaw is an open-source personal AI assistant that can execute tasks, connect with external services, and operate autonomously. It has official Docker support:

- Repository: [github.com/openclaw/openclaw](https://github.com/openclaw/openclaw)
- Docker documentation: [docs.openclaw.ai/install/docker](https://docs.openclaw.ai/install/docker)
- Pre-built image: [hub.docker.com/r/alpine/openclaw](https://hub.docker.com/r/alpine/openclaw)

### Requirements

- Run OpenClaw using Docker (can be a standalone container, does not need to be in the main `docker-compose.yml`)
- Connect OpenClaw with the RAG system in a creative way (via API, custom tool/skill, MCP, or any mechanism that works)
- Define at least one functional flow: instruction → RAG query → result
- Document the integration architecture and decisions made

> **Important:**
> - No tokens or credentials are provided. The candidate uses their own free credentials.
> - No need to configure Browser Relay, Control UI, or pairing.
> - What is evaluated is the **ability to set up, connect, and integrate** systems — not the complexity of the integration itself.

### Deliverables

- Docker configuration for OpenClaw
- Functional OpenClaw <-> RAG integration
- Clear documentation on how to reproduce
- Evidence of execution (logs, screenshots, or demo)

---

## 8. Project Defense

The candidate must deliver a technical presentation (30-45 min) where they:

- **Demonstrate the system working** end-to-end (ingestion → retrieval → generation)
- **Explain key technical decisions**: model selection, chunking strategies, retrieval techniques, corpus choice
- **Discuss trade-offs**: why one strategy was chosen over another, what limitations were found
- **Answer questions** about scalability, future improvements, and how the system would adapt to production
- **Comment on AI tool usage**: what prompts were used, what was generated vs. manually modified

> The oral defense is as important as the code. A functional system without understanding of the technical decisions will not be sufficient.

---

## Deliverables summary

| Phase | Main deliverable |
| --- | --- |
| Phase 1 | Functional Docker Compose + repo with Conventional Commits |
| Phase 2 | Complete RAG pipeline with tests |
| Phase 3 | LangGraph agent with routing and tools |
| Phase 4 | Evaluation script + metrics report |
| Phase 5 | Functional API and/or Frontend |
| Phase 6 (bonus) | OpenClaw integration via Docker |

**Phases 1-3 are expected to be complete and functional. Phases 4 and 5 are differentiators. Phase 6 is bonus.**

---

VoiceFlip Technologies — February 2026
