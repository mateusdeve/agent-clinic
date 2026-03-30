"""RBAC tests — stubs filled by Plan 02 executor."""
import pytest


@pytest.mark.rbac
@pytest.mark.xfail(reason="Plan 02 not yet executed")
def test_require_role_admin_allows_admin(test_client):
    """Admin token passes require_role('admin') check (AUTH-06)."""
    # Login as admin, access admin-only endpoint
    pass


@pytest.mark.rbac
@pytest.mark.xfail(reason="Plan 02 not yet executed")
def test_require_role_admin_rejects_medico(test_client):
    """Medico token is rejected by require_role('admin') with 403 (AUTH-06)."""
    # Login as medico, try to access admin-only endpoint
    pass


@pytest.mark.rbac
@pytest.mark.xfail(reason="Plan 02 not yet executed")
def test_get_current_tenant_extracts_from_jwt(test_client):
    """get_current_tenant returns tenant_id from JWT, not from request params (TENANT-03)."""
    pass
