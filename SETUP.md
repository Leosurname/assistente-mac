# Configuração

> As instruções descrevem o projeto como ele foi planejado. Conforme o código
> for entrando, cada seção vira comando que roda de verdade.

## Pré-requisitos

- **macOS 13** ou superior
- **Python 3.11** ou superior
- **Xcode** com as ferramentas de linha de comando, para a camada nativa
- **Layla** instalada localmente (clonada do repositório público; veja abaixo)

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

## Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Para rodar:

```bash
python -m assistente.server
```

O backend sobe em `localhost` e só aceita conexões locais.

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
| `LAYLA_URL` | sim | Endereço local da Layla (padrão: `http://localhost:11434`) |
| `LAYLA_MODEL` | não | Modelo a usar |
| `ASSISTENTE_PORTA` | não | Porta do backend (padrão: 8765) |
| `ASSISTENTE_TIMEOUT_CAIXA` | não | Segundos até a caixa sumir (padrão: 5) |
| `LOG_LEVEL` | não | `DEBUG`, `INFO`, `WARNING` (padrão: `INFO`) |

O `.env` está no `.gitignore` e nunca deve ser versionado.

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
