# Fala a resposta em voz alta com o sintetizador do macOS.

from __future__ import annotations


class Falante:
    def __init__(self) -> None:
        self._sintetizador = None

    def __call__(self, mensagem: str) -> None:
        if self._sintetizador is None:
            from AppKit import NSSpeechSynthesizer

            self._sintetizador = NSSpeechSynthesizer.alloc().init()
        self._sintetizador.startSpeakingString_(mensagem)
