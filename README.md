```markdown
# Delegacia 5.0 - Assistente Virtual da PCPE

## Introdução
O **Delegacia 5.0** é um sistema de triagem automatizada via WhatsApp desenvolvido para modernizar o atendimento da Polícia Civil de Pernambuco (PCPE). Utiliza Inteligência Artificial (Llama 3.1) e fluxos de decisão (Typebot) para orientar os cidadãos de forma oficial e segura. 

Principais funcionalidades:
* Triagem e direcionamento de Boletins de Ocorrência (Online vs. Presencial).
* Consulta de endereços físicos das 183 delegacias do estado usando banco de dados próprio (Supabase).
* Detecção de emergências graves com transferência invisível e imediata para o plantão policial.

---

## Requisitos do Sistema
Para rodar este projeto na sua máquina, você precisará de:
* [Docker](https://www.docker.com/) e Docker Compose
* [Python 3.10+](https://www.python.org/)
* Conta ativa no [Typebot](https://typebot.io/) (com o fluxo JSON do projeto importado)

---

## Instalação e Configuração

**1. Clone o repositório:**
```bash
git clone [https://projeto-integrador1@dev.azure.com/projeto-integrador1/projeto-integrador/_git/projeto-integrador]
cd projeto_integrador

```

**2. Configuração das Variáveis de Ambiente:**
Faça uma cópia do arquivo de modelo e preencha com as suas credenciais reais (API do WAHA, chave do Supabase, ID do Typebot, etc). O arquivo `.env` está protegido e não subirá para o repositório.

```bash
cp .env.example .env

```

**3. Instalação do Backend Python:**
Crie um ambiente virtual e instale as dependências necessárias:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

```

---

## Executando o Projeto

A arquitetura do sistema é dividida em três frentes principais que precisam estar ativas simultaneamente:

**1. Banco de Dados (Supabase Local):**
*(Nota: Certifique-se de ter a pasta oficial do Supabase Docker clonada no seu sistema).*
Vá até o diretório do Supabase e inicie os contêineres:

```bash
cd caminho/para/supabase/docker
docker compose up -d

```

**2. Motor do WhatsApp (WAHA):**
Na raiz do nosso repositório, suba o contêiner do WhatsApp:

```bash
docker compose up -d

```

**3. Servidor de Roteamento (Flask):**
Com os contêineres no ar, inicie o backend em Python que faz a ponte de comunicação:

```bash
python3 app.py

```

---

## Testes Automatizados

O projeto conta com uma suíte rigorosa de testes utilizando o `pytest` para garantir a estabilidade do roteamento, a segurança do Webhook contra acessos indevidos e a integridade da busca no banco de dados.

Os testes estão categorizados dentro da pasta `tests/`.

* **Rodar todos os testes de uma vez:**
```bash
pytest

```


* **Rodar testes específicos por módulo:**
```bash
# Testar apenas a lógica, menus e tolerância a erros do Typebot
pytest tests/test_typebot.py

# Testar defesas do servidor Flask contra tráfego malicioso e payloads inválidos
pytest tests/test_webhook.py

# Testar conexão com Supabase e precisão da busca de endereços
pytest tests/test_database.py

# Verificar a saúde das integrações (Latência e status do WAHA/Typebot)
pytest tests/test_integracoes.py

```



*Aviso: Certifique-se de que o seu arquivo `.env` está devidamente preenchido antes de rodar os testes, pois os scripts realizam consultas reais à sua infraestrutura local.*

```

```