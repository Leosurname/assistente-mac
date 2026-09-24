"""Quem de fato mexe nas janelas: cada acao do catalogo vira uma chamada ao
macOS aqui.

Nada aqui executa texto. `abrir_app` recebe um nome de aplicativo e chama
`NSWorkspace`, que abre um pacote `.app` — nao ha caminho para shell.
"""

from __future__ import annotations

import logging

from AppKit import NSWorkspace, NSWorkspaceOpenConfiguration
from ApplicationServices import (
    AXUIElementSetAttributeValue,
    AXValueCreate,
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

    def _abrir(self, nome: str) -> str | None:
        if rodando(nome) is not None:
            return self._focar(nome)

        caminho = caminho_do_aplicativo(nome)
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
        app = rodando(nome)
        if app is None:
            return None
        app.terminate()
        return None

    def _focar(self, nome: str) -> str | None:
        app = rodando(nome)
        if app is None:
            return f"o {nome} não está aberto"
        app.activateWithOptions_(0)
        return None

    def _minimizar(self, nome: str) -> str | None:
        janela = primeira_janela(nome)
        if janela is None:
            return f"o {nome} não tem janela para minimizar"
        AXUIElementSetAttributeValue(janela, "AXMinimized", True)
        return None

    def _posicionar(self, nome: str, regiao: str) -> str | None:
        try:
            alvo = calcular(regiao, contexto.area_util())
        except RegiaoDesconhecida as erro:
            return str(erro)

        janela = primeira_janela(nome, esperar=True)
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
