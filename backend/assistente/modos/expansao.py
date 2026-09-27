# Transforma um modo nas acoes do catalogo que ele representa.

from __future__ import annotations

from collections.abc import Sequence

from assistente.acoes import catalogo, nomes
from assistente.modos import arranjos
from assistente.tela import retrato


# O modo so vale se o usuario falou nele: sem isso a Layla teria um jeito de
# mexer em app que ninguem citou, bastando escolher um modo.
def modo_citado(chave: str, textos_do_usuario: Sequence[str]) -> bool:
    modo = arranjos.MODOS.get(chave)
    pedido = " ".join(nomes.normalizar(t) for t in textos_do_usuario)
    if (modo is None or not pedido):
        return False
    return any(nomes.normalizar(frase) in pedido for frase in modo.frases)


def apps_do_modo(chave: str) -> tuple[str, ...]:
    return tuple(app for app, _ in arranjos.MODOS[chave].passos)


def expandir(chave: str, tela: retrato.RetratoDaTela) -> list[dict]:
    abertos = {nomes.normalizar(app) for app in tela.apps_abertos}
    acoes: list[dict] = []
    for app, regiao in arranjos.MODOS[chave].passos:
        if (nomes.normalizar(app) not in abertos):
            acoes.append({"acao": catalogo.ABRIR_APP, "app": app})
        if (regiao is not None):
            acoes.append({"acao": catalogo.POSICIONAR, "app": app, "regiao": regiao})
    return acoes
