```markdown
# 🔌 Documentação de API — OpenAPI

A API central foi construída utilizando o framework **FastAPI**. A documentação interativa (Swagger UI) é gerada automaticamente e pode ser acessada em ambiente local através da rota: `http://localhost:5000/docs`.

## Principal Endpoint (Ingress Webhook)

### `POST /webhook`
Responsável por receber, validar e enfileirar os eventos de mensagens encaminhados pela infraestrutura do WAHA.

**Request Body (`application/json`)**
Validado nativamente via `WebhookEventDTO` (Pydantic V2).

```json
{
  "event": "message",
  "payload": {
    "from": "5581999999999@c.us",
    "body": "Gostaria de registrar uma ocorrência.",
    "type": "text"
  }
}

```

**Responses (Status Codes):**

* `200 OK` — `{"status": "ok"}`: O payload foi aceito, o remetente está autorizado e a mensagem foi enfileirada no *Background Task* para processamento assíncrono.
* `200 OK` — `{"status": "ignorado"}`: Disparado pela camada de segurança quando o remetente não está na whitelist (variável `NUMERO_AUTORIZADO`) ou o evento não é do tipo mensagem.
* `422 Unprocessable Entity`: O payload enviado pelo WAHA está malformado ou incompleto (ex: falta o campo `from` ou `body`).

```