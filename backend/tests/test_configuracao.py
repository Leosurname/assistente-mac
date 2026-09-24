"""Testes da leitura de configuracao a partir do ambiente."""

from __future__ import annotations

import pytest
from assistente.configuracao import URL_PADRAO_LAYLA, ConfiguracaoLayla


def test_usa_padroes_quando_o_ambiente_esta_vazio(monkeypatch: pytest.MonkeyPatch):
    for nome in ("LAYLA_URL", "LAYLA_MODEL", "LAYLA_TIMEOUT", "LAYLA_TENTATIVAS"):
        monkeypatch.delenv(nome, raising=False)

    configuracao = ConfiguracaoLayla.do_ambiente()

    assert configuracao.url == URL_PADRAO_LAYLA
    assert configuracao.modelo is None
    assert configuracao.url_conversa == "http://127.0.0.1:8080/v1/chat/completions"


def test_le_do_ambiente(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LAYLA_URL", "http://localhost:9999")
    monkeypatch.setenv("LAYLA_MODEL", "mistral-7b-v0.1-layla-v4-chatml")
    monkeypatch.setenv("LAYLA_TIMEOUT", "12.5")
    monkeypatch.setenv("LAYLA_TENTATIVAS", "5")

    configuracao = ConfiguracaoLayla.do_ambiente()

    assert configuracao.url_conversa == "http://localhost:9999/v1/chat/completions"
    assert configuracao.modelo == "mistral-7b-v0.1-layla-v4-chatml"
    assert configuracao.tempo_limite == 12.5
    assert configuracao.tentativas == 5


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
    configuracao = ConfiguracaoLayla(url=informada)

    assert configuracao.url_conversa == "http://localhost:8080/v1/chat/completions"
    assert configuracao.url_modelos == "http://localhost:8080/v1/models"


def test_recusa_valor_nao_numerico(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LAYLA_TIMEOUT", "rapido")

    with pytest.raises(ValueError, match="LAYLA_TIMEOUT"):
        ConfiguracaoLayla.do_ambiente()


def test_nenhuma_variavel_carrega_segredo():
    """A Layla roda local e nao pede chave: nao ha token para vazar."""
    configuracao = ConfiguracaoLayla()

    assert not hasattr(configuracao, "chave")
    assert "@" not in configuracao.url
