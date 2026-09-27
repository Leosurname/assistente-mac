---
name: revisar-issue
description: Confere uma issue contra o código e comenta o passo a passo, com o agente revisor-de-issue. Uso: /revisar-issue <número da issue>.
argument-hint: <número da issue>
---

Chame o agente `revisor-de-issue` com a ferramenta Agent, passando a issue $ARGUMENTS.

Sem número, rode `gh issue list` e pergunte ao dono qual issue revisar.

Ao voltar, repasse o link do comentário e as decisões que ficaram para o dono.
