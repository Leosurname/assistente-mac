---
name: revisar-pr
description: Revisa um PR deste repositório com o agente revisor-de-pr. Uso: /revisar-pr <número do PR>.
argument-hint: <número do PR>
---

Chame o agente `revisor-de-pr` com a ferramenta Agent, passando o PR $ARGUMENTS.

Sem número, rode `gh pr list` e pergunte ao dono qual PR revisar.

Ao voltar, repasse ao dono o link do comentário e os achados principais.
