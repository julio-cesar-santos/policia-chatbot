```markdown
# 🧠 Documentação de IA — Model Card

O módulo de triagem semântica é alimentado por um Large Language Model (LLM) configurado especificamente para atuar como um agente governamental de primeiro nível de atendimento.

## Especificações Técnicas do Modelo

| Propriedade | Configuração / Valor |
| :--- | :--- |
| **Modelo Base** | `llama-3.1-8b-instant` |
| **Provedor de Inferência** | Groq (LPU - Language Processing Unit) |
| **Temperatura** | `0.0` (Garante respostas determinísticas, minimizando severamente alucinações criativas) |
| **Top P** | `1.0` (Padrão) |
| **Caso de Uso Principal** | Classificação de denúncias, triagem de crimes e orientação procedimental de cidadãos. |

## Guardrails e Diretrizes de Segurança Sistêmica

O modelo opera sob regras absolutas injetadas no *System Prompt*:

1. **Vedação de Investigação:** O agente é sistemicamente proibido de realizar investigações informais ou fazer perguntas de aprofundamento ao cidadão.
2. **Postura Institucional:** Neutralidade obrigatória; proibição de demonstrar empatia excessiva que fuja ao padrão de atendimento policial.
3. **Mecanismo de Transbordo (Escalonamento):** Injeção forçada da tag estruturada `[TRANSBORDO]` acionada sempre que a IA identifica crimes graves (ex: violência física, uso de armas de fogo). Esta tag é interceptada pelo Orquestrador Python, que encerra o chat automatizado e encaminha o cidadão para o atendimento humano do plantão policial.

```
