import pytest
import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

WAHA_BASE_URL = "http://localhost:3000"
WAHA_API_KEY = os.getenv("WAHA_API_KEY")
TYPEBOT_PUBLIC_ID = os.getenv("TYPEBOT_PUBLIC_ID")
TYPEBOT_API_URL = f"https://typebot.io/api/v1/typebots/{TYPEBOT_PUBLIC_ID}/startChat"

def test_conexao_typebot():
    payload = {"message": "Teste interno Pytest", "sessionId": "diagnostico-pytest"}
    try:
        resposta = requests.post(TYPEBOT_API_URL, json=payload, timeout=10)
        assert resposta.status_code in [200, 201]
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Falha de conexão com a API do Typebot: {e}")

def test_conexao_waha():
    headers = {"X-Api-Key": WAHA_API_KEY}
    try:
        resposta = requests.get(f"{WAHA_BASE_URL}/api/sessions", headers=headers, timeout=5)
        assert resposta.status_code == 200
    except requests.exceptions.ConnectionError:
        pytest.fail("Sem conexão com o WAHA. Porta 3000?")

def test_tempo_de_resposta_typebot():
    payload = {"message": "Oi", "sessionId": "teste-latencia"}
    inicio = time.time()
    resposta = requests.post(TYPEBOT_API_URL, json=payload, timeout=10)
    fim = time.time()
    
    assert resposta.status_code in [200, 201]
    assert (fim - inicio) < 3.0, "Typebot demorou mais de 3 segundos."