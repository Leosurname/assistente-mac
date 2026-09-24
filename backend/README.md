# Backend

Transforma uma frase em uma lista de ações. Fala com a Layla, valida o que ela
devolve e responde à camada nativa.

## A Layla, concretamente

A Layla é um conjunto de pesos **GGUF** publicados em
[huggingface.co/l3utterfly](https://huggingface.co/l3utterfly) — os fine-tunes
`mistral-7b-v0.1-layla-v4-chatml-gguf`, `Qwen1.5-1.8B-layla-v4-gguf` e
`phi-2-layla-v1-chatml-gguf`. Ela não é um servidor: quem serve os pesos é o
`llama-server` do llama.cpp, rodando local.

O que isso significa para o código:

- A conversa é um `POST` em `{LAYLA_URL}/v1/chat/completions`, na API
  compatível com a da OpenAI. O streaming é o SSE de sempre: linhas `data:` com
  um JSON por pedaço, encerradas por `data: [DONE]`.
- A porta padrão é **8080**, a do `llama-server`. Não 11434, que é do Ollama.
- Não há autenticação. O servidor está no `localhost` e não pede chave, então
  não existe segredo a guardar nem a vazar.
- O health check do provedor é um `GET` em `/v1/models`.

Instalação e comando de subida do servidor: [../SETUP.md](../SETUP.md).

## Por que a saída é restrita a um esquema

Os fine-tunes layla são treinados para conversa e roleplay, não para saída
estruturada. Pedir JSON no prompt e torcer erra formato com frequência, e o
backend depende de uma lista de ações bem formada para validar.

Por isso o cliente aceita um `response_format` com `json_schema`
(`assistente.layla.formato_json`). O `llama-server` deriva uma gramática do
esquema e restringe a decodificação: a resposta é sempre um JSON válido.

Isso garante formato, não sentido. A validação do backend continua obrigatória.

## A stack: FastAPI com uvicorn

O `ARCHITECTURE.md` pede duas coisas: um WebSocket no `localhost` e um health
check ao lado. FastAPI entrega as duas no mesmo aplicativo e o `TestClient`
exercita o WebSocket dentro do processo, sem abrir porta — que é o que permite
testar o contrato inteiro sem microfone, sem janela e sem rede.

As alternativas consideradas:

- **`websockets` puro.** Faria o WebSocket, mas o health check viraria um
  segundo servidor. Duas coisas para subir e monitorar em vez de uma.
- **Flask ou Django.** Servem HTTP bem, mas o WebSocket entra por extensão, e o
  cliente da Layla já é `async`. Uma ponte entre síncrono e assíncrono no meio
  do caminho de 3 segundos do produto é latência comprada sem necessidade.

`uvicorn` porque é o servidor ASGI que o FastAPI assume, e `websockets` como o
transporte que ele usa para falar WebSocket.

## O caminho de um pedido

```
pedido (WebSocket)
   │
   ├─ tela.py        le e confere o retrato da tela
   ├─ sessao.py      recupera o historico curto
   ├─ prompt.py      junta transcricao, retrato e catalogo
   ├─ layla/         manda para a Layla com json_schema
   ├─ validacao.py   filtra o que voltou
   └─ resposta: {"tipo": "acoes", "acoes": [...], "fala": "..."}
```

## A validação, em quatro perguntas

1. **A ação está no catálogo?** `abrir_app`, `fechar_app`, `posicionar`,
   `focar`, `minimizar`. Só. E a ação aprovada é reconstruída campo a campo, de
   modo que nada que a Layla tenha inventado a mais chega ao executor.
2. **O aplicativo existe?** Responde o campo `apps_instalados` do retrato. Não
   dá para usar a lista de abertos: `abrir_app` existe justamente para o que
   ainda não está aberto. Sem `apps_instalados`, a checagem fica com a camada
   nativa, que é quem enxerga `/Applications`.
3. **As coordenadas cabem na tela?** Quando vêm coordenadas, elas precisam
   caber inteiras em algum monitor. Janela fora da tela é janela perdida.
4. **O aplicativo foi citado no pedido?** A que mais protege. O retrato da tela
   diz o que já existe, não o que está errado. O Spotify que está tocando e não
   foi mencionado continua tocando, onde estava.

A quarta pergunta olha o histórico da sessão inteira, e não só o pedido de
agora: "agora joga o Safari pra direita" vem depois de um pedido em que o
Safari foi citado. A comparação ignora acento e caixa, e conhece apelidos
(`vscode` para `Visual Studio Code`, `chrome` para `Google Chrome`).

## Sessões

Uma sessão guarda os últimos 6 turnos e vale 120 segundos, configuráveis por
`ASSISTENTE_VALIDADE_SESSAO`. Ela expira junto com a caixa de sobreposição,
porque o produto é uma caixa que some sozinha: guardar conversa além disso é
lembrar de algo que o usuário já considerou encerrado. A camada nativa também
pode encerrá-la na mão, mandando `{"tipo": "encerrar", "sessao": "..."}`.

## Só conexão local

O servidor escuta em `127.0.0.1` e recusa, com o código 1008, qualquer
WebSocket que não venha da própria máquina. Ele mexe nas janelas do usuário:
não existe motivo para alguém de fora alcançar isso.

## Organização

```
assistente/
  configuracao.py     leitura das variaveis de ambiente
  servidor.py         FastAPI: WebSocket /ws e health check /health
  tradutor.py         pedido em texto, acoes validadas na saida
  prompt.py           montagem do prompt
  acoes.py            catalogo fechado e JSON Schema da resposta
  validacao.py        as quatro perguntas
  tela.py             leitura do retrato da tela
  sessao.py           historico curto, expira junto com a caixa
  registro.py         logs
  layla/
    interface.py      Mensagem, ClienteDeLLM, corte de contexto, formato_json
    cliente.py        ClienteLayla: HTTP, streaming, novas tentativas
    erros.py          erros com mensagem pronta para o usuario
```

O resto do backend depende de `ClienteDeLLM`, nunca de `ClienteLayla`. Trocar de
provedor é escrever outra implementação do protocolo.

## Rodando

```bash
cd backend && python -m assistente.servidor
```

Logs em `LOG_LEVEL`. A transcrição não entra em log fora do `DEBUG`: o que o
usuário fala é conteúdo dele, e arquivo de log é o jeito mais fácil de vazar
isso sem querer.

## Rodando os testes

Da raiz do repositório:

```bash
ruff format . && ruff check . && pytest
```

A Layla é sempre de mentira nos testes: o cliente HTTP é interceptado por um
`httpx.MockTransport` (`backend/tests/apoio.py`) e as rotas recebem um
`ClienteDeLLM` falso que devolve o que o teste mandar. Nenhum teste abre
conexão — rodar com a máquina offline dá o mesmo resultado.
