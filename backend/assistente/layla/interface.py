"""Contrato entre o backend e o provedor de modelo de linguagem.

O resto do backend depende so deste modulo. Trocar a Layla por outro provedor
significa escrever outra implementacao de `ClienteDeLLM`, sem tocar em quem
monta prompt ou valida acoes.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterable, Sequence
from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable

Papel = Literal["sistema", "usuario", "assistente"]

# Traducao dos nomes em portugues para os nomes que a API compativel com a
# OpenAI exige no corpo do pedido.
PAPEL_PARA_API: dict[Papel, str] = {
    "sistema": "system",
    "usuario": "user",
    "assistente": "assistant",
}

# Uma estimativa grosseira serve: o objetivo e cortar historico antes de
# estourar a janela do modelo, nao contar token por token.
CARACTERES_POR_TOKEN = 4


@dataclass(frozen=True)
class Mensagem:
    """Uma fala do historico da conversa."""

    papel: Papel
    conteudo: str

    def para_api(self) -> dict[str, str]:
        return {"role": PAPEL_PARA_API[self.papel], "content": self.conteudo}

    @property
    def tokens_estimados(self) -> int:
        return max(1, len(self.conteudo) // CARACTERES_POR_TOKEN)


def estimar_tokens(mensagens: Iterable[Mensagem]) -> int:
    """Soma a estimativa de tokens de um conjunto de mensagens."""
    return sum(mensagem.tokens_estimados for mensagem in mensagens)


def limitar_contexto(
    mensagens: Sequence[Mensagem], limite_tokens: int
) -> list[Mensagem]:
    """Corta o historico para caber no limite, preservando o essencial.

    As mensagens de sistema ficam sempre, porque sao elas que carregam o
    catalogo de acoes e as regras. O que se perde e o historico mais antigo: em
    uma conversa de caixa de sobreposicao, o pedido de agora vale mais do que o
    de tres pedidos atras.
    """
    sistema = [m for m in mensagens if m.papel == "sistema"]
    conversa = [m for m in mensagens if m.papel != "sistema"]

    orcamento = limite_tokens - estimar_tokens(sistema)
    if orcamento <= 0:
        # Nem o sistema cabe. Mandar so ele ainda e melhor do que mandar nada:
        # quem decide o que fazer com um limite apertado demais e o modelo.
        return list(sistema)

    mantidas: list[Mensagem] = []
    for mensagem in reversed(conversa):
        custo = mensagem.tokens_estimados
        if custo > orcamento:
            break
        orcamento -= custo
        mantidas.append(mensagem)

    mantidas.reverse()
    return [*sistema, *mantidas]


def formato_json(nome: str, esquema: dict[str, object]) -> dict[str, object]:
    """Monta o `response_format` que obriga o modelo a devolver aquele esquema.

    Os fine-tunes layla sao treinados para conversa, nao para saida estruturada:
    pedir JSON no texto do prompt e torcer da errado com frequencia. O
    `llama-server` sabe restringir a decodificacao a uma gramatica derivada de um
    JSON Schema, e e isso que garante que a resposta seja sempre analisavel.
    """
    return {
        "type": "json_schema",
        "json_schema": {"name": nome, "strict": True, "schema": esquema},
    }


@runtime_checkable
class ClienteDeLLM(Protocol):
    """O que o backend espera de qualquer provedor de modelo de linguagem."""

    async def conversar(
        self,
        mensagens: Sequence[Mensagem],
        *,
        temperatura: float | None = None,
        maximo_de_tokens: int | None = None,
        formato_resposta: dict[str, object] | None = None,
    ) -> str:
        """Devolve a resposta completa do modelo, em texto."""
        ...

    def transmitir(
        self,
        mensagens: Sequence[Mensagem],
        *,
        temperatura: float | None = None,
        maximo_de_tokens: int | None = None,
        formato_resposta: dict[str, object] | None = None,
    ) -> AsyncIterator[str]:
        """Devolve a resposta em pedacos, conforme o modelo vai gerando."""
        ...

    async def esta_disponivel(self) -> bool:
        """Diz se o provedor esta no ar, sem gerar texto."""
        ...
