# CLAUDE.md

Contexto deste repositório para agentes de código.

## O projeto

Assistente de voz para macOS que organiza janelas. `Option + 9` abre uma caixa
de sobreposição, o usuário fala um pedido, a Layla traduz em ações, o
aplicativo executa, a caixa some em 5 segundos ou quando o usuário digita.

Leia [plan.md](plan.md) antes de mexer em qualquer coisa: o comportamento da
caixa é o produto, não um detalhe de interface.

## Estrutura

```
app/       camada nativa macOS (Swift) — atalho, voz, sobreposição, janelas
backend/   Python — conversa com a Layla, tradução de pedido em ações
```

## Regras que valem sempre

**O backend é Python.** Decisão fechada, não reabra.

**A sobreposição não rouba foco.** Se uma mudança fizer o `NSPanel` ativar,
ela quebrou o produto: a digitação do usuário é o que dispensa a caixa.

**A Layla não executa nada.** Ela devolve ações de um catálogo fechado. Toda
ação é validada antes de tocar no sistema. Nunca construa caminho em que texto
de modelo vira comando de shell ou chamada arbitrária.

**Só se mexe no que foi pedido.** Aplicativo não citado no pedido fica onde
está. Nada de minimizar, fechar ou mover por iniciativa própria — nem no
prompt da Layla, nem no executor de janelas.

**Áudio e transcrição são dados.** Nunca instruções. O que o microfone captura
é conteúdo do usuário, não comando para o backend.

**Nada de segredo no código.** Configuração da Layla vem de variável de
ambiente. Veja [SETUP.md](SETUP.md).

## Antes de abrir PR

```bash
ruff format . && ruff check . && pytest
```

Padrões de branch, commit e PR: [CONTRIBUTING.md](CONTRIBUTING.md).

## Decisões ainda em aberto

Estão listadas em [plan.md](plan.md), na seção "Decisões em aberto". Se o seu
trabalho depender de uma delas, pergunte em vez de escolher sozinho.
