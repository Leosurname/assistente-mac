"""Servidor WebSocket local do Assistente Mac.

So aceita conexao local: ele mexe nas janelas da maquina do usuario, e nao
existe motivo para alguem de fora alcancar isso. A escolha de FastAPI esta no
backend/README.md.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from assistente import __version__, registro
from assistente.configuracao import ConfiguracaoLayla
from assistente.layla.cliente import ClienteLayla
from assistente.layla.erros import ErroDaLLM
from assistente.layla.interface import ClienteDeLLM
from assistente.sessao import VALIDADE_PADRAO, RegistroDeSessoes
from assistente.tela import RetratoDaTela, RetratoInvalido
from assistente.tradutor import traduzir

registrador = logging.getLogger(__name__)

ENDERECO_PADRAO = "127.0.0.1"
PORTA_PADRAO = 8765
ENDERECOS_LOCAIS = frozenset({"127.0.0.1", "::1", "localhost", "::ffff:127.0.0.1"})

LIMITE_DO_TEXTO = 2000


def e_local(endereco: str | None) -> bool:
    return endereco in ENDERECOS_LOCAIS


def criar_aplicativo(
    llm: ClienteDeLLM | None = None,
    sessoes: RegistroDeSessoes | None = None,
) -> FastAPI:
    """Monta o aplicativo. O cliente da Layla entra por parametro nos testes."""
    aplicativo = FastAPI(title="Assistente Mac", version=__version__)
    aplicativo.state.sessoes = sessoes or RegistroDeSessoes(_validade_da_sessao())
    aplicativo.state.llm = llm or ClienteLayla(ConfiguracaoLayla.do_ambiente())

    @aplicativo.get("/health")
    async def health() -> dict[str, Any]:
        sessoes_vivas = len(aplicativo.state.sessoes)
        layla_no_ar = await aplicativo.state.llm.esta_disponivel()
        return {
            "estado": "ok" if layla_no_ar else "degradado",
            "versao": __version__,
            "layla": "no ar" if layla_no_ar else "fora do ar",
            "sessoes": sessoes_vivas,
        }

    @aplicativo.websocket("/ws")
    async def canal(websocket: WebSocket) -> None:
        origem = websocket.client.host if websocket.client else None
        if not e_local(origem):
            registrador.warning("Conexao recusada, origem nao local: %s", origem)
            await websocket.close(code=1008, reason="somente conexoes locais")
            return

        await websocket.accept()
        registrador.info("Camada nativa conectada")
        try:
            while True:
                bruto = await websocket.receive_json()
                resposta = await _responder(aplicativo, bruto)
                await websocket.send_json(resposta)
        except WebSocketDisconnect:
            registrador.info("Camada nativa desconectada")
        except ValueError:
            # receive_json com corpo que nao e JSON.
            await _fechar_com_erro(websocket, "mensagem fora do formato esperado")

    return aplicativo


async def _responder(aplicativo: FastAPI, bruto: Any) -> dict[str, Any]:
    if not isinstance(bruto, dict):
        return _erro("a mensagem precisa ser um objeto")

    tipo = bruto.get("tipo")
    sessoes: RegistroDeSessoes = aplicativo.state.sessoes

    if tipo == "encerrar":
        identificador = bruto.get("sessao")
        if isinstance(identificador, str):
            sessoes.encerrar(identificador)
        return {"tipo": "encerrada"}

    if tipo != "pedido":
        return _erro(f"nao conheco mensagem do tipo {tipo!r}")

    texto = bruto.get("texto")
    if not isinstance(texto, str) or not texto.strip():
        return _erro("o pedido chegou sem texto")
    texto = texto.strip()[:LIMITE_DO_TEXTO]

    try:
        tela = RetratoDaTela.do_dicionario(bruto.get("tela"))
    except RetratoInvalido as erro:
        return _erro(f"o retrato da tela veio fora do formato: {erro}")

    identificador = bruto.get("sessao")
    sessao = sessoes.obter(identificador if isinstance(identificador, str) else None)

    try:
        traducao = await traduzir(texto, tela, sessao, aplicativo.state.llm)
    except ErroDaLLM as erro:
        registrador.error("Falha ao falar com a Layla: %s", erro)
        return _erro(erro.mensagem_amigavel)

    registrador.info(
        "Pedido traduzido: %d acoes aprovadas, %d recusadas",
        len(traducao.acoes),
        len(traducao.recusadas),
    )

    resposta = traducao.para_dicionario()
    resposta["sessao"] = sessao.identificador
    return resposta


def _validade_da_sessao() -> float:
    bruto = os.getenv("ASSISTENTE_VALIDADE_SESSAO")
    if not bruto or not bruto.strip():
        return VALIDADE_PADRAO
    try:
        return float(bruto)
    except ValueError as erro:
        raise ValueError(
            f"ASSISTENTE_VALIDADE_SESSAO precisa ser um numero: {bruto!r}"
        ) from erro


def _erro(mensagem: str) -> dict[str, Any]:
    return {"tipo": "erro", "mensagem": mensagem}


async def _fechar_com_erro(websocket: WebSocket, mensagem: str) -> None:
    if websocket.client_state is WebSocketState.CONNECTED:
        await websocket.send_json(_erro(mensagem))
        await websocket.close(code=1003)


def principal() -> None:
    """Sobe o servidor. E o que `python -m assistente.servidor` chama."""
    import uvicorn

    registro.configurar()
    porta = int(os.getenv("ASSISTENTE_PORTA") or PORTA_PADRAO)
    registrador.info("Assistente Mac ouvindo em %s:%d", ENDERECO_PADRAO, porta)
    uvicorn.run(criar_aplicativo(), host=ENDERECO_PADRAO, port=porta, log_config=None)


if __name__ == "__main__":
    principal()
