# Testing Patterns

**Analysis Date:** 2026-03-29

## Test Framework

**Runner:**
- pytest 8.4.2 (in `requirements.txt`)
- No `pytest.ini` or `pyproject.toml` configuration detected
- Default pytest configuration assumed

**Run Commands:**
```bash
pytest                      # Run all tests
pytest -v                   # Verbose output
pytest tests/               # Run specific test directory
pytest tests/test_connections.py  # Run single test file
```

**Test Discovery:**
- pytest will find files matching `test_*.py` pattern
- Default test location: `tests/` directory at project root

## Test File Organization

**Location:**
- Test files live in `/Users/mateuspires/Dev/agent-clinic/agent-service/tests/` directory
- Currently only one test file: `test_connections.py`
- Pattern: Tests co-located in `tests/` directory (separate from source)

**Naming:**
- `test_*.py` prefix for test files (pytest convention)
- Example: `test_connections.py`
- Test functions: `test_*` prefix (detected in `test_langfuse()`, `test_llm()`)

**Structure:**
```
agent-service/
├── src/
│   ├── agent/
│   ├── api/
│   ├── core/
│   ├── memory/
│   ├── observability/
│   └── tools/
├── tests/
│   └── test_connections.py    # Integration tests
├── run_api.py
├── main.py
└── requirements.txt
```

## Test Structure

**Existing Test Pattern from `test_connections.py`:**

```python
# tests/test_connections.py
import os
from dotenv import load_dotenv

load_dotenv()

def test_langfuse():
    """Integration test for Langfuse client connection."""
    from langfuse import Langfuse

    langfuse = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST"),
    )

    trace = langfuse.trace(
        name="teste-inicial",
        user_id="dev-local",
        metadata={"env": "local", "source": "agent-clinic"},
        tags=["agent-clinic", "teste-inicial"],
    )

    span = trace.span(name="primeiro-span", input="oi")
    span.end(output="funcionou!")

    langfuse.flush()
    print("✅ Langfuse OK!")


def test_llm():
    """Integration test for LLM (OpenAI/OpenRouter) connection."""
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model=os.getenv("LLM_MODEL"),
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
    )

    response = llm.invoke("Responda apenas: conexão ok!")
    print(f"✅ LLM OK: {response.content}")


if __name__ == "__main__":
    test_langfuse()
    test_llm()
```

**Patterns Observed:**

1. **Environment Setup:**
   - Load dotenv at test file start: `load_dotenv()`
   - Access environment variables directly: `os.getenv("LANGFUSE_PUBLIC_KEY")`
   - No fixtures for environment setup

2. **Test Execution:**
   - Direct imports within test functions (lazy loading)
   - Assertions via print statements and manual verification
   - No pytest assert statements detected

3. **External Dependencies:**
   - Tests verify external service connections (Langfuse, LLM)
   - Tests are integration tests, not unit tests
   - No mocking of external services

## Test Types

**Unit Tests:**
- Not yet present in codebase
- Candidates for unit testing:
  - `src/core/extraction.py` - Data extraction logic
  - `src/tools/doctors.py` - Doctor availability calculations
  - `src/memory/rag.py` - Vector search
  - `src/memory/summarizer.py` - Conversation summarization

**Integration Tests:**
- `test_connections.py` - Verifies connections to external services:
  - Langfuse tracing service
  - OpenRouter LLM API
- Pattern: Direct instantiation of clients and simple invocation
- Suitable for testing:
  - Database connections (`_get_db()`)
  - API client initialization
  - External service integration

**End-to-End Tests:**
- Not present
- Would test full conversation flow through graph execution
- Candidates:
  - LangGraph execution with mock messages
  - WhatsApp webhook to response flow
  - Complete appointment scheduling flow

## Mocking

**Framework:** None currently detected

**Recommendations for Adding Mocking:**
- Use `unittest.mock` (Python stdlib) for mocking
- Mock external dependencies:
  - Database connections (mock `psycopg2.connect()`)
  - LLM responses (mock `ChatOpenAI.invoke()`)
  - Redis connections (mock `aioredis.from_url()`)
  - External APIs (mock `EvolutionClient.send_message()`)

**What to Mock:**
- External service calls (LLM, database, Redis, Evolution API)
- Time-dependent operations (use freezegun or mock datetime)
- File I/O and environment variables

**What NOT to Mock:**
- Core business logic in extraction and state machines
- LangChain message types (use real HumanMessage, AIMessage)
- State transitions and graph execution

## Fixtures and Factories

**Test Data:**
- Not yet implemented
- Recommended fixtures for addition:
  - Mock state objects matching `ClinicaState`
  - Mock messages lists
  - Mock appointment data
  - Mock doctor availability responses

**Location for Fixtures:**
- Create `tests/conftest.py` for pytest fixtures
- Define reusable fixtures for state, messages, database mocks

**Example Structure for Future Implementation:**
```python
# tests/conftest.py
import pytest
from langchain_core.messages import HumanMessage, AIMessage

@pytest.fixture
def sample_state():
    """Sample conversation state."""
    return {
        "messages": [],
        "nome_paciente": "João Silva",
        "motivo_consulta": "agendamento",
        "especialidade": "Clínica Geral",
        "data_agendamento": "2026-04-05",
        "horario_agendamento": "10:00",
        "etapa": "confirmar_agendamento",
        "session_id": "test-session-123",
        # ... other fields
    }

@pytest.fixture
def sample_messages():
    """Sample conversation messages."""
    return [
        HumanMessage(content="Oi, gostaria de agendar"),
        AIMessage(content="Claro! Qual especialidade?"),
    ]
```

## Coverage

**Requirements:** Not enforced
- No coverage configuration detected
- No coverage tool specified in requirements

**View Coverage (if added):**
```bash
pip install pytest-cov
pytest --cov=src --cov-report=html
```

## Current Testing Status

**What IS Tested:**
- External service connectivity (Langfuse, LLM API)
- Service initialization and basic invocation

**What IS NOT Tested:**
- Core agent logic (state machine, nodes)
- Data extraction functions
- Tool functions (doctors, appointments, patients)
- Memory operations (persistence, RAG, summarization)
- API endpoints (webhook, evolution integration)
- Database operations
- Session management (Redis)

**Test Gaps:**
- No unit tests for extraction logic in `src/core/extraction.py`
- No tests for doctor availability calculation in `src/tools/doctors.py`
- No tests for graph state transitions in `src/agent/graph.py`
- No tests for session state management in `src/api/session.py`
- No tests for message orchestration in `src/api/orchestrator.py`
- No tests for conversation summarization in `src/memory/summarizer.py`

## Recommended Testing Strategy

**Phase 1 - Add Unit Tests:**
```python
# tests/test_extraction.py
def test_extract_data_patient_name():
    messages = [HumanMessage(content="Meu nome é João")]
    extracted = extract_data(messages)
    assert extracted.get("nome_paciente") == "João"

# tests/test_doctors.py
def test_normalize_date():
    data_str, dt = _normalizar_data("amanhã")
    assert data_str is not None
    assert isinstance(dt, datetime)
```

**Phase 2 - Add Integration Tests:**
```python
# tests/test_database.py
@pytest.mark.asyncio
async def test_save_and_load_session():
    session_manager = SessionManager(REDIS_URL)
    await session_manager.save_state("test-phone", test_state)
    loaded = await session_manager.load_state("test-phone")
    assert loaded["nome_paciente"] == test_state["nome_paciente"]
```

**Phase 3 - Add Mocking for External Services:**
```python
# tests/test_orchestrator.py
from unittest.mock import patch, MagicMock

@patch('src.api.evolution.EvolutionClient.send_message')
def test_handle_message_sends_response(mock_send, test_message):
    handle_message(test_message)
    mock_send.assert_called_once()
```

## Async Testing

**Async Pattern Expected:**
- Session operations are async: `async def load_state()`, `async def save_state()`
- API endpoints are async: FastAPI with `@app.post("/webhook/evolution")`
- Redis client is async: `aioredis`

**For Testing Async Code:**
```bash
pip install pytest-asyncio
```

**Example Async Test:**
```python
import pytest

@pytest.mark.asyncio
async def test_load_state_creates_default():
    session_manager = SessionManager(redis_url)
    state = await session_manager.load_state("new-phone")
    assert state["etapa"] == "recepcionar"
```

---

*Testing analysis: 2026-03-29*
