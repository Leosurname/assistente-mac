"""Testes do subprocesso do llama-server. Nenhum sobe processo de verdade."""

from __future__ import annotations

import subprocess

import pytest
from assistente.ambiente import configuracao
from assistente.layla import processo


def _configuracao(**ajustes) -> configuracao.ConfiguracaoLayla:
    return configuracao.ConfiguracaoLayla(url="http://127.0.0.1:8080", **ajustes)


class ProcessoDeMentira:
    """Fica no lugar de um subprocess.Popen de verdade."""

    def __init__(self):
        self.terminado = False
        self.morto = False
        self._rodando = True

    def poll(self):
        return None if self._rodando else 0

    def terminate(self):
        self.terminado = True
        self._rodando = False

    def wait(self, timeout=None):
        return 0

    def kill(self):
        self.morto = True


def test_montar_argumentos_usa_a_configuracao(monkeypatch):
    monkeypatch.delenv("LAYLA_SERVER_BIN", raising=False)
    config = _configuracao(limite_contexto=2048)

    argumentos = processo.montar_argumentos(config, "/modelos/pesos.gguf")

    assert argumentos == [
        "llama-server",
        "--model",
        "/modelos/pesos.gguf",
        "--host",
        "127.0.0.1",
        "--port",
        "8080",
        "--ctx-size",
        "2048",
    ]


def test_montar_argumentos_usa_o_binario_do_ambiente(monkeypatch):
    monkeypatch.setenv("LAYLA_SERVER_BIN", "/opt/homebrew/bin/llama-server")

    argumentos = processo.montar_argumentos(_configuracao(), "/modelos/pesos.gguf")

    assert argumentos[0] == "/opt/homebrew/bin/llama-server"


def test_subir_da_erro_claro_quando_o_binario_nao_existe(monkeypatch):
    def popen_de_mentira(*_args, **_kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(processo.subprocess, "Popen", popen_de_mentira)

    with pytest.raises(RuntimeError, match="brew install llama.cpp"):
        processo.subir(_configuracao(), "/modelos/pesos.gguf")


def test_subir_registra_encerramento_no_atexit(monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        processo.subprocess, "Popen", lambda *_a, **_k: ProcessoDeMentira()
    )
    monkeypatch.setattr(
        processo.atexit, "register", lambda funcao, arg: chamadas.append((funcao, arg))
    )

    processo.subir(_configuracao(), "/modelos/pesos.gguf")

    assert len(chamadas) == 1
    assert chamadas[0][0] is processo.encerrar


def test_encerrar_termina_processo_vivo():
    fingido = ProcessoDeMentira()

    processo.encerrar(fingido)

    assert fingido.terminado


def test_encerrar_nao_mexe_em_processo_ja_morto():
    fingido = ProcessoDeMentira()
    fingido._rodando = False

    processo.encerrar(fingido)

    assert not fingido.terminado


def test_encerrar_mata_se_nao_terminar_a_tempo():
    fingido = ProcessoDeMentira()
    fingido.wait = lambda timeout=None: (_ for _ in ()).throw(
        subprocess.TimeoutExpired(cmd="llama-server", timeout=5)
    )

    processo.encerrar(fingido)

    assert fingido.morto


async def _dormir_de_mentira(_: float) -> None:
    return None


async def test_esperar_pronto_devolve_true_assim_que_disponivel(monkeypatch):
    monkeypatch.setattr(processo.asyncio, "sleep", _dormir_de_mentira)

    class LlmDeMentira:
        async def esta_disponivel(self):
            return True

    assert await processo.esperar_pronto(LlmDeMentira())


async def test_esperar_pronto_desiste_apos_as_tentativas(monkeypatch):
    monkeypatch.setattr(processo.asyncio, "sleep", _dormir_de_mentira)
    monkeypatch.setattr(processo, "TENTATIVAS_DE_ESPERA", 2)

    class LlmDeMentira:
        async def esta_disponivel(self):
            return False

    assert not await processo.esperar_pronto(LlmDeMentira())
