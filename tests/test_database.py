import pytest
import requests
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = "http://localhost:8000"
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def test_conexao_supabase_local():
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    try:
        resposta = requests.get(f"{SUPABASE_URL}/rest/v1/delegacias?select=*", headers=headers, timeout=5)
        assert resposta.status_code == 200, f"Falha no Supabase. Status retornado: {resposta.status_code}"
    except requests.exceptions.ConnectionError:
        pytest.fail("Sem conexão com o Supabase. O container está rodando na porta 8000?")

def test_busca_cidade_valida_supabase():
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    cidade_limpa = "belo jardim"
    resposta = requests.get(f"{SUPABASE_URL}/rest/v1/delegacias?cidade_busca=eq.{cidade_limpa}&select=endereco", headers=headers)
    assert resposta.status_code == 200, "Erro ao consultar a tabela delegacias."
    dados = resposta.json()
    assert len(dados) > 0, "Nenhum endereço encontrado para a cidade teste."
    assert "Av. Sebastião Rodrigues" in dados[0].get("endereco", ""), "O endereço retornado não corresponde ao esperado na base."

def test_busca_cidade_invalida_supabase():
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    cidade_limpa = "gotham_city_falsa"
    resposta = requests.get(f"{SUPABASE_URL}/rest/v1/delegacias?cidade_busca=eq.{cidade_limpa}&select=endereco", headers=headers)
    assert resposta.status_code == 200
    dados = resposta.json()
    assert len(dados) == 0, "O banco deveria retornar uma lista vazia para cidades inexistentes."