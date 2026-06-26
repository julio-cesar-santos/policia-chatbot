import os
import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from bot_logic import processar_ia, buscar_delegacias

# Carrega as variáveis do arquivo .env
load_dotenv()

app = Flask(__name__)

# Memória temporária das conversas
sessoes = {}

WAHA_URL = "http://localhost:3000/api/sendText"
WAHA_API_KEY = os.getenv("WAHA_API_KEY", "").strip()
NUMERO_AUTORIZADO = os.getenv("NUMERO_AUTORIZADO", "").strip()

def enviar_waha(chat_id, texto):
    """Envia a mensagem de volta para o WhatsApp via WAHA."""
    payload = {"chatId": chat_id, "text": texto, "session": "default"}
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": WAHA_API_KEY 
    }
    try:
        resposta = requests.post(WAHA_URL, json=payload, headers=headers)
        print(f"-> Tentativa de envio para: {chat_id} | Status: {resposta.status_code}")
    except Exception as e:
        print(f"Erro crítico de conexão com o WAHA: {e}")

def enviar_menu_principal(chat_id):
    """Envia o menu principal dividido em 3 balões."""
    sessoes[chat_id]['estado'] = 'menu'
    
    enviar_waha(chat_id, "Olá! Sou o assistente da *Polícia Civil de Pernambuco*. Como posso ajudar você hoje?")
    
    texto_opcoes = (
        "Digite o número da opção desejada:\n"
        "1 - Registrar B.O. Online\n"
        "2 - Delegacias Próximas\n"
        "3 - Denúncia Anônima\n"
        "4 - Acompanhar B.O.\n"
        "5 - Informações de licenciamento\n"
        "6 - Falar com Atendente\n\n"
        "Ou digite diretamente o seu problema abaixo."
    )
    enviar_waha(chat_id, texto_opcoes)
    enviar_waha(chat_id, 'Para voltar ao menu, digite "Menu" ou "Voltar".')

def roteador_principal(chat_id, mensagem):
    """Gerencia as escolhas do menu e aciona a IA quando necessário."""
    msg_limpa = str(mensagem).strip().lower()
    texto_voltar = 'Para voltar ao menu, digite "Menu" ou "Voltar".'

    if msg_limpa == "1":
        texto = (
            "O boletim de ocorrência online pode ser feito pelo portal oficial da Secretaria de Defesa Social.\n\n"
            "⚠️ *Atenção:* Ele é válido apenas para furtos, perda de documentos, acidentes de trânsito sem vítimas e crimes cibernéticos. Casos de violência física, roubo com arma de fogo ou furto de veículos exigem ida à delegacia física.\n\n"
            "Acesse o link para registrar: http://servicos.sds.pe.gov.br/delegacia/"
        )
        enviar_waha(chat_id, texto)
        enviar_waha(chat_id, texto_voltar)
        sessoes[chat_id]['estado'] = 'menu'
        
    elif msg_limpa == "2":
        sessoes[chat_id]['estado'] = 'busca_delegacias'
        texto = "Por favor, me informe o seu bairro e a sua cidade para que eu possa localizar a delegacia mais próxima no meu sistema. Mande exatamente: \"BAIRRO, CIDADE\""
        enviar_waha(chat_id, texto)
        enviar_waha(chat_id, texto_voltar)
        
    elif msg_limpa == "3":
        texto = (
            "Para fazer uma denúncia anônima com total sigilo, você pode ligar gratuitamente para o número *181 (Disque Denúncia)*.\n\n"
            "Se preferir, você também pode digitar os detalhes da denúncia aqui mesmo no chat e eu farei o registro inicial."
        )
        enviar_waha(chat_id, texto)
        enviar_waha(chat_id, texto_voltar)
        sessoes[chat_id]['estado'] = 'menu' 

    elif msg_limpa == "4":
        texto = (
            "O acompanhamento do seu Boletim de Ocorrência deve ser feito exclusivamente no site oficial da Polícia Civil de Pernambuco, utilizando o número de protocolo gerado no momento do seu registro.\n\n"
            "Acesse: https://delegaciapelainternet.pc.pe.gov.br/delegacia/emissaoBo"
        )
        enviar_waha(chat_id, texto)
        enviar_waha(chat_id, texto_voltar)
        sessoes[chat_id]['estado'] = 'menu'

    elif msg_limpa == "5":
        texto = (
            "A Lei 7550/77 trata das taxas de fiscalização e licenciamento policial (necessárias para alvarás de eventos, shows, segurança privada, etc.).\n\n"
            "Para prosseguir, o cidadão deve emitir o DAE (Documento de Arrecadação Estadual) através do portal de serviços da PCPE."
        )
        enviar_waha(chat_id, texto)
        enviar_waha(chat_id, texto_voltar)
        sessoes[chat_id]['estado'] = 'menu'

    elif msg_limpa == "6":
        sessoes[chat_id]['estado'] = 'atendimento_humano'
        texto = "Compreendo. Por questões de segurança ou complexidade, estou transferindo o seu atendimento para o plantão policial. Por favor, aguarde um instante na linha."
        enviar_waha(chat_id, texto)
        
        texto_sistema = "_(Para cancelar a transferência e voltar ao menu principal, digite \"Menu\")_"
        enviar_waha(chat_id, texto_sistema)
        
    elif msg_limpa in ["voltar", "menu"]:
        enviar_menu_principal(chat_id)
        
    else:
        resposta_ia = processar_ia(chat_id, mensagem)
        
        if "[TRANSBORDO]" in resposta_ia:
             texto_transbordo = "Compreendo. Por questões de segurança ou complexidade, estou transferindo o seu atendimento para o plantão policial. Por favor, aguarde um instante na linha."
             enviar_waha(chat_id, texto_transbordo)
             
             texto_sistema = "_(Para cancelar a transferência e voltar ao menu principal, digite \"Menu\")_"
             enviar_waha(chat_id, texto_sistema)
             
             sessoes[chat_id]['estado'] = 'atendimento_humano'
        else:
             enviar_waha(chat_id, resposta_ia)
             enviar_waha(chat_id, texto_voltar)


@app.route('/webhook', methods=['POST'])
def webhook_waha():
    """Ponto de entrada que escuta o WAHA e distribui as ações."""
    dados = request.json
    
    if dados.get("event") != "message":
        return jsonify({"status": "ignorado"})
        
    payload = dados.get("payload", {})
    chat_id = payload.get("from")
    mensagem = payload.get("body", "").strip()
    
    if not chat_id or "@g.us" in chat_id or not mensagem:
        return jsonify({"status": "ignorado"})

    # Bloqueio de segurança
    if NUMERO_AUTORIZADO and str(NUMERO_AUTORIZADO) not in chat_id:
        print(f"Bloqueado: Mensagem recebida de número não autorizado ({chat_id})")
        return jsonify({"status": "bloqueado"})
    
    # Inicia a sessão se o usuário for novo
    if chat_id not in sessoes:
        sessoes[chat_id] = {'estado': 'novo', 'historico': []}
        enviar_menu_principal(chat_id)
        return jsonify({"status": "sucesso"})
    
    estado_atual = sessoes[chat_id]['estado']
    
    # Máquina de estados
    if estado_atual in ['menu', 'novo', 'bo_online']:
        roteador_principal(chat_id, mensagem)
        
    elif estado_atual == 'busca_delegacias':
         if mensagem.lower() in ["voltar", "menu"]:
             enviar_menu_principal(chat_id)
         else:
             dados_banco = buscar_delegacias(mensagem)
             
             if dados_banco is None:
                 enviar_waha(chat_id, "Desculpe, não consegui consultar o banco de dados no momento.")
                 enviar_menu_principal(chat_id)
             elif len(dados_banco) == 0:
                 enviar_waha(chat_id, "Nenhum resultado encontrado. Deseja digitar sua localidade novamente?\n1 - Sim\n2 - Não")
                 sessoes[chat_id]['estado'] = 'refazer_busca'
             else:
                 # Filtro antiduplicidade
                 resultados_unicos = []
                 enderecos_vistos = set()
                 
                 for delegacia in dados_banco:
                     end_texto = delegacia.get('endereco', '').strip().lower()
                     if end_texto not in enderecos_vistos:
                         enderecos_vistos.add(end_texto)
                         resultados_unicos.append(delegacia)

                 sessoes[chat_id]['resultados_busca'] = resultados_unicos
                 sessoes[chat_id]['indice_busca'] = 0
                 
                 delegacia = resultados_unicos[0]
                 nome = delegacia.get('descricao', 'Delegacia da Polícia Civil')
                 endereco = delegacia.get('endereco', 'Endereço não cadastrado')
                 telefone = delegacia.get('telefones', 'Telefone não disponível')
                 
                 texto_resultado = f"A delegacia mais próxima seria:\n\n*{nome}*\n\nEndereço: {endereco}\n\nContato: {telefone}"
                 
                 enviar_waha(chat_id, texto_resultado)
                 enviar_waha(chat_id, "Esse resultado foi útil?\n1 - Sim\n2 - Não")
                 sessoes[chat_id]['estado'] = 'feedback_busca'

    elif estado_atual == 'feedback_busca':
         if mensagem == "1":
             enviar_waha(chat_id, "Ficamos felizes em ajudar. Deseja utilizar outro serviço?\n1 - Sim\n2 - Não")
             sessoes[chat_id]['estado'] = 'pos_feedback'
         else:
             # Avança para a próxima delegacia da lista
             sessoes[chat_id]['indice_busca'] += 1
             indice = sessoes[chat_id]['indice_busca']
             resultados = sessoes[chat_id].get('resultados_busca', [])
             
             if indice < len(resultados):
                 delegacia = resultados[indice]
                 nome = delegacia.get('descricao', 'Delegacia da Polícia Civil')
                 endereco = delegacia.get('endereco', 'Endereço não cadastrado')
                 telefone = delegacia.get('telefones', 'Telefone não disponível')
                 
                 texto_resultado = f"Aqui está outra opção próxima:\n\n*{nome}*\n\nEndereço: {endereco}\n\nContato: {telefone}"
                 
                 enviar_waha(chat_id, texto_resultado)
                 enviar_waha(chat_id, "Esse resultado foi útil?\n1 - Sim\n2 - Não")
             else:
                 enviar_waha(chat_id, "Não encontrei mais delegacias para essa localidade no sistema.\n\nDeseja digitar sua localidade novamente?\n1 - Sim\n2 - Não")
                 sessoes[chat_id]['estado'] = 'refazer_busca'

    elif estado_atual == 'pos_feedback':
         if mensagem == "1":
             enviar_menu_principal(chat_id)
         else:
             enviar_waha(chat_id, "Obrigado por utilizar nossos serviços!")
             sessoes[chat_id]['estado'] = 'novo'
             
    elif estado_atual == 'refazer_busca':
         if mensagem == "1":
             enviar_waha(chat_id, "Por favor, me informe o seu bairro e a sua cidade para que eu possa localizar a delegacia mais próxima no meu sistema. Mande exatamente: \"BAIRRO, CIDADE\"")
             sessoes[chat_id]['estado'] = 'busca_delegacias'
         else:
             enviar_menu_principal(chat_id)

    elif estado_atual == 'atendimento_humano':
         if mensagem.lower() in ["voltar", "menu", "cancelar"]:
             enviar_menu_principal(chat_id)

    return jsonify({"status": "sucesso"})

if __name__ == '__main__':
    app.run(debug=True)