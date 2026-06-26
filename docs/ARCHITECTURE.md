```markdown
# 🏛️ Documentação de Arquitetura — C4 Model

A arquitetura do sistema foi desenhada seguindo os princípios de **Domain-Driven Design (DDD)** e **Arquitetura Hexagonal (Ports and Adapters)**, isolando a regra de negócio das integrações externas.

## Nível 1: Contexto do Sistema
* **Cidadão:** Interage via WhatsApp através de linguagem natural.
* **Sistema (Delegacia 5.0):** Recebe o relato, classifica a intenção (via IA) ou busca dados operacionais (via DB) e devolve a resposta formatada.
* **Sistemas Externos:** API do WhatsApp (WAHA), Motor de IA (Groq/Llama 3.1) e Banco de Dados (Supabase/PostgreSQL).

## Nível 2: Containers
* **Container WAHA (Node.js/Docker):** Responsável por manter a sessão do WhatsApp Web, gerar o QR Code e converter as mensagens do protocolo nativo do WhatsApp para requisições HTTP (Webhooks).
* **Container Core Orquestrador (Python/FastAPI):** Aplicação backend que gerencia o estado da conversa (`sessoes`), aplica regras de segurança (Firewall lógico) e roteia as decisões para os adaptadores corretos.
* **Container de Dados (Supabase):** Armazenamento estruturado de delegacias com suporte a indexação avançada GIN (Trigramas) para buscas textuais ultra-rápidas.

## Nível 3: Componentes (FastAPI Core)
* **API Controller (`app.py`):** Expõe o endpoint HTTP `/webhook`, valida DTOs de entrada com Pydantic e aciona as *Background Tasks* para não travar o WAHA.
* **Orquestrador de Triagem (`app.py`):** Máquina de estados finita que decide se o usuário está na navegação de menu, em fluxo de busca ou em conversação aberta com a IA.
* **Adapters (`bot_logic.py`):** * `WahaOutboundAdapter`: Traduz e envia requisições de volta ao WAHA.
  * `DelegaciaRepository`: Comunica-se com o Supabase via REST/PostgREST.
  * `ServicoTriagemIA`: Comunica-se com a API do Groq para inferência de LLM.

```
