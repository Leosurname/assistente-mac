# A voz é opcional: o app sobe sem microfone e sem permissão de fala.

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


def montar_sem_macos(monkeypatch):  # noqa: ANN001, ANN201
    aplicativo = Falso()
    instalados = []
    monkeypatch.setattr(montagem, "_criar_aplicativo", lambda: aplicativo)
    monkeypatch.setattr(montagem, "Sobreposicao", Falso)
    monkeypatch.setattr(montagem, "ExecutorDeJanelas", Falso)
    monkeypatch.setattr(montagem, "ClienteDoBackend", Falso)
    monkeypatch.setattr(montagem, "Falante", Falso)
    monkeypatch.setattr(
        montagem, "_instalar_teclado", lambda c: instalados.append(c) or True
    )
    monkeypatch.setattr(montagem, "_iniciar_tique", lambda _: None)
    return aplicativo, instalados


def test_sem_microfone_o_app_monta_e_nao_encerra(monkeypatch):
    def sem_microfone(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
        raise voz.MicrofoneIndisponivel("sem microfone")

    monkeypatch.setattr(voz, "Microfone", sem_microfone)
    aplicativo, instalados = montar_sem_macos(monkeypatch)

    assert montagem.principal() == 0
    assert aplicativo.rodou
    assert instalados[0].microfone is None


def test_fala_negada_nao_derruba_o_app(monkeypatch):
    class MicrofoneSemPermissao(Falso):
        @staticmethod
        def pedir_permissao(responder) -> None:  # noqa: ANN001
            responder(False)

        def parar(self) -> None:
            pass

    monkeypatch.setattr(voz, "Microfone", MicrofoneSemPermissao)
    monkeypatch.setattr(montagem, "despachar_na_principal", lambda bloco: bloco())
    aplicativo, instalados = montar_sem_macos(monkeypatch)

    assert montagem.principal() == 0
    assert aplicativo.rodou
    assert instalados[0].microfone is None
