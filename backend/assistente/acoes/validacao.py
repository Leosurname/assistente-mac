"""Validacao das acoes que a Layla devolve.

Nada do que o modelo escreve chega ao executor sem passar por aqui. Quatro
perguntas: a acao esta no catalogo, o app existe, as coordenadas cabem na tela,
e o app foi citado no pedido. A ultima e a que protege mais: quem pede "terminal
e Safari" esta dizendo o que quer ver, nao o que quer sumir — aplicativo nao
citado fica onde esta, mesmo que a Layla ache que ficaria melhor de outro jeito.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from assistente.acoes import catalogo, nomes
from assistente.tela import retrato

# Reexportados: outros modulos usam validacao.app_foi_citado e validacao.normalizar.
app_foi_citado = nomes.app_foi_citado
normalizar = nomes.normalizar

__all__ = [
    "AcaoValidada",
    "Recusa",
    "ResultadoDaValidacao",
    "app_foi_citado",
    "normalizar",
    "validar_acoes",
]


@dataclass(frozen=True)
class AcaoValidada:
    """Uma acao que passou por tudo e pode ir para o executor."""

    acao: str
    app: str
    regiao: str | None = None

    def para_dicionario(self) -> dict[str, Any]:
        corpo: dict[str, Any] = {"acao": self.acao, "app": self.app}
        if self.regiao is not None:
            corpo["regiao"] = self.regiao
        return corpo


@dataclass(frozen=True)
class Recusa:
    """Uma acao descartada, com o motivo em portugues."""

    bruta: Any
    motivo: str


@dataclass(frozen=True)
class ResultadoDaValidacao:
    aprovadas: tuple[AcaoValidada, ...]
    recusadas: tuple[Recusa, ...]

    @property
    def houve_recusa(self) -> bool:
        return bool(self.recusadas)


def validar_acoes(
    brutas: Any,
    *,
    tela: retrato.RetratoDaTela,
    textos_do_usuario: Sequence[str],
) -> ResultadoDaValidacao:
    """Filtra a lista de acoes da Layla, guardando o motivo de cada recusa."""
    if not isinstance(brutas, list):
        return ResultadoDaValidacao(
            (), (Recusa(brutas, "a lista de acoes nao e uma lista"),)
        )

    aprovadas: list[AcaoValidada] = []
    recusadas: list[Recusa] = []

    for bruta in brutas:
        erro = _motivo_da_recusa(bruta, tela=tela, textos_do_usuario=textos_do_usuario)
        if erro is not None:
            recusadas.append(Recusa(bruta, erro))
            continue
        aprovadas.append(
            AcaoValidada(
                acao=bruta["acao"],
                app=str(bruta["app"]).strip(),
                regiao=bruta.get("regiao"),
            )
        )

    return ResultadoDaValidacao(tuple(aprovadas), tuple(recusadas))


def _motivo_da_recusa(
    bruta: Any, *, tela: retrato.RetratoDaTela, textos_do_usuario: Sequence[str]
) -> str | None:
    if not isinstance(bruta, dict):
        return "a acao nao e um objeto"

    acao = bruta.get("acao")
    if not isinstance(acao, str) or acao not in catalogo.CATALOGO:
        return f"a acao {acao!r} nao esta no catalogo"

    app = bruta.get("app")
    if not isinstance(app, str) or not app.strip():
        return "a acao nao diz sobre qual aplicativo"
    app = app.strip()

    if not nomes.app_existe(app, tela):
        return f"nao encontrei o aplicativo {app!r} nesta maquina"

    if not nomes.app_foi_citado(app, textos_do_usuario):
        return f"o aplicativo {app!r} nao foi citado no pedido"

    if acao == catalogo.POSICIONAR:
        return _motivo_da_recusa_de_posicionamento(bruta, tela=tela)

    if bruta.get("regiao") is not None:
        return f"a acao {acao!r} nao aceita regiao"

    return None


def _motivo_da_recusa_de_posicionamento(
    bruta: dict, *, tela: retrato.RetratoDaTela
) -> str | None:
    regiao = bruta.get("regiao")
    if regiao is None:
        return "posicionar sem dizer a regiao"
    if not isinstance(regiao, str) or regiao not in catalogo.REGIOES:
        return f"a regiao {regiao!r} nao existe"

    # A Layla trabalha com nomes de regiao, mas se mandar coordenadas elas
    # precisam caber em algum monitor. Janela fora da tela e janela perdida.
    coordenadas = [bruta.get(c) for c in ("x", "y", "largura", "altura")]
    if any(c is not None for c in coordenadas):
        if any(not isinstance(c, int) or isinstance(c, bool) for c in coordenadas):
            return "as coordenadas precisam ser quatro numeros inteiros"
        x, y, largura, altura = coordenadas  # type: ignore[misc]
        if not tela.cabe_em_algum_monitor(x, y, largura, altura):
            return "as coordenadas nao cabem na tela"

    return None
