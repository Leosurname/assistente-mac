---
name: revisar-issue
description: Confere uma issue contra o código e comenta o passo a passo, com o agente revisor-de-issue. Uso: /revisar-issue <número da issue>.
argument-hint: <número da issue>
---

Chame o agente `revisor-de-issue` com a ferramenta Agent, com o pedido no
modelo do CLAUDE.md: Estamos em: issue $ARGUMENTS. Você faz: conferir e
comentar o passo a passo. Devolva: link do comentário e as decisões do
dono, com sugestão. Some ao pedido o que o dono já decidiu ou tirou do
escopo nesta conversa.

Sem número, rode `gh issue list` e pergunte ao dono qual issue revisar.

Ao voltar, repasse o link do comentário e as decisões que ficaram para o dono.
