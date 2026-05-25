import pytest
import requests
import concurrent.futures
import time

# Configuracoes base
WAHA_BASE_URL = "http://localhost:3000"
WAHA_API_KEY = "delegacia50"
TYPEBOT_PUBLIC_ID = "delegacia-5-0-x0qqp0z"
TYPEBOT_API_URL = f"https://typebot.io/api/v1/typebots/{TYPEBOT_PUBLIC_ID}/startChat"
FLASK_WEBHOOK_URL = "http://localhost:5000/webhook"
NUMERO_AUTORIZADO = "39355339014152@lid"

def test_conexao_typebot():
    """
    Testa se o fluxo do Typebot está publicado, acessível e respondendo a requisições de início de chat.
    """
    payload = {
        "message": "Teste interno Pytest",
        "sessionId": "diagnostico-pytest"
    }
    
    try:
        resposta = requests.post(TYPEBOT_API_URL, json=payload, timeout=10)
        # O pytest verifica se a condição é verdadeira. Se não for, o teste falha.
        assert resposta.status_code in [200, 201], f"Erro na API do Typebot. Status retornado: {resposta.status_code}"
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Falha de conexão com a API do Typebot: {e}")

def test_conexao_waha():
    """
    Testa se o container do WAHA está rodando localmente na porta 3000 e se a API Key é válida.
    """
    headers = {"X-Api-Key": WAHA_API_KEY}
    
    try:
        resposta = requests.get(f"{WAHA_BASE_URL}/api/sessions", headers=headers, timeout=5)
        assert resposta.status_code == 200, f"Falha no WAHA. Verifique se ele está rodando e se a API Key está correta. Status: {resposta.status_code}"
    except requests.exceptions.ConnectionError:
        pytest.fail("Sem conexão com o WAHA. O serviço está ativo na porta 3000?")

def test_webhook_flask():
    """
    Testa se o servidor Flask local está de pé e processando o payload esperado pelo Webhook.
    """
    payload_simulado = {
        "event": "message",
        "payload": {
            "from": NUMERO_AUTORIZADO,
            "body": "Teste de loopback interno - Pytest"
        }
    }
    
    try:
        resposta = requests.post(FLASK_WEBHOOK_URL, json=payload_simulado, timeout=5)
        assert resposta.status_code == 200, f"O servidor Flask retornou erro HTTP {resposta.status_code}"
        
        dados_json = resposta.json()
        assert dados_json.get("status") == "ok", "O Webhook conectou, mas o status retornado não foi 'ok'."
    except requests.exceptions.ConnectionError:
        pytest.fail("Sem conexão com o Flask. O arquivo 'app.py' está em execução na porta 5000?")

def test_webhook_bloqueia_numero_nao_autorizado():
    """
    [Segurança] Testa se o sistema bloqueia tentativas de contato 
    de números que não estão na variável NUMERO_AUTORIZADO.
    """
    payload_invasor = {
        "event": "message",
        "payload": {
            "from": "5511999999999@c.us", # Número não cadastrado
            "body": "Quero falar com a inteligência artificial!"
        }
    }
    
    resposta = requests.post(FLASK_WEBHOOK_URL, json=payload_invasor, timeout=5)
    
    assert resposta.status_code == 200, "O servidor deve responder HTTP 200 mesmo ignorando."
    assert resposta.json().get("status") == "ignorado", "Falha de segurança: O número não autorizado não foi ignorado!"

def test_tempo_de_resposta_typebot():
    """
    [Performance] Testa se a ponte com o Typebot está rápida o suficiente.
    O ideal para chatbots no WhatsApp é que a API responda em menos de 3 segundos.
    """
    payload = {
        "message": "Oi",
        "sessionId": "teste-latencia"
    }
    
    inicio = time.time()
    resposta = requests.post(TYPEBOT_API_URL, json=payload, timeout=10)
    fim = time.time()
    
    tempo_decorrido = fim - inicio
    
    assert resposta.status_code in [200, 201]
    assert tempo_decorrido < 3.0, f"Lentidão detectada! O Typebot demorou {tempo_decorrido:.2f} segundos para responder."

def test_carga_simultanea_flask():
    """
    [Stress Test] Dispara 15 requisições simultâneas para o Flask para garantir
    que o servidor não vai cair se vários usuários mandarem mensagem ao mesmo tempo.
    """
    def simular_mensagem(id_requisicao):
        payload = {
            "event": "message",
            "payload": {
                # Usamos um número falso para não sujar o fluxo real do Typebot durante o teste
                "from": f"119999000{id_requisicao}@c.us", 
                "body": f"Mensagem de teste simultâneo {id_requisicao}"
            }
        }
        return requests.post(FLASK_WEBHOOK_URL, json=payload, timeout=5)

    # Usa threads para disparar 15 requisições de uma vez só
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        # Cria uma lista de tarefas (IDs de 0 a 14)
        resultados = list(executor.map(simular_mensagem, range(15)))
    
    # Verifica se todas as 15 requisições foram processadas sem derrubar o servidor
    for res in resultados:
        assert res.status_code == 200, "O servidor falhou ou engasgou durante o teste de carga!"
        assert res.json().get("status") in ["ok", "ignorado"], "Resposta inesperada sob carga."