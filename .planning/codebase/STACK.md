# Technology Stack

**Analysis Date:** 2026-03-29

## Languages

**Primary:**
- Python 3.9.6 - Backend API, agents, and tools

**Secondary:**
- HTML (site.html) - Frontend static content in `/Users/mateuspires/Dev/agent-clinic/frontend/`

## Runtime

**Environment:**
- Python 3.9.6

**Package Manager:**
- pip
- Lockfile: requirements.txt (managed at `/Users/mateuspires/Dev/agent-clinic/agent-service/requirements.txt`)

## Frameworks

**Core:**
- FastAPI 0.115.5 - HTTP server for webhook endpoints and API
- Uvicorn 0.41.0 - ASGI server (running on port 8000)

**AI/LLM:**
- LangChain 0.3.28 - LLM orchestration framework
- LangChain OpenAI 0.3.35 - OpenAI integration
- LangGraph 0.2.76 - Agent/workflow graph framework
- LangGraph SDK 0.1.74 - SDK for graph management
- LangGraph Prebuilt 1.0.1 - Pre-built graph components

**Message Management:**
- LangChain Core - Base message types and tools
- LangSmith 0.7.17 - LangChain debugging and monitoring

**Observability:**
- Langfuse 2.57.13 - LLM observability and tracing
- OpenTelemetry SDK 1.40.0 - Observability framework
- OpenTelemetry API 1.40.0 - Telemetry API
- OpenTelemetry Exporter OTLP (HTTP) 1.40.0 - OTLP exporting

**Async & Scheduling:**
- APScheduler 3.11.0 - Task scheduling (follow-up dispatcher)

**Testing:**
- pytest 8.4.2 - Test framework

## Key Dependencies

**Critical:**
- langchain (0.3.28) - Core LLM framework for agents (Sofia and Carla graphs)
- langchain-openai (0.3.35) - LLM calls to OpenRouter API
- langgraph (0.2.76) - Agent state graphs for multi-step workflows
- fastapi (0.115.5) - WhatsApp webhook and API server
- redis (7.3.0) - Session state persistence (async via aioredis)
- psycopg2-binary (2.9.11) - PostgreSQL database access

**Infrastructure:**
- SQLAlchemy 2.0.48 - SQL toolkit and ORM
- Alembic 1.16.5 - Database migration tool
- pydantic (2.12.5) - Data validation and settings
- python-dotenv (1.2.2) - Environment variable loading

**HTTP & Networking:**
- httpx (0.28.1) - Async HTTP client for Evolution API calls
- requests (2.32.5) - Sync HTTP client
- urllib3 (2.6.3) - HTTP client library

**Data Processing:**
- orjson (3.11.7) - Fast JSON serialization
- PyYAML (6.0.3) - YAML parsing
- dateparser (1.2.2) - Natural language date parsing
- jsonpatch (1.33) - JSON patch utilities

**Encoding & Text:**
- tiktoken (0.12.0) - Token counting for LLM inputs
- regex (2026.2.28) - Advanced regex support

## Configuration

**Environment:**
- Loaded via `python-dotenv` (load_dotenv() in entry points)
- `.env` file present at `/Users/mateuspires/Dev/agent-clinic/agent-service/.env`

**Key configs required:**
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

**Build:**
- No build configuration detected (Python application, no compilation)
- Entry points:
  - `run_api.py` - FastAPI webhook server
  - `main.py` - Interactive CLI for Sofia+Carla pipeline
  - `main_carla.py` - Carla formatter standalone

## Platform Requirements

**Development:**
- Python 3.9+
- PostgreSQL database
- Redis server
- OpenRouter API account (or compatible LLM provider)
- Evolution API account (WhatsApp integration)
- Langfuse account (observability)

**Production:**
- Python 3.9+ runtime
- PostgreSQL 12+ database
- Redis 6+ cache store
- FastAPI server (uvicorn) listening on port 8000
- External connectivity to:
  - Evolution API (WhatsApp messaging)
  - OpenRouter API (LLM inference)
  - Langfuse backend (observability)
  - PostgreSQL database
  - Redis server

---

*Stack analysis: 2026-03-29*
