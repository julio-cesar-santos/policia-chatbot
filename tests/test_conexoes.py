import pytest
import requests
import concurrent.futures
import time
import os
from dotenv import load_dotenv

# Carrega as chaves do arquivo .env
load_dotenv()

# Configuracoes base
WAHA_BASE_URL = "http://localhost:3000"
WAHA_API_KEY = os.getenv("WAHA_API_KEY")
TYPEBOT_PUBLIC_ID = os.getenv("TYPEBOT_PUBLIC_ID")
TYPEBOT_API_URL = f"https://typebot.io/api/v1/typebots/{TYPEBOT_PUBLIC_ID}/startChat"
FLASK_WEBHOOK_URL = "http://localhost:5000/webhook"
NUMERO_AUTORIZADO = os.getenv("NUMERO_AUTORIZADO")
SUPABASE_URL = "http://localhost:8000"
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def test_conexao_supabase_local():
    """
    Testa se o banco de dados Supabase local (Docker) está rodando e acessível via API REST.
    """
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    try:
        resposta = requests.get(f"{SUPABASE_URL}/rest/v1/delegacias?select=*", headers=headers, timeout=5)
        assert resposta.status_code == 200, f"Falha no Supabase. Status retornado: {resposta.status_code}"
    except requests.exceptions.ConnectionError:
        pytest.fail("Sem conexão com o Supabase. O container está rodando na porta 8000?")

def test_busca_cidade_valida_supabase():
    """
    Testa se o banco retorna o endereço correto para uma cidade cadastrada, 
    simulando a string já limpa pelo Typebot.
    """
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    cidade_limpa = "belo jardim"
    resposta = requests.get(f"{SUPABASE_URL}/rest/v1/delegacias?cidade_busca=eq.{cidade_limpa}&select=endereco", headers=headers)
    
    assert resposta.status_code == 200, "Erro ao consultar a tabela delegacias."
    dados = resposta.json()
    assert len(dados) > 0, "Nenhum endereço encontrado para a cidade teste."
    assert "Av. Sebastião Rodrigues" in dados[0].get("endereco", ""), "O endereço retornado não corresponde ao esperado na base."

def test_busca_cidade_invalida_supabase():
    """
    Testa o comportamento do banco ao buscar uma cidade inexistente.
    Deve retornar uma lista vazia para o Typebot acionar o fluxo 'Else'.
    """
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    cidade_limpa = "gotham_city_falsa"
    resposta = requests.get(f"{SUPABASE_URL}/rest/v1/delegacias?cidade_busca=eq.{cidade_limpa}&select=endereco", headers=headers)
    
    assert resposta.status_code == 200
    dados = resposta.json()
    assert len(dados) == 0, "O banco deveria retornar uma lista vazia para cidades inexistentes."

def test_webhook_resiliencia_payload_invalido():
    """
    [Resiliência] Testa se o Flask (app.py) sobrevive ao receber um evento do WhatsApp 
    que não seja uma mensagem de texto (ex: confirmação de leitura ou status de bateria).
    """
    payload_malformado = {
        "event": "message.ack", # Evento diferente de 'message'
        "payload": {
            "id": "12345",
            "status": "READ"
        }
    }
    
    resposta = requests.post(FLASK_WEBHOOK_URL, json=payload_malformado, timeout=5)
    
    # O servidor NÃO deve quebrar (Erro 500). Deve retornar 200 OK silencioso ignorando a requisição.
    assert resposta.status_code == 200, f"O servidor quebrou com payload inesperado! HTTP {resposta.status_code}"
    assert resposta.json().get("status") == "ok", "O servidor não ignorou o payload malformado corretamente."



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

def test_webhook_metodo_get_nao_permitido():
    """
    Testa se o webhook está blindado contra acessos via navegador (GET).
    Apenas métodos POST devem ser permitidos.
    """
    resposta = requests.get(FLASK_WEBHOOK_URL, timeout=5)
    # Como definimos methods=['POST'] no app.py, requisições GET devem retornar 405 (Method Not Allowed)
    assert resposta.status_code == 405, f"Falha de segurança: Endpoint aceitou método GET com status {resposta.status_code}"

def test_webhook_mensagem_vazia_ou_espacos():
    """
    Testa se o sistema evita processar mensagens que contêm apenas espaços em branco,
    o que poderia causar falhas na API do Typebot.
    """
    payload_vazio = {
        "event": "message",
        "payload": {
            "from": NUMERO_AUTORIZADO,
            "body": "     "
        }
    }
    resposta = requests.post(FLASK_WEBHOOK_URL, json=payload_vazio, timeout=5)
    assert resposta.status_code == 200
    assert resposta.json().get("status") == "ok"

def test_webhook_midia_sem_texto():
    """
    Testa a resiliência do webhook caso o utilizador envie um áudio, sticker ou imagem 
    (onde o campo 'body' costuma vir vazio ou inexistente).
    """
    payload_midia = {
        "event": "message",
        "payload": {
            "from": NUMERO_AUTORIZADO,
            "type": "audio",
            "body": "" # Sem texto
        }
    }
    resposta = requests.post(FLASK_WEBHOOK_URL, json=payload_midia, timeout=5)
    # O Python não deve crashar com erro KeyError ou NoneType
    assert resposta.status_code == 200, "O servidor quebrou ao receber uma mídia sem texto!"

def test_carga_extrema_texto_longo():
    """
    Testa se o sistema suporta o envio de um texto massivo (ex: um relato de crime muito longo),
    sem estoirar o limite do JSON ou causar timeout na API do Typebot.
    """
    texto_gigante = "Relato de crime: " + ("texto " * 1000)
    payload_longo = {
        "event": "message",
        "payload": {
            "from": NUMERO_AUTORIZADO,
            "body": texto_gigante
        }
    }
    resposta = requests.post(FLASK_WEBHOOK_URL, json=payload_longo, timeout=15)
    assert resposta.status_code == 200, "O servidor não suportou uma mensagem com muitos caracteres."

# --- NOVOS TESTES: FLUXO LÓGICO E UX DO TYPEBOT ---

def test_typebot_menu_case_insensitive():
    """
    [UX e Navegação] Testa se o bot reconhece o comando de voltar ao menu 
    independentemente de letras maiúsculas ou minúsculas (ex: mEnU, vOLtaR).
    """
    payload_menu = {
        "message": "mEnU",
        "sessionId": "teste-case-insensitive-1"
    }
    payload_voltar = {
        "message": "vOLtaR",
        "sessionId": "teste-case-insensitive-2"
    }
    
    # Testando a palavra 'Menu' misturada
    res_menu = requests.post(TYPEBOT_API_URL, json=payload_menu, timeout=10)
    assert res_menu.status_code == 200
    retorno_menu = str(res_menu.json())
    assert "Digite o número da opção desejada" in retorno_menu, "FALHA: O Typebot não reconheceu 'mEnU' (Case Sensitive ativado)."

    # Testando a palavra 'Voltar' misturada
    res_voltar = requests.post(TYPEBOT_API_URL, json=payload_voltar, timeout=10)
    assert res_voltar.status_code == 200
    retorno_voltar = str(res_voltar.json())
    assert "Digite o número da opção desejada" in retorno_voltar, "FALHA: O Typebot não reconheceu 'vOLtaR' (Case Sensitive ativado)."

def test_typebot_opcao_numerica_invalida():
    """
    [Roteamento] Testa o comportamento do sistema quando o usuário digita 
    um número que não existe no menu (ex: 9). O fluxo deve ir para a IA.
    """
    payload = {
        "message": "9",
        "sessionId": "teste-opcao-invalida"
    }
    resposta = requests.post(TYPEBOT_API_URL, json=payload, timeout=10)
    assert resposta.status_code == 200
    
    textos_retornados = str(resposta.json())
    # Como 9 não é uma opção (1 a 6), a IA do Llama deve assumir o controle
    # O bot NÃO pode retornar o menu novamente e NÃO pode quebrar.
    assert "1 - Registrar B.O. Online" not in textos_retornados, "O bot repetiu o menu em vez de acionar a IA."
    assert len(textos_retornados) > 20, "O fluxo quebrou e não retornou nada ao receber uma opção inválida."

def test_typebot_texto_no_lugar_de_numero():
    """
    [Inteligência] Testa se o roteador do menu aceita texto livre e 
    encaminha corretamente para o Cérebro da IA para triagem.
    """
    payload = {
        "message": "Roubaram minha moto agora de manhã",
        "sessionId": "teste-texto-livre-menu"
    }
    resposta = requests.post(TYPEBOT_API_URL, json=payload, timeout=15)
    assert resposta.status_code == 200
    
    textos_retornados = str(resposta.json())
    # Pela regra do seu prompt, a IA deve bloquear BO online de veículo e mandar para a física.
    assert "delegacia" in textos_retornados.lower() or "presencial" in textos_retornados.lower(), "A IA não conseguiu interpretar o texto livre enviado pelo menu."