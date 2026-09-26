"""Testes das rotas. A Layla e sempre de mentira; nada abre conexao."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Sequence
from typing import Any

import pytest
from assistente.layla import erros, interface
from assistente.pedido import sessao
from assistente.rede import servidor
from fastapi.testclient import TestClient

TELA = {
    "monitores": [{"largura": 3456, "altura": 2234}],
    "apps_abertos": ["Finder", "Safari", "Spotify"],
    "janelas": [{"app": "Safari", "x": 100, "y": 80, "largura": 1200, "altura": 900}],
    "apps_instalados": ["Finder", "Safari", "Spotify", "Terminal", "Claude Code"],
}


class LaylaDeMentira:
    """Cliente de LLM que devolve o que o teste mandar, sem tocar na rede."""

    def __init__(self, respostas: Sequence[Any], disponivel: bool = True):
        self._respostas = list(respostas)
        self.disponivel = disponivel
        self.chamadas: list[list[interface.Mensagem]] = []

    async def conversar(self, mensagens, **_: Any) -> str:
        self.chamadas.append(list(mensagens))
        resposta = self._respostas[
            min(len(self.chamadas) - 1, len(self._respostas) - 1)
        ]
        if isinstance(resposta, Exception):
            raise resposta
        return resposta if isinstance(resposta, str) else json.dumps(resposta)

    async def transmitir(self, mensagens, **kwargs: Any) -> AsyncIterator[str]:
        yield await self.conversar(mensagens, **kwargs)

    async def esta_disponivel(self) -> bool:
        return self.disponivel


def _resposta(acoes, fala="concluído") -> dict:
    return {"acoes": acoes, "fala": fala}


def _cliente(llm: LaylaDeMentira, **kwargs) -> TestClient:
    # O TestClient se apresenta como "testclient" por padrao, e o servidor so
    # aceita conexao local: o teste precisa dizer de onde esta chamando.
    return TestClient(
        servidor.criar_aplicativo(
            llm=llm, sessoes=sessao.RegistroDeSessoes(**kwargs)
        ),
        client=("127.0.0.1", 50000),
    )


def test_o_cliente_de_mentira_cumpre_a_interface():
    assert isinstance(LaylaDeMentira([]), interface.ClienteDeLLM)


# ── health check ─────────────────────────────────────────────────────────────


def test_health_diz_ok_com_a_layla_no_ar():
    with _cliente(LaylaDeMentira([], disponivel=True)) as cliente:
        corpo = cliente.get("/health").json()

    assert corpo["estado"] == "ok"
    assert corpo["layla"] == "no ar"
    assert "versao" in corpo


def test_health_diz_degradado_com_a_layla_fora():
    with _cliente(LaylaDeMentira([], disponivel=False)) as cliente:
        resposta = cliente.get("/health")

    assert resposta.status_code == 200
    assert resposta.json()["estado"] == "degradado"


# ── o contrato do ARCHITECTURE.md ────────────────────────────────────────────


def test_pedido_devolve_acoes_no_formato_do_contrato():
    acoes = [
        {"acao": "abrir_app", "app": "Terminal"},
        {"acao": "abrir_app", "app": "Claude Code"},
        {"acao": "posicionar", "app": "Terminal", "regiao": "metade_esquerda"},
        {"acao": "posicionar", "app": "Safari", "regiao": "metade_direita"},
    ]
    llm = LaylaDeMentira([_resposta(acoes)])

    with _cliente(llm) as cliente, cliente.websocket_connect("/ws") as ws:
        ws.send_json(
            {
                "tipo": "pedido",
                "texto": "quero terminal e safari, e ja deixa o claude code aberto",
                "tela": TELA,
            }
        )
        corpo = ws.receive_json()

    assert corpo["tipo"] == "acoes"
    assert corpo["acoes"] == acoes
    assert corpo["fala"] == "concluído"


def test_a_resposta_traz_o_identificador_da_sessao():
    llm = LaylaDeMentira([_resposta([{"acao": "abrir_app", "app": "Terminal"}])])

    with _cliente(llm) as cliente, cliente.websocket_connect("/ws") as ws:
        ws.send_json({"tipo": "pedido", "texto": "abre o terminal", "tela": TELA})
        corpo = ws.receive_json()

    assert isinstance(corpo["sessao"], str) and corpo["sessao"]


def test_acao_sobre_app_nao_pedido_nao_chega_ao_executor():
    """A promessa do produto, conferida na borda: o Spotify nao foi citado."""
    llm = LaylaDeMentira(
        [
            _resposta(
                [
                    {"acao": "abrir_app", "app": "Terminal"},
                    {"acao": "minimizar", "app": "Spotify"},
                ]
            )
        ]
    )

    with _cliente(llm) as cliente, cliente.websocket_connect("/ws") as ws:
        ws.send_json({"tipo": "pedido", "texto": "abre o terminal", "tela": TELA})
        corpo = ws.receive_json()

    assert corpo["acoes"] == [{"acao": "abrir_app", "app": "Terminal"}]


def test_acao_fora_do_catalogo_nao_chega_ao_executor():
    llm = LaylaDeMentira(
        [_resposta([{"acao": "rodar_shell", "app": "Terminal", "cmd": "rm -rf /"}])]
    )

    with _cliente(llm) as cliente, cliente.websocket_connect("/ws") as ws:
        ws.send_json({"tipo": "pedido", "texto": "abre o terminal", "tela": TELA})
        corpo = ws.receive_json()

    assert corpo["acoes"] == []
    assert corpo["fala"] == "não entendi o pedido"


def test_a_sessao_guarda_o_historico_entre_dois_pedidos():
    llm = LaylaDeMentira(
        [
            _resposta([{"acao": "abrir_app", "app": "Terminal"}]),
            _resposta(
                [{"acao": "posicionar", "app": "Safari", "regiao": "metade_direita"}]
            ),
        ]
    )

    with _cliente(llm) as cliente, cliente.websocket_connect("/ws") as ws:
        ws.send_json(
            {"tipo": "pedido", "texto": "quero terminal e safari", "tela": TELA}
        )
        sessao = ws.receive_json()["sessao"]

        ws.send_json(
            {
                "tipo": "pedido",
                "texto": "agora joga ele pra direita",
                "tela": TELA,
                "sessao": sessao,
            }
        )
        segundo = ws.receive_json()

    # O Safari so passa porque foi citado no primeiro pedido da mesma sessao.
    assert segundo["acoes"] == [
        {"acao": "posicionar", "app": "Safari", "regiao": "metade_direita"}
    ]
    assert len(llm.chamadas[1]) > len(llm.chamadas[0])


def test_encerrar_esquece_a_sessao():
    llm = LaylaDeMentira([_resposta([{"acao": "abrir_app", "app": "Terminal"}])])

    with _cliente(llm) as cliente, cliente.websocket_connect("/ws") as ws:
        ws.send_json({"tipo": "pedido", "texto": "abre o terminal", "tela": TELA})
        sessao = ws.receive_json()["sessao"]

        ws.send_json({"tipo": "encerrar", "sessao": sessao})
        assert ws.receive_json() == {"tipo": "encerrada"}

        assert cliente.get("/health").json()["sessoes"] == 0


# ── entradas malformadas ─────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "mensagem",
    [
        {"tipo": "pedido", "texto": "", "tela": TELA},
        {"tipo": "pedido", "tela": TELA},
        {"tipo": "outra_coisa", "texto": "oi"},
        {"tipo": "pedido", "texto": "oi", "tela": "uma tela grande"},
        {
            "tipo": "pedido",
            "texto": "oi",
            "tela": {"monitores": [{"largura": "muita"}]},
        },
    ],
)
def test_mensagem_malformada_vira_erro_e_nao_derruba_a_conexao(mensagem: dict):
    llm = LaylaDeMentira([_resposta([])])

    with _cliente(llm) as cliente, cliente.websocket_connect("/ws") as ws:
        ws.send_json(mensagem)
        corpo = ws.receive_json()

        assert corpo["tipo"] == "erro"
        assert corpo["mensagem"]

        # A conexao segue viva: a caixa nao deve morrer por um pedido ruim.
        ws.send_json({"tipo": "pedido", "texto": "abre o terminal", "tela": TELA})
        assert ws.receive_json()["tipo"] == "acoes"


def test_pedido_malformado_nao_chega_a_incomodar_a_layla():
    llm = LaylaDeMentira([_resposta([])])

    with _cliente(llm) as cliente, cliente.websocket_connect("/ws") as ws:
        ws.send_json({"tipo": "pedido", "texto": "   ", "tela": TELA})
        ws.receive_json()

    assert llm.chamadas == []


# ── limites do pedido ────────────────────────────────────────────────────────


def test_texto_maior_que_o_limite_e_cortado_antes_de_ir_para_a_layla():
    llm = LaylaDeMentira([_resposta([])])
    # "z" nao aparece no resumo da tela: sobra so o que veio do pedido do usuario.
    texto = "z" * (servidor.LIMITE_DO_TEXTO + 500)

    with _cliente(llm) as cliente, cliente.websocket_connect("/ws") as ws:
        ws.send_json({"tipo": "pedido", "texto": texto, "tela": TELA})
        ws.receive_json()

    ultima_mensagem = llm.chamadas[0][-1]
    assert ultima_mensagem.conteudo.count("z") == servidor.LIMITE_DO_TEXTO


def test_mensagem_que_nao_e_json_fecha_a_conexao_com_erro():
    from starlette.websockets import WebSocketDisconnect

    llm = LaylaDeMentira([])

    with _cliente(llm) as cliente, cliente.websocket_connect("/ws") as ws:
        ws.send_text("isso nao e json")
        corpo = ws.receive_json()

        assert corpo["tipo"] == "erro"
        with pytest.raises(WebSocketDisconnect):
            ws.receive_json()


def test_validade_de_sessao_invalida_no_ambiente_da_erro_claro(monkeypatch):
    monkeypatch.setenv("ASSISTENTE_VALIDADE_SESSAO", "nao e numero")

    with pytest.raises(ValueError, match="ASSISTENTE_VALIDADE_SESSAO"):
        servidor.montar_do_ambiente()


# ── erros da Layla ───────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("erro", "trecho"),
    [
        (erros.ErroDeTempoEsgotado("demorou"), "demorou demais"),
        (erros.ErroDeIndisponibilidade("fora"), "não está respondendo"),
    ],
)
def test_falha_da_layla_vira_erro_com_mensagem_clara(erro: Exception, trecho: str):
    llm = LaylaDeMentira([erro])

    with _cliente(llm) as cliente, cliente.websocket_connect("/ws") as ws:
        ws.send_json({"tipo": "pedido", "texto": "abre o terminal", "tela": TELA})
        corpo = ws.receive_json()

    assert corpo["tipo"] == "erro"
    assert trecho in corpo["mensagem"]


def test_resposta_da_layla_que_nao_e_json_vira_erro():
    llm = LaylaDeMentira(["claro! vou abrir o terminal pra voce :)"])

    with _cliente(llm) as cliente, cliente.websocket_connect("/ws") as ws:
        ws.send_json({"tipo": "pedido", "texto": "abre o terminal", "tela": TELA})
        corpo = ws.receive_json()

    assert corpo["tipo"] == "erro"


# ── so conexao local ─────────────────────────────────────────────────────────


@pytest.mark.parametrize("endereco", ["127.0.0.1", "::1", "localhost"])
def test_enderecos_locais_sao_aceitos(endereco: str):
    assert servidor.e_local(endereco)


@pytest.mark.parametrize("endereco", ["192.168.0.10", "10.0.0.1", "8.8.8.8", None])
def test_enderecos_de_fora_sao_recusados(endereco):
    assert not servidor.e_local(endereco)


def test_o_websocket_recusa_quem_nao_vem_do_localhost():
    from starlette.websockets import WebSocketDisconnect

    aplicativo = servidor.criar_aplicativo(
        llm=LaylaDeMentira([]), sessoes=sessao.RegistroDeSessoes()
    )
    cliente = TestClient(aplicativo, client=("203.0.113.7", 55000))

    with (
        pytest.raises(WebSocketDisconnect) as capturado,
        cliente.websocket_connect("/ws"),
    ):
        pass

    assert capturado.value.code == 1008


# ── ponto de entrada ─────────────────────────────────────────────────────────


def test_montar_do_ambiente_com_validade_invalida_da_erro_claro(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("ASSISTENTE_VALIDADE_SESSAO", "eterna")

    with pytest.raises(ValueError, match="ASSISTENTE_VALIDADE_SESSAO"):
        servidor.montar_do_ambiente()


def test_montar_do_ambiente_monta_app_com_rota_de_health(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv("ASSISTENTE_VALIDADE_SESSAO", raising=False)

    aplicativo = servidor.montar_do_ambiente()

    caminhos = {rota.path for rota in aplicativo.routes}
    assert "/health" in caminhos


def test_montar_do_ambiente_leva_a_validade_do_ambiente_ao_registro_de_sessoes(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("ASSISTENTE_VALIDADE_SESSAO", "45")
    assert servidor.montar_do_ambiente().state.sessoes.validade == 45

    monkeypatch.delenv("ASSISTENTE_VALIDADE_SESSAO", raising=False)
    assert servidor.montar_do_ambiente().state.sessoes.validade == 120.0


def test_subir_usa_host_e_porta_padrao(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ASSISTENTE_PORTA", raising=False)
    chamadas: list[dict[str, Any]] = []

    def uvicorn_run_de_mentira(aplicativo, **kwargs: Any) -> None:
        chamadas.append({"aplicativo": aplicativo, **kwargs})

    monkeypatch.setattr(servidor.uvicorn, "run", uvicorn_run_de_mentira)

    aplicativo = servidor.criar_aplicativo(
        llm=LaylaDeMentira([]), sessoes=sessao.RegistroDeSessoes()
    )
    servidor.subir(aplicativo)

    assert len(chamadas) == 1
    assert chamadas[0]["aplicativo"] is aplicativo
    assert chamadas[0]["host"] == "127.0.0.1"
    assert chamadas[0]["port"] == 8765
    assert chamadas[0]["log_config"] is None


def test_subir_usa_a_porta_do_ambiente(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ASSISTENTE_PORTA", "9001")
    portas: list[int] = []

    monkeypatch.setattr(
        servidor.uvicorn,
        "run",
        lambda aplicativo, **kwargs: portas.append(kwargs["port"]),
    )

    aplicativo = servidor.criar_aplicativo(
        llm=LaylaDeMentira([]), sessoes=sessao.RegistroDeSessoes()
    )
    servidor.subir(aplicativo)

    assert portas == [9001]
