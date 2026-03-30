"""Testes para os endpoints de campanhas de mensagens em massa (D-11 a D-16, WPP-13 a WPP-16).

Stubs marcados com xfail — passam a xpassed quando implementacao estiver completa
e testes integrados com banco de teste.
"""

import pytest


@pytest.mark.xfail(reason="Requer banco de teste com pacientes e template", strict=False)
def test_create_campaign():
    """POST /api/campaigns cria campanha e popula recipients."""
    # response = client.post("/api/campaigns", json={
    #     "nome": "Retorno Cardiologia",
    #     "template_id": template_id,
    #     "filtros": {"especialidade": "Cardiologia"}
    # }, headers=admin_headers)
    # assert response.status_code == 201
    # data = response.json()
    # assert "id" in data
    # assert data["status"] == "enviando"
    raise NotImplementedError("Requer TestClient integrado")


@pytest.mark.xfail(reason="Requer banco de teste com template e Evolution API mockada", strict=False)
def test_quick_send():
    """POST /api/conversations/{phone}/send-template envia template renderizado."""
    # response = client.post(f"/api/conversations/5511999999999/send-template", json={
    #     "template_id": template_id,
    #     "variaveis": {"nome": "Maria", "data": "01/04/2026", "hora": "14:00"}
    # }, headers=admin_headers)
    # assert response.status_code == 200
    # assert response.json() == {"status": "sent"}
    raise NotImplementedError("Requer TestClient com Evolution API mockada")


@pytest.mark.xfail(reason="Requer banco de teste com campanha ativa e mock de Evolution API", strict=False)
def test_dispatch_rate_limit():
    """Dispatch job respeita throttle de 20 msg/seg (asyncio.sleep 0.05 entre envios)."""
    # Verifica que BATCH de 20 recipients leva ao menos 1 segundo
    # (20 * 0.05s = 1.0s com 0.05s entre cada)
    # Medido pelo mock de evolution_client.send_message_with_typing
    raise NotImplementedError("Requer mock de evolution_client e medicao de tempo")


@pytest.mark.xfail(reason="Requer banco de teste com campanha e recipients", strict=False)
def test_campaign_status():
    """GET /api/campaigns/{id} retorna status com stats de entrega."""
    # response = client.get(f"/api/campaigns/{campaign_id}", headers=admin_headers)
    # assert response.status_code == 200
    # data = response.json()
    # assert "stats" in data
    # assert "enviado" in data["stats"]
    raise NotImplementedError("Requer TestClient integrado")


@pytest.mark.xfail(reason="Requer banco de teste com pacientes populados", strict=False)
def test_preview_segment():
    """GET /api/campaigns/preview-segment retorna count e sample de pacientes."""
    # response = client.get("/api/campaigns/preview-segment", headers=admin_headers)
    # assert response.status_code == 200
    # data = response.json()
    # assert "count" in data
    # assert "sample" in data
    # assert len(data["sample"]) <= 5
    raise NotImplementedError("Requer TestClient integrado")
