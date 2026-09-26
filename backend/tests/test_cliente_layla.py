"""Testes do cliente da Layla. Nenhum deles abre conexao de rede."""

from __future__ import annotations

import httpx
import pytest
from assistente import configuracao
from assistente.layla import cliente, erros, interface

from tests.apoio import (
    LaylaDeMentira,
    erro_de_conexao,
    resposta_de_conversa,
    resposta_transmitida,
    tempo_esgotado,
)

PEDIDO = [
    interface.Mensagem("sistema", "Voce traduz pedidos em acoes."),
    interface.Mensagem("usuario", "quero terminal e safari"),
]

# Sem espera entre tentativas: o teste exercita a logica, nao o relogio.
SEM_ESPERA = {"tentativas": 3}


@pytest.fixture(autouse=True)
def _nao_espere_entre_tentativas(monkeypatch: pytest.MonkeyPatch):
    async def dormir_de_mentira(_: float) -> None:
        return None

    monkeypatch.setattr("assistente.layla.cliente.asyncio.sleep", dormir_de_mentira)


def _cliente(layla: LaylaDeMentira, **ajustes) -> cliente.ClienteLayla:
    ajustada = configuracao.ConfiguracaoLayla(url="http://127.0.0.1:8080", **ajustes)
    return cliente.ClienteLayla(ajustada, cliente_http=layla.cliente())


# ── contrato ─────────────────────────────────────────────────────────────────


def test_o_cliente_satisfaz_a_interface():
    """O resto do backend depende so da interface, nunca da classe concreta."""
    layla = LaylaDeMentira([resposta_de_conversa("ok")])

    assert isinstance(_cliente(layla), interface.ClienteDeLLM)


# ── conversa simples ─────────────────────────────────────────────────────────


async def test_conversar_devolve_o_texto_da_layla():
    layla = LaylaDeMentira([resposta_de_conversa("concluido")])

    resposta = await _cliente(layla).conversar(PEDIDO)

    assert resposta == "concluido"


async def test_o_pedido_vai_para_o_endpoint_compativel_com_openai():
    layla = LaylaDeMentira([resposta_de_conversa("ok")])

    await _cliente(layla).conversar(PEDIDO)

    pedido = layla.pedidos[0]
    assert pedido.method == "POST"
    assert str(pedido.url) == "http://127.0.0.1:8080/v1/chat/completions"


async def test_o_corpo_traduz_os_papeis_e_marca_stream_falso():
    layla = LaylaDeMentira([resposta_de_conversa("ok")])

    await _cliente(layla).conversar(PEDIDO)

    corpo = layla.corpos[0]
    assert corpo["stream"] is False
    assert corpo["messages"] == [
        {"role": "system", "content": "Voce traduz pedidos em acoes."},
        {"role": "user", "content": "quero terminal e safari"},
    ]


async def test_o_modelo_so_vai_no_corpo_quando_configurado():
    layla = LaylaDeMentira([resposta_de_conversa("ok"), resposta_de_conversa("ok")])

    await _cliente(layla).conversar(PEDIDO)
    assert "model" not in layla.corpos[0]

    await _cliente(layla, modelo="mistral-7b-v0.1-layla-v4-chatml").conversar(PEDIDO)
    assert layla.corpos[1]["model"] == "mistral-7b-v0.1-layla-v4-chatml"


async def test_nenhum_cabecalho_de_autenticacao_e_enviado():
    """A Layla roda no localhost e nao pede chave. Nada de segredo no pedido."""
    layla = LaylaDeMentira([resposta_de_conversa("ok")])

    await _cliente(layla).conversar(PEDIDO)

    cabecalhos = {nome.lower() for nome in layla.pedidos[0].headers}
    assert "authorization" not in cabecalhos
    assert "x-api-key" not in cabecalhos


async def test_repassa_o_formato_de_resposta_restrito():
    """Decodificacao restrita e o que garante um JSON de acoes bem formado."""
    layla = LaylaDeMentira([resposta_de_conversa("{}")])
    esquema = {"type": "object", "properties": {"acoes": {"type": "array"}}}

    await _cliente(layla).conversar(
        PEDIDO, formato_resposta=interface.formato_json("acoes", esquema)
    )

    assert layla.corpos[0]["response_format"]["json_schema"]["schema"] == esquema


async def test_o_historico_e_cortado_antes_de_sair():
    layla = LaylaDeMentira([resposta_de_conversa("ok")])
    longo = [
        interface.Mensagem("sistema", "regras"),
        *[interface.Mensagem("usuario", "x" * 400) for _ in range(20)],
    ]

    await _cliente(layla, limite_contexto=200).conversar(longo)

    assert len(layla.corpos[0]["messages"]) < len(longo)
    assert layla.corpos[0]["messages"][0]["role"] == "system"


# ── streaming ────────────────────────────────────────────────────────────────


async def test_transmitir_devolve_a_resposta_em_pedacos():
    layla = LaylaDeMentira([resposta_transmitida(["con", "clu", "ido"])])

    pedacos = [p async for p in _cliente(layla).transmitir(PEDIDO)]

    assert pedacos == ["con", "clu", "ido"]
    assert "".join(pedacos) == "concluido"


async def test_transmitir_marca_stream_verdadeiro():
    layla = LaylaDeMentira([resposta_transmitida(["oi"])])

    _ = [p async for p in _cliente(layla).transmitir(PEDIDO)]

    assert layla.corpos[0]["stream"] is True


async def test_transmitir_para_no_done_e_ignora_linhas_vazias():
    corpo = b"\n: comentario\ndata: " + (
        b'{"choices":[{"delta":{"content":"oi"}}]}\n\ndata: [DONE]\n\n'
        b'data: {"choices":[{"delta":{"content":"nao deveria aparecer"}}]}\n\n'
    )
    layla = LaylaDeMentira(
        [
            httpx.Response(
                200, content=corpo, headers={"Content-Type": "text/event-stream"}
            )
        ]
    )

    pedacos = [p async for p in _cliente(layla).transmitir(PEDIDO)]

    assert pedacos == ["oi"]


async def test_transmitir_avisa_quando_a_layla_esta_fora():
    layla = LaylaDeMentira([erro_de_conexao])

    with pytest.raises(erros.ErroDeIndisponibilidade):
        _ = [p async for p in _cliente(layla).transmitir(PEDIDO)]


async def test_transmitir_avisa_quando_o_status_e_de_erro():
    layla = LaylaDeMentira([httpx.Response(503)])

    with pytest.raises(erros.ErroDeIndisponibilidade):
        _ = [p async for p in _cliente(layla).transmitir(PEDIDO)]


# ── erros e novas tentativas ─────────────────────────────────────────────────


async def test_tenta_de_novo_depois_de_uma_falha_transitoria():
    layla = LaylaDeMentira([httpx.Response(503), resposta_de_conversa("ok")])

    resposta = await _cliente(layla, **SEM_ESPERA).conversar(PEDIDO)

    assert resposta == "ok"
    assert len(layla.pedidos) == 2


async def test_desiste_depois_do_numero_de_tentativas_configurado():
    layla = LaylaDeMentira([erro_de_conexao])

    with pytest.raises(erros.ErroDeIndisponibilidade) as capturado:
        await _cliente(layla, tentativas=3).conversar(PEDIDO)

    assert len(layla.pedidos) == 3
    assert "Layla" in capturado.value.mensagem_amigavel


async def test_tempo_esgotado_vira_erro_proprio_com_mensagem_clara():
    layla = LaylaDeMentira([tempo_esgotado])

    with pytest.raises(erros.ErroDeTempoEsgotado) as capturado:
        await _cliente(layla, tentativas=2).conversar(PEDIDO)

    assert capturado.value.mensagem_amigavel == "A Layla demorou demais para responder."


async def test_excesso_de_pedidos_vira_erro_de_limite():
    layla = LaylaDeMentira([httpx.Response(429)])

    with pytest.raises(erros.ErroDeLimiteDeUso):
        await _cliente(layla, tentativas=2).conversar(PEDIDO)


async def test_erro_de_cliente_nao_e_repetido():
    """Repetir um pedido malformado so gasta o orcamento de 3 segundos."""
    layla = LaylaDeMentira([httpx.Response(400)])

    with pytest.raises(erros.ErroDeIndisponibilidade):
        await _cliente(layla, tentativas=3).conversar(PEDIDO)

    assert len(layla.pedidos) == 1


async def test_resposta_sem_conteudo_vira_erro_de_resposta():
    layla = LaylaDeMentira([httpx.Response(200, json={"choices": []})])

    with pytest.raises(erros.ErroDeResposta):
        await _cliente(layla).conversar(PEDIDO)


async def test_resposta_que_nao_e_json_vira_erro_de_resposta():
    layla = LaylaDeMentira([httpx.Response(200, content=b"nao sou json")])

    with pytest.raises(erros.ErroDeResposta):
        await _cliente(layla).conversar(PEDIDO)


# ── disponibilidade ──────────────────────────────────────────────────────────


async def test_esta_disponivel_consulta_a_lista_de_modelos():
    layla = LaylaDeMentira([httpx.Response(200, json={"data": []})])

    assert await _cliente(layla).esta_disponivel() is True
    assert str(layla.pedidos[0].url) == "http://127.0.0.1:8080/v1/models"


async def test_esta_disponivel_devolve_falso_sem_levantar_erro():
    layla = LaylaDeMentira([erro_de_conexao])

    assert await _cliente(layla).esta_disponivel() is False
