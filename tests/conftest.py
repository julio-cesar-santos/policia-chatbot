import os
import pytest
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture(scope="session")
def fastapi_webhook_url() -> str:
    return "http://localhost:5000/webhook"


@pytest.fixture(scope="session")
def authorized_number() -> str:
    numero = os.getenv("NUMERO_AUTORIZADO", "5581999999999@c.us").strip()
    
    if numero and "@" not in numero:
        numero = f"{numero}@c.us"
        
    return numero or "5581999999999@c.us"

@pytest.fixture(scope="session")
def supabase_url() -> str:
    """Retorna a URL limpa da API do Supabase."""
    url = os.getenv("SUPABASE_URL", "http://localhost:8000")
    return url.strip().rstrip('/')


@pytest.fixture(scope="session")
def supabase_headers() -> dict:
    chave = os.getenv("SUPABASE_KEY", "chave_teste_invalida").strip()
    return {
        "apikey": chave,
        "Authorization": f"Bearer {chave}",
        "Content-Type": "application/json"
    }

@pytest.fixture(autouse=True)
def garbage_collector_sessoes():
    from app import sessoes
    sessoes.clear()
    yield
    sessoes.clear()