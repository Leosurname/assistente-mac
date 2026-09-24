"""O retrato da tela que vai junto com cada pedido.

Sem isto a Layla nao tem como decidir o que abrir e o que ja esta aberto. E
tambem daqui que sai `apps_instalados`: o backend nao le `/Applications` — ele
nao deve tocar no disco do usuario — entao quem diz o que existe na maquina e
esta camada.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from AppKit import (
    NSApplicationActivationPolicyRegular,
    NSScreen,
    NSWorkspace,
)
from Quartz import (
    CGWindowListCopyWindowInfo,
    kCGNullWindowID,
    kCGWindowListExcludeDesktopElements,
    kCGWindowListOptionOnScreenOnly,
)

from assistente_app.regioes import AreaUtil

registrador = logging.getLogger(__name__)

PASTAS_DE_APLICATIVOS = (
    "/Applications",
    "/Applications/Utilities",
    "/System/Applications",
    "/System/Applications/Utilities",
    os.path.expanduser("~/Applications"),
)


def montar() -> dict[str, Any]:
    """Monta o retrato no formato do contrato do ARCHITECTURE.md."""
    return {
        "monitores": monitores(),
        "apps_abertos": apps_abertos(),
        "janelas": janelas(),
        "apps_instalados": apps_instalados(),
    }


def monitores() -> list[dict[str, int]]:
    return [
        {
            "largura": int(tela.frame().size.width),
            "altura": int(tela.frame().size.height),
        }
        for tela in NSScreen.screens()
    ]


def area_util(indice: int = 0) -> AreaUtil:
    """A area onde da para por janela: sem a barra de menu e sem o Dock.

    O `visibleFrame` do AppKit ja desconta as duas, mas vem em coordenadas com
    origem embaixo. A API de acessibilidade, que e quem move a janela, usa
    origem em cima — a conversao de y acontece aqui.
    """
    telas = NSScreen.screens()
    if not telas:
        raise RuntimeError("nenhum monitor encontrado")
    tela = telas[indice] if indice < len(telas) else telas[0]

    visivel = tela.visibleFrame()
    completa = tela.frame()
    y_de_cima = completa.size.height - (visivel.origin.y + visivel.size.height)

    return AreaUtil(
        x=int(visivel.origin.x),
        y=int(y_de_cima),
        largura=int(visivel.size.width),
        altura=int(visivel.size.height),
    )


def apps_abertos() -> list[str]:
    """Aplicativos com interface, na ordem em que o sistema os lista.

    Processos de fundo ficam de fora: o usuario nao pensa neles como janelas, e
    incluir tudo encheria o prompt de ruido.
    """
    nomes: list[str] = []
    for app in NSWorkspace.sharedWorkspace().runningApplications():
        if app.activationPolicy() != NSApplicationActivationPolicyRegular:
            continue
        nome = app.localizedName()
        if nome and nome not in nomes:
            nomes.append(str(nome))
    return nomes


def janelas() -> list[dict[str, Any]]:
    """Janelas visiveis, com posicao e tamanho em coordenadas de tela."""
    informacoes = (
        CGWindowListCopyWindowInfo(
            kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements,
            kCGNullWindowID,
        )
        or []
    )

    encontradas: list[dict[str, Any]] = []
    for janela in informacoes:
        dono = janela.get("kCGWindowOwnerName")
        limites = janela.get("kCGWindowBounds")
        if not dono or not limites:
            continue
        largura = int(limites.get("Width", 0))
        altura = int(limites.get("Height", 0))
        # Janelas minusculas sao quase sempre sombra, tooltip ou barra de
        # status. Nao ajudam a Layla e so gastam contexto.
        if largura < 100 or altura < 100:
            continue
        encontradas.append(
            {
                "app": str(dono),
                "x": int(limites.get("X", 0)),
                "y": int(limites.get("Y", 0)),
                "largura": largura,
                "altura": altura,
            }
        )
    return encontradas


def apps_instalados() -> list[str]:
    """O que existe na maquina, pelo nome que o usuario ve no Finder."""
    nomes: list[str] = []
    for pasta in PASTAS_DE_APLICATIVOS:
        try:
            itens = os.listdir(pasta)
        except OSError:
            continue
        for item in itens:
            if not item.endswith(".app"):
                continue
            nome = item[: -len(".app")]
            if nome not in nomes:
                nomes.append(nome)
    return sorted(nomes)
