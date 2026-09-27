# A beta é só texto: o app sobe sem microfone e sem permissão de fala.

from __future__ import annotations

import pytest

pytest.importorskip("AppKit")

from assistente_app import montagem, voz  # noqa: E402


class Falso:
    def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
        self.rodou = False

    def iniciar(self) -> None:
        pass

    def enviar(self, corpo) -> None:  # noqa: ANN001
        pass

    def run(self) -> None:
        self.rodou = True


def test_sem_microfone_o_app_monta_e_nao_encerra(monkeypatch):
    def sem_microfone(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
        raise voz.MicrofoneIndisponivel("sem microfone")

    aplicativo = Falso()
    instalados = []
    monkeypatch.setattr(voz, "Microfone", sem_microfone)
    monkeypatch.setattr(montagem, "_criar_aplicativo", lambda: aplicativo)
    monkeypatch.setattr(montagem, "Sobreposicao", Falso)
    monkeypatch.setattr(montagem, "ExecutorDeJanelas", Falso)
    monkeypatch.setattr(montagem, "ClienteDoBackend", Falso)
    monkeypatch.setattr(montagem, "Falante", Falso)
    monkeypatch.setattr(
        montagem, "_instalar_teclado", lambda c: instalados.append(c) or True
    )
    monkeypatch.setattr(montagem, "_iniciar_tique", lambda _: None)

    assert montagem.principal() == 0
    assert aplicativo.rodou
    assert len(instalados) == 1
