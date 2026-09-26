# Monta a camada nativa e entrega o controle ao run loop do AppKit.

from __future__ import annotations

import logging
import time

from AppKit import (
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSTimer,
)
from Foundation import NSRunLoop

from assistente_app import contexto
from assistente_app.atalho import PermissaoNegada, Teclado
from assistente_app.cliente import ClienteDoBackend
from assistente_app.configuracao import Configuracao
from assistente_app.coordenador import Coordenador
from assistente_app.fala import Falante
from assistente_app.fila import despachar_na_principal
from assistente_app.janelas import ExecutorDeJanelas
from assistente_app.ponte import Ponte
from assistente_app.sobreposicao import Sobreposicao
from assistente_app.voz import Microfone, MicrofoneIndisponivel

registrador = logging.getLogger(__name__)

INTERVALO_DO_TIQUE = 0.25


def principal() -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    configuracao = Configuracao.do_ambiente()
    aplicativo = _criar_aplicativo()
    caixa = Sobreposicao()
    executor = ExecutorDeJanelas()

    ponte = Ponte(despachar_na_principal)
    cliente = ClienteDoBackend(
        endereco=configuracao.backend,
        ao_responder=ponte.ao_responder,
        ao_falhar=ponte.ao_falhar,
        despachar=despachar_na_principal,
    )
    cliente.iniciar()

    try:
        microfone = Microfone(configuracao.idioma, ponte.ao_transcrever)
    except MicrofoneIndisponivel as erro:
        registrador.error("%s", erro)
        return 1

    coordenador = _montar_coordenador(configuracao, caixa, executor, cliente, microfone)
    ponte.coordenador = coordenador
    if not _instalar_teclado(coordenador):
        return 1
    _iniciar_tique(coordenador)

    Microfone.pedir_permissao(_registrar_permissao)
    registrador.info("Assistente Mac de pé. Aperte Option+9.")
    NSRunLoop.currentRunLoop()
    aplicativo.run()
    return 0


def _criar_aplicativo() -> NSApplication:
    aplicativo = NSApplication.sharedApplication()
    # Accessory: sem icone no Dock e sem menu proprio. O assistente nao e uma
    # janela a mais, e um atalho.
    aplicativo.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    return aplicativo


def _montar_coordenador(configuracao, caixa, executor, cliente, microfone):  # noqa: ANN001, ANN202
    return Coordenador(
        caixa=caixa,
        microfone=microfone,
        executor=executor,
        retrato=contexto.montar,
        enviar=cliente.enviar,
        relogio=time.monotonic,
        espera=configuracao.espera,
        falar=Falante() if configuracao.falar_resposta else None,
    )


def _instalar_teclado(coordenador: Coordenador) -> bool:
    teclado = Teclado(
        ao_atalho=coordenador.ao_atalho,
        ao_digitar=coordenador.ao_digitar,
        ao_escape=coordenador.ao_escape,
    )
    try:
        teclado.instalar()
    except PermissaoNegada as erro:
        registrador.error("%s", erro)
        return False
    return True


def _iniciar_tique(coordenador: Coordenador) -> None:
    NSTimer.scheduledTimerWithTimeInterval_repeats_block_(
        INTERVALO_DO_TIQUE, True, lambda _: coordenador.ao_tique()
    )


def _registrar_permissao(concedida: bool) -> None:
    registrador.info("Reconhecimento de fala %s", "liberado" if concedida else "negado")
