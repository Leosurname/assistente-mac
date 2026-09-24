"""Sobe a camada nativa.

`python -m assistente_app`. O aplicativo vive na barra de menu, sem icone no
Dock, esperando o Option+9.
"""

from __future__ import annotations

import logging
import sys

from AppKit import (
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSTimer,
)
from Foundation import NSOperationQueue, NSRunLoop

from assistente_app import contexto
from assistente_app.atalho import PermissaoNegada, Teclado
from assistente_app.cliente import ClienteDoBackend
from assistente_app.configuracao import Configuracao
from assistente_app.coordenador import Coordenador
from assistente_app.janelas import ExecutorDeJanelas
from assistente_app.sobreposicao import Sobreposicao
from assistente_app.voz import Microfone, MicrofoneIndisponivel

registrador = logging.getLogger(__name__)

INTERVALO_DO_TIQUE = 0.25


def despachar_na_principal(bloco) -> None:  # noqa: ANN001
    """Roda o bloco na thread principal. Tudo que e AppKit precisa disso."""
    NSOperationQueue.mainQueue().addOperationWithBlock_(bloco)


def principal() -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    configuracao = Configuracao.do_ambiente()

    aplicativo = NSApplication.sharedApplication()
    # Accessory: sem icone no Dock e sem menu proprio. O assistente nao e uma
    # janela a mais, e um atalho.
    aplicativo.setActivationPolicy_(NSApplicationActivationPolicyAccessory)

    caixa = Sobreposicao()
    executor = ExecutorDeJanelas()

    coordenador: Coordenador | None = None

    def responder(corpo) -> None:  # noqa: ANN001
        if coordenador is not None:
            coordenador.ao_responder(corpo)

    def falhar(erro: Exception) -> None:
        if coordenador is not None:
            coordenador.ao_falhar(erro)

    cliente = ClienteDoBackend(
        endereco=configuracao.backend,
        ao_responder=responder,
        ao_falhar=falhar,
        despachar=despachar_na_principal,
    )
    cliente.iniciar()

    def transcrever(texto: str, final: bool) -> None:
        despachar_na_principal(
            lambda: (
                coordenador.ao_transcrever(texto, final)
                if coordenador is not None
                else None
            )
        )

    try:
        microfone = Microfone(configuracao.idioma, transcrever)
    except MicrofoneIndisponivel as erro:
        registrador.error("%s", erro)
        return 1

    coordenador = Coordenador(
        caixa=caixa,
        microfone=microfone,
        executor=executor,
        retrato=contexto.montar,
        enviar=cliente.enviar,
        relogio=_relogio,
        espera=configuracao.espera,
        falar=_falar if configuracao.falar_resposta else None,
    )

    teclado = Teclado(
        ao_atalho=coordenador.ao_atalho,
        ao_digitar=coordenador.ao_digitar,
        ao_escape=coordenador.ao_escape,
    )
    try:
        teclado.instalar()
    except PermissaoNegada as erro:
        registrador.error("%s", erro)
        return 1

    NSTimer.scheduledTimerWithTimeInterval_repeats_block_(
        INTERVALO_DO_TIQUE, True, lambda _: coordenador.ao_tique()
    )

    Microfone.pedir_permissao(
        lambda concedida: registrador.info(
            "Reconhecimento de fala %s", "liberado" if concedida else "negado"
        )
    )

    registrador.info("Assistente Mac de pé. Aperte Option+9.")
    NSRunLoop.currentRunLoop()
    aplicativo.run()
    return 0


def _relogio() -> float:
    import time

    return time.monotonic()


def _falar(mensagem: str) -> None:
    from AppKit import NSSpeechSynthesizer

    sintetizador = getattr(_falar, "_sintetizador", None)
    if sintetizador is None:
        sintetizador = NSSpeechSynthesizer.alloc().init()
        _falar._sintetizador = sintetizador  # noqa: SLF001
    sintetizador.startSpeakingString_(mensagem)


if __name__ == "__main__":
    sys.exit(principal())
