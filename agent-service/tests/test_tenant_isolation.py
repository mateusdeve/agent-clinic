"""Tenant isolation tests — stubs filled by Plan 01/02 executors."""
import pytest


@pytest.mark.tenant
@pytest.mark.xfail(reason="Plan 01 not yet executed")
def test_rls_policies_exist(db_conn):
    """RLS policies are enabled on all data tables (TENANT-01)."""
    cursor = db_conn.cursor()
    tables = ["patients", "appointments", "doctors", "conversations",
              "conversation_summaries", "knowledge_chunks", "follow_ups", "users"]
    for table in tables:
        cursor.execute(
            "SELECT relrowsecurity FROM pg_class WHERE relname = %s",
            (table,)
        )
        row = cursor.fetchone()
        assert row is not None, f"Table {table} not found"
        assert row[0] is True, f"RLS not enabled on {table}"


@pytest.mark.tenant
@pytest.mark.xfail(reason="Plan 01 not yet executed")
def test_tenant_isolation_across_clinics(db_conn, default_tenant_id):
    """A query with app.tenant_id = clinic_A never returns rows from clinic_B (TENANT-02)."""
    cursor = db_conn.cursor()
    # Set tenant context to a non-existent tenant
    cursor.execute("SET LOCAL app.tenant_id = '00000000-0000-0000-0000-000000000099'")
    cursor.execute("SELECT count(*) FROM patients")
    count = cursor.fetchone()[0]
    assert count == 0, "RLS should filter out rows for non-matching tenant"


@pytest.mark.tenant
@pytest.mark.xfail(reason="Plan 02 not yet executed")
def test_get_db_for_tenant_sets_session_var(test_client):
    """get_db_for_tenant executes SET LOCAL app.tenant_id (TENANT-02, TENANT-03)."""
    pass
