# Coding Conventions

**Analysis Date:** 2026-03-29

## Naming Patterns

**Files:**
- `snake_case.py` - All Python modules
- Module purpose clear in name: `agenda.py`, `persistence.py`, `extraction.py`, `summarizer.py`
- Internal/private modules with underscore prefix: `_get_db()` contextmanager, `_get_llm()` function
- Test files: `test_connections.py` (pytest naming convention)

**Functions:**
- `snake_case` for all functions
- Public functions: `verificar_disponibilidade()`, `salvar_paciente()`, `load_session_history()`
- Private/internal functions prefixed with underscore: `_get_db()`, `_invoke_llm()`, `_gerar_slots()`, `_normalizar_data()`
- Tool functions exported for LangChain use: `@tool` decorator marks public tools in `src/tools/`
- Helper utilities in modules: `_get_periodo()`, `_get_genero()`, `_get_dados_coletados()` in `src/agent/nodes.py`

**Variables:**
- `snake_case` for all variables and parameters
- State dictionaries: `state`, `data`, `extracted`, `result`
- Environment variables: UPPERCASE with underscores: `DATABASE_URL`, `REDIS_URL`, `LLM_MODEL`, `OPENROUTER_API_KEY`
- Constants as UPPERCASE: `ESPECIALIDADES`, `CONVENIOS`, `SESSION_TTL = 86400`, `HORARIOS_MOCK`
- Portuguese variable names used in domain logic: `nome_paciente`, `motivo_consulta`, `data_agendamento`, `horario_agendamento`, `etapa`, `convenio`, `protocolo_consulta`

**Types:**
- TypedDict for state objects: `class ClinicaState(TypedDict)` in `src/agent/state.py`
- Type hints in function signatures: `def buscar_paciente(phone: str) -> Optional[dict]:`
- Import types from `typing`: `Optional`, `List`, `Dict`, `Any`
- BaseMessage types from LangChain: `HumanMessage`, `AIMessage`, `SystemMessage`

**Classes:**
- `PascalCase` for class names: `ClinicRAG`, `SessionManager`, `EvolutionClient`, `ConversationSummarizer`
- Classes are minimal — mostly stateful helpers or managers
- Methods follow function naming convention: `snake_case`
- Private methods: `_embed()` in `ClinicRAG`

## Code Style

**Formatting:**
- No formatter enforced (no `.prettierrc`, `black` config, or `pyproject.toml` detected)
- Indentation: 4 spaces (standard Python)
- Line length: appears to be 100-120 characters typical
- Import style: direct imports, not star imports

**Linting:**
- No linting configuration detected (no `.pylintrc`, `.flake8`, or similar)
- Pattern: Follow PEP 8 informally based on code samples
- Imports verified: `# noqa: F401` used to suppress unused import warnings in `src/tools/appointments.py` line 10

**Comments:**
- Module docstrings present: `"""Operações de pacientes — reconhecimento e persistência por número."""` in `src/tools/patients.py`
- Triple quotes for block documentation in prompts and docstrings
- Inline comments minimal — code is self-documenting
- Prompt constants heavily commented with section markers: `# ────────────────────────────────────────────────────────────`

## Import Organization

**Order:**
1. Standard library imports: `os`, `json`, `logging`, `uuid`, `time`, `datetime`, etc.
2. Third-party framework imports: `fastapi`, `langchain`, `redis`, `psycopg2`, etc.
3. Application imports: `from src.agent...`, `from src.tools...`, `from src.memory...`

**Example from `src/agent/nodes.py`:**
```python
import os
import json
import logging
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from src.agent.state import ClinicaState
from src.agent.prompts import (
    PROMPT_RECEPCIONAR,
    # ...
)
from src.tools.agenda import (
    verificar_disponibilidade,
    # ...
)
```

**Path Aliases:**
- No aliases detected — all imports use absolute paths from project root: `from src.tools.patients import...`
- Relative imports not used; absolute imports from `src/` prefix

## Error Handling

**Patterns:**
- Broad `except Exception as e:` catch-all in production code
- Errors logged with module context: `logger.error(f"[persistence] save_messages error: {e}")`
- Module prefix in log messages: `[persistence]`, `[doctors]`, `[appointments]`, `[patients]`
- Functions return safe defaults on error (None, empty dict, empty list):
  - `buscar_paciente()` returns `None` on exception
  - `retrieve()` in RAG returns `""` on exception
  - `load_session_history()` returns `[]` on exception
- No explicit exception raising except for configuration errors: `raise RuntimeError("DATABASE_URL não configurado")`

**Error Recovery:**
- Silent failures with logging: Most functions catch and log errors, then return None/empty
- Connection context managers in `_get_db()` ensure cleanup via try/finally
- Session manager handles corrupted Redis data by creating new session: `except (json.JSONDecodeError, KeyError) as e:` followed by fallback

## Logging

**Framework:** Python `logging` standard library

**Setup:**
```python
logger = logging.getLogger("agent-clinic.module_name")
```

**Patterns:**
- Module-scoped loggers: each file creates its own logger with module name
- Log levels used: `info`, `warning`, `error`
- Log format set in `src/api/webhook.py`: `"%(asctime)s [%(name)s] %(levelname)s: %(message)s"`
- All logs include module context in message: `logger.info(f"[patients] Paciente salvo: {phone} — {nome}")`

**When to Log:**
- Info: Key operations completed successfully: "Grafo Sofia inicializado", "Paciente salvo"
- Warning: Expected but unusual conditions: "Sessão corrompida", "data inválida"
- Error: Exceptions and failures: "erro ao buscar horários", "save_messages error"

**Examples:**
```python
logger.info(f"[patients] Paciente salvo: {phone} — {nome}")
logger.error(f"[persistence] save_messages error: {e}")
logger.warning(f"[doctors] data inválida: '{data}'")
```

## Function Design

**Size:** Small, focused functions (10-30 lines typical)
- Tool functions: ~15-25 lines
- Helper functions: ~5-10 lines
- Complex orchestration functions: up to 50 lines with clear sections

**Parameters:**
- Type hints on all parameters: `def buscar_paciente(phone: str) -> Optional[dict]:`
- Optional parameters have defaults: `def criar_followup(..., feedback_score=None):`
- No position-only or keyword-only arguments observed
- Maximum 4-5 parameters typical; longer signatures in orchestrator functions

**Return Values:**
- Explicit return types in annotations
- Return None/empty collections on error (not exceptions)
- Dictionaries for structured returns: `{"disponivel": True, "medicos": [...], "mensagem": "..."}`
- Tuples only in specific cases: `_normalizar_data()` returns `(data_str, datetime_obj)`

**Docstrings:**
- Tool functions use docstring format compatible with LangChain tools:
```python
@tool
def verificar_disponibilidade(especialidade: str, data: str) -> dict:
    """Verifica horários disponíveis para uma especialidade em uma data específica.

    Args:
        especialidade: A especialidade médica desejada.
        data: A data desejada para a consulta.
    """
```
- Non-tool functions have minimal docstrings or none
- Docstrings explain purpose and key parameters/returns

## Module Design

**Exports:**
- Modules export public functions and constants
- Public items: no leading underscore
- Private/internal items: underscore prefix `_get_db()`, `_get_llm()`

**Module Organization by Responsibility:**

**`src/tools/`** - Database operations and tool definitions:
- `patients.py`: Patient lookup and creation
- `appointments.py`: Appointment CRUD operations
- `doctors.py`: Doctor availability and selection
- `agenda.py`: High-level appointment workflow tools
- `followup.py`: Follow-up reminders
- `faq.py`: FAQ lookups

**`src/agent/`** - Core LangGraph state machine:
- `state.py`: TypedDict definition for conversation state
- `prompts.py`: System prompts for each conversation stage
- `nodes.py`: Node functions (recepcionar, coletar_dados, etc.)
- `graph.py`: LangGraph construction and session management

**`src/memory/`** - Conversation persistence and retrieval:
- `persistence.py`: Database save/load for messages and summaries
- `rag.py`: Vector search for conversation context
- `summarizer.py`: LLM-based conversation summarization

**`src/api/`** - FastAPI endpoints and external integrations:
- `webhook.py`: FastAPI app and Evolution API webhook endpoint
- `orchestrator.py`: Message buffering and graph orchestration
- `session.py`: Redis session management
- `evolution.py`: WhatsApp Evolution API client

**`src/core/`** - Shared extraction logic:
- `extraction.py`: LLM-based data extraction from conversations

**`src/observability/`** - Monitoring and tracing:
- `langfuse_setup.py`: Langfuse integration for trace logging

## Language and Text

**Portuguese Domain Terms:**
- All state field names in Portuguese: `nome_paciente`, `motivo_consulta`, `especialidade`, `convenio`, `data_agendamento`
- All prompt text in Portuguese (natural language for patient interaction)
- Comments and docstrings in Portuguese
- Variable names in Portuguese for domain concepts, English for infrastructure: `session_id`, `phone`, `query`, but `nome`, `especialidade`, `etapa`

## Database Conventions

**Query Style:**
- Parameterized queries with `%s` placeholders for PostgreSQL
- Multi-line SQL strings in triple quotes
- Contextmanager `_get_db()` used consistently for connection lifecycle
- Connection closed in finally block via context manager

**Transaction Pattern:**
```python
with _get_db() as conn:
    with conn.cursor() as cur:
        cur.execute(sql, params)
    conn.commit()
```

---

*Convention analysis: 2026-03-29*
