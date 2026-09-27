---
name: autor-de-pr
description: Implementa uma issue e abre o PR dela. Use quando o dono pedir "faz o PR da issue <n>" ou "modo criar PR".
---

Você implementa uma issue do assistente-mac e abre o PR. Você entrega o link e para.

## Leia só isto

- A issue e os comentários dela: `gh issue view <n> --comments`. Se houver um passo a passo do revisor de issue, siga-o.
- `CLAUDE.md`, inteiro.
- `CONTRIBUTING.md`, seções "Branches", "Commits", "Pull requests" e "Tamanho do trabalho".
- `preferencias.md`, inteiro, antes da primeira linha de código.
- O código que a issue cita e os testes dele.

## Roteiro

1. Confira o tipo de entrega: código ou só `.md`. Se a issue deixar dúvida, pergunte antes de escrever.
2. Se a issue depender de uma "Decisão em aberto" do `plan.md`, pergunte em vez de escolher.
3. A branch sai da `main` atualizada, com o prefixo do `CONTRIBUTING.md`.
4. Mexa só no que a issue pede. Se não couber num PR, empilhe com `--base`.
5. Rode `ruff check . && pytest`.
6. `git status --short`, depois `git add <caminhos>`. Commit no imperativo, com até 72 caracteres.
7. A descrição tem três partes: **O que muda**, **Por quê** e **Como testar**. Feche a issue com `Closes #<n>`.
8. Entregue o link. Não mescle.
