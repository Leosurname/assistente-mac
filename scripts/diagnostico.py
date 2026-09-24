"""Confere o que precisa estar de pé antes do primeiro teste de verdade.

`python scripts/diagnostico.py`
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

import httpx

ESQUEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["acoes"],
    "properties": {
        "acoes": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["app"],
                "properties": {"app": {"type": "string"}},
            },
        }
    },
}


class Falha(Exception):
    pass


def url_da_layla() -> str:
    bruto = os.getenv("LAYLA_URL") or "http://127.0.0.1:8080"
    return bruto.removesuffix("/").removesuffix("/v1/chat/completions")


async def layla_no_ar(cliente: httpx.AsyncClient) -> str:
    resposta = await cliente.get(f"{url_da_layla()}/v1/models")
    resposta.raise_for_status()
    modelos = [m.get("id", "?") for m in resposta.json().get("data", [])]
    if not modelos:
        raise Falha("o servidor respondeu, mas não há modelo carregado")
    return ", ".join(modelos)


async def gramatica_funciona(cliente: httpx.AsyncClient) -> str:
    """O teste que decide se o backend inteiro se sustenta.

    Os fine-tunes da Layla são feitos para conversa. Todo o desenho do backend
    aposta que o `llama-server` restringe a decodificação pelo `json_schema` e
    devolve JSON válido mesmo assim. Se esta checagem falhar, a aposta caiu.
    """
    corpo = {
        "messages": [
            {"role": "system", "content": "Responda em JSON."},
            {"role": "user", "content": "Quero o Safari aberto."},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "teste", "schema": ESQUEMA, "strict": True},
        },
        "temperature": 0.0,
        "max_tokens": 120,
    }
    resposta = await cliente.post(
        f"{url_da_layla()}/v1/chat/completions", json=corpo, timeout=120.0
    )
    resposta.raise_for_status()
    bruta = resposta.json()["choices"][0]["message"]["content"]

    try:
        corpo_lido = json.loads(bruta)
    except ValueError as erro:
        raise Falha(f"a resposta não é JSON: {bruta[:120]!r}") from erro
    if not isinstance(corpo_lido, dict) or "acoes" not in corpo_lido:
        raise Falha(f"JSON válido, mas fora do esquema: {bruta[:120]!r}")
    return "o servidor respeitou o esquema"


async def backend_no_ar(cliente: httpx.AsyncClient) -> str:
    porta = os.getenv("ASSISTENTE_PORTA") or "8765"
    resposta = await cliente.get(f"http://127.0.0.1:{porta}/health")
    resposta.raise_for_status()
    saude = resposta.json()
    return f"estado {saude.get('estado')}, Layla {saude.get('layla')}"


def acessibilidade() -> str:
    """Sem esta permissão o Option+9 nunca chega."""
    try:
        from ApplicationServices import AXIsProcessTrusted
    except ImportError as erro:
        raise Falha("PyObjC não instalado; rode dentro do ambiente do app") from erro
    if not AXIsProcessTrusted():
        raise Falha(
            "não concedida. Ajustes do Sistema ▸ Privacidade e Segurança ▸ "
            "Acessibilidade, e reabra o programa"
        )
    return "concedida"


async def principal() -> int:
    problemas = 0
    async with httpx.AsyncClient(timeout=10.0) as cliente:
        for nome, checagem in (
            ("llama-server", layla_no_ar(cliente)),
            ("decodificação restrita", gramatica_funciona(cliente)),
            ("backend", backend_no_ar(cliente)),
        ):
            problemas += await _mostrar(nome, checagem)

    problemas += _mostrar_sincrono("acessibilidade", acessibilidade)
    print()
    print("tudo pronto" if not problemas else f"{problemas} item(ns) a resolver")
    return 1 if problemas else 0


async def _mostrar(nome: str, checagem) -> int:  # noqa: ANN001
    try:
        print(f"  ok   {nome}: {await checagem}")
    except Exception as erro:  # noqa: BLE001
        print(f"  ERRO {nome}: {_curto(erro)}")
        return 1
    return 0


def _mostrar_sincrono(nome: str, checagem) -> int:  # noqa: ANN001
    try:
        print(f"  ok   {nome}: {checagem()}")
    except Exception as erro:  # noqa: BLE001
        print(f"  ERRO {nome}: {_curto(erro)}")
        return 1
    return 0


def _curto(erro: Exception) -> str:
    texto = str(erro) or type(erro).__name__
    return texto if len(texto) < 160 else texto[:157] + "..."


if __name__ == "__main__":
    sys.exit(asyncio.run(principal()))
