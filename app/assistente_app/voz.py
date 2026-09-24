"""Microfone e transcricao ao vivo, com `SFSpeechRecognizer`.

O que sai daqui e transcricao do usuario: dado, nunca instrucao.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from AVFoundation import AVAudioEngine
from Foundation import NSLocale
from Speech import (
    SFSpeechAudioBufferRecognitionRequest,
    SFSpeechRecognizer,
    SFSpeechRecognizerAuthorizationStatusAuthorized,
)

registrador = logging.getLogger(__name__)

TAMANHO_DO_BUFFER = 1024


class MicrofoneIndisponivel(RuntimeError):
    """Nao da para ouvir: permissao negada ou idioma sem suporte."""


class Microfone:
    """Liga o microfone e entrega transcricao parcial e final."""

    def __init__(
        self,
        idioma: str,
        ao_transcrever: Callable[[str, bool], None],
    ) -> None:
        self._ao_transcrever = ao_transcrever
        self._reconhecedor = SFSpeechRecognizer.alloc().initWithLocale_(
            NSLocale.localeWithLocaleIdentifier_(idioma)
        )
        if self._reconhecedor is None or not self._reconhecedor.isAvailable():
            raise MicrofoneIndisponivel(
                f"o reconhecimento de fala não está disponível para {idioma}"
            )
        self._motor = AVAudioEngine.alloc().init()
        self._pedido = None
        self._tarefa = None

    @staticmethod
    def pedir_permissao(quando_responder: Callable[[bool], None]) -> None:
        """Pergunta ao usuario. O macOS so pergunta uma vez por instalacao."""

        def tratar(estado) -> None:  # noqa: ANN001
            quando_responder(estado == SFSpeechRecognizerAuthorizationStatusAuthorized)

        SFSpeechRecognizer.requestAuthorization_(tratar)

    def ouvir(self) -> None:
        """Comeca a escutar. Chamar de novo reinicia a escuta do zero."""
        self.parar()

        self._pedido = SFSpeechAudioBufferRecognitionRequest.alloc().init()
        self._pedido.setShouldReportPartialResults_(True)

        entrada = self._motor.inputNode()
        formato = entrada.outputFormatForBus_(0)
        entrada.installTapOnBus_bufferSize_format_block_(
            0, TAMANHO_DO_BUFFER, formato, self._receber_audio
        )

        self._motor.prepare()
        sucesso, erro = self._motor.startAndReturnError_(None)
        if not sucesso:
            raise MicrofoneIndisponivel(f"não consegui ligar o microfone: {erro}")

        self._tarefa = self._reconhecedor.recognitionTaskWithRequest_resultHandler_(
            self._pedido, self._receber_resultado
        )

    def parar(self) -> None:
        if self._motor.isRunning():
            self._motor.stop()
            self._motor.inputNode().removeTapOnBus_(0)
        if self._pedido is not None:
            self._pedido.endAudio()
            self._pedido = None
        if self._tarefa is not None:
            self._tarefa.cancel()
            self._tarefa = None

    def _receber_audio(self, buffer, quando) -> None:  # noqa: ANN001, ARG002
        if self._pedido is not None:
            self._pedido.appendAudioPCMBuffer_(buffer)

    def _receber_resultado(self, resultado, erro) -> None:  # noqa: ANN001
        if erro is not None:
            registrador.debug("Reconhecimento interrompido: %s", erro)
            return
        if resultado is None:
            return
        texto = str(resultado.bestTranscription().formattedString())
        self._ao_transcrever(texto, bool(resultado.isFinal()))
