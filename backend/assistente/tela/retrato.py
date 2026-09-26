"""O retrato da tela que a camada nativa manda junto com o pedido."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class RetratoInvalido(ValueError):
    """O retrato da tela chegou fora do formato do contrato."""


@dataclass(frozen=True)
class Monitor:
    largura: int
    altura: int


@dataclass(frozen=True)
class Janela:
    app: str
    x: int
    y: int
    largura: int
    altura: int


@dataclass(frozen=True)
class RetratoDaTela:
    """O que esta na tela no momento do pedido.

    Serve para a Layla saber o que ja esta aberto — e so para isso. Nao e
    licenca para arrumar o que ninguem mandou arrumar.
    """

    monitores: tuple[Monitor, ...] = ()
    apps_abertos: tuple[str, ...] = ()
    janelas: tuple[Janela, ...] = ()
    apps_instalados: tuple[str, ...] = field(default=())

    @property
    def apps_conhecidos(self) -> tuple[str, ...]:
        vistos: dict[str, None] = {}
        for nome in (
            *self.apps_abertos,
            *(j.app for j in self.janelas),
            *self.apps_instalados,
        ):
            vistos.setdefault(nome, None)
        return tuple(vistos)

    def cabe_em_algum_monitor(self, x: int, y: int, largura: int, altura: int) -> bool:
        """Diz se um retangulo cabe inteiro em pelo menos um monitor."""
        if largura <= 0 or altura <= 0 or x < 0 or y < 0:
            return False
        return any(
            x + largura <= monitor.largura and y + altura <= monitor.altura
            for monitor in self.monitores
        )

    @classmethod
    def do_dicionario(cls, bruto: Any) -> RetratoDaTela:
        """Le o retrato do JSON que chega pelo WebSocket.

        Entrada vinda de fora: campo fora do formato vira erro, nunca palpite.
        """
        if bruto is None:
            return cls()
        if not isinstance(bruto, dict):
            raise RetratoInvalido("O campo 'tela' precisa ser um objeto")

        return cls(
            monitores=tuple(
                Monitor(
                    largura=_inteiro_positivo(m, "largura"),
                    altura=_inteiro_positivo(m, "altura"),
                )
                for m in _lista(bruto, "monitores")
            ),
            apps_abertos=tuple(_textos(bruto, "apps_abertos")),
            janelas=tuple(
                Janela(
                    app=_texto(j, "app"),
                    x=_inteiro(j, "x"),
                    y=_inteiro(j, "y"),
                    largura=_inteiro_positivo(j, "largura"),
                    altura=_inteiro_positivo(j, "altura"),
                )
                for j in _lista(bruto, "janelas")
            ),
            apps_instalados=tuple(_textos(bruto, "apps_instalados")),
        )

    def resumo(self) -> str:
        """Descricao curta do retrato, para entrar no prompt."""
        linhas: list[str] = []
        if self.monitores:
            medidas = ", ".join(f"{m.largura}x{m.altura}" for m in self.monitores)
            linhas.append(f"Monitores: {medidas}")
        linhas.append(
            "Aplicativos abertos: "
            + (", ".join(self.apps_abertos) if self.apps_abertos else "nenhum")
        )
        for janela in self.janelas:
            linhas.append(
                f"Janela de {janela.app}: x={janela.x} y={janela.y} "
                f"{janela.largura}x{janela.altura}"
            )
        return "\n".join(linhas)


def _lista(bruto: dict, campo: str) -> list[dict]:
    valor = bruto.get(campo) or []
    if not isinstance(valor, list):
        raise RetratoInvalido(f"O campo '{campo}' precisa ser uma lista")
    for item in valor:
        if not isinstance(item, dict):
            raise RetratoInvalido(f"Cada item de '{campo}' precisa ser um objeto")
    return valor


def _textos(bruto: dict, campo: str) -> list[str]:
    valor = bruto.get(campo) or []
    if not isinstance(valor, list) or any(not isinstance(i, str) for i in valor):
        raise RetratoInvalido(f"O campo '{campo}' precisa ser uma lista de textos")
    return [i.strip() for i in valor if i.strip()]


def _texto(bruto: dict, campo: str) -> str:
    valor = bruto.get(campo)
    if not isinstance(valor, str) or not valor.strip():
        raise RetratoInvalido(f"O campo '{campo}' precisa ser um texto")
    return valor.strip()


def _inteiro(bruto: dict, campo: str) -> int:
    valor = bruto.get(campo)
    if isinstance(valor, bool) or not isinstance(valor, int | float):
        raise RetratoInvalido(f"O campo '{campo}' precisa ser um numero")
    return int(valor)


def _inteiro_positivo(bruto: dict, campo: str) -> int:
    valor = _inteiro(bruto, campo)
    if valor <= 0:
        raise RetratoInvalido(f"O campo '{campo}' precisa ser maior que zero")
    return valor
