# Assistente Mac

Um assistente de voz que organiza a tela do seu Mac.

Aperte `Option + 9`, fale o que você quer — *"terminal e Safari, e já deixa o
Claude Code aberto"* — e as janelas se arrumam sozinhas. A caixa some depois de
5 segundos, ou assim que você voltar a digitar.

> **Status:** em construção. Nenhuma etapa foi implementada ainda; o que existe
> por enquanto é a documentação.
>
> **Beta:** só texto. O pedido chega digitado; voz vem depois da beta.

## Como funciona

1. `Option + 9` — uma caixa de texto aparece sobre a tela, sem tirar o foco
   do que você estava fazendo.
2. Você manda o pedido. Na beta ele é digitado; depois dela, você fala e a
   transcrição aparece na caixa em tempo real.
3. A [Layla](docs/) interpreta o pedido e devolve uma lista de ações.
4. O assistente abre os aplicativos, posiciona as janelas e responde
   "concluído".
5. A caixa some sozinha: 5 segundos sem pedido novo, ou quando você digita, ou
   com `Esc`.

O detalhamento do produto está em [plan.md](plan.md).

## Estrutura

| Parte | Linguagem | Responsabilidade |
|---|---|---|
| Camada nativa | Python com PyObjC | Atalho global, caixa, controle de janelas (microfone depois da beta) |
| Backend | Python | Conversa com a Layla, tradução de pedido em ações |

A divisão e o porquê dela estão em [ARCHITECTURE.md](ARCHITECTURE.md).

## Começando

Pré-requisitos, instalação e variáveis de ambiente: [SETUP.md](SETUP.md).

## Contribuindo

Padrões de branch, commit e PR: [CONTRIBUTING.md](CONTRIBUTING.md).

## Requisitos do sistema

- macOS 13 ou superior
- Python 3.11 ou superior
- Permissão de **Acessibilidade**
- **Microfone** e **Reconhecimento de fala** só depois da beta, na fase de voz
