import pytest
import requests
import os
from dotenv import load_dotenv

load_dotenv()

TYPEBOT_PUBLIC_ID = os.getenv("TYPEBOT_PUBLIC_ID")
TYPEBOT_API_URL = f"https://typebot.io/api/v1/typebots/{TYPEBOT_PUBLIC_ID}/startChat"

def test_typebot_menu_case_insensitive():
    payload_menu = {"message": "mEnU", "sessionId": "teste-case-1"}
    payload_voltar = {"message": "vOLtaR", "sessionId": "teste-case-2"}
    
    res_menu = requests.post(TYPEBOT_API_URL, json=payload_menu, timeout=10)
    assert res_menu.status_code == 200
    assert "Digite o número da opção desejada" in str(res_menu.json())

    res_voltar = requests.post(TYPEBOT_API_URL, json=payload_voltar, timeout=10)
    assert res_voltar.status_code == 200
    assert "Digite o número da opção desejada" in str(res_voltar.json())

def test_typebot_opcao_numerica_invalida():
    payload = {"message": "9", "sessionId": "teste-opcao-invalida"}
    resposta = requests.post(TYPEBOT_API_URL, json=payload, timeout=10)
    assert resposta.status_code == 200
    
    textos = str(resposta.json())
    assert "1 - Registrar B.O. Online" not in textos
    assert len(textos) > 20

def test_typebot_texto_no_lugar_de_numero():
    payload = {"message": "Roubaram minha moto agora de manhã", "sessionId": "teste-texto"}
    resposta = requests.post(TYPEBOT_API_URL, json=payload, timeout=15)
    assert resposta.status_code == 200
    
    textos = str(resposta.json()).lower()
    assert "delegacia" in textos or "presencial" in textos