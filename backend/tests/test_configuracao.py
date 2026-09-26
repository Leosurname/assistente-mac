"""Testes da leitura de configuracao a partir do ambiente."""

from __future__ import annotations

import pytest
from assistente import configuracao


def test_usa_padroes_quando_o_ambiente_esta_vazio(monkeypatch: pytest.MonkeyPatch):
    for nome in ("LAYLA_URL", "LAYLA_MODEL", "LAYLA_TIMEOUT", "LAYLA_TENTATIVAS"):
        monkeypatch.delenv(nome, raising=False)

    lida = configuracao.ConfiguracaoLayla.do_ambiente()

    assert lida.url == configuracao.URL_PADRAO_LAYLA
    assert lida.modelo is None
    assert lida.url_conversa == "http://127.0.0.1:8080/v1/chat/completions"


def test_le_do_ambiente(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LAYLA_URL", "http://localhost:9999")
    monkeypatch.setenv("LAYLA_MODEL", "mistral-7b-v0.1-layla-v4-chatml")
    monkeypatch.setenv("LAYLA_TIMEOUT", "12.5")
    monkeypatch.setenv("LAYLA_TENTATIVAS", "5")

    lida = configuracao.ConfiguracaoLayla.do_ambiente()

    assert lida.url_conversa == "http://localhost:9999/v1/chat/completions"
    assert lida.modelo == "mistral-7b-v0.1-layla-v4-chatml"
    assert lida.tempo_limite == 12.5
    assert lida.tentativas == 5


@pytest.mark.parametrize(
    "informada",
    [
        "http://localhost:8080",
        "http://localhost:8080/",
        "http://localhost:8080/v1",
        "http://localhost:8080/v1/chat/completions",
    ],
)
def test_aceita_a_url_com_ou_sem_o_caminho_do_endpoint(informada: str):
    """Quem configura costuma colar a URL completa que o llama-server imprime."""
    lida = configuracao.ConfiguracaoLayla(url=informada)

    assert lida.url_conversa == "http://localhost:8080/v1/chat/completions"
    assert lida.url_modelos == "http://localhost:8080/v1/models"


def test_recusa_valor_nao_numerico(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LAYLA_TIMEOUT", "rapido")

    with pytest.raises(ValueError, match="LAYLA_TIMEOUT"):
        configuracao.ConfiguracaoLayla.do_ambiente()


def test_nenhuma_variavel_carrega_segredo():
    """A Layla roda local e nao pede chave: nao ha token para vazar."""
    lida = configuracao.ConfiguracaoLayla()

    assert not hasattr(lida, "chave")
    assert "@" not in lida.url


def test_validade_da_sessao_cai_no_padrao_quando_vazia(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ASSISTENTE_VALIDADE_SESSAO", raising=False)

    assert configuracao.validade_da_sessao_do_ambiente(120.0) == 120.0


def test_validade_da_sessao_le_do_ambiente(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ASSISTENTE_VALIDADE_SESSAO", "30")

    assert configuracao.validade_da_sessao_do_ambiente(120.0) == 30.0


def test_validade_da_sessao_invalida_levanta_erro_claro(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("ASSISTENTE_VALIDADE_SESSAO", "eterna")

    with pytest.raises(ValueError, match="ASSISTENTE_VALIDADE_SESSAO"):
        configuracao.validade_da_sessao_do_ambiente(120.0)


def test_porta_cai_no_padrao_quando_vazia(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ASSISTENTE_PORTA", raising=False)

    assert configuracao.porta_do_ambiente(8765) == 8765


def test_porta_le_do_ambiente(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ASSISTENTE_PORTA", "9001")

    assert configuracao.porta_do_ambiente(8765) == 9001
