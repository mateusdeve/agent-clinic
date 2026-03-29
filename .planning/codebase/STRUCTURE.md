# Codebase Structure

**Analysis Date:** 2026-03-29

## Directory Layout

```
agent-clinic/
├── agent-service/                   # Backend Python service (main application)
│   ├── src/                         # Source code root
│   │   ├── agent/                   # Sofia conversation agent (LangGraph)
│   │   ├── agent_carla/             # Carla formatting agent (LangGraph)
│   │   ├── api/                     # FastAPI server & webhooks
│   │   ├── core/                    # Shared extraction & state logic
│   │   ├── memory/                  # Persistence, RAG, summarization
│   │   ├── observability/           # Langfuse tracing setup
│   │   └── tools/                   # Domain-specific operations
│   ├── migrations/                  # Database schema (SQL)
│   ├── tests/                       # Test files
│   ├── docs/                        # Documentation
│   ├── main.py                      # CLI interactive entry point
│   ├── main_carla.py                # Carla-only CLI (legacy)
│   ├── run_api.py                   # FastAPI server entry point
│   └── requirements.txt             # Python dependencies
├── frontend/                        # Static marketing website
│   └── site.html                    # Landing page (single file)
├── .planning/                       # GSD planning documents
│   └── codebase/                    # Architecture analysis (this directory)
└── .claude/                         # Claude workspace configuration
```

## Directory Purposes

**agent-service/src/agent/**
- Purpose: Sofia — primary conversation agent for clinic interactions
- Contains: LangGraph state machine, conversation nodes, system prompts
- Key files: `graph.py` (workflow), `state.py` (state schema), `nodes.py` (agent logic), `prompts.py` (LLM instructions)
- Pattern: StateGraph with conditional routing based on conversation etapa

**agent-service/src/agent_carla/**
- Purpose: Carla — formatting & message-chunking agent
- Contains: Simple linear pipeline to reformat Sofia's output for WhatsApp
- Key files: `graph.py` (3-node pipeline), `state.py` (state schema), `nodes.py` (LLM formatting)
- Pattern: Linear StateGraph (no branching)

**agent-service/src/api/**
- Purpose: WhatsApp integration & FastAPI server
- Contains: Webhook handler, Evolution API client, session management, message orchestrator
- Key files: `webhook.py` (FastAPI app), `evolution.py` (WhatsApp client), `orchestrator.py` (message buffering & graph dispatch), `session.py` (Redis state)
- Pattern: Async request handling with per-phone message buffering

**agent-service/src/core/**
- Purpose: Shared logic across CLI and API
- Contains: Data extraction (LLM-based JSON), state validation, etapa determination
- Key files: `extraction.py` (extraction prompts, patient name validation, state defaults)
- Pattern: Stateless functions used by both main.py and orchestrator.py

**agent-service/src/memory/**
- Purpose: Conversation persistence, retrieval, summarization
- Contains: PostgreSQL operations, vector embeddings (RAG), conversation summaries
- Key files: `persistence.py` (save/load messages & summaries), `rag.py` (vector search), `summarizer.py` (LLM summarization)
- Pattern: Lazy LLM initialization, exception handling for DB operations

**agent-service/src/observability/**
- Purpose: Tracing and observability integration
- Contains: Langfuse client setup and configuration
- Key files: `langfuse_setup.py` (singleton client initialization)
- Pattern: Lazy initialization, safe get_langfuse() function

**agent-service/src/tools/**
- Purpose: Domain-specific operations for clinic (scheduling, patients, appointments)
- Contains: Encapsulated database operations and business logic
- Key files: `agenda.py` (scheduling, specialties, available times), `appointments.py` (cancel/alter), `patients.py` (patient lookup/save), `doctors.py` (doctor data), `followup.py` (follow-up messages), `faq.py` (knowledge base queries)
- Pattern: Functions decorated with `@tool` for LangChain integration; database queries with psycopg2

**agent-service/migrations/**
- Purpose: Database schema version control
- Contains: SQL migration files for PostgreSQL
- Key files: SQL scripts numbered 001-006+ defining tables (patients, conversations, appointments, etc.)
- Pattern: Sequential migration files, managed by Alembic

**agent-service/tests/**
- Purpose: Unit and integration tests
- Contains: Test modules (pytest)
- Key files: `test_connections.py` (database connectivity)
- Pattern: Minimal test coverage at this stage

**frontend/**
- Purpose: Public landing page and marketing
- Contains: Single static HTML file with embedded CSS
- Key files: `site.html` (complete single-page site with responsive design)
- Pattern: No build process; served as static asset

## Key File Locations

**Entry Points:**
- `main.py`: Interactive CLI for testing/development (reads stdin, displays formatted output)
- `run_api.py`: FastAPI server entry point (starts uvicorn on port 8000)
- `src/api/webhook.py`: FastAPI app definition with POST `/webhook/evolution` endpoint

**Configuration:**
- `.env`: Environment variables (API keys, database URL, LLM model, etc.) — NOT committed
- `requirements.txt`: Python dependencies (langchain, fastapi, psycopg2, redis, etc.)

**Core Logic:**
- `src/agent/graph.py`: Sofia's conversation state machine and routing logic
- `src/agent/nodes.py`: Implementation of 9 conversation nodes (recepcionar, coletar_dados, verificar_agenda, etc.)
- `src/api/orchestrator.py`: Message buffering and graph invocation for WhatsApp
- `src/core/extraction.py`: LLM-based data extraction shared across CLI and API

**Testing:**
- `tests/test_connections.py`: Database connection verification
- No test fixtures or factories currently defined

## Naming Conventions

**Files:**
- Python modules: lowercase with underscores (`extraction.py`, `persistence.py`, `agenda.py`)
- Entry points: simple names (`main.py`, `run_api.py`)
- No prefixes or suffixes for organization

**Directories:**
- Package folders (with `__init__.py`): lowercase singular or plural as appropriate (`agent`, `api`, `tools`, `memory`)
- Feature folders: descriptive, no prefixes (`agent`, `agent_carla`, `core`)

**Functions:**
- Public: lowercase with underscores (`build_graph()`, `handle_message()`, `save_messages()`)
- Private (module-scoped): leading underscore (`_invoke_llm()`, `_get_db()`, `_entry_router()`)
- LLM invocation: `_invoke_llm(system_prompt, messages, span, rag_context)`

**Variables:**
- State variables: snake_case, descriptive (`nome_paciente`, `motivo_consulta`, `etapa`)
- Constants: UPPERCASE (`SESSION_TTL`, `ESPECIALIDADES`, `CONVENIOS`)
- Abbreviations: `msg`, `cur` (cursor), `conn` (connection), `llm`, `rag`

**Types:**
- State dicts: `TypedDict` classes (`ClinicaState`, `CarlaState`)
- No custom exception classes; use built-in exceptions with logging

**Classes:**
- Managers/Clients: `SessionManager`, `EvolutionClient`, `ClinicRAG`, `ConversationSummarizer`
- Named with descriptive suffix indicating responsibility

## Where to Add New Code

**New Conversation Node (extends Sofia's behavior):**
- File: `src/agent/nodes.py`
- Add function: `def new_node(state: ClinicaState) -> dict:`
- Register in `src/agent/graph.py`: Add to node list and wire edges
- Update `ClinicaState` in `src/agent/state.py` if new fields needed
- Update `determine_etapa()` in `src/core/extraction.py` if new etapa needed

**New Tool/Operation (clinic logic):**
- File: `src/tools/{new_domain}.py` (e.g., `src/tools/billing.py`)
- Function: Decorate with `@tool` if exposing to LLM, or plain function
- Import and call from appropriate node in `src/agent/nodes.py`
- Add database operations to `migrations/` if schema changes

**New External Integration:**
- File: `src/api/{service}.py` (e.g., `src/api/slack.py`)
- Class: Mimic `EvolutionClient` pattern — `async` methods, error handling, logging
- Initialize in `src/api/webhook.py` or `src/api/orchestrator.py`

**Database Schema Change:**
- File: `migrations/{NNN}_description.sql` (increment NNN from last migration)
- Apply via Alembic or manual psycopg2 execution
- Update `src/memory/persistence.py` queries if reading/writing new tables

**Observability/Tracing Enhancement:**
- File: `src/observability/langfuse_setup.py`
- Add configuration variables
- Initialize new Langfuse features (e.g., custom span attributes)

**Tests for New Feature:**
- Location: `tests/test_{domain}.py` (e.g., `tests/test_billing.py`)
- Framework: pytest
- Pattern: Test extraction logic separately from graph nodes

## Special Directories

**agent-service/.venv:**
- Purpose: Python virtual environment
- Generated: Yes (via `python -m venv .venv`)
- Committed: No (git-ignored)
- Do not edit

**agent-service/migrations/:**
- Purpose: Database version control
- Generated: No (manually created SQL files)
- Committed: Yes
- Safe to add new files; never modify existing migrations

**agent-service/docs/**
- Purpose: Documentation and notes
- Generated: No (manual documents)
- Committed: Yes
- Add project documentation, API specs, or design decisions here

**agent-service/.env:**
- Purpose: Local environment variables (secrets, API keys)
- Generated: No (manually created)
- Committed: No (git-ignored for security)
- Template: See `.env.example` if available; required vars: DATABASE_URL, EVOLUTION_API_KEY, OPENROUTER_API_KEY, LLM_MODEL, REDIS_URL

**frontend/**
- Purpose: Deployed static content
- Generated: No
- Committed: Yes
- Single HTML file; no build step

## Database Schema Reference

Key tables used throughout codebase:

- `patients`: phone (PK), nome, total_consultas, ultima_visita
- `conversations`: id (PK), session_id, role, content, patient_id, metadata, created_at
- `conversation_summaries`: session_id (PK), summary, key_topics[], sentiment, resolved, feedback_score, patient_id
- `knowledge_chunks`: id (PK), source_type, source_id, title, content, embedding (vector), created_at
- `doctors`: id (PK), name, specialty, availability_json
- `appointments`: id (PK), patient_id, doctor_id, date, time, status, protocol
- `followups`: id (PK), phone, message, scheduled_for, sent_at

## Import Patterns

**Standard imports:**
```python
import os
import json
import logging
from typing import Dict, List, Optional, TypedDict

# Third-party
from fastapi import FastAPI
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
import psycopg2
import redis.asyncio as aioredis

# Local
from src.agent.state import ClinicaState
from src.tools.agenda import verificar_disponibilidade
```

**Avoid circular imports:**
- Tools do not import nodes
- Nodes do not import other nodes
- Graphs import nodes and state only
- API layer imports orchestrator but not individual nodes

---

*Structure analysis: 2026-03-29*
