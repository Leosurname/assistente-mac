# Camada nativa

O que encosta no macOS: o atalho global, o microfone, a caixa que aparece sobre
a tela e o controle das janelas. A conversa com a Layla mora no backend, em
outro processo.

## Stack: Python com PyObjC

Decisão do dono do projeto, registrada aqui porque ela explica o formato do
código. O projeto fica em uma linguagem só, e a camada nativa reaproveita o
ambiente Python que o backend já exige.

O custo dessa escolha é que todo acesso ao macOS passa por uma ponte, e erro
de ponte aparece como `None` silencioso em vez de erro de compilação. A defesa
é a divisão abaixo.

## Como o código está dividido

O que dá para testar sem macOS fica separado do que não dá:

| Módulo | Toca o macOS? | O que faz |
|---|---|---|
| `dispensa.py` | não | As três regras de sumiço da caixa |
| `regioes.py` | não | Nome de região vira retângulo em pixels |
| `protocolo.py` | não | Monta o pedido, lê a resposta do backend |
| `configuracao.py` | não | Variáveis de ambiente |
| `coordenador.py` | não | O fluxo inteiro, com tudo injetado |
| `atalho.py` | sim | Event tap do Quartz: Option+9 e digitação |
| `sobreposicao.py` | sim | O `NSPanel` que não rouba foco |
| `voz.py` | sim | `SFSpeechRecognizer` + `AVAudioEngine` |
| `janelas.py` | sim | `NSWorkspace` e a API de acessibilidade |
| `busca.py` | sim | Acha o aplicativo e a janela pelo nome |
| `contexto.py` | sim | O retrato da tela |
| `cliente.py` | sim (thread) | WebSocket com o backend |

Os cinco primeiros cobrem o comportamento do produto e têm teste. O
`coordenador.py` recebe caixa, microfone, executor, relógio e envio por
parâmetro — é o que permite testar do atalho até a caixa sumindo sem abrir
janela, sem microfone e sem backend no ar.

## Decisões que valem explicação

**A caixa não rouba foco.** `NSWindowStyleMaskNonactivatingPanel`,
`canBecomeKeyWindow` devolvendo falso e `orderFrontRegardless` em vez de
`makeKeyAndOrderFront`. Se isso quebrar, o produto quebra junto: é a digitação
no aplicativo de baixo que serve de sinal para a caixa sumir.

**O atalho é consumido, a digitação não.** O event tap devolve `None` para o
`Option + 9`, senão o caractere `ª` seria digitado no aplicativo da frente.
Qualquer outra tecla passa adiante intacta.

**O atalho com a caixa aberta não fecha a caixa.** Ele reinicia a escuta. Um
atalho que alterna faria o usuário apertar duas vezes por engano e perder o
pedido que estava falando.

**Nada expira enquanto se fala ou enquanto o backend pensa.** Os 5 segundos só
começam a contar depois de "concluído". A Layla local pode demorar, e sumir no
meio deixaria o usuário sem resposta e com as janelas mexendo depois.

**Resposta atrasada é descartada.** Se a caixa já sumiu quando a resposta
chega, as ações não são executadas. O usuário voltou ao trabalho; mexer nas
janelas agora seria pior que não fazer nada.

**`apps_instalados` sai daqui.** O backend não lê `/Applications` — não deve
tocar no disco do usuário — então quem diz o que existe na máquina é esta
camada.

**Posição antes de tamanho.** Ao posicionar, a posição é aplicada primeiro: se
a janela for maior que a área de destino, redimensionar antes faz o macOS
empurrá-la de volta para dentro do monitor e desfazer o movimento.

## Coordenadas

A API de acessibilidade usa origem no canto superior esquerdo, com y crescendo
para baixo. O AppKit usa origem embaixo. A conversão acontece em
`contexto.area_util()`, e daí para a frente tudo é coordenada de acessibilidade
— inclusive o que vai no retrato da tela para o backend.

A área usada é a `visibleFrame`, não o monitor inteiro: a barra de menu e o
Dock ficam de fora.

## Rodando

```bash
cd app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m assistente_app
```

Precisa do backend no ar (`ASSISTENTE_BACKEND`, padrão
`ws://127.0.0.1:8765/ws`) e das três permissões do macOS: Acessibilidade,
Microfone e Reconhecimento de Fala.

Sem Acessibilidade, o event tap não é criado e o aplicativo sai com erro
explicando o que fazer. É a falha mais comum na primeira execução.

## Verificação

```bash
cd app
ruff format . && ruff check . && pytest
```

Nenhum teste abre janela, liga microfone ou usa rede.

## Variáveis de ambiente

| Variável | Padrão | Para quê |
|---|---|---|
| `ASSISTENTE_BACKEND` | `ws://127.0.0.1:8765/ws` | Endereço do backend |
| `ASSISTENTE_TIMEOUT_CAIXA` | `5` | Segundos até a caixa sumir |
| `ASSISTENTE_IDIOMA` | `pt-BR` | Idioma do reconhecimento de fala |
| `ASSISTENTE_FALAR` | ligado | Falar a resposta em voz alta |

## O que não está aqui

Empacotar isso como um `.app` de verdade. Hoje roda por `python -m`, o que
basta para desenvolver, mas um aplicativo distribuível precisa de bundle,
assinatura e `Info.plist` com as descrições de uso do microfone — sem elas o
macOS nega a permissão sem perguntar.
