"""O fio que liga atalho, voz, caixa, backend e janelas.

Tudo entra por parametro e nenhum import do macOS acontece aqui: e o que permite
testar o fluxo inteiro, do atalho ate a caixa sumindo, sem abrir janela, sem
microfone e sem backend no ar.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, Protocol

from assistente_app.dispensa import Dispensa, Efeito, Estado
from assistente_app.protocolo import (
    ErroDoBackend,
    Resposta,
    RespostaInvalida,
    ler_resposta,
    montar_encerramento,
    montar_pedido,
)

registrador = logging.getLogger(__name__)

MENSAGEM_DE_FALHA = "não consegui falar com a Layla"

# O reconhecimento do macOS so marca a frase como final quando o audio acaba, e
# o microfone segue ligado: quem encerra o pedido e o silencio depois da fala.
SILENCIO = 1.2


class Caixa(Protocol):
    def mostrar(self) -> None: ...
    def ocultar(self) -> None: ...
    def escrever(self, texto: str) -> None: ...
    def marcar_pensando(self, pensando: bool) -> None: ...


class Microfone(Protocol):
    def ouvir(self) -> None: ...
    def parar(self) -> None: ...


class Executor(Protocol):
    def executar(self, acoes: tuple) -> list[str]: ...


class Coordenador:
    """Recebe eventos da interface e conduz um pedido do inicio ao fim."""

    def __init__(
        self,
        caixa: Caixa,
        microfone: Microfone,
        executor: Executor,
        retrato: Callable[[], dict[str, Any]],
        enviar: Callable[[dict[str, Any]], None],
        relogio: Callable[[], float],
        espera: float,
        falar: Callable[[str], None] | None = None,
    ) -> None:
        self.caixa = caixa
        self.microfone = microfone
        self.executor = executor
        self.retrato = retrato
        self.enviar = enviar
        self.relogio = relogio
        self.falar = falar
        self.dispensa = Dispensa(espera=espera)
        self.sessao: str | None = None
        self._fala: tuple[str, float] | None = None

    def ao_atalho(self) -> None:
        """Option+9."""
        self._fala = None
        efeito = self.dispensa.atalho(self.relogio())
        if efeito is Efeito.MOSTRAR:
            self.caixa.mostrar()
        self.caixa.escrever("")
        self.caixa.marcar_pensando(False)
        self.microfone.ouvir()

    def ao_transcrever(self, texto: str, final: bool) -> None:
        """Chegou texto do microfone, parcial ou definitivo."""
        if (self.estado in (Estado.OCULTA, Estado.PENSANDO)):
            return
        self.dispensa.transcricao_parcial()
        self.caixa.escrever(texto)
        if (final and texto.strip()):
            self._enviar_pedido(texto.strip())
        elif (texto.strip()):
            self._fala = (texto.strip(), self.relogio())

    def ao_digitar(self) -> None:
        self._aplicar(self.dispensa.digitou())

    def ao_escape(self) -> None:
        self._aplicar(self.dispensa.escape())

    def ao_tique(self) -> None:
        """Chamado pelo temporizador da interface, algumas vezes por segundo."""
        agora = self.relogio()
        if (self.estado is Estado.ESCUTANDO and self._fala is not None):
            texto, quando = self._fala
            if (agora - quando >= SILENCIO):
                self._enviar_pedido(texto)
        self._aplicar(self.dispensa.tique(agora))

    def ao_responder(self, bruto: Any) -> None:
        if not self.dispensa.visivel:
            return
        try:
            resposta = ler_resposta(bruto)
        except ErroDoBackend as erro:
            self._concluir(erro.mensagem)
            return
        except RespostaInvalida as erro:
            registrador.error("Resposta fora do contrato: %s", erro)
            self._concluir(MENSAGEM_DE_FALHA)
            return

        if resposta.sessao:
            self.sessao = resposta.sessao
        self._executar(resposta)

    def ao_falhar(self, erro: Exception) -> None:
        registrador.error("Falha no backend: %s", erro)
        if self.dispensa.visivel:
            self._concluir(MENSAGEM_DE_FALHA)

    def _enviar_pedido(self, texto: str) -> None:
        self._fala = None
        # O microfone desliga: ligado, ele ouve o "concluído" falado pela caixa
        # e manda de novo como pedido. Pedido emendado e outro Option+9.
        self.microfone.parar()
        self.dispensa.pedido_enviado()
        self.caixa.marcar_pensando(True)
        self.enviar(montar_pedido(texto, self.retrato(), self.sessao))

    def _executar(self, resposta: Resposta) -> None:
        falhas: list[str] = []
        if resposta.acoes:
            try:
                falhas = self.executor.executar(resposta.acoes)
            except Exception as erro:  # noqa: BLE001 - a caixa nao pode morrer
                registrador.exception("Falha ao executar acoes: %s", erro)
                falhas = ["não consegui mexer nas janelas"]

        if falhas:
            self._concluir("; ".join(falhas))
        else:
            self._concluir(resposta.fala)

    def _concluir(self, mensagem: str) -> None:
        self.caixa.marcar_pensando(False)
        self.caixa.escrever(mensagem)
        if self.falar is not None:
            self.falar(mensagem)
        self.dispensa.concluido(self.relogio())

    def _aplicar(self, efeito: Efeito) -> None:
        if efeito is not Efeito.OCULTAR:
            return
        self.microfone.parar()
        self.caixa.ocultar()
        if self.sessao:
            # A sessao morre junto com a caixa: um pedido novo nao deve herdar
            # o historico de uma conversa que o usuario ja encerrou.
            try:
                self.enviar(montar_encerramento(self.sessao))
            except Exception as erro:  # noqa: BLE001
                registrador.debug("Nao consegui encerrar a sessao: %s", erro)
            self.sessao = None

    @property
    def estado(self) -> Estado:
        return self.dispensa.estado
