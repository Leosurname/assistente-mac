from __future__ import annotations

import pytest

pytest.importorskip("AppKit")

from assistente_app import busca  # noqa: E402


class Processo:
    def __init__(self, nome: str, de_fundo: bool = False) -> None:
        self._nome = nome
        self._politica = 1 if (de_fundo) else busca.NSApplicationActivationPolicyRegular

    def localizedName(self) -> str:  # noqa: N802
        return self._nome

    def activationPolicy(self) -> int:  # noqa: N802
        return self._politica

    def processIdentifier(self) -> int:  # noqa: N802
        return 42


@pytest.fixture
def processos(monkeypatch: pytest.MonkeyPatch) -> list[Processo]:
    lista: list[Processo] = []

    class Area:
        def runningApplications(self):  # noqa: N802
            return lista

    class NSWorkspace:
        sharedWorkspace = Area  # noqa: N815

    monkeypatch.setattr(busca, "NSWorkspace", NSWorkspace)
    return lista


def test_rodando_acha_o_app_sem_ligar_para_maiusculas(processos):
    processos.append(Processo("Safari"))

    assert busca.rodando("safari").localizedName() == "Safari"


def test_rodando_ignora_processo_de_fundo(processos):
    processos.append(Processo("Terminal", de_fundo=True))

    assert busca.rodando("Terminal") is None


def test_caminho_do_aplicativo_acha_o_pacote_pelo_nome(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    (tmp_path / "Claude Code.app").mkdir()
    (tmp_path / "claude code.txt").touch()
    pastas = (str(tmp_path / "nao-existe"), str(tmp_path))
    monkeypatch.setattr(busca.contexto, "PASTAS_DE_APLICATIVOS", pastas)

    assert busca.caminho_do_aplicativo("claude code") == f"{tmp_path}/Claude Code.app"
    assert busca.caminho_do_aplicativo("Photoshop") is None


def test_primeira_janela_espera_o_app_recem_aberto(
    processos, monkeypatch: pytest.MonkeyPatch
):
    esperas: list[float] = []

    def dormir(segundos: float) -> None:
        esperas.append(segundos)
        if (len(esperas) == 2):
            processos.append(Processo("Terminal"))

    monkeypatch.setattr(busca.time, "sleep", dormir)
    monkeypatch.setattr(busca, "AXUIElementCreateApplication", lambda pid: pid)
    monkeypatch.setattr(
        busca,
        "AXUIElementCopyAttributeValue",
        lambda _elemento, _atributo, _nada: (busca.kAXErrorSuccess, ["janela"]),
    )

    assert busca.primeira_janela("Terminal", esperar=True) == "janela"
    assert len(esperas) == 2
