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

## Organização

```
assistente/
  configuracao.py     leitura das variaveis de ambiente
  layla/
    interface.py      Mensagem, ClienteDeLLM, corte de contexto, formato_json
    cliente.py        ClienteLayla: HTTP, streaming, novas tentativas
    erros.py          erros com mensagem pronta para o usuario
```

O resto do backend depende de `ClienteDeLLM`, nunca de `ClienteLayla`. Trocar de
provedor é escrever outra implementação do protocolo.

## Rodando os testes

Da raiz do repositório:

```bash
ruff format . && ruff check . && pytest
```

A Layla é sempre de mentira nos testes: um `httpx.MockTransport` intercepta o
pedido dentro do processo (`backend/tests/apoio.py`). Nenhum teste abre conexão.
