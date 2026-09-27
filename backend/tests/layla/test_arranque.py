"""Testes do arranque da Layla. Nenhum baixa peso nem sobe processo real."""

from __future__ import annotations

import pytest
from assistente.ambiente import configuracao
from assistente.layla import arranque


class LlmDeMentira:
    def __init__(self, disponivel: bool):
        self.disponivel = disponivel

    async def esta_disponivel(self):
        return self.disponivel


def _configuracao() -> configuracao.ConfiguracaoLayla:
    return configuracao.ConfiguracaoLayla(url="http://127.0.0.1:8080")


async def test_nao_mexe_em_nada_quando_a_layla_ja_esta_no_ar(monkeypatch):
    chamado = []
    monkeypatch.setattr(arranque.pesos, "garantir", lambda: chamado.append("pesos"))
    monkeypatch.setattr(
        arranque.processo, "subir", lambda *_a, **_k: chamado.append("subir")
    )

    await arranque.garantir(_configuracao(), LlmDeMentira(disponivel=True))

    assert chamado == []


async def test_baixa_pesos_e_sobe_o_processo_quando_a_layla_esta_fora(monkeypatch):
    chamado = []
    monkeypatch.setattr(
        arranque.pesos, "garantir", lambda: chamado.append("pesos") or "/pesos.gguf"
    )
    monkeypatch.setattr(
        arranque.processo, "subir", lambda *_a, **_k: chamado.append("subir")
    )

    async def pronto_de_mentira(_llm):
        chamado.append("pronto")
        return True

    monkeypatch.setattr(arranque.processo, "esperar_pronto", pronto_de_mentira)

    await arranque.garantir(_configuracao(), LlmDeMentira(disponivel=False))

    assert chamado == ["pesos", "subir", "pronto"]


async def test_da_erro_claro_quando_o_llama_server_nao_fica_pronto(monkeypatch):
    monkeypatch.setattr(arranque.pesos, "garantir", lambda: "/pesos.gguf")
    monkeypatch.setattr(arranque.processo, "subir", lambda *_a, **_k: None)

    async def nunca_fica_pronto(_llm):
        return False

    monkeypatch.setattr(arranque.processo, "esperar_pronto", nunca_fica_pronto)

    with pytest.raises(RuntimeError, match="não respondeu a tempo"):
        await arranque.garantir(_configuracao(), LlmDeMentira(disponivel=False))
