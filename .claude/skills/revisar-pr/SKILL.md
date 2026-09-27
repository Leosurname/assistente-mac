---
name: revisar-pr
description: Revisa um PR deste repositório com o agente revisor-de-pr. Uso: /revisar-pr <número do PR>.
argument-hint: <número do PR>
---

Chame o agente `revisor-de-pr` com a ferramenta Agent, com o pedido no modelo
do CLAUDE.md: Estamos em: PR $ARGUMENTS. Você faz: revisar e comentar.
Devolva: link da revisão e achados principais. Some ao pedido o que o dono
já decidiu ou tirou do escopo nesta conversa.

Sem número, rode `gh pr list` e pergunte ao dono qual PR revisar.

Ao voltar, repasse ao dono o link do comentário e os achados principais.
