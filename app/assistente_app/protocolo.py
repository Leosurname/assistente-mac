"""O contrato com o backend, do lado da camada nativa.

O formato esta descrito no ARCHITECTURE.md. Este modulo monta a mensagem de
pedido e le a resposta — sem tocar em rede, para que o formato possa ser
testado sozinho.

Tudo que chega pelo WebSocket e tratado como dado. Uma resposta fora do formato
vira erro, nunca um palpite: o outro lado da conversa tem um modelo de
linguagem no caminho, e resposta de modelo nao vira comando sem passar por
conferencia.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from assistente_app.regioes import REGIOES

CATALOGO: frozenset[str] = frozenset(
    {"abrir_app", "fechar_app", "posicionar", "focar", "minimizar"}
)

FALA_PADRAO = "concluído"


class RespostaInvalida(ValueError):
    """O backend respondeu fora do contrato."""


class ErroDoBackend(RuntimeError):
    """O backend respondeu com uma mensagem de erro para mostrar ao usuario."""

    def __init__(self, mensagem: str) -> None:
        super().__init__(mensagem)
        self.mensagem = mensagem


@dataclass(frozen=True)
class Acao:
    acao: str
    app: str
    regiao: str | None = None


@dataclass(frozen=True)
class Resposta:
    acoes: tuple[Acao, ...]
    fala: str
    sessao: str | None = None


def montar_pedido(
    texto: str, tela: dict[str, Any], sessao: str | None = None
) -> dict[str, Any]:
    """Monta a mensagem `pedido` que vai pelo WebSocket."""
    pedido: dict[str, Any] = {"tipo": "pedido", "texto": texto, "tela": tela}
    if sessao:
        pedido["sessao"] = sessao
    return pedido


def montar_encerramento(sessao: str) -> dict[str, Any]:
    """Avisa o backend que a caixa sumiu e a sessao pode morrer agora.

    Sem isso a sessao ainda expiraria sozinha, mas ficaria viva depois de a
    caixa sumir — e um pedido novo herdaria o historico de uma conversa que o
    usuario ja considera encerrada.
    """
    return {"tipo": "encerrar", "sessao": sessao}


def ler_resposta(bruto: Any) -> Resposta:
    """Le a resposta do backend, recusando tudo que fuja do contrato."""
    if not isinstance(bruto, dict):
        raise RespostaInvalida("a resposta precisa ser um objeto")

    tipo = bruto.get("tipo")
    if tipo == "erro":
        mensagem = bruto.get("mensagem")
        raise ErroDoBackend(
            mensagem if isinstance(mensagem, str) and mensagem else "erro no backend"
        )
    if tipo == "encerrada":
        return Resposta(acoes=(), fala="")
    if tipo != "acoes":
        raise RespostaInvalida(f"nao conheco resposta do tipo {tipo!r}")

    brutas = bruto.get("acoes")
    if not isinstance(brutas, list):
        raise RespostaInvalida("o campo 'acoes' precisa ser uma lista")

    acoes = tuple(_ler_acao(item) for item in brutas)

    fala = bruto.get("fala")
    if not isinstance(fala, str) or not fala.strip():
        fala = FALA_PADRAO

    sessao = bruto.get("sessao")
    return Resposta(
        acoes=acoes,
        fala=fala.strip(),
        sessao=sessao if isinstance(sessao, str) and sessao else None,
    )


def _ler_acao(bruto: Any) -> Acao:
    if not isinstance(bruto, dict):
        raise RespostaInvalida("cada acao precisa ser um objeto")

    nome = bruto.get("acao")
    if nome not in CATALOGO:
        raise RespostaInvalida(f"acao fora do catalogo: {nome!r}")

    app = bruto.get("app")
    if not isinstance(app, str) or not app.strip():
        raise RespostaInvalida("a acao chegou sem aplicativo")

    regiao = bruto.get("regiao")
    if regiao is not None:
        if regiao not in REGIOES:
            raise RespostaInvalida(f"regiao fora do catalogo: {regiao!r}")
    elif nome == "posicionar":
        raise RespostaInvalida("posicionar sem regiao nao diz o que fazer")

    return Acao(acao=nome, app=app.strip(), regiao=regiao)
