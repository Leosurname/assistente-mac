# O retrato da tela com o AppKit de mentira: nada de tela ou app de verdade.

from __future__ import annotations

from types import SimpleNamespace

import pytest

pytest.importorskip("AppKit")

from assistente_app import contexto  # noqa: E402


class RetanguloFalso:
    def __init__(self, x: float, y: float, largura: float, altura: float) -> None:
        self.origin = SimpleNamespace(x=x, y=y)
        self.size = SimpleNamespace(width=largura, height=altura)


class TelaFalsa:
    def __init__(self, completa: RetanguloFalso, visivel: RetanguloFalso) -> None:
        self._completa = completa
        self._visivel = visivel

    def frame(self):
        return self._completa

    def visibleFrame(self):
        return self._visivel


class AppFalso:
    def __init__(self, nome: str, regular: bool) -> None:
        self._nome = nome
        self._regular = regular

    def localizedName(self):
        return self._nome

    def activationPolicy(self):
        from AppKit import (
            NSApplicationActivationPolicyAccessory,
            NSApplicationActivationPolicyRegular,
        )

        return (
            NSApplicationActivationPolicyRegular
            if (self._regular)
            else NSApplicationActivationPolicyAccessory
        )


def test_area_util_converte_o_y_do_cocoa_para_origem_de_cima(
    monkeypatch: pytest.MonkeyPatch,
):
    completa = RetanguloFalso(x=0, y=0, largura=1000, altura=1000)
    visivel = RetanguloFalso(x=0, y=30, largura=1000, altura=920)
    monkeypatch.setattr(
        contexto, "NSScreen", SimpleNamespace(screens=lambda: [TelaFalsa(completa, visivel)])
    )

    area = contexto.area_util()

    assert area.y == 50
    assert area.altura == 920


def test_janelas_filtra_as_muito_pequenas(monkeypatch: pytest.MonkeyPatch):
    def informacoes(*_args, **_kwargs):
        return [
            {
                "kCGWindowOwnerName": "Safari",
                "kCGWindowBounds": {"X": 0, "Y": 0, "Width": 800, "Height": 600},
            },
            {
                "kCGWindowOwnerName": "Notificacao",
                "kCGWindowBounds": {"X": 0, "Y": 0, "Width": 40, "Height": 40},
            },
        ]

    monkeypatch.setattr(contexto, "CGWindowListCopyWindowInfo", informacoes)

    resultado = contexto.janelas()

    assert [j["app"] for j in resultado] == ["Safari"]


def test_apps_abertos_remove_duplicado_e_ignora_processo_de_fundo(
    monkeypatch: pytest.MonkeyPatch,
):
    rodando = [
        AppFalso("Safari", regular=True),
        AppFalso("Safari", regular=True),
        AppFalso("SistemaDeFundo", regular=False),
    ]
    workspace = SimpleNamespace(
        sharedWorkspace=lambda: SimpleNamespace(runningApplications=lambda: rodando)
    )
    monkeypatch.setattr(contexto, "NSWorkspace", workspace)

    assert contexto.apps_abertos() == ["Safari"]


def test_apps_instalados_sai_ordenado_sem_duplicado(tmp_path, monkeypatch):
    pasta_a = tmp_path / "a"
    pasta_b = tmp_path / "b"
    pasta_a.mkdir()
    pasta_b.mkdir()
    (pasta_a / "Zoom.app").mkdir()
    (pasta_a / "Terminal.app").mkdir()
    (pasta_b / "Terminal.app").mkdir()
    monkeypatch.setattr(contexto, "PASTAS_DE_APLICATIVOS", (str(pasta_a), str(pasta_b)))

    assert contexto.apps_instalados() == ["Terminal", "Zoom"]


def test_apps_instalados_ignora_itens_que_nao_sao_app(tmp_path, monkeypatch):
    pasta = tmp_path / "a"
    pasta.mkdir()
    (pasta / "Terminal.app").mkdir()
    (pasta / "leiame.txt").write_text("nada")
    monkeypatch.setattr(contexto, "PASTAS_DE_APLICATIVOS", (str(pasta),))

    assert contexto.apps_instalados() == ["Terminal"]
