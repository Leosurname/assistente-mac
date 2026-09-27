# Modos de trabalho

Como o agente trabalha quando o dono pede um modo: "modo revisão de PR",
"revisa a issue 40". Cada modo é um roteiro. As regras do
[CLAUDE.md](CLAUDE.md) e do [CONTRIBUTING.md](CONTRIBUTING.md) continuam
valendo em todos.

Um modo faz só o que o nome diz. Revisar não é implementar: o agente só abre PR
de código quando o dono pedir.

## Revisão de PR

1. Leia o PR e a issue ligada a ele: `gh pr view <n> --comments`, `gh pr diff <n>`.
2. Rode na sua máquina: `gh pr checkout <n>`, depois `ruff check . && pytest`.
3. Confira:
   - **Escopo.** O diff só mexe no que a issue pede, e não traz arquivo que o
     autor não escreveu, como `.pyc` ou sobras de uma base velha.
   - **Regras do `CLAUDE.md`.** A Layla não executa nada, só se mexe no app
     citado e a sobreposição não rouba foco.
   - **[preferencias.md](preferencias.md).** Código curto, comentário com `#` só
     para o porquê, sem docstring e com `if (condicao):`.
   - **Testes.** Descrevem comportamento, a Layla vai mockada e não há rede.
   - **Documentação.** Se o comportamento mudou, o `.md` mudou junto.
4. Comente no PR. Cada achado com `arquivo:linha`, o problema e o porquê.
5. Não aprove, não mescle, não feche.

## Criar PR

1. Parta de uma issue. Sem issue, crie uma antes (veja [Criar issue](#criar-issue)).
2. A branch sai da `main` atualizada, com o prefixo do `CONTRIBUTING.md`.
3. Mexa só no que a issue pede. Se não couber num PR, empilhe com `--base`.
4. Rode `ruff check . && pytest`.
5. Confira o que vai: `git status --short`, depois `git add <caminhos>`. Commit
   no imperativo, com até 72 caracteres.
6. A descrição tem três partes: **O que muda**, **Por quê** e **Como testar**.
   Feche a issue com `Closes #<n>`.
7. Entregue o link e pare.

## Revisar issue

1. Leia a issue e os comentários: `gh issue view <n> --comments`.
2. Confira a issue contra o código da `main`:
   - o que já existe;
   - o que contradiz uma regra do projeto;
   - de quais outras issues ela depende;
   - quais "Decisões em aberto" do [plan.md](plan.md) ela toca.
3. Comente na issue um passo a passo para outro agente executar sem adivinhar:
   - o que a issue não diz e vai travar a execução;
   - as decisões que são do dono, com uma sugestão para cada;
   - a quebra em PRs pequenos, com arquivos, funções e testes;
   - as regras que valem em todo PR.
4. Não implemente. O PR vem quando o dono pedir.

## Criar issue

1. Procure se a issue já existe: `gh issue list --search "<termo>" --state all`.
2. Estruture assim:
   - resumo;
   - como a issue cabe nas regras do projeto;
   - perguntas em aberto;
   - o que fica fora do escopo;
   - critério de pronto;
   - dependências (`Depende de #<n>`).
3. No critério de pronto, use `ruff check . && pytest`, sem `ruff format`.
4. Se a issue não couber num PR, vira uma guarda-chuva com uma lista de issues menores.
5. Ponha label (`enhancement`, `bug`, `documentation`).

## Organizar repositório

1. Levante o que está velho:
   - branches já mescladas: `git branch -r --merged origin/main`;
   - issues resolvidas por PR mesclado que continuam abertas;
   - issues duplicadas;
   - labels sem uso;
   - `.md` que não batem mais com o código.
2. Entregue a lista ao dono com uma sugestão para cada item.
3. Apagar branch, fechar issue ou mexer em label só com autorização, e ela vale
   para os itens citados.
4. Doc desatualizada vira PR `docs/`, como qualquer outro.
