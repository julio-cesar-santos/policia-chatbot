import pytest
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Puxa a URL e a Chave do seu ficheiro .env (com fallback para o localhost caso a URL não esteja no .env)
SUPABASE_URL = os.getenv("SUPABASE_URL", "http://localhost:8000")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Headers obrigatórios para bater na API REST do Supabase
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def test_conexao_supabase_tabela_existe():
    """
    Testa se o Supabase está acessível e se a tabela 'delegacias' existe e responde.
    """
    # Adicionamos limit=1 para a requisição ficar super leve
    url = f"{SUPABASE_URL}/rest/v1/delegacias?select=*&limit=1"
    resposta = requests.get(url, headers=headers, timeout=5)
    
    assert resposta.status_code == 200, f"Falha ao conectar no Supabase ou tabela não encontrada. Status HTTP: {resposta.status_code}"

def test_busca_cidade_valida():
    """
    Testa se a pesquisa por 'belo jardim' retorna resultados ignorando formatação/case.
    """
    url = f"{SUPABASE_URL}/rest/v1/delegacias"
    
    # Passamos a busca para o 'params'. Isso garante que o Python formate o espaço corretamente!
    parametros = {
        "endereco": "ilike.*belo jardim*",
        "select": "*"
    }
    
    resposta = requests.get(url, headers=headers, params=parametros, timeout=5)
    
    assert resposta.status_code == 200, f"A API rejeitou a pesquisa. Status: {resposta.status_code}"
    dados = resposta.json()
    
    assert len(dados) > 0, "Nenhuma delegacia encontrada. RLS bloqueando ou cidade ausente."
    
    endereco_banco = dados[0].get("endereco", "").lower()
    assert "sebasti" in endereco_banco, f"O endereço não pareceu correto: {endereco_banco}"
    
def test_busca_cidade_invalida():
    """
    Testa se o sistema lida corretamente com cidades que não existem na base de dados.
    """
    # Trocámos 'cidade_busca' por 'endereco' e usamos ilike
    url = f"{SUPABASE_URL}/rest/v1/delegacias?endereco=ilike.*gotham*&select=*"
    resposta = requests.get(url, headers=headers, timeout=5)
    
    assert resposta.status_code == 200
    dados = resposta.json()
    
    assert len(dados) == 0, "A base de dados retornou dados para uma cidade fictícia!"