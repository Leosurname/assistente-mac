---
name: organizar-repo
description: Levanta branches, issues, labels e docs velhos com o agente organizador e propõe a limpeza. Uso: /organizar-repo.
---

Chame o agente `organizador` com a ferramenta Agent, com o pedido no modelo
do CLAUDE.md: Estamos em: o repositório, na main. Você faz: levantar o que
está velho (branches, issues, labels, docs). Devolva: a lista, com uma
sugestão por item. Some ao pedido o que o dono já decidiu ou tirou do escopo
nesta conversa.

Foco pedido pelo dono, vazio quando não há foco: $ARGUMENTS

Ao voltar, mostre a lista ao dono. Apagar ou fechar qualquer coisa só depois de ele autorizar os itens, e só esses itens.
