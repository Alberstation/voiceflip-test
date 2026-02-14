# Prueba Tecnica — RAG AI Engineer

**VoiceFlip Technologies**
Version 1.3 | Febrero 2026

---

**Duracion estimada:** 12–16 horas (puede completarse en multiples sesiones)

**Formato:** Repositorio Git con entregables por fase

**Stack requerido:** Python 3.11+, Docker, Git, LangChain / LangGraph

**Entrega:** Link al repositorio (GitHub / GitLab)

---

## Modo recomendado (sin costos y sin correr modelos localmente)

Todos los modelos se ejecutan remotamente a traves de **Hugging Face Inference API** (free tier). Solo se necesita un token gratuito. No se requiere GPU ni computo local.

| Recurso | Detalle |
| --- | --- |
| **Hugging Face Token** | Gratuito en [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) |
| **Qdrant** | `docker run -d -p 6333:6333 -p 6334:6334 qdrant/qdrant` |
| **Embeddings** | `langchain-huggingface` → `HuggingFaceEndpointEmbeddings` |
| **LLM** | `langchain-huggingface` → `HuggingFaceEndpoint` + `ChatHuggingFace` |
| **Vector Store** | `langchain-qdrant` → `QdrantVectorStore` |

---

## 1. Introduccion y Objetivos

Esta prueba tecnica evalua las competencias de un **RAG AI Engineer** en un escenario realista end-to-end. El candidato debera construir un sistema de Retrieval-Augmented Generation completo, desde la infraestructura hasta la exposicion del servicio, demostrando dominio en:

- Containerizacion y buenas practicas DevOps (Docker, Docker Compose)
- Control de versiones con convenciones profesionales (Conventional Commits)
- Diseno e implementacion de pipelines RAG (ingesta, chunking, embeddings, retrieval)
- Orquestacion de agentes con LangGraph (grafos de estado, routing, tools)
- Evaluacion sistematica de calidad del sistema
- Extensiones agentic y protocolos emergentes (bonus)

> **Nota sobre uso de IA:** Se espera que el candidato utilice asistentes de IA (Copilot, Cursor, Claude, etc.) como herramienta de productividad. Sin embargo, debera demostrar comprension profunda de cada decision tecnica en la defensa oral del proyecto. El uso de AI se evalua positivamente cuando se combina con criterio tecnico propio.

---

## 2. Fase 1 — Setup del Entorno (Docker + Git)

### Objetivo

Configurar un entorno de desarrollo reproducible y profesional utilizando Docker y Git.

### Requerimientos

**A) Docker & Docker Compose**

- Dockerfile multi-stage (build + runtime)
- `docker-compose.yml` con al menos:
  - `app` (aplicacion principal)
  - `vectordb` (Qdrant)
  - `redis` (opcional, valorado)
- Health checks para cada servicio
- Uso de variables de entorno con `.env.example`
- Volumen persistente para la base vectorial

**B) Git & Conventional Commits**

- `.gitignore` adecuado para Python/Docker
- Uso obligatorio de **Conventional Commits**
- Commits atomicos y descriptivos
- `README.md` con instrucciones claras

El repositorio debe poder levantarse con:

```bash
docker compose up --build
```

---

## 3. Fase 2 — Pipeline RAG Basico

### Objetivo

Implementar un pipeline RAG funcional cubriendo ingesta, procesamiento, almacenamiento vectorial, retrieval y generacion.

### Corpus de datos

El candidato debe elegir un corpus de documentos para alimentar el sistema y **justificar la eleccion** en el README. Puede ser documentacion tecnica, articulos, papers, manuales, o cualquier conjunto de documentos que permita demostrar las capacidades del pipeline. Se recomienda un corpus de al menos 10 documentos.

### Requerimientos

- Loaders para al menos 2 formatos (PDF, HTML, Markdown, DOCX)
- Limpieza y normalizacion de texto
- Al menos 2 estrategias de chunking justificadas
- Preservacion de metadata
- Embeddings y LLM open-source via Hugging Face Inference API (remoto, sin computo local)
- Almacenamiento en la base vectorial configurada
- Al menos 2 tecnicas de retrieval
- Prompt estructurado y manejo de edge cases
- Tests unitarios para chunking y retrieval

### Modelos verificados con el free tier

| Tipo | Modelos disponibles |
| --- | --- |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` (384 dim), `BAAI/bge-small-en-v1.5` (384 dim) |
| **LLM** | `Qwen/Qwen2.5-1.5B-Instruct`, `mistralai/Mistral-7B-Instruct-v0.2`, `HuggingFaceH4/zephyr-7b-beta` |

> **Tips:**
> - Los modelos de chat usan la tarea `conversational` en la Inference API. Si usas `langchain-huggingface`, revisa la documentacion de `HuggingFaceEndpoint` y `ChatHuggingFace`.
> - El free tier tiene limites de requests por hora. Los modelos pueden tardar 20-60s en cargar la primera vez (cold start).
> - Se puede usar cualquier otro modelo disponible en el free tier, siempre que se justifique la eleccion.

---

## 4. Fase 3 — Agente con LangGraph

### Objetivo

Evolucionar el pipeline RAG hacia un **agente** capaz de tomar decisiones usando LangGraph.

### Requerimientos

- StateGraph con TypedDict
- Nodo de routing de queries
- Nodo RAG
- Nodo de evaluacion de relevancia
- Nodo de deteccion de alucinaciones
- Fallback con busqueda web
- Al menos 1 tool personalizada
- Memoria conversacional
- Logging estructurado

---

## 5. Fase 4 — Evaluacion del Sistema RAG

### Objetivo

Evaluar sistematicamente la calidad del sistema RAG mediante metricas reproducibles.

### Requerimientos

- Dataset de evaluacion (>=15 pares pregunta/respuesta)
- Evaluacion de al menos 4 metricas de entre las siguientes:
  - Faithfulness
  - Answer Relevancy
  - Context Precision
  - Context Recall
  - Hallucination Score
  - Latencia
- Script de evaluacion ejecutable
- Reporte agregado con resultados
- Al menos 1 mejora documentada basada en los resultados

### Herramientas

Usar herramientas **open-source** para evaluacion. Opciones recomendadas:

- **RAGAS** (recomendado)
- **DeepEval**
- **LangSmith Evaluation**

La eleccion debe ser justificada y documentada.

> **Nota:** Si la herramienta requiere un LLM como "judge", debe utilizar el mismo LLM open-source remoto definido en la Fase 2. Modelos pequenos (1.5B-7B) como judge tienen limitaciones conocidas en calidad de evaluacion — **documentar estas limitaciones es valorado positivamente**.

---

## 6. Fase 5 — API / Frontend

### Objetivo

Exponer el sistema RAG como un servicio consumible.

### Opciones (elegir al menos una)

- **API REST** con FastAPI (documentacion OpenAPI automatica)
- **Frontend** con Streamlit, Gradio o Chainlit
- **Ambos** (valorado)

### Requerimientos

- Endpoint(s) funcional(es) para consultas RAG
- Documentacion de uso (README o OpenAPI)
- Ejemplo funcional demostrable
- Manejo de errores apropiado

---

## 7. Fase 6 — Integracion con OpenClaw (Bonus)

**Esta fase es opcional y se considera un diferenciador.**

### Objetivo

Integrar el sistema RAG con [OpenClaw](https://openclaw.ai/) — un agente autonomo open-source — demostrando capacidad de conectar sistemas de forma creativa.

### Contexto

OpenClaw es un asistente personal de IA open-source que puede ejecutar tareas, conectar con servicios externos y operar de forma autonoma. Cuenta con soporte oficial de Docker:

- Repositorio: [github.com/openclaw/openclaw](https://github.com/openclaw/openclaw)
- Documentacion Docker: [docs.openclaw.ai/install/docker](https://docs.openclaw.ai/install/docker)
- Imagen pre-built: [hub.docker.com/r/alpine/openclaw](https://hub.docker.com/r/alpine/openclaw)

### Requerimientos

- Levantar OpenClaw usando Docker (puede ser un contenedor independiente, no necesita estar en el `docker-compose.yml` principal)
- Conectar OpenClaw con el sistema RAG de alguna forma creativa (via API, tool/skill custom, MCP, o cualquier mecanismo que funcione)
- Definir al menos un flujo funcional: instruccion → consulta RAG → resultado
- Documentar la arquitectura de integracion y las decisiones tomadas

> **Importante:**
> - No se proveen tokens ni accesos. El candidato usa sus propias credenciales gratuitas.
> - No es necesario configurar Browser Relay, Control UI ni pairing.
> - Lo que se evalua es la **capacidad de levantar, conectar e integrar** sistemas — no la complejidad de la integracion en si.

### Entregables

- Configuracion Docker para OpenClaw
- Integracion funcional OpenClaw <-> RAG
- Documentacion clara de como reproducir
- Evidencia de ejecucion (logs, screenshots o demo)

---

## 8. Defensa del Proyecto

El candidato debera realizar una presentacion tecnica (30-45 min) donde:

- **Demuestre el sistema funcionando** end-to-end (ingesta → retrieval → generacion)
- **Explique decisiones tecnicas** clave: eleccion de modelos, estrategias de chunking, tecnicas de retrieval, eleccion de corpus
- **Discuta trade-offs**: por que eligio una estrategia sobre otra, que limitaciones encontro
- **Responda preguntas** sobre escalabilidad, mejoras futuras y como el sistema se adaptaria a produccion
- **Comente su uso de herramientas de IA**: que prompts uso, que genero vs que modifico manualmente

> La defensa oral es tan importante como el codigo. Un sistema funcional sin comprension de las decisiones tecnicas no sera suficiente.

---

## Resumen de entregables

| Fase | Entregable principal |
| --- | --- |
| Fase 1 | Docker Compose funcional + repo con Conventional Commits |
| Fase 2 | Pipeline RAG completo con tests |
| Fase 3 | Agente LangGraph con routing y tools |
| Fase 4 | Script de evaluacion + reporte de metricas |
| Fase 5 | API y/o Frontend funcional |
| Fase 6 (bonus) | Integracion OpenClaw via Docker |

**Se espera que las Fases 1-3 esten completas y funcionales. Las Fases 4 y 5 son diferenciadoras. La Fase 6 es bonus.**

---

VoiceFlip Technologies — Febrero 2026
