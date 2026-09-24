# Configuração

> As instruções descrevem o projeto como ele foi planejado. Conforme o código
> for entrando, cada seção vira comando que roda de verdade.

## Pré-requisitos

- **macOS 13** ou superior
- **Python 3.11** ou superior
- **Xcode** com as ferramentas de linha de comando, para a camada nativa
- **`llama.cpp`** compilado, com o `llama-server` disponível
- **Pesos da Layla** em formato GGUF, baixados do HuggingFace (veja abaixo)

## Permissões do macOS

O assistente não funciona sem estas três, concedidas em
**Ajustes do Sistema ▸ Privacidade e Segurança**:

| Permissão | Para quê |
|---|---|
| Acessibilidade | Mover e redimensionar janelas de outros aplicativos |
| Microfone | Ouvir o pedido |
| Reconhecimento de Fala | Transcrever o que foi falado |

Na primeira execução o sistema pergunta. Se você negar por engano, precisa
conceder na mão nos Ajustes — o macOS não pergunta de novo.

## A Layla

A Layla não é um servidor próprio: é um conjunto de pesos em formato **GGUF**
publicados em [huggingface.co/l3utterfly](https://huggingface.co/l3utterfly).
Quem serve esses pesos é o `llama-server` do
[llama.cpp](https://github.com/ggml-org/llama.cpp), rodando na sua máquina.

### 1. Instale o llama.cpp

```bash
brew install llama.cpp
```

Ou compile do código-fonte, se preferir controlar as opções de build.

### 2. Baixe os pesos

O modelo recomendado é o `mistral-7b-v0.1-layla-v4-chatml`, quantizado em
`Q4_K_M`. É o fine-tune layla mais capaz em formato ChatML, que é o que lida
melhor com conversa estruturada.

```bash
mkdir -p ~/modelos
huggingface-cli download l3utterfly/mistral-7b-v0.1-layla-v4-chatml-gguf \
  mistral-7b-v0.1-layla-v4-chatml-Q4_K_M.gguf \
  --local-dir ~/modelos
```

Alternativa leve, para quem quiser menos latência em troca de menos
capacidade: `l3utterfly/Qwen1.5-1.8B-layla-v4-gguf`.

### 3. Suba o servidor

```bash
llama-server \
  --model ~/modelos/mistral-7b-v0.1-layla-v4-chatml-Q4_K_M.gguf \
  --host 127.0.0.1 --port 8080 \
  --ctx-size 4096
```

O `llama-server` expõe uma API compatível com a da OpenAI em
`http://localhost:8080/v1/chat/completions`, com streaming por SSE. É por aí
que o backend fala com a Layla. Não há chave de API: o servidor é local.

Para conferir que subiu:

```bash
curl http://localhost:8080/v1/models
```

### Por que a saída é restrita a um esquema

Os fine-tunes layla são voltados a conversa e roleplay, não a saída
estruturada. Pedir JSON no texto do prompt e torcer dá errado com frequência, e
o backend depende de uma lista de ações bem formada.

Por isso o backend manda o campo `response_format` com um `json_schema` em todo
pedido de tradução: o `llama-server` deriva uma gramática do esquema e restringe
a decodificação, de modo que a resposta é sempre um JSON válido no formato do
catálogo de ações. O esquema fica no código do backend, junto da montagem do
prompt.

Formato garantido não é sentido garantido. A validação do lado do backend
continua valendo: catálogo fechado, aplicativos que existem, coordenadas que
cabem na tela e a regra de não mexer em aplicativo que não foi pedido.

## Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Para rodar:

```bash
python -m assistente.servidor
```

O backend sobe em `127.0.0.1` e recusa qualquer conexão que não venha da
própria máquina. O WebSocket fica em `ws://127.0.0.1:8765/ws` e o health check
em `http://127.0.0.1:8765/health`.

## Camada nativa

```bash
cd app
open AssistenteMac.xcodeproj
```

Compile e rode pelo Xcode. O aplicativo vive na barra de menu, sem ícone no
Dock.

## Variáveis de ambiente

Copie o modelo e preencha:

```bash
cp .env.example .env
```

| Variável | Obrigatória | Para quê |
|---|---|---|
| `LAYLA_URL` | não | Endereço do `llama-server` (padrão: `http://127.0.0.1:8080`) |
| `LAYLA_MODEL` | não | Nome do modelo a pedir ao servidor |
| `LAYLA_TIMEOUT` | não | Segundos de espera por resposta (padrão: 30) |
| `LAYLA_TENTATIVAS` | não | Tentativas antes de desistir (padrão: 3) |
| `LAYLA_LIMITE_CONTEXTO` | não | Tokens de contexto (padrão: 4096) |
| `LAYLA_TEMPERATURA` | não | Temperatura da geração (padrão: 0.2) |
| `ASSISTENTE_PORTA` | não | Porta do backend (padrão: 8765) |
| `ASSISTENTE_VALIDADE_SESSAO` | não | Segundos de vida da sessão (padrão: 120) |
| `ASSISTENTE_TIMEOUT_CAIXA` | não | Segundos até a caixa sumir (padrão: 5) |
| `LOG_LEVEL` | não | `DEBUG`, `INFO`, `WARNING` (padrão: `INFO`) |

O `.env` está no `.gitignore` e nunca deve ser versionado. Nenhuma dessas
variáveis carrega segredo: a Layla roda no `localhost` e não pede chave.

## Antes do primeiro teste

```bash
python scripts/diagnostico.py
```

Confere as quatro coisas que precisam estar de pé: o `llama-server` no ar com
modelo carregado, a decodificação restrita respeitando o `json_schema`, o
backend respondendo, e a permissão de Acessibilidade concedida.

A segunda é a que importa mais. Todo o desenho do backend aposta que o
`llama-server` devolve JSON válido quando recebe um esquema — os fine-tunes da
Layla são feitos para conversa, não para saída estruturada. Se essa checagem
falhar, a estratégia precisa mudar antes de qualquer outra coisa.

## Verificando que funcionou

1. Suba o backend. Ele deve responder em `http://localhost:8765/health`.
2. Rode o aplicativo. O ícone aparece na barra de menu.
3. Aperte `Option + 9` em qualquer lugar. A caixa deve aparecer.
4. Não faça nada por 5 segundos. A caixa deve sumir sozinha.

Se o passo 3 falhar, quase sempre é permissão de Acessibilidade faltando.

## Problemas comuns

**A caixa não aparece.** Outro aplicativo pode ter tomado o `Option + 9`.
Verifique em Ajustes do Sistema ▸ Teclado ▸ Atalhos de Teclado.

**A caixa aparece mas as janelas não se movem.** Falta permissão de
Acessibilidade. Depois de conceder, reinicie o aplicativo — o macOS só relê a
permissão na inicialização.

**A transcrição fica vazia.** Confira o microfone de entrada nos Ajustes de Som
e a permissão de Reconhecimento de Fala.
