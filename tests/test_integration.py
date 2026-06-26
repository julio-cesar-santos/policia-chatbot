import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app import app, sessoes

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_sessions():
    sessoes.clear()
    yield

@patch('bot_logic.requests.get')
def test_database_fallback_integration(mock_get):
    from bot_logic import DelegaciaRepository
    repo = DelegaciaRepository()
    
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.side_effect = [
        [],
        [{"descricao": "DELEGACIA DE TESTE", "endereco": "CENTRO, PAULISTA"}] 
    ]
    
    resultados = repo.buscar_por_localidade("Janga, Paulista")
    
    assert mock_get.call_count == 2
    assert len(resultados) == 1
    assert resultados[0]["descricao"] == "DELEGACIA DE TESTE"

@patch('app.WahaOutboundAdapter.enviar')
def test_webhook_full_happy_path(mock_waha_enviar, authorized_number):
    chat_id = authorized_number 
    
    payload_base = {
        "event": "message",
        "payload": {
            "from": chat_id,
            "type": "text"
        }
    }
    
    payload_base["payload"]["body"] = "Oi"
    response = client.post("/webhook", json=payload_base)
    assert response.status_code == 200
    assert sessoes[chat_id]['estado'] == 'menu'
    
    payload_base["payload"]["body"] = "2"
    client.post("/webhook", json=payload_base)
    assert sessoes[chat_id]['estado'] == 'busca_delegacias'