# Liga cliente e microfone ao coordenador, que só passa a existir depois deles.

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import Any


class Ponte:
    def __init__(self, despachar: Callable[[Callable[[], None]], None]) -> None:
        self.coordenador = None
        self._despachar = despachar

    def ao_responder(self, corpo: Any) -> None:
        if self.coordenador is not None:
            self.coordenador.ao_responder(corpo)

    def ao_falhar(self, erro: Exception) -> None:
        if self.coordenador is not None:
            self.coordenador.ao_falhar(erro)

    def ao_transcrever(self, texto: str, final: bool) -> None:
        self._despachar(partial(self._transcrever, texto, final))

    def _transcrever(self, texto: str, final: bool) -> None:
        if self.coordenador is not None:
            self.coordenador.ao_transcrever(texto, final)
