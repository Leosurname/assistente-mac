# Leva um bloco para a thread principal: tudo que é AppKit precisa rodar nela.

from __future__ import annotations

from Foundation import NSOperationQueue


def despachar_na_principal(bloco) -> None:  # noqa: ANN001
    NSOperationQueue.mainQueue().addOperationWithBlock_(bloco)
