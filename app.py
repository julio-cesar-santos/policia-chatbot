import os
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from fastapi import FastAPI, BackgroundTasks, Depends, status, Request
from pydantic import BaseModel, Field, ConfigDict

from bot_logic import (
    ServicoTriagemIA,
    DelegaciaRepository,
    IAIntegrationError,
    DatabaseIntegrationError
)

load_dotenv()

app = FastAPI(
    title="Polícia Civil PE - Delegacia 5.0 API",
    description="Core Orquestrador de Triagem Inteligente via WhatsApp (DDD / Arquitetura Hexagonal)",
    version="2.0.0"
)

sessoes: Dict[str, Dict[str, Any]] = {}
NUMERO_AUTORIZADO = os.getenv("NUMERO_AUTORIZADO", "").strip()

class WahaPayloadDTO(BaseModel):
    remetente: str = Field(..., alias="from")
    corpo: str = Field(default="", alias="body")
    tipo: Optional[str] = Field(default="text", alias="type")

    model_config = ConfigDict(populate_by_name=True)

    @property
    def texto_limpo(self) -> str:
        return self.corpo.strip()


class WebhookEventDTO(BaseModel):
    event: str
    payload: WahaPayloadDTO

class WahaOutboundAdapter:
    
    def __init__(self):
        self.url = "http://localhost:3000/api/sendText"
        self.api_key = os.getenv("WAHA_API_KEY", "").strip()

    def enviar(self, chat_id: str, texto: str) -> None:
        payload = {"chatId": chat_id, "text": texto, "session": "default"}
        headers = {"Content-Type": "application/json", "X-Api-Key": self.api_key}
        try:
            res = requests.post(self.url, json=payload, headers=headers, timeout=5)
            print(f"[WAHA OUT] -> Alvo: {chat_id} | HTTP: {res.status_code}")
        except Exception as exc:
            print(f"[ERRO CRÍTICO INFRA] Falha ao contactar WAHA: {exc}")

class OrquestradorDeTriagem:
    def __init__(
        self,
        waha: WahaOutboundAdapter,
        repo: DelegaciaRepository,
        ia: ServicoTriagemIA
    ):
        self.waha = waha
        self.repo = repo
        self.ia = ia
        self.msg_voltar = 'Para voltar ao menu, digite "Menu" ou "Voltar".'

    def executar_ciclo(self, chat_id: str, mensagem: str) -> None:
        if chat_id not in sessoes:
            sessoes[chat_id] = {'estado': 'novo', 'historico': [], 'primeiro_acesso': True}
            self._enviar_menu_principal(chat_id)
            return

        if mensagem.lower() in ["menu", "voltar"]:
            self._enviar_menu_principal(chat_id)
            return

        estado_atual = sessoes[chat_id]['estado']

        if estado_atual in ['menu', 'novo', 'bo_online']:
            self._lidar_menu(chat_id, mensagem)
        elif estado_atual == 'busca_delegacias':
            self._lidar_busca(chat_id, mensagem)
        elif estado_atual == 'feedback_busca':
            self._lidar_feedback(chat_id, mensagem)
        elif estado_atual == 'pos_feedback':
            self._lidar_pos_feedback(chat_id, mensagem)
        elif estado_atual == 'refazer_busca':
            self._lidar_refazer(chat_id, mensagem)
        elif estado_atual == 'atendimento_humano':
            self._lidar_humano(chat_id, mensagem)

    def _enviar_menu_principal(self, chat_id: str) -> None:
        sessoes[chat_id]['estado'] = 'menu'
        
        texto_completo = (
            "Olá! Sou o assistente da *Polícia Civil de Pernambuco*. Como posso ajudar você hoje?\n\n"
            "Digite o número da opção desejada:\n"
            "1 - Registrar B.O. Online\n"
            "2 - Delegacias Próximas\n"
            "3 - Denúncia Anônima\n"
            "4 - Acompanhar B.O.\n"
            "5 - Informações de licenciamento\n"
            "6 - Falar com Atendente\n\n"
            "Ou digite diretamente o seu problema abaixo."
        )
        
        if sessoes[chat_id].get('primeiro_acesso'):
            texto_completo += '\n\nPara voltar ao menu, digite "Menu" ou "Voltar".'
            sessoes[chat_id]['primeiro_acesso'] = False
            
        self.waha.enviar(chat_id, texto_completo)

    def _apresentar_delegacia(self, chat_id: str, alternativa: bool = False) -> None:
        indice = sessoes[chat_id].get('indice_busca', 0)
        resultados = sessoes[chat_id].get('resultados_busca', [])
        
        if indice < len(resultados):
            delegacia = resultados[indice]
            nome = delegacia.get('descricao', 'Delegacia da Polícia Civil')
            endereco = delegacia.get('endereco', 'Endereço não cadastrado')
            telefone = delegacia.get('telefones', 'Telefone não disponível')
            
            intro = "Aqui está outra opção próxima:\n\n" if alternativa else "A delegacia mais próxima seria:\n\n"
            self.waha.enviar(chat_id, f"{intro}*{nome}*\n\nEndereço: {endereco}\n\nContato: {telefone}")
            self.waha.enviar(chat_id, "Esse resultado foi útil?\n1 - Sim\n2 - Não")
        else:
            self.waha.enviar(chat_id, "Não encontrei mais delegacias para essa localidade no sistema.\n\nDeseja digitar sua localidade novamente?\n1 - Sim\n2 - Não")
            sessoes[chat_id]['estado'] = 'refazer_busca'

    def _lidar_menu(self, chat_id: str, mensagem: str) -> None:
        msg_lower = mensagem.lower()

        if msg_lower == "1":
            texto = (
                "O boletim de ocorrência online pode ser feito pelo portal oficial da Secretaria de Defesa Social.\n\n"
                "⚠️ *Atenção:* Ele é válido apenas para furtos, perda de documentos, acidentes de trânsito sem vítimas e crimes cibernéticos. Casos de violência física, roubo com arma de fogo ou furto de veículos exigem ida à delegacia física.\n\n"
                "Acesse o link para registrar: http://servicos.sds.pe.gov.br/delegacia/\n\n"
                f"_{self.msg_voltar}_"
            )
            self.waha.enviar(chat_id, texto)
            sessoes[chat_id]['estado'] = 'menu'
            
        elif msg_lower == "2":
            sessoes[chat_id]['estado'] = 'busca_delegacias'
            self.waha.enviar(chat_id, 'Por favor, me informe o seu bairro e a sua cidade para que eu possa localizar a delegacia mais próxima no meu sistema. Mande exatamente: "BAIRRO, CIDADE"')
            
        elif msg_lower == "3":
            texto = (
                "Para fazer uma denúncia anônima com total sigilo, você pode ligar gratuitamente para o número *181 (Disque Denúncia)*.\n\n"
                "Se preferir, você também pode digitar os detalhes da denúncia aqui mesmo no chat e eu farei o registro inicial.\n\n"
                f"_{self.msg_voltar}_"
            )
            self.waha.enviar(chat_id, texto)
            sessoes[chat_id]['estado'] = 'menu' 

        elif msg_lower == "4":
            texto = (
                "O acompanhamento do seu Boletim de Ocorrência deve ser feito exclusivamente no site oficial da Polícia Civil de Pernambuco, utilizando o número de protocolo gerado no momento do seu registro.\n\n"
                "Acesse: https://delegaciapelainternet.pc.pe.gov.br/delegacia/emissaoBo\n\n"
                f"_{self.msg_voltar}_"
            )
            self.waha.enviar(chat_id, texto)
            sessoes[chat_id]['estado'] = 'menu'

        elif msg_lower == "5":
            texto = (
                "A Lei 7550/77 trata das taxas de fiscalização e licenciamento policial (necessárias para alvarás de eventos, shows, segurança privada, etc.).\n\n"
                "Para prosseguir, o cidadão deve emitir o DAE (Documento de Arrecadação Estadual) através do portal de serviços da PCPE.\n\n"
                f"_{self.msg_voltar}_"
            )
            self.waha.enviar(chat_id, texto)
            sessoes[chat_id]['estado'] = 'menu'

        elif msg_lower == "6":
            sessoes[chat_id]['estado'] = 'atendimento_humano'
            texto_humano = (
                "Compreendo. Por questões de segurança ou complexidade, estou transferindo o seu atendimento para o plantão policial. Por favor, aguarde um instante na linha.\n\n"
                "_(Para cancelar a transferência e voltar ao menu principal, digite \"Menu\")_"
            )
            self.waha.enviar(chat_id, texto_humano)
            
        elif msg_lower in ["voltar", "menu"]:
            self._enviar_menu_principal(chat_id)
            
        else:
            try:
                resposta_ia = self.ia.analisar_relato(mensagem)
                if "[TRANSBORDO]" in resposta_ia:
                    texto_transbordo = (
                        "Compreendo. Por questões de segurança ou complexidade, estou transferindo o seu atendimento para o plantão policial. Por favor, aguarde um instante na linha.\n\n"
                        "_(Para cancelar a transferência e voltar ao menu principal, digite \"Menu\")_"
                    )
                    self.waha.enviar(chat_id, texto_transbordo)
                    sessoes[chat_id]['estado'] = 'atendimento_humano'
                else:
                    mensagem_final = f"{resposta_ia}\n\n_{self.msg_voltar}_"
                    self.waha.enviar(chat_id, mensagem_final)
            except IAIntegrationError as erro:
                print(f"[FALHA LLM] {erro}")
                self.waha.enviar(chat_id, "Desculpe, estou a enfrentar instabilidades técnicas no momento. Tente novamente em alguns minutos.")

    def _lidar_busca(self, chat_id: str, mensagem: str) -> None:
        if mensagem.lower() in ["voltar", "menu"]:
            self._enviar_menu_principal(chat_id)
            return

        try:
            dados_banco = self.repo.buscar_por_localidade(mensagem)
            if not dados_banco:
                self.waha.enviar(chat_id, "Nenhum resultado encontrado. Deseja digitar sua localidade novamente?\n1 - Sim\n2 - Não")
                sessoes[chat_id]['estado'] = 'refazer_busca'
            else:
                resultados_unicos = []
                vistos = set()
                for d in dados_banco:
                    end = d.get('endereco', '').strip().lower()
                    if end not in vistos:
                        vistos.add(end)
                        resultados_unicos.append(d)

                sessoes[chat_id]['resultados_busca'] = resultados_unicos
                sessoes[chat_id]['indice_busca'] = 0
                sessoes[chat_id]['estado'] = 'feedback_busca'
                self._apresentar_delegacia(chat_id)
        except DatabaseIntegrationError as exc:
            print(f"[FALHA DB] {exc}")
            self.waha.enviar(chat_id, "O nosso sistema de localização está temporariamente indisponível.")
            self._enviar_menu_principal(chat_id)

    def _lidar_feedback(self, chat_id: str, mensagem: str) -> None:
        if mensagem == "1":
            self.waha.enviar(chat_id, "Ficamos felizes em ajudar. Deseja utilizar outro serviço?\n1 - Sim\n2 - Não")
            sessoes[chat_id]['estado'] = 'pos_feedback'
        elif mensagem == "2":
            sessoes[chat_id]['indice_busca'] += 1
            self._apresentar_delegacia(chat_id, alternativa=True)
        else:
            self.waha.enviar(chat_id, "Por favor, responda com o número 1 para Sim ou 2 para Não.")

    def _lidar_pos_feedback(self, chat_id: str, mensagem: str) -> None:
        if mensagem == "1":
            self._enviar_menu_principal(chat_id)
        elif mensagem == "2":
            self.waha.enviar(chat_id, "Obrigado por utilizar nossos serviços! A Polícia Civil de Pernambuco está sempre à disposição.")
            sessoes[chat_id]['estado'] = 'novo'
        else:
            self.waha.enviar(chat_id, "Por favor, responda com o número 1 para Sim ou 2 para Não.")

    def _lidar_refazer(self, chat_id: str, mensagem: str) -> None:
        if mensagem == "1":
            self.waha.enviar(chat_id, "Por favor, me informe o seu bairro e a sua cidade para que eu possa localizar a delegacia mais próxima no meu sistema. Mande exatamente: \"BAIRRO, CIDADE\"")
            sessoes[chat_id]['estado'] = 'busca_delegacias'
        else:
            self.waha.enviar(chat_id, "Compreendo. Deseja utilizar outro serviço?\n1 - Sim\n2 - Não")
            sessoes[chat_id]['estado'] = 'pos_feedback'

    def _lidar_humano(self, chat_id: str, mensagem: str) -> None:
        if mensagem.lower() in ["voltar", "menu", "cancelar"]:
            self._enviar_menu_principal(chat_id)

print("\n[SISTEMA] Inicializando adaptadores...")
waha_global = WahaOutboundAdapter()
repo_global = DelegaciaRepository()

print("[SISTEMA] Aquecendo o cérebro da Inteligência Artificial...")
ia_global = ServicoTriagemIA()

print("[SISTEMA] Montando o Orquestrador...")
orquestrador_global = OrquestradorDeTriagem(
    waha=waha_global, 
    repo=repo_global, 
    ia=ia_global
)
print("[SISTEMA] Servidor 100% pronto e aguardando mensagens!\n")

def get_orquestrador() -> OrquestradorDeTriagem:
    return orquestrador_global

@app.post("/webhook", status_code=status.HTTP_200_OK)
async def receber_webhook(
    evento: WebhookEventDTO,
    background_tasks: BackgroundTasks,
    orquestrador: OrquestradorDeTriagem = Depends(get_orquestrador)
):

    if evento.event != "message":
        return {"status": "ignorado"}

    remetente = evento.payload.remetente
    corpo = evento.payload.texto_limpo

    if not remetente or "@g.us" in remetente or not corpo:
        return {"status": "ignorado"}

    if NUMERO_AUTORIZADO and NUMERO_AUTORIZADO not in remetente:
        print(f"[SEGURANÇA] Bloqueado remetente não autorizado: {remetente}")
        return {"status": "ignorado"}

    background_tasks.add_task(orquestrador.executar_ciclo, remetente, corpo)
    
    return {"status": "ok"}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)