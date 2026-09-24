"""As regras que fazem a caixa sumir.

Este e o coracao do produto. A caixa precisa sumir sozinha: se ela exigir que o
usuario a dispense, vira mais uma janela para gerenciar — exatamente o problema
que veio resolver.

Sao tres gatilhos, o que vier primeiro:

* passam 5 segundos sem pedido novo;
* o usuario comeca a digitar, sinal claro de que voltou ao trabalho;
* o usuario aperta Esc.

O modulo e uma maquina de estados pura: nao importa NSPanel, nao le relogio do
sistema e nao toca em nada do macOS. Recebe o instante por parametro e devolve
o que deve acontecer. E por isso que da para testar as tres regras sem abrir
janela nenhuma.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

ESPERA_PADRAO = 5.0


class Estado(Enum):
    """Onde a caixa esta no ciclo de vida de um pedido."""

    OCULTA = auto()
    ESCUTANDO = auto()
    """Microfone ligado, esperando o usuario falar."""
    PENSANDO = auto()
    """Pedido enviado ao backend, esperando as acoes."""
    AGUARDANDO = auto()
    """Acoes executadas. O microfone segue ligado para um pedido emendado."""


class Efeito(Enum):
    """O que a camada de interface deve fazer depois de um evento."""

    NADA = auto()
    MOSTRAR = auto()
    OCULTAR = auto()


@dataclass
class Dispensa:
    """Decide quando a caixa aparece e quando some.

    O tempo entra sempre por parametro (`agora`), em segundos monotonicos.
    """

    espera: float = ESPERA_PADRAO
    estado: Estado = Estado.OCULTA
    _prazo: float | None = None

    @property
    def visivel(self) -> bool:
        return self.estado is not Estado.OCULTA

    @property
    def prazo(self) -> float | None:
        """Instante em que a caixa some sozinha, se houver contagem em curso."""
        return self._prazo

    def atalho(self, agora: float) -> Efeito:
        """O usuario apertou Option+9.

        Com a caixa ja na tela, o atalho nao a fecha: ele reinicia a escuta. Um
        atalho que alterna entre abrir e fechar faria o usuario apertar duas
        vezes por engano e perder o pedido que estava falando.
        """
        ja_estava = self.visivel
        self.estado = Estado.ESCUTANDO
        self._prazo = None
        return Efeito.NADA if ja_estava else Efeito.MOSTRAR

    def transcricao_parcial(self) -> Efeito:
        """Chegou texto novo do microfone. Enquanto se fala, nada expira."""
        if self.estado in (Estado.ESCUTANDO, Estado.AGUARDANDO):
            self.estado = Estado.ESCUTANDO
            self._prazo = None
        return Efeito.NADA

    def pedido_enviado(self) -> Efeito:
        """O pedido foi para o backend. A espera do backend nao tem prazo."""
        if self.visivel:
            self.estado = Estado.PENSANDO
            self._prazo = None
        return Efeito.NADA

    def concluido(self, agora: float) -> Efeito:
        """As acoes foram executadas. Comeca a contagem dos 5 segundos."""
        if not self.visivel:
            return Efeito.NADA
        self.estado = Estado.AGUARDANDO
        self._prazo = agora + self.espera
        return Efeito.NADA

    def digitou(self) -> Efeito:
        """O usuario digitou no aplicativo de baixo.

        Vale em qualquer estado, inclusive enquanto o backend responde: quem
        voltou a digitar ja saiu da conversa.
        """
        return self._ocultar()

    def escape(self) -> Efeito:
        """O usuario apertou Esc."""
        return self._ocultar()

    def tique(self, agora: float) -> Efeito:
        """Passagem de tempo. Devolve OCULTAR quando o prazo venceu."""
        if self._prazo is not None and agora >= self._prazo:
            return self._ocultar()
        return Efeito.NADA

    def _ocultar(self) -> Efeito:
        if not self.visivel:
            return Efeito.NADA
        self.estado = Estado.OCULTA
        self._prazo = None
        return Efeito.OCULTAR
