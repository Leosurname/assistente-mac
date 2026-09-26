# O __main__ só chama a montagem e sai com o código dela.

from __future__ import annotations

import runpy

import pytest

pytest.importorskip("AppKit")

from assistente_app import montagem  # noqa: E402


def test_main_sobe_a_montagem_e_sai_com_o_codigo_dela(monkeypatch):
    chamadas = []
    monkeypatch.setattr(montagem, "principal", lambda: chamadas.append(1) or 7)

    with pytest.raises(SystemExit) as saida:
        runpy.run_module("assistente_app", run_name="__main__")

    assert saida.value.code == 7
    assert chamadas == [1]
