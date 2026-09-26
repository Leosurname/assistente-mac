# Testes do formato de pedido e resposta compativel com a API da OpenAI.

from __future__ import annotations

import pytest
from assistente.ambiente import configuracao
from assistente.layla import erros, interface, protocolo

MENSAGENS = [interface.Mensagem("usuario", "quero terminal e safari")]


def test_evento_de_streaming_sem_choices_e_ignorado():
    evento = '{"outra_coisa": true}'

    assert protocolo.pedaco_do_evento(f"data: {evento}") == ""


def test_resposta_com_conteudo_nulo_vira_erro_de_resposta():
    dados = {
        "choices": [{"index": 0, "message": {"role": "assistant", "content": None}}]
    }

    with pytest.raises(erros.ErroDeResposta):
        protocolo.texto_da_resposta(dados)


def test_corpo_do_pedido_so_leva_max_tokens_quando_informado():
    ajustes = configuracao.ConfiguracaoLayla(url="http://127.0.0.1:8080")

    sem_limite = protocolo.corpo_do_pedido(
        ajustes,
        MENSAGENS,
        transmitir=False,
        temperatura=None,
        maximo_de_tokens=None,
        formato_resposta=None,
    )
    com_limite = protocolo.corpo_do_pedido(
        ajustes,
        MENSAGENS,
        transmitir=False,
        temperatura=None,
        maximo_de_tokens=256,
        formato_resposta=None,
    )

    assert "max_tokens" not in sem_limite
    assert com_limite["max_tokens"] == 256
