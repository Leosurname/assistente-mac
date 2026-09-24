"""Configuracao dos logs do backend."""

from __future__ import annotations

import logging
import os

FORMATO = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


def configurar(nivel: str | None = None) -> None:
    """Liga os logs no nivel pedido por `LOG_LEVEL`.

    Nada de transcricao em log por padrao: o que o usuario fala e conteudo dele,
    e um log e o lugar mais facil de vazar isso sem querer. Em DEBUG o texto
    aparece, e ai a escolha e de quem ligou o DEBUG.
    """
    bruto = (nivel or os.getenv("LOG_LEVEL") or "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, bruto, logging.INFO), format=FORMATO, force=True
    )
