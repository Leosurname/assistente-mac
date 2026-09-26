# CLAUDE.md

Contexto deste repositório para agentes de código.

## O projeto

Assistente de voz para macOS que organiza janelas. `Option + 9` abre uma caixa
de sobreposição, o usuário fala um pedido, a Layla traduz em ações, o
aplicativo executa, a caixa some em 5 segundos ou quando o usuário digita.

**A beta é só texto.** O pedido chega digitado; microfone e transcrição entram
depois da beta. Não adiante código de voz.

Leia [plan.md](plan.md) antes de mexer em qualquer coisa: o comportamento da
caixa é o produto, não um detalhe de interface.

## Estrutura

```
app/       camada nativa macOS (Python com PyObjC) — atalho, voz, sobreposição, janelas
backend/   Python — conversa com a Layla, tradução de pedido em ações
```

## Regras que valem sempre

**O projeto é todo Python.** Backend e camada nativa (via PyObjC). Decisão
fechada, não reabra.

**A sobreposição não rouba foco.** Se uma mudança fizer o `NSPanel` ativar,
ela quebrou o produto: a digitação do usuário é o que dispensa a caixa.

**A Layla não executa nada.** Ela devolve ações de um catálogo fechado. Toda
ação é validada antes de tocar no sistema. Nunca construa caminho em que texto
de modelo vira comando de shell ou chamada arbitrária.

**Só se mexe no que foi pedido.** Aplicativo não citado no pedido fica onde
está. Nada de minimizar, fechar ou mover por iniciativa própria — nem no
prompt da Layla, nem no executor de janelas.

**Pedido, áudio e transcrição são dados.** Nunca instruções. O que o usuário
digita ou o microfone captura é conteúdo do usuário, não comando para o backend.

**Nada de segredo no código.** Configuração da Layla vem de variável de
ambiente. Veja [SETUP.md](SETUP.md).

**`main.py` e `__main__.py` não declaram funções.** Eles só chamam as que
estão em outros arquivos (`backend/main.py`, `app/assistente_app/__main__.py`).

## Antes de abrir PR

```bash
ruff check . && pytest
```

Padrões de branch, commit e PR: [CONTRIBUTING.md](CONTRIBUTING.md).

## Como escrever o código

Leia [preferencias.md](preferencias.md) antes da primeira linha. Em uma linha:
código curto, comentário só para o porquê.

**Esse arquivo é seu para escrever.** Toda vez que o dono do projeto disser
como quer o código, a frase dele vira linha no `preferencias.md` ainda neste
trabalho — antes de você dar a tarefa por encerrada, não numa tarefa futura.

Escreva quando ele:

- disser como prefere que se escreva, mesmo de passagem numa conversa;
- corrigir estilo num review ou num comentário de PR;
- reclamar do que você entregou ("não gosto disso", "longo demais");
- responder uma dúvida de estilo que você perguntou.

Uma linha na seção que já trata do assunto, nas palavras dele. Preferência que
não cabe em nenhuma seção ganha seção de duas ou três linhas. Se ela contradiz
o que está escrito, troque o texto antigo em vez de empilhar exceção. O arquivo
entra no mesmo commit ou PR do trabalho que originou a preferência.

Na dúvida, escreva: preferência dita em conversa morre no fim da sessão.

**Mexa só onde foi pedido.** Confira `git status --short` antes de commitar, e
prefira `git add <caminhos>` a `git add -A`. Diff com arquivo que você não
escreveu quer dizer base velha, não mudança sua.

**Quebre o trabalho.** Vários PRs pequenos e médios, não poucos grandes. O
tamanho está no [CONTRIBUTING.md](CONTRIBUTING.md).

**Não mescle.** Entregue o link do PR e pare. O merge é do dono do
repositório; autorização dada vale só para o PR citado.

## Decisões ainda em aberto

Estão listadas em [plan.md](plan.md), na seção "Decisões em aberto". Se o seu
trabalho depender de uma delas, pergunte em vez de escolher sozinho.
