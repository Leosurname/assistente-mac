"""Validacao das acoes que a Layla devolve.

Nada do que o modelo escreve chega ao executor sem passar por aqui. A
decodificacao restrita do `llama-server` garante que a resposta seja um JSON
bem formado; garantir que ela faca sentido e trabalho deste modulo.

Quatro perguntas, na ordem:

1. A acao esta no catalogo fechado?
2. O aplicativo existe nesta maquina?
3. As coordenadas cabem na tela?
4. O aplicativo foi citado no pedido?

A quarta e a que custa mais e protege mais. Quem pede "terminal e Safari" esta
dizendo o que quer ver, nao o que quer sumir. Aplicativo nao citado fica onde
esta, mesmo que a Layla ache que ficaria melhor de outro jeito.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from assistente.acoes import CATALOGO, POSICIONAR, REGIOES
from assistente.tela import RetratoDaTela

# Nomes alternativos pelos quais um aplicativo costuma ser chamado em voz alta.
# Sem isso, "abre o terminal" nao casaria com o aplicativo "Terminal.app", e
# ninguem fala "Visual Studio Code" inteiro.
APELIDOS: dict[str, tuple[str, ...]] = {
    "terminal": ("terminal", "iterm", "console"),
    "safari": ("safari", "navegador"),
    "claude code": ("claude code", "claude", "cloud code"),
    "visual studio code": ("visual studio code", "vscode", "vs code", "code"),
    "finder": ("finder", "arquivos"),
    "google chrome": ("google chrome", "chrome"),
    "notas": ("notas", "notes"),
    "musica": ("musica", "music", "itunes"),
    "spotify": ("spotify",),
    "mensagens": ("mensagens", "messages", "imessage"),
}


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


def normalizar(texto: str) -> str:
    """Deixa o texto comparavel: sem acento, sem caixa, sem espaco sobrando."""
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return " ".join(sem_acento.lower().split())


def _formas_do_app(app: str) -> tuple[str, ...]:
    """Todos os jeitos de chamar um aplicativo, ja normalizados."""
    base = normalizar(app)
    formas = {base, *base.split()} if base else set()
    for canonico, apelidos in APELIDOS.items():
        if base == canonico or base in apelidos:
            formas.update(normalizar(a) for a in apelidos)
            formas.add(canonico)
    return tuple(f for f in formas if f)


def app_foi_citado(app: str, textos_do_usuario: Iterable[str]) -> bool:
    """Diz se o aplicativo aparece em alguma fala do usuario nesta sessao.

    O historico conta, e nao so o pedido de agora: "agora joga o Safari pra
    direita" vem depois de um pedido em que o Safari foi citado, e continua
    sendo um aplicativo sobre o qual o usuario falou.
    """
    pedido = " ".join(normalizar(t) for t in textos_do_usuario)
    if not pedido:
        return False
    return any(forma in pedido for forma in _formas_do_app(app))


def _app_existe(app: str, tela: RetratoDaTela) -> bool:
    """Diz se o aplicativo existe nesta maquina.

    Quem responde isso e o campo `apps_instalados` do retrato. Nao da para usar
    a lista de aplicativos abertos: `abrir_app` existe justamente para o que
    ainda nao esta aberto, e exigir que o app ja estivesse na tela tornaria a
    acao impossivel.

    Sem `apps_instalados`, o backend nao tem como saber o que existe em
    /Applications — quem enxerga isso e a camada nativa, e e ela que recusa na
    hora de abrir. A regra do "so se mexe no que foi pedido" continua valendo, e
    e ela que segura a porta.
    """
    if not tela.apps_instalados:
        return True
    conhecidos = (*tela.apps_instalados, *tela.apps_abertos)
    formas = set(_formas_do_app(app))
    return any(formas & set(_formas_do_app(conhecido)) for conhecido in conhecidos)


def validar_acoes(
    brutas: Any,
    *,
    tela: RetratoDaTela,
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
    bruta: Any, *, tela: RetratoDaTela, textos_do_usuario: Sequence[str]
) -> str | None:
    if not isinstance(bruta, dict):
        return "a acao nao e um objeto"

    acao = bruta.get("acao")
    if not isinstance(acao, str) or acao not in CATALOGO:
        return f"a acao {acao!r} nao esta no catalogo"

    app = bruta.get("app")
    if not isinstance(app, str) or not app.strip():
        return "a acao nao diz sobre qual aplicativo"
    app = app.strip()

    if not _app_existe(app, tela):
        return f"nao encontrei o aplicativo {app!r} nesta maquina"

    if not app_foi_citado(app, textos_do_usuario):
        return f"o aplicativo {app!r} nao foi citado no pedido"

    if acao == POSICIONAR:
        return _motivo_da_recusa_de_posicionamento(bruta, tela=tela)

    if bruta.get("regiao") is not None:
        return f"a acao {acao!r} nao aceita regiao"

    return None


def _motivo_da_recusa_de_posicionamento(
    bruta: dict, *, tela: RetratoDaTela
) -> str | None:
    regiao = bruta.get("regiao")
    if regiao is None:
        return "posicionar sem dizer a regiao"
    if not isinstance(regiao, str) or regiao not in REGIOES:
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
