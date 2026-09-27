---
name: equipe
description: Entrega um pedido ao agente certo, ou roda o fluxo completo de uma issue (revisar issue, criar PR, revisar PR). Uso: /equipe <pedido> ou /equipe fluxo <número da issue>.
argument-hint: <pedido> | fluxo <número da issue>
---

Os agentes deste repositório estão em `.claude/agents/`:

| Pedido | Agente |
|---|---|
| Revisar PR | `revisor-de-pr` |
| Criar PR | `autor-de-pr` |
| Revisar issue | `revisor-de-issue` |
| Criar issue | `autor-de-issue` |
| Organizar repositório | `organizador` |

Pedido: $ARGUMENTS

## Pedido avulso

Escolha o agente pela tabela e chame-o com o pedido no modelo do CLAUDE.md,
preenchido como o agente descreve em "Como você é chamado". Se o pedido não
se encaixar em nenhum, ou em mais de um, pergunte ao dono.

## `fluxo <n>`

Um agente por vez. Pare em cada ponto em que a decisão é do dono.

1. `revisor-de-issue` na issue `<n>`. Mostre ao dono as decisões em aberto e **espere a resposta**.
2. Com as decisões respondidas, `autor-de-pr` na issue `<n>`. **Estamos em**
   leva a issue `<n>` e o link do comentário devolvido pelo `revisor-de-issue`.
   **Já decidido pelo dono** leva as respostas dele às decisões do passo 1. Um
   PR por chamada. Se o passo a passo tiver vários PRs, faça o primeiro e
   pergunte antes do próximo.
3. `revisor-de-pr` no PR que acabou de abrir. **Estamos em** leva o PR
   devolvido pelo `autor-de-pr` e a issue `<n>`. **Fora do escopo** repete o
   que veio do passo 2.
4. Entregue ao dono o link do PR e os achados da revisão. Não corrija nem mescle sem ele pedir.
