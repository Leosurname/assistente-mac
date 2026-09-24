"""Quem de fato mexe nas janelas.

Cada acao do catalogo vira uma chamada ao macOS aqui. O que chega ja passou
pela validacao do backend e pela leitura do contrato em `protocolo.py`; esta
camada confere de novo o que depende da maquina (o aplicativo existe? tem
janela?) e devolve uma mensagem legivel quando nao da para fazer.

Nada aqui executa texto. `abrir_app` recebe um nome de aplicativo e chama
`NSWorkspace`, que abre um pacote `.app` — nao ha caminho para shell.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from AppKit import (
    NSApplicationActivationPolicyRegular,
    NSWorkspace,
    NSWorkspaceOpenConfiguration,
)
from ApplicationServices import (
    AXUIElementCopyAttributeValue,
    AXUIElementCreateApplication,
    AXUIElementSetAttributeValue,
    AXValueCreate,
    kAXErrorSuccess,
    kAXPositionAttribute,
    kAXSizeAttribute,
    kAXValueTypeCGPoint,
    kAXValueTypeCGSize,
    kAXWindowsAttribute,
)
from Foundation import NSURL

from assistente_app import contexto
from assistente_app.protocolo import Acao
from assistente_app.regioes import RegiaoDesconhecida, calcular

registrador = logging.getLogger(__name__)

ESPERA_ENTRE_TENTATIVAS = 0.25
TENTATIVAS_APOS_ABRIR = 20


class ExecutorDeJanelas:
    """Executa a lista de acoes e devolve as falhas em portugues."""

    def executar(self, acoes: tuple[Acao, ...]) -> list[str]:
        falhas: list[str] = []
        for acao in acoes:
            try:
                erro = self._uma(acao)
            except Exception as erro_inesperado:  # noqa: BLE001
                registrador.exception("Falha em %s", acao)
                erro = f"não consegui {acao.acao} {acao.app}: {erro_inesperado}"
            if erro:
                falhas.append(erro)
        return falhas

    def _uma(self, acao: Acao) -> str | None:
        match acao.acao:
            case "abrir_app":
                return self._abrir(acao.app)
            case "fechar_app":
                return self._fechar(acao.app)
            case "focar":
                return self._focar(acao.app)
            case "minimizar":
                return self._minimizar(acao.app)
            case "posicionar":
                return self._posicionar(acao.app, acao.regiao or "")
        return f"não sei fazer {acao.acao!r}"

    # --- acoes -----------------------------------------------------------

    def _abrir(self, nome: str) -> str | None:
        if _rodando(nome) is not None:
            return self._focar(nome)

        caminho = _caminho_do_aplicativo(nome)
        if caminho is None:
            return f"não achei o {nome}"

        area = NSWorkspace.sharedWorkspace()
        configuracao = NSWorkspaceOpenConfiguration.configuration()
        configuracao.setActivates_(True)
        area.openApplicationAtURL_configuration_completionHandler_(
            NSURL.fileURLWithPath_(caminho), configuracao, None
        )
        return None

    def _fechar(self, nome: str) -> str | None:
        app = _rodando(nome)
        if app is None:
            return None
        app.terminate()
        return None

    def _focar(self, nome: str) -> str | None:
        app = _rodando(nome)
        if app is None:
            return f"o {nome} não está aberto"
        app.activateWithOptions_(0)
        return None

    def _minimizar(self, nome: str) -> str | None:
        janela = _primeira_janela(nome)
        if janela is None:
            return f"o {nome} não tem janela para minimizar"
        AXUIElementSetAttributeValue(janela, "AXMinimized", True)
        return None

    def _posicionar(self, nome: str, regiao: str) -> str | None:
        try:
            alvo = calcular(regiao, contexto.area_util())
        except RegiaoDesconhecida as erro:
            return str(erro)

        janela = _primeira_janela(nome, esperar=True)
        if janela is None:
            return f"o {nome} não tem janela para posicionar"

        ponto = AXValueCreate(kAXValueTypeCGPoint, (float(alvo.x), float(alvo.y)))
        tamanho = AXValueCreate(
            kAXValueTypeCGSize, (float(alvo.largura), float(alvo.altura))
        )
        # Posicao antes de tamanho: se a janela for maior que a area de destino,
        # redimensionar primeiro evita que o macOS a empurre de volta para
        # dentro do monitor e desfaça o movimento.
        AXUIElementSetAttributeValue(janela, kAXPositionAttribute, ponto)
        AXUIElementSetAttributeValue(janela, kAXSizeAttribute, tamanho)
        return None


# --- apoio ---------------------------------------------------------------


def _rodando(nome: str) -> Any | None:
    """Acha o aplicativo rodando pelo nome que o usuario usaria."""
    procurado = nome.casefold()
    for app in NSWorkspace.sharedWorkspace().runningApplications():
        if app.activationPolicy() != NSApplicationActivationPolicyRegular:
            continue
        local = (app.localizedName() or "").casefold()
        if local == procurado or procurado in local:
            return app
    return None


def _caminho_do_aplicativo(nome: str) -> str | None:
    procurado = nome.casefold()
    for pasta in contexto.PASTAS_DE_APLICATIVOS:
        try:
            itens = os.listdir(pasta)
        except OSError:
            continue
        for item in itens:
            if not item.endswith(".app"):
                continue
            if item[: -len(".app")].casefold() == procurado:
                return f"{pasta}/{item}"
    return None


def _primeira_janela(nome: str, esperar: bool = False) -> Any | None:
    """A janela principal do aplicativo, pela API de acessibilidade.

    Com `esperar`, tenta de novo por alguns segundos: aplicativo recem-aberto
    demora a ter janela, e posicionar logo depois de abrir e o caso comum.
    """
    tentativas = TENTATIVAS_APOS_ABRIR if esperar else 1
    for _ in range(tentativas):
        app = _rodando(nome)
        if app is not None:
            elemento = AXUIElementCreateApplication(app.processIdentifier())
            codigo, janelas = AXUIElementCopyAttributeValue(
                elemento, kAXWindowsAttribute, None
            )
            if codigo == kAXErrorSuccess and janelas:
                return janelas[0]
        if esperar:
            time.sleep(ESPERA_ENTRE_TENTATIVAS)
    return None
