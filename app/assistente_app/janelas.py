"""Quem de fato mexe nas janelas: cada acao do catalogo vira uma chamada ao
macOS aqui.

Nada aqui executa texto. `abrir_app` recebe um nome de aplicativo e chama
`NSWorkspace`, que abre um pacote `.app` — nao ha caminho para shell.
"""

from __future__ import annotations

import logging
import time

from AppKit import NSWorkspace, NSWorkspaceOpenConfiguration
from ApplicationServices import (
    AXUIElementCopyAttributeValue,
    AXUIElementIsAttributeSettable,
    AXUIElementSetAttributeValue,
    AXValueCreate,
    kAXErrorSuccess,
    kAXPositionAttribute,
    kAXSizeAttribute,
    kAXValueTypeCGPoint,
    kAXValueTypeCGSize,
)
from Foundation import NSURL

from assistente_app import contexto
from assistente_app.busca import caminho_do_aplicativo, primeira_janela, rodando
from assistente_app.protocolo import Acao
from assistente_app.regioes import RegiaoDesconhecida, calcular

registrador = logging.getLogger(__name__)

ATRIBUTO_TELA_CHEIA = "AXFullScreen"
ESPERA_SAIR_DA_TELA_CHEIA = 0.25
TENTATIVAS_SAIR_DA_TELA_CHEIA = 20


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
            case "entrar_tela_cheia":
                return self._entrar_tela_cheia(acao.app)
        return f"não sei fazer {acao.acao!r}"

    def _abrir(self, nome: str) -> str | None:
        if rodando(nome) is not None:
            return self._focar(nome)

        caminho = caminho_do_aplicativo(nome)
        if caminho is None:
            return f"não achei o {nome}"

        _trazer_para_frente(NSURL.fileURLWithPath_(caminho))
        return None

    def _fechar(self, nome: str) -> str | None:
        app = rodando(nome)
        if app is None:
            return None
        app.terminate()
        return None

    def _focar(self, nome: str) -> str | None:
        app = rodando(nome)
        if app is None:
            return f"o {nome} não está aberto"
        _trazer_para_frente(app.bundleURL())
        return None

    def _minimizar(self, nome: str) -> str | None:
        janela = primeira_janela(nome)
        if janela is None:
            return f"o {nome} não tem janela para minimizar"
        AXUIElementSetAttributeValue(janela, "AXMinimized", True)
        return None

    def _entrar_tela_cheia(self, nome: str) -> str | None:
        janela = primeira_janela(nome)
        if janela is None:
            return f"o {nome} não tem janela para entrar em tela cheia"
        if not AXUIElementIsAttributeSettable(janela, ATRIBUTO_TELA_CHEIA):
            return f"o {nome} não entra em tela cheia"
        if not _em_tela_cheia(janela):
            AXUIElementSetAttributeValue(janela, ATRIBUTO_TELA_CHEIA, True)
        return None

    def _posicionar(self, nome: str, regiao: str) -> str | None:
        try:
            alvo = calcular(regiao, contexto.area_util())
        except RegiaoDesconhecida as erro:
            return str(erro)

        janela = primeira_janela(nome, esperar=True)
        if janela is None:
            return f"o {nome} não tem janela para posicionar"

        # A troca de tela cheia e animada: so grava posicao e tamanho depois
        # que a janela sair de verdade, senao o sistema desfaz o movimento.
        if _em_tela_cheia(janela):
            AXUIElementSetAttributeValue(janela, ATRIBUTO_TELA_CHEIA, False)
            if not _esperar_sair_da_tela_cheia(janela):
                return f"o {nome} não saiu da tela cheia"

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


def _em_tela_cheia(janela) -> bool:  # noqa: ANN001
    codigo, valor = AXUIElementCopyAttributeValue(janela, ATRIBUTO_TELA_CHEIA, None)
    return codigo == kAXErrorSuccess and bool(valor)


def _esperar_sair_da_tela_cheia(janela) -> bool:  # noqa: ANN001
    for _ in range(TENTATIVAS_SAIR_DA_TELA_CHEIA):
        if not _em_tela_cheia(janela):
            return True
        time.sleep(ESPERA_SAIR_DA_TELA_CHEIA)
    return not _em_tela_cheia(janela)


def _trazer_para_frente(url) -> None:  # noqa: ANN001
    # Desde o macOS 14, activateWithOptions_ vindo de app em segundo plano
    # devolve True e nao faz nada. Abrir pelo LaunchServices ativa de verdade,
    # e para app ja aberto so traz para frente.
    configuracao = NSWorkspaceOpenConfiguration.configuration()
    configuracao.setActivates_(True)
    NSWorkspace.sharedWorkspace().openApplicationAtURL_configuration_completionHandler_(
        url, configuracao, None
    )
