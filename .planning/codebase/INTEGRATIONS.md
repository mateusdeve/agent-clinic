# External Integrations

**Analysis Date:** 2026-03-29

## APIs & External Services

**LLM Provider:**
- OpenRouter - LLM inference service for Sofia agent
  - SDK/Client: `langchain-openai` via OpenRouter proxy
  - Auth: `OPENROUTER_API_KEY` (environment variable)
  - Base URL: `OPENROUTER_BASE_URL` (configurable)
  - Usage locations:
    - `src/agent/nodes.py` - Sofia agent responses
    - `src/agent_carla/nodes.py` - Carla formatter
    - `src/core/extraction.py` - Data extraction from messages
    - `src/memory/summarizer.py` - Conversation summarization
    - `src/memory/rag.py` - Embeddings generation

**WhatsApp Messaging:**
- Evolution API - WhatsApp message integration
  - SDK/Client: Custom `EvolutionClient` class in `src/api/evolution.py`
  - Auth: `EVOLUTION_API_KEY` (API key in headers)
  - Endpoints:
    - `POST /message/sendText/{instance}` - Send text messages
    - `POST /message/sendButtons/{instance}` - Send interactive buttons
    - `POST /message/sendList/{instance}` - Send list menus
    - `POST /chat/updatePresence/{instance}` - Send typing indicators
    - `POST /instance/setPresence/{instance}` - Set online/offline status
  - Configuration:
    - `EVOLUTION_API_URL` - API base URL
    - `EVOLUTION_INSTANCE_NAME` - WhatsApp instance identifier
    - `EVOLUTION_TYPING_SPEED` - Character speed for typing simulation (default: 30 chars/sec)
    - `EVOLUTION_TYPING_MIN` - Minimum typing delay (default: 1.0 sec)
    - `EVOLUTION_TYPING_MAX` - Maximum typing delay (default: 8.0 sec)
    - `EVOLUTION_SEND_DELAY` - Delay between multiple messages (default: 1.0 sec)
  - Receives messages via webhook at `POST /webhook/evolution`

## Data Storage

**Databases:**
- PostgreSQL - Primary data store
  - Connection: `DATABASE_URL` environment variable
  - Client: `psycopg2-binary` (direct connection)
  - ORM: SQLAlchemy 2.0.48 for higher-level queries
  - Migrations: Alembic 1.16.5
  - Location: `/Users/mateuspires/Dev/agent-clinic/agent-service/migrations/`
  - Usage:
    - `src/memory/persistence.py` - Conversation storage and summarization
    - `src/tools/appointments.py` - Appointment data
    - `src/tools/doctors.py` - Doctor information
    - `src/tools/patients.py` - Patient profiles
    - `src/tools/followup.py` - Follow-up reminders
    - `src/memory/rag.py` - Knowledge chunks with pgvector embeddings

**Caching:**
- Redis - Session state and temporary data
  - Connection: `REDIS_URL` environment variable
  - Client: `redis` library with async support (`redis.asyncio`)
  - TTL: 24 hours (SESSION_TTL = 86400 seconds)
  - Storage location: `src/api/session.py`
  - Key pattern: `session:{phone}` stores conversation state per WhatsApp number
  - Data: JSON serialized conversation messages and extracted fields

**File Storage:**
- Local filesystem only - No cloud storage detected
  - Static content: `/Users/mateuspires/Dev/agent-clinic/frontend/site.html`

## Authentication & Identity

**Auth Provider:**
- Custom implementation - No third-party OAuth/OIDC detected
  - WhatsApp phone numbers used as session identifiers
  - API authentication via environment variables (OpenRouter, Langfuse, Evolution)
  - No user login system (bot-driven)

## Monitoring & Observability

**Error Tracking & Tracing:**
- Langfuse - LLM observability and trace tracking
  - SDK: `langfuse` library (2.57.13)
  - Authentication:
    - `LANGFUSE_PUBLIC_KEY` - Public API key
    - `LANGFUSE_SECRET_KEY` - Secret API key
    - `LANGFUSE_HOST` - Self-hosted or cloud backend
  - Usage: `src/observability/langfuse_setup.py`
  - Initialization: `get_langfuse()` singleton
  - Trace points:
    - Agent graph executions (Sofia and Carla)
    - LLM calls via LangChain integration
    - Session lifecycle (start/end)
  - Flush locations:
    - `src/api/orchestrator.py` - After session end
    - `main.py` - After atendimento (conversation) ends

**Logs:**
- Python logging module (built-in)
  - Logger names by module: `agent-clinic.{module}`
  - Configuration: `logging.basicConfig()` in `src/api/webhook.py`
  - Level: INFO by default
  - Format: `%(asctime)s [%(name)s] %(levelname)s: %(message)s`
  - Output: stdout/stderr

**Telemetry:**
- OpenTelemetry (experimental setup detected)
  - SDK: `opentelemetry-sdk` (1.40.0)
  - Exporter: OTLP over HTTP
  - Status: Configured but may not be actively used

## CI/CD & Deployment

**Hosting:**
- Self-hosted or cloud deployment (not specified)
- FastAPI running on uvicorn, port 8000
- Entry point: `run_api.py` via `uvicorn src.api.webhook:app`

**CI Pipeline:**
- Not detected - No GitHub Actions, GitLab CI, or other CI config found

## Environment Configuration

**Required env vars:**
- `OPENROUTER_API_KEY` - LLM provider authentication
- `OPENROUTER_BASE_URL` - LLM provider endpoint
- `LLM_MODEL` - Model identifier for Sofia and extraction
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `EVOLUTION_API_URL` - WhatsApp Evolution API endpoint
- `EVOLUTION_API_KEY` - Evolution API authentication
- `EVOLUTION_INSTANCE_NAME` - WhatsApp instance ID
- `LANGFUSE_PUBLIC_KEY` - Observability tracing
- `LANGFUSE_SECRET_KEY` - Observability tracing
- `LANGFUSE_HOST` - Observability backend

**Optional env vars:**
- `EMBEDDING_MODEL` (default: "openai/text-embedding-3-small")
- `SUMMARIZER_MODEL` (default: falls back to LLM_MODEL)
- `EVOLUTION_TYPING_SPEED` (default: 30)
- `EVOLUTION_TYPING_MIN` (default: 1.0)
- `EVOLUTION_TYPING_MAX` (default: 8.0)
- `EVOLUTION_SEND_DELAY` (default: 1.0)
- `ORCHESTRATOR_BUFFER_WAIT_BASE` (default: 3.5)
- `ORCHESTRATOR_BUFFER_WAIT_FAST` (default: 2.5)
- `ORCHESTRATOR_FAST_TYPING_THRESHOLD` (default: 4.0)

**Secrets location:**
- `.env` file (not committed, in `.gitignore`)
- Environment variables (for production deployment)

## Webhooks & Callbacks

**Incoming:**
- WhatsApp Evolution API → POST `/webhook/evolution`
  - Endpoint: `src/api/webhook.py` - FastAPI endpoint
  - Payload parsing: `_parse_evolution_payload()`
  - Event types: `messages.upsert` (text message events)
  - Message extraction: Handles direct messages and extended text formats
  - Filtering: Ignores group messages (@g.us) and bot's own messages (fromMe)
  - Processing: Async message buffering and orchestration

**Outgoing:**
- FastAPI → Evolution API (text, buttons, lists)
  - Methods in `EvolutionClient`:
    - `send_text()` - Simple text messages
    - `send_buttons()` - Interactive buttons (max 3)
    - `send_list()` - Menu lists with sections
    - `send_presence()` - Typing indicators
    - `set_online()` - Online/offline status
  - Typing simulation: Proportional to message length

**Scheduled Callbacks:**
- APScheduler job: `dispatch_followups()` every 5 minutes
  - Checks `buscar_followups_pendentes()` in database
  - Sends pending follow-up messages
  - Marks as sent via `marcar_enviado()`
  - Uses Evolution API `send_message_with_typing()`

## Data Flow Architecture

**Inbound (WhatsApp to Sofia):**
1. Evolution API sends webhook to `/webhook/evolution`
2. `handle_message()` buffers messages with adaptive timing
3. Session state loaded from Redis
4. Patient recognition via `buscar_paciente()`
5. Data extraction via LLM (`extract_data()`)
6. Sofia graph invoked with state
7. Response passed to Carla formatter
8. Messages sent back via Evolution API
9. State persisted to Redis

**Outbound (Follow-ups):**
1. APScheduler triggers every 5 minutes
2. `dispatch_followups()` queries PostgreSQL
3. Messages sent via Evolution API `send_message_with_typing()`
4. Status marked as sent in PostgreSQL

---

*Integration audit: 2026-03-29*
