"""Testes para os endpoints do dashboard (DASH-01 a DASH-06).

Stubs marcados com xfail — passam a xpassed quando implementacao estiver completa
e testes integrados com banco de teste.
"""

import pytest


@pytest.mark.xfail(reason="Requer banco de teste com fixtures de consultas", strict=False)
def test_stats_kpis():
    """GET /api/dashboard/stats retorna 200 com consultas_hoje."""
    # TODO: usar TestClient com banco de teste configurado
    # response = client.get("/api/dashboard/stats", headers=auth_headers)
    # assert response.status_code == 200
    # data = response.json()
    # assert "consultas_hoje" in data
    raise NotImplementedError("Requer TestClient integrado")


@pytest.mark.xfail(reason="Requer banco de teste com fixtures de consultas", strict=False)
def test_proximas_consultas():
    """Response de stats inclui proximas_consultas como lista."""
    # data = response.json()
    # assert isinstance(data["proximas_consultas"], list)
    raise NotImplementedError("Requer TestClient integrado")


@pytest.mark.xfail(reason="Requer Redis de teste para contagem de sessoes ativas", strict=False)
def test_conversas_ativas():
    """Response de stats inclui conversas_ativas como inteiro."""
    # data = response.json()
    # assert isinstance(data["conversas_ativas"], int)
    raise NotImplementedError("Requer TestClient integrado com Redis")


@pytest.mark.xfail(reason="Requer banco de teste com fixtures de consultas", strict=False)
def test_charts_data():
    """GET /api/dashboard/charts retorna 200 com trend e especialidades."""
    # response = client.get("/api/dashboard/charts", headers=admin_headers)
    # assert response.status_code == 200
    # data = response.json()
    # assert "trend" in data
    # assert "especialidades" in data
    # assert len(data["trend"]) == 7
    raise NotImplementedError("Requer TestClient integrado")


@pytest.mark.xfail(reason="Requer banco de teste com usuario recepcionista", strict=False)
def test_charts_admin_only():
    """GET /api/dashboard/charts com token de recepcionista retorna 403."""
    # response = client.get("/api/dashboard/charts", headers=recepcionista_headers)
    # assert response.status_code == 403
    raise NotImplementedError("Requer TestClient integrado com usuario recepcionista")
