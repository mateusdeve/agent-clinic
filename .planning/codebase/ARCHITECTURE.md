# Architecture

**Analysis Date:** 2026-03-29

## Pattern Overview

**Overall:** LLM-powered agent orchestration with dual-agent pipeline and adaptive message buffering.

**Key Characteristics:**
- Two cooperating agents: Sofia (conversation) + Carla (formatting) pipeline
- LangGraph state machines for conversation workflow
- Adaptive message buffering to simulate natural typing rhythm
- Knowledge-augmented conversation via RAG (Retrieval-Augmented Generation)
- Persistent session state in Redis for multi-turn conversations
- Database persistence for patient history, appointments, and knowledge chunks

## Layers

**API/Webhook Layer:**
- Purpose: Handle WhatsApp integration via Evolution API
- Location: `src/api/webhook.py`, `src/api/evolution.py`, `src/api/session.py`
- Contains: FastAPI app, webhook handlers, Evolution API client, session management
- Depends on: Orchestrator, Session Manager, Evolution Client
- Used by: WhatsApp users, external platforms

**Orchestration Layer:**
- Purpose: Coordinate message buffering, graph invocation, and message dispatch
- Location: `src/api/orchestrator.py`
- Contains: Message buffer management, async dispatch logic, rate limiting
- Depends on: Sofia graph, Carla graph, Session Manager, Evolution Client
- Used by: Webhook endpoint

**Agent Layer (Sofia - Primary Agent):**
- Purpose: Handle multi-turn clinic conversations, state management, decision routing
- Location: `src/agent/graph.py`, `src/agent/nodes.py`, `src/agent/state.py`, `src/agent/prompts.py`
- Contains: Conversation graph, node functions, system prompts, state schema
- Depends on: OpenAI LLM, RAG retrieval, tools layer, extraction logic
- Used by: Orchestrator, CLI main.py

**Agent Layer (Carla - Formatter Agent):**
- Purpose: Reformat Sofia's responses into natural, message-sized chunks for WhatsApp
- Location: `src/agent_carla/graph.py`, `src/agent_carla/nodes.py`, `src/agent_carla/state.py`
- Contains: Simple linear processing graph (format → chunk → send)
- Depends on: OpenAI LLM
- Used by: Orchestrator, CLI main.py

**Tools Layer:**
- Purpose: Encapsulate domain-specific operations (scheduling, patient data, FAQ)
- Location: `src/tools/agenda.py`, `src/tools/appointments.py`, `src/tools/patients.py`, `src/tools/doctors.py`, `src/tools/followup.py`, `src/tools/faq.py`
- Contains: Database queries, schedule logic, appointment management
- Depends on: PostgreSQL database
- Used by: Agent nodes in Sofia graph

**Memory/Context Layer:**
- Purpose: Manage conversation history, embeddings, summaries, and knowledge retrieval
- Location: `src/memory/persistence.py`, `src/memory/rag.py`, `src/memory/summarizer.py`
- Contains: Database persistence, vector embeddings, conversation summarization
- Depends on: PostgreSQL, OpenAI embeddings API
- Used by: Agent nodes, graph lifecycle hooks

**Core/Extraction Layer:**
- Purpose: Shared data extraction and state determination logic
- Location: `src/core/extraction.py`
- Contains: LLM-based JSON extraction, patient name validation, etapa determination
- Depends on: OpenAI LLM
- Used by: Main CLI, Orchestrator, Agent nodes

**Observability Layer:**
- Purpose: Trace execution and performance metrics via Langfuse
- Location: `src/observability/langfuse_setup.py`
- Contains: Langfuse client initialization, tracing configuration
- Depends on: Langfuse API
- Used by: Agent nodes

**Frontend/Web:**
- Purpose: Marketing and information landing page
- Location: `frontend/site.html`
- Contains: Static HTML with styling
- Deployed as: Static file serving

## Data Flow

**Incoming WhatsApp Message Flow:**

1. WhatsApp user sends message → Evolution API webhook
2. `webhook.py` receives POST `/webhook/evolution`
3. Message parsed: phone number extracted, text validated
4. `handle_message()` called in `orchestrator.py` with (phone, text)
5. Message buffered by phone number (adaptive wait: 3.5s base, 2.5s if typing fast)
6. After buffer timeout, accumulated messages joined into single state update
7. `SessionManager` loads existing state from Redis or creates new default state
8. State enriched with message history (LangChain HumanMessage)
9. Data extraction via `extract_data()` → JSON with patient name, specialty, etc.
10. Conversation state reconciliation (avoid Sofia/Carla name confusion)
11. Etapa determined: recepcionar | identificar_motivo | coletar_dados | verificar_agenda | confirmar_agendamento | encerrar | responder_faq | cancelar_consulta | alterar_consulta
12. Sofia graph invoked with state + message buffer

**Sofia Graph Processing Flow:**

1. Entry node `retrieve_context`: Query RAG with latest message to fetch relevant past interactions
2. Router evaluates state.etapa and routes to appropriate specialized node
3. Specialized node (e.g., `identificar_motivo`):
   - Calls `_invoke_llm()` with system prompt + conversation history + RAG context
   - May invoke tools (e.g., `verificar_disponibilidade()` for scheduling)
   - Appends AIMessage to state messages
4. Edge to `save_and_learn` node:
   - Persists messages to PostgreSQL via `save_messages()`
   - Summarizes conversation via `ConversationSummarizer`
5. If etapa is "encerrar":
   - Save summary to database
   - Index resolved interactions into RAG vector store
6. Graph returns updated state with new assistant message

**Carla Graph Processing Flow:**

1. Sofia's response text passed as input
2. Node `processar_texto`: LLM reformats response into short paragraphs for WhatsApp
3. Node `quebrar_mensagens`: Chunks formatted text into individual message objects
4. Node `enviar`: Mock send (in CLI) or returns structured message list
5. Each message: `{"conteudo": str}` containing single WhatsApp-appropriate chunk

**WhatsApp Output Flow:**

1. Carla-formatted messages returned to orchestrator
2. For each message:
   - `evolution_client.send_message_with_typing()` called
   - Typing indicator shown proportionally to message length
   - Delay = min(3.5s, max(1s, len(text)/30 chars per second))
   - Message sent via Evolution API
   - Delay before next message (configurable, default 1s)
3. Orchestrator saves updated state to Redis (session TTL: 24 hours)
4. Response logged, tracing stored in Langfuse

**State Persistence:**

- Session state stored in Redis with key `session:{phone}`
- Serialized as JSON with messages converted via `messages_to_dict()`
- TTL: 24 hours per conversation
- On load, deserialized and validated for corruption
- On etapa="encerrar", flag set to prevent re-saving on next message

**Database Operations:**

- `patients`: phone → name, total_consultas, ultima_visita
- `conversations`: session_id, role (user/assistant), content, metadata
- `conversation_summaries`: session_id, summary, key_topics, sentiment, resolved
- `knowledge_chunks`: RAG index with embeddings (vector column)
- `doctors`: name, specialty, availability
- `appointments`: patient_id, date, time, doctor_id, protocol, status
- `followups`: pending messages scheduled for future delivery

## Key Abstractions

**ClinicaState (TypedDict):**
- Purpose: Immutable state schema for Sofia graph
- Examples: `src/agent/state.py`
- Pattern: TypedDict with message history, extracted patient data, conversation metadata, appointment details, and workflow flags

**CarlaState (TypedDict):**
- Purpose: Immutable state for formatting pipeline
- Examples: `src/agent_carla/state.py`
- Pattern: TypedDict with text_original, texto_formatado, mensagens_quebradas

**Node Functions:**
- Purpose: Pure functions that read state and return dict updates
- Examples: `recepcionar()`, `identificar_motivo()`, `verificar_agenda()` in `src/agent/nodes.py`
- Pattern: `(state: ClinicaState) → dict` with side effects (DB, LLM calls) wrapped in try-except

**Tools (LangChain @tool):**
- Purpose: Encapsulate callable operations for agent context
- Examples: `verificar_disponibilidade()`, `agendar_consulta()` in `src/tools/agenda.py`
- Pattern: Functions decorated with `@tool` that call database or external APIs

**Message Buffers:**
- Purpose: Accumulate rapid user messages before processing
- Location: `_message_buffers` dict in `src/api/orchestrator.py`
- Pattern: Per-phone deque, flushed after silence threshold with adaptive timing

## Entry Points

**WebAPI Server:**
- Location: `src/api/webhook.py` → `app = FastAPI()`
- Triggers: External webhook calls from Evolution API
- Responsibilities: Validate payload, extract phone/text, dispatch to orchestrator

**Webhook Endpoint:**
- Location: `POST /webhook/evolution`
- Triggers: WhatsApp messages routed by Evolution API
- Responsibilities: Parse payload, call `handle_message()`, return 200 OK

**CLI Interactive Mode:**
- Location: `main.py`
- Triggers: Direct Python execution
- Responsibilities: Build graphs, loop on stdin, display formatted output

**CLI API Server:**
- Location: `run_api.py` → `uvicorn.run("src.api.webhook:app", ...)`
- Triggers: Direct Python execution
- Responsibilities: Start FastAPI with uvicorn, enable hot reload

## Error Handling

**Strategy:** Try-catch with logging; graceful degradation without breaking conversation

**Patterns:**

- **Extraction failures:** If LLM JSON parsing fails, default to null values; conversation continues
- **Database errors:** Log error, skip persistence step; conversation continues
- **LLM timeouts:** Catch via `langchain_openai` exception handling, fallback to generic response
- **Evolution API failures:** Log warning, retry or fallback to text-only (no buttons)
- **RAG retrieval:** Return empty string if no context found; prompt still valid without it
- **Session corruption:** On Redis decode error, create new default state; old session lost

**Logger names:** `"agent-clinic.{module}"` (e.g., `"agent-clinic.nodes"`, `"agent-clinic.webhook"`)

## Cross-Cutting Concerns

**Logging:**
- Per-module loggers initialized as `logging.getLogger("agent-clinic.{module}")`
- Level: INFO for operations, WARNING for potential issues, ERROR for failures
- Format: `"%(asctime)s [%(name)s] %(levelname)s: %(message)s"`

**Authentication:**
- Evolution API: API key passed in headers `{"apikey": EVOLUTION_API_KEY}`
- Database: Connection via `DATABASE_URL` environment variable with psycopg2
- LLM APIs: API key via `OPENROUTER_API_KEY`, base URL via `OPENROUTER_BASE_URL`

**Validation:**
- Patient names: `sanitize_extracted_nome_paciente()` in `src/core/extraction.py` prevents Sofia/Carla confusion
- Specialties/Convênios: Exact match against frozen sets in `src/tools/agenda.py`
- Dates/times: Passed through as strings; formatting handled by LLM context

**Concurrency:**
- Async locks per phone: `_phone_locks[phone]` in orchestrator prevents race conditions
- Single-threaded SQLAlchemy + psycopg2 connections (no connection pooling)
- Redis async client for session I/O
- LLM calls are blocking (httpx via openai library)

---

*Architecture analysis: 2026-03-29*
