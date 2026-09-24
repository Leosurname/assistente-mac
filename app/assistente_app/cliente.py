"""Conversa com o backend pelo WebSocket local.

O AppKit ocupa a thread principal com o seu run loop e o cliente WebSocket quer
um loop de asyncio: os dois nao cabem na mesma thread. Daqui cada resposta volta
para a principal por `despachar`, porque mexer em NSPanel fora dela trava.
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from collections.abc import Callable
from typing import Any

import websockets

registrador = logging.getLogger(__name__)

ESPERA_PARA_RECONECTAR = 2.0


class ClienteDoBackend:
    """Mantem a conexao de pe e entrega as mensagens nos dois sentidos."""

    def __init__(
        self,
        endereco: str,
        ao_responder: Callable[[Any], None],
        ao_falhar: Callable[[Exception], None],
        despachar: Callable[[Callable[[], None]], None],
    ) -> None:
        self._endereco = endereco
        self._ao_responder = ao_responder
        self._ao_falhar = ao_falhar
        self._despachar = despachar
        self._laco: asyncio.AbstractEventLoop | None = None
        self._conexao: Any | None = None
        self._thread: threading.Thread | None = None
        self._pronto = threading.Event()

    def iniciar(self) -> None:
        self._thread = threading.Thread(target=self._rodar, name="backend", daemon=True)
        self._thread.start()
        self._pronto.wait(timeout=5.0)

    def enviar(self, mensagem: dict[str, Any]) -> None:
        """Chamado da thread principal. Nao bloqueia."""
        if self._laco is None:
            self._reportar(RuntimeError("o cliente do backend ainda não subiu"))
            return
        asyncio.run_coroutine_threadsafe(self._enviar(mensagem), self._laco)

    def parar(self) -> None:
        if self._laco is not None:
            self._laco.call_soon_threadsafe(self._laco.stop)

    def _rodar(self) -> None:
        self._laco = asyncio.new_event_loop()
        asyncio.set_event_loop(self._laco)
        self._pronto.set()
        try:
            self._laco.run_forever()
        finally:
            self._laco.close()

    async def _garantir_conexao(self) -> Any:
        if self._conexao is not None:
            return self._conexao
        self._conexao = await websockets.connect(self._endereco)
        registrador.info("Conectado ao backend em %s", self._endereco)
        asyncio.ensure_future(self._escutar(self._conexao))
        return self._conexao

    async def _enviar(self, mensagem: dict[str, Any]) -> None:
        try:
            conexao = await self._garantir_conexao()
            await conexao.send(json.dumps(mensagem))
        except Exception as erro:  # noqa: BLE001 - qualquer falha vira aviso
            self._conexao = None
            self._reportar(erro)

    async def _escutar(self, conexao: Any) -> None:
        try:
            async for bruto in conexao:
                try:
                    corpo = json.loads(bruto)
                except ValueError as erro:
                    self._reportar(erro)
                    continue
                self._despachar(lambda corpo=corpo: self._ao_responder(corpo))
        except Exception as erro:  # noqa: BLE001
            self._reportar(erro)
        finally:
            if self._conexao is conexao:
                self._conexao = None

    def _reportar(self, erro: Exception) -> None:
        self._despachar(lambda: self._ao_falhar(erro))
