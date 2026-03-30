"""Testes para os endpoints de templates de mensagem (WPP-12, D-08 a D-10).

Stubs marcados com xfail — passam a xpassed quando implementacao estiver completa
e testes integrados com banco de teste.
"""

import pytest


@pytest.mark.xfail(reason="Requer banco de teste com tenant configurado", strict=False)
def test_create_template():
    """POST /api/templates cria template e retorna id com variaveis extraidas."""
    # response = client.post("/api/templates", json={
    #     "nome": "Lembrete de consulta",
    #     "corpo": "Ola {{nome}}, sua consulta com {{medico}} esta marcada para {{data}} as {{hora}}."
    # }, headers=admin_headers)
    # assert response.status_code == 201
    # data = response.json()
    # assert "id" in data
    # assert set(data["variaveis_usadas"]) == {"nome", "medico", "data", "hora"}
    raise NotImplementedError("Requer TestClient integrado")


@pytest.mark.xfail(reason="Requer banco de teste com tenant configurado", strict=False)
def test_list_templates():
    """GET /api/templates retorna lista paginada de templates."""
    # response = client.get("/api/templates", headers=admin_headers)
    # assert response.status_code == 200
    # data = response.json()
    # assert "items" in data
    # assert "total" in data
    # assert "page" in data
    raise NotImplementedError("Requer TestClient integrado")


@pytest.mark.xfail(reason="Requer banco de teste com tenant configurado", strict=False)
def test_update_template():
    """PUT /api/templates/{id} atualiza corpo e re-extrai variaveis."""
    # response = client.put(f"/api/templates/{template_id}", json={
    #     "corpo": "Ola {{nome}}, confirme sua consulta."
    # }, headers=admin_headers)
    # assert response.status_code == 200
    # data = response.json()
    # assert data["variaveis_usadas"] == ["nome"]
    raise NotImplementedError("Requer TestClient integrado")


@pytest.mark.xfail(reason="Requer banco de teste com tenant configurado", strict=False)
def test_delete_template():
    """DELETE /api/templates/{id} remove template e retorna status deleted."""
    # response = client.delete(f"/api/templates/{template_id}", headers=admin_headers)
    # assert response.status_code == 200
    # assert response.json() == {"status": "deleted"}
    raise NotImplementedError("Requer TestClient integrado")
