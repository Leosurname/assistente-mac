---
name: criar-issue
description: Escreve uma issue nova com o agente autor-de-issue. Uso: /criar-issue <o que a issue pede>.
argument-hint: <o que a issue pede>
---

Chame o agente `autor-de-issue` com a ferramenta Agent, com o pedido no modelo
do CLAUDE.md: Estamos em: o pedido do dono — $ARGUMENTS — e issues parecidas
se houver. Você faz: escrever a issue. Devolva: link da issue, ou da issue
parecida que já existe. Some ao pedido o que o dono já decidiu ou tirou do
escopo nesta conversa.

Sem pedido, pergunte ao dono o que a issue deve pedir.

Ao voltar, repasse o link da issue, ou a issue parecida que o agente achou.
