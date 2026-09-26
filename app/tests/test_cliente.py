# O backend de mentira fala pelo websockets_falso: nenhuma rede de verdade.

from __future__ import annotations

import json
import time
from types import SimpleNamespace

import pytest

from assistente_app.cliente import ClienteDoBackend


class ConexaoFalsa:
    def __init__(self, mensagens: list[str]) -> None:
        self._restantes = list(mensagens)
        self.enviadas: list[str] = []

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self._restantes:
            raise StopAsyncIteration
        return self._restantes.pop(0)

    async def send(self, dado: str) -> None:
        self.enviadas.append(dado)


class ConectarFalso:
    def __init__(self, comportamentos: list) -> None:
        self._restantes = list(comportamentos)
        self.chamadas = 0

    async def __call__(self, _endereco: str):
        self.chamadas += 1
        resultado = self._restantes.pop(0)
        if isinstance(resultado, Exception):
            raise resultado
        return resultado


def montar(monkeypatch: pytest.MonkeyPatch, conectar):
    respostas: list[dict] = []
    falhas: list[Exception] = []
    import assistente_app.cliente as cliente_mod

    monkeypatch.setattr(cliente_mod, "websockets", SimpleNamespace(connect=conectar))
    cliente = ClienteDoBackend(
        endereco="ws://localhost:0",
        ao_responder=respostas.append,
        ao_falhar=falhas.append,
        despachar=lambda tarefa: tarefa(),
    )
    return cliente, respostas, falhas


def esperar(condicao, tempo=2.0):
    fim = time.time() + tempo
    while time.time() < fim:
        if (condicao()):
            return
        time.sleep(0.01)
    raise TimeoutError("condicao nao ocorreu a tempo")


def test_enviar_antes_de_iniciar_relata_falha(monkeypatch: pytest.MonkeyPatch):
    cliente, _respostas, falhas = montar(monkeypatch, ConectarFalso([]))

    cliente.enviar({"tipo": "pedido"})

    assert len(falhas) == 1
    assert isinstance(falhas[0], RuntimeError)


def test_json_invalido_do_backend_e_relatado_e_conexao_continua(
    monkeypatch: pytest.MonkeyPatch,
):
    conexao = ConexaoFalsa(["isto nao e json", json.dumps({"tipo": "ok"})])
    conectar = ConectarFalso([conexao])
    cliente, respostas, falhas = montar(monkeypatch, conectar)
    cliente.iniciar()

    cliente.enviar({"tipo": "pedido"})
    esperar(lambda: (falhas and respostas))

    assert isinstance(falhas[0], ValueError)
    assert respostas[0] == {"tipo": "ok"}
    assert conectar.chamadas == 1

    cliente.parar()


def test_falha_ao_conectar_e_relatada_e_tentada_de_novo(monkeypatch: pytest.MonkeyPatch):
    conexao = ConexaoFalsa([])
    conectar = ConectarFalso([ConnectionRefusedError(), conexao])
    cliente, _respostas, falhas = montar(monkeypatch, conectar)
    cliente.iniciar()

    cliente.enviar({"tipo": "pedido"})
    esperar(lambda: falhas)
    assert isinstance(falhas[0], ConnectionRefusedError)

    cliente.enviar({"tipo": "pedido"})
    esperar(lambda: conexao.enviadas)

    assert conectar.chamadas == 2
    assert json.loads(conexao.enviadas[0]) == {"tipo": "pedido"}

    cliente.parar()
