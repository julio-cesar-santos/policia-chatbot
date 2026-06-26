import os
import requests
from dotenv import load_dotenv

# Carrega as variáveis do ficheiro .env para a memória
load_dotenv()

# Puxa as chaves de acesso diretamente do ambiente
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# --- CORREÇÃO: O URL agora vem do .env. Se não existir, usa o local para os testes ---
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
SUPABASE_URL = os.getenv("SUPABASE_URL", "http://localhost:8000/rest/v1/delegacias")

def processar_ia(chat_id, mensagem_usuario):
    """Integração com o Llama 3.1 a correr via serviço do Groq."""
    
    prompt_sistema = (
        "Você é o assistente de triagem da Polícia Civil de Pernambuco. Seu tom é oficial e objetivo.\n\n"
        "REGRAS ABSOLUTAS E INQUEBRÁVEIS:\n"
        "1. É ESTRITAMENTE PROIBIDO fazer investigação informal. NUNCA faça perguntas ao cidadão.\n"
        "2. É ESTRITAMENTE PROIBIDO demonstrar empatia excessiva.\n"
        "3. Se o cidadão relatar um CRIME GRAVE: Pare imediatamente e oriente ir a uma delegacia física ou ligar 190.\n"
        "4. Se o cidadão relatar furto simples: Oriente B.O. Online.\n"
        "5. REGRA DE ROTEAMENTO: Se a resposta for para um CRIME GRAVE ou exigir atendimento humano, adicione OBRIGATORIAMENTE a exata tag [TRANSBORDO] no final do seu texto."
    )

    payload_ia = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": f"O cidadão enviou: {mensagem_usuario}\nResponda APENAS como o assistente."}
        ],
        "temperature": 0
    }
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload_ia)
        response.raise_for_status() 
        
        return response.json()['choices'][0]['message']['content']
        
    except Exception as e:
        print(f"Erro na API do Groq: {e}")
        return "Desculpe, estou a enfrentar instabilidades no momento. Tente novamente mais tarde."

def buscar_delegacias(localidade):
    """Faz a busca e retorna a lista inteira de resultados do Supabase."""
    if not SUPABASE_KEY:
         return None

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    
    url_busca = f"{SUPABASE_URL}?endereco=ilike.*{localidade}*"
    
    try:
        resposta = requests.get(url_busca, headers=headers)
        resposta.raise_for_status()
        
        # Devolve a lista pura (ex: [delegacia1, delegacia2]) ou uma lista vazia []
        return resposta.json()
        
    except Exception as e:
        print(f"Erro na API do Supabase: {e}")
        return None