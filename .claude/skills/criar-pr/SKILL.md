---
name: criar-pr
description: Implementa uma issue e abre o PR com o agente autor-de-pr. Uso: /criar-pr <número da issue>.
argument-hint: <número da issue>
---

Chame o agente `autor-de-pr` com a ferramenta Agent, com o pedido no modelo
do CLAUDE.md: Estamos em: issue $ARGUMENTS. Você faz: a issue inteira (ou o
PR do passo a passo, se o dono pedir um específico). Devolva: link do PR.
Some ao pedido o que o dono já decidiu ou tirou do escopo nesta conversa.

Sem número, rode `gh issue list` e pergunte ao dono qual issue fazer.

Se o agente voltar com uma pergunta (tipo de entrega, decisão em aberto), leve a pergunta ao dono. Não responda por ele.

Ao voltar, repasse o link do PR. Não mescle.
