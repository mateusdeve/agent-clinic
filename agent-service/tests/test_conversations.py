"""Testes de contrato para os endpoints de conversas WhatsApp.

Todos os testes sao marcados como xfail pois dependem de auth middleware
e banco de dados real. Servem como especificacao executavel dos requisitos WPP.
xfail: quando a implementacao estiver completa, os testes passarao (xpassed).
"""

import pytest


@pytest.mark.xfail(reason="Phase 4 — conversation list endpoint")
def test_conversation_list_returns_data(test_client):
    """WPP-01: GET /api/conversations returns conversation list."""
    response = test_client.get("/api/conversations", headers={"Authorization": "Bearer test"})
    assert response.status_code == 200


@pytest.mark.xfail(reason="Phase 4 — message history endpoint")
def test_message_history_returns_messages(test_client):
    """WPP-02: GET /api/conversations/{phone}/messages returns messages."""
    response = test_client.get(
        "/api/conversations/5511999999999/messages",
        headers={"Authorization": "Bearer test"},
    )
    assert response.status_code == 200


@pytest.mark.xfail(reason="Phase 4 — takeover sets Redis flag")
def test_takeover_sets_redis_flag(test_client, mock_redis):
    """WPP-07: POST /api/conversations/{phone}/takeover sets Redis flag."""
    response = test_client.post(
        "/api/conversations/5511999999999/takeover",
        headers={"Authorization": "Bearer test"},
    )
    assert response.status_code == 200
    mock_redis.set.assert_called_once()


@pytest.mark.xfail(reason="Phase 4 — handback clears Redis flag")
def test_handback_clears_redis_flag(test_client, mock_redis):
    """WPP-09: POST /api/conversations/{phone}/handback clears Redis flag."""
    response = test_client.post(
        "/api/conversations/5511999999999/handback",
        headers={"Authorization": "Bearer test"},
    )
    assert response.status_code == 200
    mock_redis.delete.assert_called_once()


@pytest.mark.xfail(reason="Phase 4 — send message stores and broadcasts")
def test_send_message_stores_and_broadcasts(test_client, mock_redis, mock_sio, mock_evolution):
    """WPP-08: POST /api/conversations/{phone}/send sends via Evolution + stores + broadcasts."""
    response = test_client.post(
        "/api/conversations/5511999999999/send",
        json={"text": "Ola paciente"},
        headers={"Authorization": "Bearer test"},
    )
    assert response.status_code == 200


@pytest.mark.xfail(reason="Phase 4 — webhook takeover bypass")
def test_webhook_takeover_bypass(test_client, mock_redis):
    """WPP-10: Webhook skips Sofia when takeover flag exists."""
    mock_redis.get.return_value = '{"human_id": "test", "human_name": "Admin", "timestamp": 1}'
    payload = {
        "event": "messages.upsert",
        "data": {
            "key": {"remoteJid": "5511999999999@s.whatsapp.net", "fromMe": False},
            "message": {"conversation": "Oi doutor"},
        },
    }
    response = test_client.post("/webhook/evolution", json=payload)
    assert response.json()["status"] == "takeover_mode"
