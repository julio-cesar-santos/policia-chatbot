import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("SUPABASE_KEY", "")
base_url = os.getenv("SUPABASE_URL", "")

print(f"[1] URL configurada: {base_url}")

headers = {
    "apikey": api_key,
    "Authorization": f"Bearer {api_key}"
}

url_ping = f"{base_url}?select=*&limit=2"

try:
    print("[2] A disparar requisição para o Supabase...")
    resposta = requests.get(url_ping, headers=headers, timeout=10)
    
    print(f"[3] Status HTTP Retornado: {resposta.status_code}")
    
    if resposta.status_code == 200:
        dados = resposta.json()
        if not dados:
            print("\nALERTA: O Supabase devolveu uma lista vazia []. A sua tabela está VAZIA.")
        else:
            print("\nSUCESSO! Veja a estrutura exata dos seus dados:")
            print(dados)
    else:
        print(f"\n❌ ERRO DO SUPABASE: {resposta.text}")
        
except Exception as e:
    print(f"\n💥 FALHA DE REDE: {e}")