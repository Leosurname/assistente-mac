# Arquitetura

## Visão geral

O sistema tem duas peças que rodam na máquina do usuário:

```
   ┌──────────────────────────────────────────┐
   │  Camada nativa (macOS)                   │
   │                                          │
   │  atalho global  ──▶ microfone            │
   │        │              │                  │
   │        ▼              ▼                  │
   │     sobreposição  transcrição            │
   │        ▲              │                  │
   │        │              ▼                  │
   │     executor  ◀── ações                  │
   │     de janelas                           │
   └───────────┬──────────────────────────────┘
               │  WebSocket (localhost)
   ┌───────────▼──────────────────────────────┐
   │  Backend (Python)                        │
   │                                          │
   │  sessão ──▶ montagem do prompt           │
   │                   │                      │
   │                   ▼                      │
   │            cliente Layla ──▶ LLM         │
   │                   │                      │
   │                   ▼                      │
   │            validação das ações           │
   └──────────────────────────────────────────┘
```

## Por que duas peças

Atalho global, captura de microfone, janela sem foco e manipulação de outras
janelas são todas APIs nativas do macOS. Conversar com um modelo de linguagem,
montar prompt e validar resposta é trabalho de servidor comum.

Separar as duas deixa o backend testável sem tocar no sistema operacional: dá
para exercitar toda a tradução de "quero terminal e Safari" em ações mandando
texto por WebSocket, sem microfone e sem janela nenhuma.

## Camada nativa

Responsável por tudo que encosta no macOS.

**Atalho global.** `Option + 9` registrado no sistema inteiro, via
`NSEvent.addGlobalMonitorForEvents` ou a API de `HotKey` do Carbon. Precisa
funcionar com qualquer aplicativo em foco.

**Sobreposição.** Um `NSPanel` com `.nonactivatingPanel`, nível
`.floating`, sem barra de título. O detalhe que importa: ele **não pode roubar
o foco**. O usuário continua digitando no aplicativo de baixo, e é essa
digitação que serve de sinal para a caixa sumir.

**Regras de desaparecimento.** Três gatilhos, o que vier primeiro:
- temporizador de 5 segundos, reiniciado a cada novo pedido;
- monitor global de teclado detectando digitação no aplicativo de baixo;
- `Esc`.

**Transcrição.** Microfone via `AVAudioEngine`, reconhecimento por
`SFSpeechRecognizer` com resultados parciais, para que o texto apareça na caixa
enquanto o usuário fala. O fim da fala é detectado por silêncio.

**Executor de janelas.** Abertura de aplicativos por `NSWorkspace`, e
posicionamento pela API de acessibilidade (`AXUIElement`, atributos
`kAXPositionAttribute` e `kAXSizeAttribute`). Exige permissão de
Acessibilidade concedida pelo usuário.

**Coletor de contexto.** Antes de mandar o pedido, monta um retrato da tela:
aplicativos rodando, janelas visíveis com posição e tamanho, resolução e
quantidade de monitores. Sem isso a Layla não tem como decidir o que abrir e o
que já está aberto.

## Backend (Python)

Responsável por transformar uma frase em uma lista de ações.

**Sessão.** Guarda o histórico da conversa por um curto período, para que
"agora joga o Safari pra direita" logo depois do primeiro pedido faça sentido.
A sessão expira junto com a caixa.

**Montagem do prompt.** Junta a transcrição, o retrato da tela e o catálogo de
ações disponíveis, e pede à Layla uma resposta estruturada.

**Cliente Layla.** Isolado atrás de uma interface própria, para que trocar de
provedor não espalhe mudança pelo resto do código. Configuração por variável de
ambiente. Detalhes na issue de integração.

**Validação.** A resposta da Layla nunca vai direto para o executor. O backend
confere que cada ação está no catálogo, que os aplicativos citados existem e
que as coordenadas cabem na tela. Ação inválida é descartada, e o backend diz
o que não entendeu em vez de executar um palpite.

## O contrato entre as duas peças

A camada nativa manda um pedido:

```json
{
  "tipo": "pedido",
  "texto": "quero terminal e safari, e já deixa o claude code aberto",
  "tela": {
    "monitores": [{ "largura": 3456, "altura": 2234 }],
    "apps_abertos": ["Finder", "Safari"],
    "janelas": [
      { "app": "Safari", "x": 100, "y": 80, "largura": 1200, "altura": 900 }
    ]
  }
}
```

O backend responde com ações:

```json
{
  "tipo": "acoes",
  "acoes": [
    { "acao": "abrir_app", "app": "Terminal" },
    { "acao": "abrir_app", "app": "Claude Code" },
    { "acao": "posicionar", "app": "Terminal", "regiao": "metade_esquerda" },
    { "acao": "posicionar", "app": "Safari", "regiao": "metade_direita" }
  ],
  "fala": "concluído"
}
```

O catálogo de ações começa pequeno e cresce conforme a necessidade:
`abrir_app`, `fechar_app`, `posicionar`, `focar`, `minimizar`.

## Princípio de segurança

A Layla descreve o que quer, não faz. Toda ação passa por um catálogo fechado e
por validação antes de tocar no sistema. Não existe caminho em que um texto
vindo do modelo vira comando de shell ou chamada arbitrária de API.

Vale o mesmo para o que o microfone captura: é entrada de usuário, tratada como
dado, nunca como instrução para o backend.
