import os
from dotenv import load_dotenv
import requests
from flask import Flask, request, jsonify

load_dotenv()

app = Flask(__name__)

# --- CONFIGURAÇÕES DE ACESSO ---
NUMERO_AUTORIZADO = os.getenv("NUMERO_AUTORIZADO")
TYPEBOT_PUBLIC_ID = os.getenv("TYPEBOT_PUBLIC_ID")
WAHA_API_KEY = os.getenv("WAHA_API_KEY")
WAHA_SEND_URL = "http://localhost:3000/api/sendText"
TYPEBOT_API_URL = f"https://typebot.io/api/v1/typebots/{TYPEBOT_PUBLIC_ID}/startChat"

@app.route('/webhook', methods=['POST'])
def receber_mensagem():
    dados = request.json

    if dados and dados.get('event') == 'message':
        payload = dados.get('payload', {})
        chat_id = payload.get('from', '')
        texto_usuario = payload.get('body', '')

        # Trava de Segurança
        if chat_id != NUMERO_AUTORIZADO:
            return jsonify({"status": "ignorado"}), 200

        print(f" Mensagem recebida: {texto_usuario}")

        try:
            # 1. ENVIAR PARA O TYPEBOT
            res_typebot = requests.post(TYPEBOT_API_URL, json={
                "message": texto_usuario,
                "sessionId": chat_id # Mantém o contexto do usuário no Typebot
            })

            if res_typebot.status_code in [200, 201]:
                dados_typebot = res_typebot.json()
                mensagens = dados_typebot.get('messages', [])

                # 2. EXTRAIR A RESPOSTA (Tratando RichText)
                for msg in mensagens:
                    content = msg.get('content', {})
                    texto_final = ""

                    if content.get('type') == 'richText':
                        rich_text_data = content.get('richText', [])
                        for entry in rich_text_data:
                            for child in entry.get('children', []):
                                texto_final += child.get('text', '') + " "

                    elif 'text' in content:
                        texto_final = content.get('text', '')

                    # 3. DEVOLVER PARA O WHATSAPP
                    if texto_final.strip():
                        requests.post(WAHA_SEND_URL, json={
                            "chatId": chat_id,
                            "text": texto_final.strip(),
                            "session": "default"
                        }, headers={"X-Api-Key": WAHA_API_KEY})

                        print(f" Typebot respondeu: {texto_final.strip()}")

        except Exception as e:
            print(f" Erro na ponte do Typebot: {e}")

    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    print(" Servidor Conectado ao Typebot!")
    app.run(host='0.0.0.0', port=5000)
