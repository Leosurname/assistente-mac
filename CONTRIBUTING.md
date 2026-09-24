# Contribuindo

## Fluxo

1. Uma issue descreve o trabalho antes de ele começar.
2. Uma branch por issue, saindo de `main`.
3. Um PR por branch, referenciando a issue.
4. `main` é protegida: nada entra direto, só por PR.

## Branches

```
docs/     documentação
feat/     funcionalidade nova
fix/      correção
refactor/ mudança sem alteração de comportamento
chore/    build, dependências, configuração
```

Exemplo: `feat/atalho-global`.

## Commits

Primeira linha no imperativo, até 72 caracteres, sem ponto final:

```
Adiciona atalho global Option+9
```

Se o porquê não for óbvio pelo diff, explique no corpo. O diff já mostra o
*o quê*; o corpo serve para o *por quê*.

Feche issues pelo PR, não pelo commit: `Closes #1` na descrição do PR.

## Pull requests

Uma descrição de PR responde a três coisas:

- **O que muda** — resumo em uma ou duas frases
- **Por quê** — a issue, e o que ela pedia
- **Como testar** — passos concretos, não "rode e veja"

PR grande demais para revisar de uma sentada deve ser quebrado. O limite
prático é o que o revisor consegue ler com atenção.

## Python

- Formatação com `ruff format`, verificação com `ruff check`
- Tipagem nas funções públicas
- Testes com `pytest`; a Layla sempre mockada nos testes
- Nada de chamada de rede em teste

Antes de abrir o PR:

```bash
ruff format . && ruff check . && pytest
```

## Swift

- Formatação com `swift-format`
- Nada de `print` no código final; use o `Logger` do sistema

## O que nunca entra no repositório

- `.env`, chaves de API, tokens
- Gravações de áudio ou transcrições reais
- Caminhos absolutos da máquina de quem escreveu

## Documentação

Mudou o comportamento, atualize o `.md` correspondente no mesmo PR.
Documentação desatualizada é pior que documentação ausente: ela mente com
confiança.
