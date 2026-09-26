# Preferências de código

Como escrever código neste projeto. Vale para quem escreve à mão e para
agentes.

## A regra

**Código curto.** Se dá para dizer a mesma coisa com menos, diz com menos.

Isto não é preferência de estilo: código longo esconde o que importa. Um
arquivo de 200 linhas onde 120 são comentário obriga quem revisa a garimpar a
lógica no meio da prosa.

## Comentário

Comente o **porquê**, e só quando ele não estiver no código. O diff já mostra o
quê.

Os comentários devem ser feitos com `#`. Nada de docstring, nem em módulo nem
em função.

```python
# Bom: o motivo não está no código.
# Posição antes de tamanho: o macOS empurra a janela de volta para dentro
# do monitor e desfaz o movimento.

# Ruim: repete a linha de baixo.
# Abre o aplicativo.
abrir(app)
```

Não escreva:

- comentário que narra a linha seguinte;
- comentário em função cujo nome já diz tudo (`def parar()`, `def ocultar()`);
- comentário explicando arquitetura — isso é papel do `ARCHITECTURE.md`;
- comentário de separação (`# --- apoio ---`) em arquivo curto.

Um módulo pode ter uma frase no topo, com `#`, dizendo o que ele faz. Uma frase.

## Tamanho

| Coisa | Limite prático |
|---|---|
| Módulo | 150 linhas |
| Função | 20 linhas |
| Comentário de topo do módulo | 1 a 3 linhas |

Não são regras de linter, são sinais. Passar do limite quer dizer "olhe de
novo", não "está proibido". Se a coisa é mesmo complexa, passe — e o comentário
que explica o porquê aí vale ouro.

## Teste

Teste cobre comportamento, não linha. Prefira poucos testes que descrevem o que
o produto faz a muitos que repetem o mesmo caminho com dados diferentes.

Nome de teste é frase: `test_digitar_faz_sumir_na_hora`. Sem comentário em
cima, porque o nome já é o comentário.

## Documentação

Um assunto, um lugar. A decisão de arquitetura mora no `ARCHITECTURE.md`; o
`README.md` do módulo diz como rodar e o que não é óbvio. Repetir a mesma
explicação nos dois garante que um dos dois vai envelhecer errado.

## Formato

Condição de `if` vai entre parênteses em todo o projeto: `if (condicao):`. Por
isso não se usa `ruff format`: ele tira os parênteses.

## Execução e imports

No backend, todos os outros arquivos fazem as funções; o `main.py` só chama.
Só o `main.py` é executado, e o resto é import pelo nome do outro arquivo:
`from assistente.ambiente import configuracao` → `configuracao.ConfiguracaoLayla`.
Separa tudo em várias pastas e não repita o nome de arquivos.

## Escopo

Mexa só onde foi pedido. O que o pedido não cita, não se toca: sem reformatar
arquivo vizinho, sem "já que estou aqui".

Antes de commitar, olhe o que está indo:

```bash
git status --short
git diff --cached --stat
```

Prefira `git add <caminhos>` a `git add -A`. Um PR de documentação desta
sessão levou 35 binários `.pyc` junto porque ninguém olhou — e o conserto
custou mais que o trabalho original.

Se o diff mostra arquivo que você não escreveu, pare: quase sempre a branch
saiu de uma base velha, e o que parece mudança sua é o resto do repositório
aparecendo como removido.

## Como este arquivo cresce

Preferência nova entra aqui assim que for dita — na conversa, no review, na
reclamação — junto com o trabalho que a originou. Uma linha na seção que já
trata do assunto; se contradiz o que está escrito, troque o texto antigo.
Detalhe de quando escrever: [CLAUDE.md](CLAUDE.md).

## O que isto não quer dizer

Não é licença para nome curto e obscuro, função que faz três coisas, ou
esperteza que economiza cinco linhas e custa dez minutos de leitura. Curto é
meio; o fim é ser fácil de ler.
