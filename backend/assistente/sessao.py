"""Sessoes: o historico curto que faz "agora joga pra direita" ter sentido.

A sessao vive tanto quanto a caixa de sobreposicao. Ela expira junto, porque
o produto e uma caixa que some sozinha: guardar conversa alem disso seria
lembrar de algo que o usuario ja considerou encerrado.
"""

from __future__ import annotations

import time
import uuid
from collections import deque
from dataclasses import dataclass, field

from assistente.layla.interface import Mensagem

VALIDADE_PADRAO = 120.0
MAXIMO_DE_TURNOS = 6


@dataclass
class Sessao:
    identificador: str
    validade: float = VALIDADE_PADRAO
    atualizada_em: float = field(default_factory=time.monotonic)
    historico: deque[Mensagem] = field(
        default_factory=lambda: deque(maxlen=MAXIMO_DE_TURNOS * 2)
    )
    pedidos: deque[str] = field(default_factory=lambda: deque(maxlen=MAXIMO_DE_TURNOS))

    def expirou(self, agora: float | None = None) -> bool:
        agora = time.monotonic() if agora is None else agora
        return agora - self.atualizada_em > self.validade

    def registrar(self, pedido: str, resposta: str) -> None:
        """Guarda um turno completo e reinicia a contagem de validade."""
        self.pedidos.append(pedido)
        self.historico.append(Mensagem("usuario", pedido))
        self.historico.append(Mensagem("assistente", resposta))
        self.atualizada_em = time.monotonic()

    def tocar(self) -> None:
        self.atualizada_em = time.monotonic()


class RegistroDeSessoes:
    """Guarda as sessoes vivas e joga fora as que passaram da validade."""

    def __init__(self, validade: float = VALIDADE_PADRAO) -> None:
        self.validade = validade
        self._sessoes: dict[str, Sessao] = {}

    def obter(self, identificador: str | None) -> Sessao:
        """Devolve a sessao pedida, ou uma nova se ela nao existe ou expirou."""
        self.limpar()
        if identificador and identificador in self._sessoes:
            sessao = self._sessoes[identificador]
            sessao.tocar()
            return sessao

        nova = Sessao(
            identificador=identificador or uuid.uuid4().hex, validade=self.validade
        )
        self._sessoes[nova.identificador] = nova
        return nova

    def encerrar(self, identificador: str) -> None:
        """Esquece a sessao. A caixa sumiu, a conversa acabou."""
        self._sessoes.pop(identificador, None)

    def limpar(self) -> int:
        """Descarta as sessoes expiradas e diz quantas foram."""
        agora = time.monotonic()
        vencidas = [i for i, s in self._sessoes.items() if s.expirou(agora)]
        for identificador in vencidas:
            del self._sessoes[identificador]
        return len(vencidas)

    def __len__(self) -> int:
        return len(self._sessoes)
