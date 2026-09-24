"""Apoio dos testes: uma Layla de mentira, sem rede.

Nenhum teste deste repositorio pode abrir conexao. O `httpx.MockTransport`
intercepta o pedido dentro do proprio processo, entao o cliente exercita o
codigo de verdade — montagem de corpo, novas tentativas, leitura de SSE — sem
que nada saia da maquina.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Sequence

import httpx


def resposta_de_conversa(texto: str) -> httpx.Response:
    """Uma resposta nao transmitida, no formato da API compativel com a OpenAI."""
    return httpx.Response(
        200,
        json={
            "choices": [
                {"index": 0, "message": {"role": "assistant", "content": texto}}
            ]
        },
    )


def corpo_sse(pedacos: Iterable[str], *, encerrar: bool = True) -> bytes:
    """Monta um corpo de SSE com um pedaco por evento."""
    linhas: list[str] = []
    for pedaco in pedacos:
        evento = {"choices": [{"index": 0, "delta": {"content": pedaco}}]}
        linhas.append(f"data: {json.dumps(evento)}\n\n")
    if encerrar:
        linhas.append("data: [DONE]\n\n")
    return "".join(linhas).encode()


def resposta_transmitida(pedacos: Iterable[str]) -> httpx.Response:
    return httpx.Response(
        200,
        content=corpo_sse(pedacos),
        headers={"Content-Type": "text/event-stream"},
    )


class LaylaDeMentira:
    """Serve respostas combinadas e guarda os pedidos que recebeu."""

    def __init__(self, respostas: Sequence[httpx.Response | Callable[..., object]]):
        self._respostas = list(respostas)
        self.pedidos: list[httpx.Request] = []

    def _responder(self, pedido: httpx.Request) -> httpx.Response:
        self.pedidos.append(pedido)
        indice = min(len(self.pedidos) - 1, len(self._respostas) - 1)
        resposta = self._respostas[indice]
        if callable(resposta):
            resultado = resposta(pedido)
            assert isinstance(resultado, httpx.Response)
            return resultado
        return resposta

    def cliente(self, **kwargs: object) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            transport=httpx.MockTransport(self._responder), **kwargs
        )

    @property
    def corpos(self) -> list[dict]:
        return [json.loads(pedido.content) for pedido in self.pedidos]


def erro_de_conexao(_: httpx.Request) -> httpx.Response:
    raise httpx.ConnectError("conexao recusada")


def tempo_esgotado(_: httpx.Request) -> httpx.Response:
    raise httpx.ReadTimeout("demorou demais")
