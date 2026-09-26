"""Testes do corte de historico para caber na janela de contexto."""

from __future__ import annotations

from assistente.layla import interface


def _fala(papel, tamanho: int) -> interface.Mensagem:
    return interface.Mensagem(papel=papel, conteudo="x" * tamanho)


def test_historico_pequeno_passa_inteiro():
    mensagens = [
        interface.Mensagem("sistema", "regras"),
        interface.Mensagem("usuario", "quero terminal e safari"),
    ]

    assert interface.limitar_contexto(mensagens, 4096) == mensagens


def test_corta_o_historico_mais_antigo_primeiro():
    mensagens = [
        _fala("sistema", 4 * interface.CARACTERES_POR_TOKEN),
        _fala("usuario", 10 * interface.CARACTERES_POR_TOKEN),
        _fala("assistente", 10 * interface.CARACTERES_POR_TOKEN),
        _fala("usuario", 10 * interface.CARACTERES_POR_TOKEN),
    ]

    mantidas = interface.limitar_contexto(mensagens, 4 + 20)

    assert mantidas == [mensagens[0], mensagens[2], mensagens[3]]


def test_a_mensagem_de_sistema_nunca_e_cortada():
    """E ela que carrega o catalogo de acoes e a regra do que nao se toca."""
    mensagens = [
        _fala("sistema", 100 * interface.CARACTERES_POR_TOKEN),
        _fala("usuario", 100 * interface.CARACTERES_POR_TOKEN),
    ]

    mantidas = interface.limitar_contexto(mensagens, 10)

    assert mantidas == [mensagens[0]]


def test_estimativa_de_tokens_cresce_com_o_texto():
    curta = [interface.Mensagem("usuario", "oi")]
    longa = [interface.Mensagem("usuario", "oi" * 500)]

    assert interface.estimar_tokens(curta) < interface.estimar_tokens(longa)


def test_papeis_viram_os_nomes_da_api():
    assert interface.Mensagem("sistema", "a").para_api() == {
        "role": "system",
        "content": "a",
    }
    assert interface.Mensagem("usuario", "b").para_api() == {
        "role": "user",
        "content": "b",
    }
    assert interface.Mensagem("assistente", "c").para_api() == {
        "role": "assistant",
        "content": "c",
    }


def test_formato_json_monta_o_response_format_do_llama_server():
    esquema = {"type": "object", "properties": {"acoes": {"type": "array"}}}

    formato = interface.formato_json("resposta_do_assistente", esquema)

    assert formato["type"] == "json_schema"
    assert formato["json_schema"]["name"] == "resposta_do_assistente"
    assert formato["json_schema"]["strict"] is True
    assert formato["json_schema"]["schema"] == esquema
