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
