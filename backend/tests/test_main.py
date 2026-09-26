"""Testes do ponto de entrada. Nunca sobe servidor de verdade: uvicorn.run e mockado."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi import FastAPI


def test_principal_sobe_o_uvicorn_no_host_e_porta_certos(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("ASSISTENTE_PORTA", "9001")
    chamadas: list[dict[str, Any]] = []

    def uvicorn_run_de_mentira(aplicativo: FastAPI, **kwargs: Any) -> None:
        chamadas.append({"aplicativo": aplicativo, **kwargs})

    import main

    monkeypatch.setattr(main.uvicorn, "run", uvicorn_run_de_mentira)

    main.principal()

    assert len(chamadas) == 1
    assert isinstance(chamadas[0]["aplicativo"], FastAPI)
    assert chamadas[0]["host"] == main.servidor.ENDERECO_PADRAO
    assert chamadas[0]["port"] == 9001
    assert chamadas[0]["log_config"] is None


def test_principal_usa_a_porta_padrao_sem_variavel_de_ambiente(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv("ASSISTENTE_PORTA", raising=False)
    portas: list[int] = []

    import main

    monkeypatch.setattr(
        main.uvicorn, "run", lambda aplicativo, **kwargs: portas.append(kwargs["port"])
    )

    main.principal()

    assert portas == [main.servidor.PORTA_PADRAO]


def test_validade_de_sessao_invalida_no_ambiente_levanta_erro_claro(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("ASSISTENTE_VALIDADE_SESSAO", "eterna")

    import main

    monkeypatch.setattr(main.uvicorn, "run", lambda *a, **k: None)

    with pytest.raises(ValueError, match="ASSISTENTE_VALIDADE_SESSAO"):
        main.principal()


def test_validade_de_sessao_vazia_cai_no_padrao(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ASSISTENTE_VALIDADE_SESSAO", raising=False)
    sessoes_criadas: list[Any] = []

    import main

    registro_original = main.sessao.RegistroDeSessoes

    def registro_de_sessoes_espiao(*args: Any, **kwargs: Any):
        sessoes = registro_original(*args, **kwargs)
        sessoes_criadas.append(sessoes)
        return sessoes

    monkeypatch.setattr(main.sessao, "RegistroDeSessoes", registro_de_sessoes_espiao)
    monkeypatch.setattr(main.uvicorn, "run", lambda *a, **k: None)

    main.principal()

    assert sessoes_criadas[0].validade == main.sessao.VALIDADE_PADRAO
