from __future__ import annotations

import pytest

from assistente_app.configuracao import BACKEND_PADRAO, Configuracao


def test_padroes_sem_ambiente():
    configuracao = Configuracao.do_ambiente({})

    assert configuracao.backend == BACKEND_PADRAO
    assert configuracao.espera == 5.0
    assert configuracao.idioma == "pt-BR"
    assert configuracao.falar_resposta is True


def test_le_do_ambiente():
    configuracao = Configuracao.do_ambiente(
        {
            "ASSISTENTE_BACKEND": "ws://127.0.0.1:9000/ws",
            "ASSISTENTE_TIMEOUT_CAIXA": "3",
            "ASSISTENTE_IDIOMA": "en-US",
            "ASSISTENTE_FALAR": "0",
        }
    )

    assert configuracao.backend == "ws://127.0.0.1:9000/ws"
    assert configuracao.espera == 3.0
    assert configuracao.idioma == "en-US"
    assert configuracao.falar_resposta is False


def test_espera_invalida_e_erro_claro():
    with pytest.raises(ValueError, match="ASSISTENTE_TIMEOUT_CAIXA"):
        Configuracao.do_ambiente({"ASSISTENTE_TIMEOUT_CAIXA": "depois"})


def test_espera_negativa_e_recusada():
    with pytest.raises(ValueError):
        Configuracao.do_ambiente({"ASSISTENTE_TIMEOUT_CAIXA": "-1"})


def test_valor_em_branco_cai_no_padrao():
    configuracao = Configuracao.do_ambiente({"ASSISTENTE_BACKEND": "   "})

    assert configuracao.backend == BACKEND_PADRAO
