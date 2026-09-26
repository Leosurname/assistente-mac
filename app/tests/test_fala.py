from __future__ import annotations

import sys
from types import SimpleNamespace

from assistente_app.fala import Falante


def appkit_falso(monkeypatch):
    falas = []
    criados = []

    class Sintetizador:
        @classmethod
        def alloc(cls):
            criados.append(1)
            return cls()

        def init(self):
            return self

        def startSpeakingString_(self, mensagem):  # noqa: N802
            falas.append(mensagem)

    monkeypatch.setitem(
        sys.modules, "AppKit", SimpleNamespace(NSSpeechSynthesizer=Sintetizador)
    )
    return falas, criados


def test_fala_a_mensagem_reaproveitando_o_sintetizador(monkeypatch):
    falas, criados = appkit_falso(monkeypatch)
    falar = Falante()

    falar("pronto")
    falar("feito")

    assert falas == ["pronto", "feito"]
    assert len(criados) == 1
