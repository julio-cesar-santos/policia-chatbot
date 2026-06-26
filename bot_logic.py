import os
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class IAIntegrationError(Exception):
    """Erro disparado quando o motor de Inteligência Artificial falha."""
    pass

class DatabaseIntegrationError(Exception):
    """Erro disparado quando a comunicação com a Base de Dados falha."""
    pass

class ServicoTriagemIA:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.modelo = "llama-3.1-8b-instant"
        self.prompt_sistema = (
            "Você é o assistente de triagem da Polícia Civil de Pernambuco. Seu tom é oficial e objetivo.\n\n"
            "REGRAS ABSOLUTAS E INQUEBRÁVEIS:\n"
            "1. É ESTRITAMENTE PROIBIDO fazer investigação informal. NUNCA faça perguntas ao cidadão.\n"
            "2. É ESTRITAMENTE PROIBIDO demonstrar empatia excessiva.\n"
            "3. Se o cidadão relatar um CRIME GRAVE: Pare imediatamente e oriente ir a uma delegacia física ou ligar 190.\n"
            "4. Se o cidadão relatar furto simples: Oriente B.O. Online.\n"
            "5. REGRA DE ROTEAMENTO: Se a resposta for para um CRIME GRAVE ou exigir atendimento humano, adicione OBRIGATORIAMENTE a exata tag [TRANSBORDO] no final do seu texto."
        )

    def analisar_relato(self, mensagem_usuario: str) -> str:
        """Envia a mensagem do cidadão para o LLM e retorna a orientação."""
        
        payload = {
            "model": self.modelo,
            "messages": [
                {"role": "system", "content": self.prompt_sistema},
                {"role": "user", "content": f"O cidadão enviou: {mensagem_usuario}\nResponda APENAS como o assistente."}
            ],
            "temperature": 0.0
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=15)
            response.raise_for_status() 
            return response.json()['choices'][0]['message']['content']
        
        except requests.RequestException as erro:
            raise IAIntegrationError(f"Falha de comunicação com o LLM (Groq): {erro}")


class DelegaciaRepository:
    def __init__(self):
        self.api_key = os.getenv("SUPABASE_KEY", "")
        self.base_url = os.getenv("SUPABASE_URL", "http://localhost:8000/rest/v1/delegacias")

    def buscar_por_localidade(self, localidade: str) -> Optional[List[Dict]]:
        """Busca delegacias filtrando pelo endereço fornecido."""
        
        if not self.api_key:
            raise DatabaseIntegrationError("A chave de API da base de dados não foi encontrada no ambiente.")

        headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}"
        }
        
        url_busca = f"{self.base_url}?endereco=ilike.*{localidade}*"
        
        try:
            resposta = requests.get(url_busca, headers=headers, timeout=10)
            resposta.raise_for_status()
            
            return resposta.json()
            
        except requests.RequestException as erro:
            raise DatabaseIntegrationError(f"Falha de comunicação com o Supabase: {erro}")