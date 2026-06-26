```markdown
# 🛡️ Documentação de Segurança — Padrão OWASP ASVS

A arquitetura e o código-fonte deste projeto implementam controles estritos de segurança, alinhados ao *Application Security Verification Standard (ASVS)* da OWASP.

## V2: Autenticação e Gestão de Sessões
* O tráfego de saída (Outbound) entre o backend FastAPI e o contêiner WAHA é autenticado em todas as requisições através de API Keys configuradas via variáveis de ambiente (Header `X-Api-Key`).

## V5: Validação, Sanitização e Codificação
* **Anti-Mass Assignment:** Todas as entradas JSON do webhook são rigorosamente tipadas e validadas pela biblioteca `Pydantic`. Chaves desconhecidas ou não esperadas no JSON de entrada são automaticamente rejeitadas.
* **Prevenção de SQL Injection:** O sistema não utiliza concatenação de strings para montar queries SQL cruas. A comunicação com o Supabase é feita exclusivamente através do SDK HTTP REST (PostgREST), que parametriza as buscas de forma nativa e segura no PostgreSQL. A sanitização também remove quebras de linha e espaços ocultos na busca de localidades.

## V7: Proteção de Erros e Gestão de Logs
* **Fail-Safe Design:** Exceções críticas (como `IAIntegrationError` e `DatabaseIntegrationError`) são tratadas isoladamente. O erro técnico (Stack Trace) é registrado no terminal/log interno, mas nunca é vazado (Data Leakage) para o cidadão no WhatsApp. Em vez disso, o sistema retorna uma mensagem amigável e padronizada de indisponibilidade técnica temporária.

## Controle de Acesso (Zero-Trust)
* **Whitelist Baseada em Código:** O sistema possui uma trava de proteção no Ingress do webhook (`NUMERO_AUTORIZADO`). Em ambiente de desenvolvimento e homologação, o sistema atua em *default-deny*, ignorando qualquer requisição proveniente de números que não estejam explicitamente declarados no `.env`.

```