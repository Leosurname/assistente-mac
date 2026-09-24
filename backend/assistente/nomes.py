"""Reconhecimento de nome de aplicativo no que o usuario falou."""

from __future__ import annotations

import unicodedata
from collections.abc import Iterable

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


def normalizar(texto: str) -> str:
    """Deixa o texto comparavel: sem acento, sem caixa, sem espaco sobrando."""
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return " ".join(sem_acento.lower().split())


def formas_do_app(app: str) -> tuple[str, ...]:
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
    return any(forma in pedido for forma in formas_do_app(app))


def app_existe(app: str, tela: RetratoDaTela) -> bool:
    """Diz se o aplicativo existe nesta maquina.

    Quem responde isso e `apps_instalados`, e nao a lista de apps abertos:
    `abrir_app` existe justamente para o que ainda nao esta aberto.

    Sem `apps_instalados` o backend nao enxerga /Applications, e quem recusa na
    hora de abrir e a camada nativa. A regra do "so se mexe no que foi pedido"
    continua valendo, e e ela que segura a porta.
    """
    if not tela.apps_instalados:
        return True
    conhecidos = (*tela.apps_instalados, *tela.apps_abertos)
    formas = set(formas_do_app(app))
    return any(formas & set(formas_do_app(conhecido)) for conhecido in conhecidos)
