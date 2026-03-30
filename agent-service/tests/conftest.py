import os
import pytest
from contextlib import contextmanager

import psycopg2
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture(scope="session")
def db_url():
    """Database URL for test connections."""
    url = os.getenv("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set — skipping DB tests")
    return url


@pytest.fixture
def db_conn(db_url):
    """Raw psycopg2 connection for test queries. Rolls back after each test."""
    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    yield conn
    conn.rollback()
    conn.close()


@pytest.fixture
def default_tenant_id():
    """UUID of the default 'Clinica Padrao' tenant created by migration 001."""
    return "00000000-0000-0000-0000-000000000001"


@pytest.fixture
def fastapi_app():
    """FastAPI test app — available after Plan 02 mounts auth router."""
    try:
        from src.api.webhook import app
        return app
    except Exception:
        pytest.skip("FastAPI app not yet importable")


@pytest.fixture
def test_client(fastapi_app):
    """FastAPI TestClient — available after Plan 02."""
    from fastapi.testclient import TestClient
    return TestClient(fastapi_app)


@pytest.fixture
def mock_redis(monkeypatch):
    """Mock redis.asyncio client — simulates takeover flag operations.

    Monkeypatches src.api.socketio_server.redis_client.
    """
    from unittest.mock import AsyncMock

    mock = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=None)
    mock.delete = AsyncMock(return_value=None)

    try:
        import src.api.socketio_server as sio_module
        monkeypatch.setattr(sio_module, "redis_client", mock)
    except Exception:
        pass

    return mock


@pytest.fixture
def mock_sio(monkeypatch):
    """Mock socketio.AsyncServer — simulates emit and save_session calls.

    Monkeypatches src.api.socketio_server.sio.
    """
    from unittest.mock import AsyncMock, MagicMock

    mock = AsyncMock()
    mock.emit = AsyncMock(return_value=None)
    mock.save_session = AsyncMock(return_value=None)
    mock.enter_room = AsyncMock(return_value=None)
    mock.leave_room = AsyncMock(return_value=None)

    try:
        import src.api.socketio_server as sio_module
        monkeypatch.setattr(sio_module, "sio", mock)
    except Exception:
        pass

    return mock


@pytest.fixture
def mock_evolution(monkeypatch):
    """Mock EvolutionClient — simulates WhatsApp message sending.

    Monkeypatches src.api.webhook.evolution_client.
    """
    from unittest.mock import AsyncMock

    mock = AsyncMock()
    mock.send_message_with_typing = AsyncMock(return_value=None)
    mock.send_messages = AsyncMock(return_value=None)

    try:
        import src.api.webhook as webhook_module
        monkeypatch.setattr(webhook_module, "evolution_client", mock)
    except Exception:
        pass

    return mock
