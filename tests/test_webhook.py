import pytest
import requests
import concurrent.futures
import os
from dotenv import load_dotenv

load_dotenv()

FLASK_WEBHOOK_URL = "http://localhost:5000/webhook"
NUMERO_AUTORIZADO = os.getenv("NUMERO_AUTORIZADO")

def test_webhook_flask():
    payload_simulado = {"event": "message", "payload": {"from": NUMERO_AUTORIZADO, "body": "Teste loopback"}}
    try:
        resposta = requests.post(FLASK_WEBHOOK_URL, json=payload_simulado, timeout=5)
        assert resposta.status_code == 200
        assert resposta.json().get("status") == "ok"
    except requests.exceptions.ConnectionError:
        pytest.fail("Sem conexão com o Flask. Porta 5000?")

def test_webhook_bloqueia_numero_nao_autorizado():
    payload_invasor = {"event": "message", "payload": {"from": "5511999999999@c.us", "body": "Teste"}}
    resposta = requests.post(FLASK_WEBHOOK_URL, json=payload_invasor, timeout=5)
    assert resposta.status_code == 200
    assert resposta.json().get("status") == "ignorado"

def test_webhook_resiliencia_payload_invalido():
    payload_malformado = {"event": "message.ack", "payload": {"id": "12345", "status": "READ"}}
    resposta = requests.post(FLASK_WEBHOOK_URL, json=payload_malformado, timeout=5)
    assert resposta.status_code == 200
    assert resposta.json().get("status") == "ok"

def test_carga_simultanea_flask():
    def simular_mensagem(id_requisicao):
        payload = {"event": "message", "payload": {"from": f"119999000{id_requisicao}@c.us", "body": "Teste"}}
        return requests.post(FLASK_WEBHOOK_URL, json=payload, timeout=5)

    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        resultados = list(executor.map(simular_mensagem, range(15)))
    
    for res in resultados:
        assert res.status_code == 200

def test_webhook_metodo_get_nao_permitido():
    resposta = requests.get(FLASK_WEBHOOK_URL, timeout=5)
    assert resposta.status_code == 405

def test_webhook_mensagem_vazia_ou_espacos():
    payload_vazio = {"event": "message", "payload": {"from": NUMERO_AUTORIZADO, "body": "     "}}
    resposta = requests.post(FLASK_WEBHOOK_URL, json=payload_vazio, timeout=5)
    assert resposta.status_code == 200

def test_webhook_midia_sem_texto():
    payload_midia = {"event": "message", "payload": {"from": NUMERO_AUTORIZADO, "type": "audio", "body": ""}}
    resposta = requests.post(FLASK_WEBHOOK_URL, json=payload_midia, timeout=5)
    assert resposta.status_code == 200

def test_carga_extrema_texto_longo():
    payload_longo = {"event": "message", "payload": {"from": NUMERO_AUTORIZADO, "body": "texto " * 1000}}
    resposta = requests.post(FLASK_WEBHOOK_URL, json=payload_longo, timeout=15)
    assert resposta.status_code == 200