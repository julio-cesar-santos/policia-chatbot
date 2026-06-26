```markdown
# 🚓 Polícia Civil PE - Delegacia 5.0 (Triagem IA)

Sistema de orquestração de chatbot para o WhatsApp da Polícia Civil de Pernambuco, focado na triagem inteligente de cidadãos, encaminhamento para Boletim de Ocorrência Online e busca indexada de delegacias físicas.

## 📖 Índice de Documentação
Para aprofundar-se na engenharia deste projeto, consulte nossa documentação técnica na pasta `/docs`:
* [Arquitetura e C4 Model](docs/ARCHITECTURE.md)
* [Documentação da API](docs/API.md)
* [Model Card da Inteligência Artificial](docs/MODEL_CARD.md)
* [Segurança e Compliance](docs/SECURITY.md)

---

## ⚙️ Runbook (Guia de Execução)

### Pré-requisitos
* Docker e Docker Compose instalados.
* Python 3.10+.
* Chaves de API do Groq e Supabase.

### Variáveis de Ambiente (`.env`)
Crie um arquivo `.env` na raiz do projeto com o seguinte formato:
```env
# Segurança WAHA
WAHA_API_KEY=sua_chave_secreta_aqui

# Integrações
GROQ_API_KEY=gsk_suachave
SUPABASE_URL=[https://seusupabase.supabase.co](https://seusupabase.supabase.co)
SUPABASE_KEY=sua_chave_service_role_ou_anon

# Autorização (Deixe vazio para produção ou defina um número para testes)
NUMERO_AUTORIZADO=5581999999999@c.us

```

### Configuração do Banco de Dados (Supabase)

Para garantir buscas na casa dos milissegundos (< 5ms), execute este script SQL no painel do Supabase para criar o índice de Trigramas:

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_delegacias_endereco_trgm ON delegacias USING GIN (endereco gin_trgm_ops);

```

### Subindo a Aplicação

1. Inicie a infraestrutura do WhatsApp (WAHA):
```bash
docker-compose up -d

```


2. Prepare o ambiente e inicie o Orquestrador Python:
```bash
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py

```


3. Acesse `http://localhost:3000/dashboard`, gere o QR Code e conecte o WhatsApp.

```