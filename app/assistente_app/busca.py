"""Acha o aplicativo e a janela no sistema, pelo nome que o usuario usaria."""

from __future__ import annotations

import os
import time
from typing import Any

from AppKit import NSApplicationActivationPolicyRegular, NSWorkspace
from ApplicationServices import (
    AXUIElementCopyAttributeValue,
    AXUIElementCreateApplication,
    kAXErrorSuccess,
    kAXWindowsAttribute,
)

from assistente_app import contexto

ESPERA_ENTRE_TENTATIVAS = 0.25
TENTATIVAS_APOS_ABRIR = 20


def rodando(nome: str) -> Any | None:
    procurado = nome.casefold()
    for app in NSWorkspace.sharedWorkspace().runningApplications():
        if app.activationPolicy() != NSApplicationActivationPolicyRegular:
            continue
        local = (app.localizedName() or "").casefold()
        if local == procurado or procurado in local:
            return app
    return None


def caminho_do_aplicativo(nome: str) -> str | None:
    procurado = nome.casefold()
    for pasta in contexto.PASTAS_DE_APLICATIVOS:
        try:
            itens = os.listdir(pasta)
        except OSError:
            continue
        for item in itens:
            if not item.endswith(".app"):
                continue
            if item[: -len(".app")].casefold() == procurado:
                return f"{pasta}/{item}"
    return None


def primeira_janela(nome: str, esperar: bool = False) -> Any | None:
    """A janela principal do aplicativo, pela API de acessibilidade.

    Com `esperar`, tenta de novo por alguns segundos: aplicativo recem-aberto
    demora a ter janela, e posicionar logo depois de abrir e o caso comum.
    """
    tentativas = TENTATIVAS_APOS_ABRIR if esperar else 1
    for _ in range(tentativas):
        app = rodando(nome)
        if app is not None:
            elemento = AXUIElementCreateApplication(app.processIdentifier())
            codigo, janelas = AXUIElementCopyAttributeValue(
                elemento, kAXWindowsAttribute, None
            )
            if codigo == kAXErrorSuccess and janelas:
                return janelas[0]
        if esperar:
            time.sleep(ESPERA_ENTRE_TENTATIVAS)
    return None
