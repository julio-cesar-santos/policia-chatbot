import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_waha_api_should_return_status_200_when_fetching_sessions():
    waha_base_url = "http://localhost:3000"
    headers = {"X-Api-Key": os.getenv("WAHA_API_KEY", "")}
    
    try:
        url = f"{waha_base_url}/api/sessions"
        response = requests.get(url, headers=headers, timeout=5)
        assert response.status_code == 200
    except requests.exceptions.ConnectionError:
        pytest.fail("WAHA não está rodando na porta 3000.")

def test_groq_api_should_return_status_200_when_authenticating():
    groq_url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 5
    }
    
    response = requests.post(groq_url, headers=headers, json=payload, timeout=10)
    
    assert response.status_code == 200, "Falha de comunicação ou Autenticação com a API do Groq"