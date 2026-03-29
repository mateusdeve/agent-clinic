<!-- GSD:project-start source:PROJECT.md -->
## Project

**MedIA — Sistema de Gestao de Clinicas com IA**

Plataforma SaaS multi-tenant de gestao de clinicas medicas com atendente de IA no WhatsApp. O sistema combina um agente conversacional inteligente (agendamento, follow-up, FAQ, lembretes) com um painel web completo para administradores, recepcionistas e medicos. Inclui landing page de captura que redireciona leads direto para o WhatsApp.

**Core Value:** O paciente consegue agendar, remarcar e tirar duvidas pelo WhatsApp 24h por dia sem intervencao humana, e a equipe da clinica tem visibilidade total das conversas e agendamentos em tempo real.

### Constraints

- **Tech stack frontend**: Next.js + Tailwind CSS — decisao do usuario
- **Tech stack backend**: Python/FastAPI — ja existe, manter
- **WhatsApp**: Evolution API — ja integrado, manter
- **LLM**: OpenRouter — ja configurado, manter
- **Multi-tenancy**: Dados isolados por clinica desde v1
- **Idioma**: Interface em portugues brasileiro (pt-BR)
- **Design**: Seguir identidade visual do site.html (paleta verde, tipografia DM)
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.9.6 - Backend API, agents, and tools
- HTML (site.html) - Frontend static content in `/Users/mateuspires/Dev/agent-clinic/frontend/`
## Runtime
- Python 3.9.6
- pip
- Lockfile: requirements.txt (managed at `/Users/mateuspires/Dev/agent-clinic/agent-service/requirements.txt`)
## Frameworks
- FastAPI 0.115.5 - HTTP server for webhook endpoints and API
- Uvicorn 0.41.0 - ASGI server (running on port 8000)
- LangChain 0.3.28 - LLM orchestration framework
- LangChain OpenAI 0.3.35 - OpenAI integration
- LangGraph 0.2.76 - Agent/workflow graph framework
- LangGraph SDK 0.1.74 - SDK for graph management
- LangGraph Prebuilt 1.0.1 - Pre-built graph components
- LangChain Core - Base message types and tools
- LangSmith 0.7.17 - LangChain debugging and monitoring
- Langfuse 2.57.13 - LLM observability and tracing
- OpenTelemetry SDK 1.40.0 - Observability framework
- OpenTelemetry API 1.40.0 - Telemetry API
- OpenTelemetry Exporter OTLP (HTTP) 1.40.0 - OTLP exporting
- APScheduler 3.11.0 - Task scheduling (follow-up dispatcher)
- pytest 8.4.2 - Test framework
## Key Dependencies
- langchain (0.3.28) - Core LLM framework for agents (Sofia and Carla graphs)
- langchain-openai (0.3.35) - LLM calls to OpenRouter API
- langgraph (0.2.76) - Agent state graphs for multi-step workflows
- fastapi (0.115.5) - WhatsApp webhook and API server
- redis (7.3.0) - Session state persistence (async via aioredis)
- psycopg2-binary (2.9.11) - PostgreSQL database access
- SQLAlchemy 2.0.48 - SQL toolkit and ORM
- Alembic 1.16.5 - Database migration tool
- pydantic (2.12.5) - Data validation and settings
- python-dotenv (1.2.2) - Environment variable loading
- httpx (0.28.1) - Async HTTP client for Evolution API calls
- requests (2.32.5) - Sync HTTP client
- urllib3 (2.6.3) - HTTP client library
- orjson (3.11.7) - Fast JSON serialization
- PyYAML (6.0.3) - YAML parsing
- dateparser (1.2.2) - Natural language date parsing
- jsonpatch (1.33) - JSON patch utilities
- tiktoken (0.12.0) - Token counting for LLM inputs
- regex (2026.2.28) - Advanced regex support
## Configuration
- Loaded via `python-dotenv` (load_dotenv() in entry points)
- `.env` file present at `/Users/mateuspires/Dev/agent-clinic/agent-service/.env`
- `OPENROUTER_API_KEY` - LLM API key for OpenRouter
- `OPENROUTER_BASE_URL` - OpenRouter API base URL
- `LLM_MODEL` - Model identifier (e.g., gpt-4, claude-3)
- `EMBEDDING_MODEL` - Model for embeddings (default: openai/text-embedding-3-small)
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection for sessions
- `EVOLUTION_API_URL` - Evolution API base URL
- `EVOLUTION_API_KEY` - Evolution API authentication key
- `EVOLUTION_INSTANCE_NAME` - WhatsApp instance identifier
- `LANGFUSE_PUBLIC_KEY` - Langfuse tracing public key
- `LANGFUSE_SECRET_KEY` - Langfuse tracing secret key
- `LANGFUSE_HOST` - Langfuse backend host
- No build configuration detected (Python application, no compilation)
- Entry points:
## Platform Requirements
- Python 3.9+
- PostgreSQL database
- Redis server
- OpenRouter API account (or compatible LLM provider)
- Evolution API account (WhatsApp integration)
- Langfuse account (observability)
- Python 3.9+ runtime
- PostgreSQL 12+ database
- Redis 6+ cache store
- FastAPI server (uvicorn) listening on port 8000
- External connectivity to:
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Naming Patterns
- `snake_case.py` - All Python modules
- Module purpose clear in name: `agenda.py`, `persistence.py`, `extraction.py`, `summarizer.py`
- Internal/private modules with underscore prefix: `_get_db()` contextmanager, `_get_llm()` function
- Test files: `test_connections.py` (pytest naming convention)
- `snake_case` for all functions
- Public functions: `verificar_disponibilidade()`, `salvar_paciente()`, `load_session_history()`
- Private/internal functions prefixed with underscore: `_get_db()`, `_invoke_llm()`, `_gerar_slots()`, `_normalizar_data()`
- Tool functions exported for LangChain use: `@tool` decorator marks public tools in `src/tools/`
- Helper utilities in modules: `_get_periodo()`, `_get_genero()`, `_get_dados_coletados()` in `src/agent/nodes.py`
- `snake_case` for all variables and parameters
- State dictionaries: `state`, `data`, `extracted`, `result`
- Environment variables: UPPERCASE with underscores: `DATABASE_URL`, `REDIS_URL`, `LLM_MODEL`, `OPENROUTER_API_KEY`
- Constants as UPPERCASE: `ESPECIALIDADES`, `CONVENIOS`, `SESSION_TTL = 86400`, `HORARIOS_MOCK`
- Portuguese variable names used in domain logic: `nome_paciente`, `motivo_consulta`, `data_agendamento`, `horario_agendamento`, `etapa`, `convenio`, `protocolo_consulta`
- TypedDict for state objects: `class ClinicaState(TypedDict)` in `src/agent/state.py`
- Type hints in function signatures: `def buscar_paciente(phone: str) -> Optional[dict]:`
- Import types from `typing`: `Optional`, `List`, `Dict`, `Any`
- BaseMessage types from LangChain: `HumanMessage`, `AIMessage`, `SystemMessage`
- `PascalCase` for class names: `ClinicRAG`, `SessionManager`, `EvolutionClient`, `ConversationSummarizer`
- Classes are minimal — mostly stateful helpers or managers
- Methods follow function naming convention: `snake_case`
- Private methods: `_embed()` in `ClinicRAG`
## Code Style
- No formatter enforced (no `.prettierrc`, `black` config, or `pyproject.toml` detected)
- Indentation: 4 spaces (standard Python)
- Line length: appears to be 100-120 characters typical
- Import style: direct imports, not star imports
- No linting configuration detected (no `.pylintrc`, `.flake8`, or similar)
- Pattern: Follow PEP 8 informally based on code samples
- Imports verified: `# noqa: F401` used to suppress unused import warnings in `src/tools/appointments.py` line 10
- Module docstrings present: `"""Operações de pacientes — reconhecimento e persistência por número."""` in `src/tools/patients.py`
- Triple quotes for block documentation in prompts and docstrings
- Inline comments minimal — code is self-documenting
- Prompt constants heavily commented with section markers: `# ────────────────────────────────────────────────────────────`
## Import Organization
- No aliases detected — all imports use absolute paths from project root: `from src.tools.patients import...`
- Relative imports not used; absolute imports from `src/` prefix
## Error Handling
- Broad `except Exception as e:` catch-all in production code
- Errors logged with module context: `logger.error(f"[persistence] save_messages error: {e}")`
- Module prefix in log messages: `[persistence]`, `[doctors]`, `[appointments]`, `[patients]`
- Functions return safe defaults on error (None, empty dict, empty list):
- No explicit exception raising except for configuration errors: `raise RuntimeError("DATABASE_URL não configurado")`
- Silent failures with logging: Most functions catch and log errors, then return None/empty
- Connection context managers in `_get_db()` ensure cleanup via try/finally
- Session manager handles corrupted Redis data by creating new session: `except (json.JSONDecodeError, KeyError) as e:` followed by fallback
## Logging
- Module-scoped loggers: each file creates its own logger with module name
- Log levels used: `info`, `warning`, `error`
- Log format set in `src/api/webhook.py`: `"%(asctime)s [%(name)s] %(levelname)s: %(message)s"`
- All logs include module context in message: `logger.info(f"[patients] Paciente salvo: {phone} — {nome}")`
- Info: Key operations completed successfully: "Grafo Sofia inicializado", "Paciente salvo"
- Warning: Expected but unusual conditions: "Sessão corrompida", "data inválida"
- Error: Exceptions and failures: "erro ao buscar horários", "save_messages error"
## Function Design
- Tool functions: ~15-25 lines
- Helper functions: ~5-10 lines
- Complex orchestration functions: up to 50 lines with clear sections
- Type hints on all parameters: `def buscar_paciente(phone: str) -> Optional[dict]:`
- Optional parameters have defaults: `def criar_followup(..., feedback_score=None):`
- No position-only or keyword-only arguments observed
- Maximum 4-5 parameters typical; longer signatures in orchestrator functions
- Explicit return types in annotations
- Return None/empty collections on error (not exceptions)
- Dictionaries for structured returns: `{"disponivel": True, "medicos": [...], "mensagem": "..."}`
- Tuples only in specific cases: `_normalizar_data()` returns `(data_str, datetime_obj)`
- Tool functions use docstring format compatible with LangChain tools:
- Non-tool functions have minimal docstrings or none
- Docstrings explain purpose and key parameters/returns
## Module Design
- Modules export public functions and constants
- Public items: no leading underscore
- Private/internal items: underscore prefix `_get_db()`, `_get_llm()`
- `patients.py`: Patient lookup and creation
- `appointments.py`: Appointment CRUD operations
- `doctors.py`: Doctor availability and selection
- `agenda.py`: High-level appointment workflow tools
- `followup.py`: Follow-up reminders
- `faq.py`: FAQ lookups
- `state.py`: TypedDict definition for conversation state
- `prompts.py`: System prompts for each conversation stage
- `nodes.py`: Node functions (recepcionar, coletar_dados, etc.)
- `graph.py`: LangGraph construction and session management
- `persistence.py`: Database save/load for messages and summaries
- `rag.py`: Vector search for conversation context
- `summarizer.py`: LLM-based conversation summarization
- `webhook.py`: FastAPI app and Evolution API webhook endpoint
- `orchestrator.py`: Message buffering and graph orchestration
- `session.py`: Redis session management
- `evolution.py`: WhatsApp Evolution API client
- `extraction.py`: LLM-based data extraction from conversations
- `langfuse_setup.py`: Langfuse integration for trace logging
## Language and Text
- All state field names in Portuguese: `nome_paciente`, `motivo_consulta`, `especialidade`, `convenio`, `data_agendamento`
- All prompt text in Portuguese (natural language for patient interaction)
- Comments and docstrings in Portuguese
- Variable names in Portuguese for domain concepts, English for infrastructure: `session_id`, `phone`, `query`, but `nome`, `especialidade`, `etapa`
## Database Conventions
- Parameterized queries with `%s` placeholders for PostgreSQL
- Multi-line SQL strings in triple quotes
- Contextmanager `_get_db()` used consistently for connection lifecycle
- Connection closed in finally block via context manager
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- Two cooperating agents: Sofia (conversation) + Carla (formatting) pipeline
- LangGraph state machines for conversation workflow
- Adaptive message buffering to simulate natural typing rhythm
- Knowledge-augmented conversation via RAG (Retrieval-Augmented Generation)
- Persistent session state in Redis for multi-turn conversations
- Database persistence for patient history, appointments, and knowledge chunks
## Layers
- Purpose: Handle WhatsApp integration via Evolution API
- Location: `src/api/webhook.py`, `src/api/evolution.py`, `src/api/session.py`
- Contains: FastAPI app, webhook handlers, Evolution API client, session management
- Depends on: Orchestrator, Session Manager, Evolution Client
- Used by: WhatsApp users, external platforms
- Purpose: Coordinate message buffering, graph invocation, and message dispatch
- Location: `src/api/orchestrator.py`
- Contains: Message buffer management, async dispatch logic, rate limiting
- Depends on: Sofia graph, Carla graph, Session Manager, Evolution Client
- Used by: Webhook endpoint
- Purpose: Handle multi-turn clinic conversations, state management, decision routing
- Location: `src/agent/graph.py`, `src/agent/nodes.py`, `src/agent/state.py`, `src/agent/prompts.py`
- Contains: Conversation graph, node functions, system prompts, state schema
- Depends on: OpenAI LLM, RAG retrieval, tools layer, extraction logic
- Used by: Orchestrator, CLI main.py
- Purpose: Reformat Sofia's responses into natural, message-sized chunks for WhatsApp
- Location: `src/agent_carla/graph.py`, `src/agent_carla/nodes.py`, `src/agent_carla/state.py`
- Contains: Simple linear processing graph (format → chunk → send)
- Depends on: OpenAI LLM
- Used by: Orchestrator, CLI main.py
- Purpose: Encapsulate domain-specific operations (scheduling, patient data, FAQ)
- Location: `src/tools/agenda.py`, `src/tools/appointments.py`, `src/tools/patients.py`, `src/tools/doctors.py`, `src/tools/followup.py`, `src/tools/faq.py`
- Contains: Database queries, schedule logic, appointment management
- Depends on: PostgreSQL database
- Used by: Agent nodes in Sofia graph
- Purpose: Manage conversation history, embeddings, summaries, and knowledge retrieval
- Location: `src/memory/persistence.py`, `src/memory/rag.py`, `src/memory/summarizer.py`
- Contains: Database persistence, vector embeddings, conversation summarization
- Depends on: PostgreSQL, OpenAI embeddings API
- Used by: Agent nodes, graph lifecycle hooks
- Purpose: Shared data extraction and state determination logic
- Location: `src/core/extraction.py`
- Contains: LLM-based JSON extraction, patient name validation, etapa determination
- Depends on: OpenAI LLM
- Used by: Main CLI, Orchestrator, Agent nodes
- Purpose: Trace execution and performance metrics via Langfuse
- Location: `src/observability/langfuse_setup.py`
- Contains: Langfuse client initialization, tracing configuration
- Depends on: Langfuse API
- Used by: Agent nodes
- Purpose: Marketing and information landing page
- Location: `frontend/site.html`
- Contains: Static HTML with styling
- Deployed as: Static file serving
## Data Flow
- Session state stored in Redis with key `session:{phone}`
- Serialized as JSON with messages converted via `messages_to_dict()`
- TTL: 24 hours per conversation
- On load, deserialized and validated for corruption
- On etapa="encerrar", flag set to prevent re-saving on next message
- `patients`: phone → name, total_consultas, ultima_visita
- `conversations`: session_id, role (user/assistant), content, metadata
- `conversation_summaries`: session_id, summary, key_topics, sentiment, resolved
- `knowledge_chunks`: RAG index with embeddings (vector column)
- `doctors`: name, specialty, availability
- `appointments`: patient_id, date, time, doctor_id, protocol, status
- `followups`: pending messages scheduled for future delivery
## Key Abstractions
- Purpose: Immutable state schema for Sofia graph
- Examples: `src/agent/state.py`
- Pattern: TypedDict with message history, extracted patient data, conversation metadata, appointment details, and workflow flags
- Purpose: Immutable state for formatting pipeline
- Examples: `src/agent_carla/state.py`
- Pattern: TypedDict with text_original, texto_formatado, mensagens_quebradas
- Purpose: Pure functions that read state and return dict updates
- Examples: `recepcionar()`, `identificar_motivo()`, `verificar_agenda()` in `src/agent/nodes.py`
- Pattern: `(state: ClinicaState) → dict` with side effects (DB, LLM calls) wrapped in try-except
- Purpose: Encapsulate callable operations for agent context
- Examples: `verificar_disponibilidade()`, `agendar_consulta()` in `src/tools/agenda.py`
- Pattern: Functions decorated with `@tool` that call database or external APIs
- Purpose: Accumulate rapid user messages before processing
- Location: `_message_buffers` dict in `src/api/orchestrator.py`
- Pattern: Per-phone deque, flushed after silence threshold with adaptive timing
## Entry Points
- Location: `src/api/webhook.py` → `app = FastAPI()`
- Triggers: External webhook calls from Evolution API
- Responsibilities: Validate payload, extract phone/text, dispatch to orchestrator
- Location: `POST /webhook/evolution`
- Triggers: WhatsApp messages routed by Evolution API
- Responsibilities: Parse payload, call `handle_message()`, return 200 OK
- Location: `main.py`
- Triggers: Direct Python execution
- Responsibilities: Build graphs, loop on stdin, display formatted output
- Location: `run_api.py` → `uvicorn.run("src.api.webhook:app", ...)`
- Triggers: Direct Python execution
- Responsibilities: Start FastAPI with uvicorn, enable hot reload
## Error Handling
- **Extraction failures:** If LLM JSON parsing fails, default to null values; conversation continues
- **Database errors:** Log error, skip persistence step; conversation continues
- **LLM timeouts:** Catch via `langchain_openai` exception handling, fallback to generic response
- **Evolution API failures:** Log warning, retry or fallback to text-only (no buttons)
- **RAG retrieval:** Return empty string if no context found; prompt still valid without it
- **Session corruption:** On Redis decode error, create new default state; old session lost
## Cross-Cutting Concerns
- Per-module loggers initialized as `logging.getLogger("agent-clinic.{module}")`
- Level: INFO for operations, WARNING for potential issues, ERROR for failures
- Format: `"%(asctime)s [%(name)s] %(levelname)s: %(message)s"`
- Evolution API: API key passed in headers `{"apikey": EVOLUTION_API_KEY}`
- Database: Connection via `DATABASE_URL` environment variable with psycopg2
- LLM APIs: API key via `OPENROUTER_API_KEY`, base URL via `OPENROUTER_BASE_URL`
- Patient names: `sanitize_extracted_nome_paciente()` in `src/core/extraction.py` prevents Sofia/Carla confusion
- Specialties/Convênios: Exact match against frozen sets in `src/tools/agenda.py`
- Dates/times: Passed through as strings; formatting handled by LLM context
- Async locks per phone: `_phone_locks[phone]` in orchestrator prevents race conditions
- Single-threaded SQLAlchemy + psycopg2 connections (no connection pooling)
- Redis async client for session I/O
- LLM calls are blocking (httpx via openai library)
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
