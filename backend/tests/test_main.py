from __future__ import annotations

import runpy
from pathlib import Path
from typing import Any

import pytest
import uvicorn
from fastapi import FastAPI

MAIN = Path(__file__).resolve().parent.parent / "main.py"


def test_main_configura_os_logs_e_sobe_o_uvicorn_com_o_app(
    monkeypatch: pytest.MonkeyPatch,
):
    chamadas: list[dict[str, Any]] = []

    def uvicorn_run_de_mentira(aplicativo: FastAPI, **kwargs: Any) -> None:
        chamadas.append({"aplicativo": aplicativo, **kwargs})

    monkeypatch.setattr(uvicorn, "run", uvicorn_run_de_mentira)

    runpy.run_path(str(MAIN), run_name="__main__")

    assert len(chamadas) == 1
    assert isinstance(chamadas[0]["aplicativo"], FastAPI)
