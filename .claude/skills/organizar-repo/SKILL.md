---
name: organizar-repo
description: Levanta branches, issues, labels e docs velhos com o agente organizador e propõe a limpeza. Uso: /organizar-repo.
---

Chame o agente `organizador` com a ferramenta Agent, com o pedido no modelo
do CLAUDE.md: Estamos em: o repositório, na main. Você faz: levantar o que
está velho, com foco opcional (branches, issues, labels, docs) — $ARGUMENTS.
Devolva: a lista, com uma sugestão por item.

Ao voltar, mostre a lista ao dono. Apagar ou fechar qualquer coisa só depois de ele autorizar os itens, e só esses itens.
