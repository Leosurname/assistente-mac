# Sobe e derruba o llama-server como subprocesso do backend.

from __future__ import annotations

import asyncio
import atexit
import logging
import os
import subprocess
from urllib.parse import urlsplit

from assistente.ambiente import configuracao as configuracao_modulo
from assistente.layla import interface

registrador = logging.getLogger(__name__)

BINARIO_PADRAO = "llama-server"
TENTATIVAS_DE_ESPERA = 30
INTERVALO_DE_ESPERA = 1.0


def binario_do_ambiente() -> str:
    return os.getenv("LAYLA_SERVER_BIN") or BINARIO_PADRAO


def montar_argumentos(
    configuracao: configuracao_modulo.ConfiguracaoLayla, caminho_dos_pesos: str
) -> list[str]:
    # Lista fixa, montada em codigo: nada aqui vem de texto de modelo ou de
    # resposta HTTP.
    endereco = urlsplit(configuracao.url)
    return [
        binario_do_ambiente(),
        "--model",
        caminho_dos_pesos,
        "--host",
        endereco.hostname or "127.0.0.1",
        "--port",
        str(endereco.port or 8080),
        "--ctx-size",
        str(configuracao.limite_contexto),
    ]


def subir(
    configuracao: configuracao_modulo.ConfiguracaoLayla, caminho_dos_pesos: str
) -> subprocess.Popen:
    argumentos = montar_argumentos(configuracao, caminho_dos_pesos)
    registrador.info("Subindo o llama-server: %s", " ".join(argumentos))
    try:
        processo = subprocess.Popen(argumentos)
    except FileNotFoundError as erro:
        raise RuntimeError(
            f"{binario_do_ambiente()} nao encontrado. Instale com "
            "`brew install llama.cpp` (veja SETUP.md)."
        ) from erro

    atexit.register(encerrar, processo)
    return processo


def encerrar(processo: subprocess.Popen) -> None:
    if (processo.poll() is not None):
        return
    processo.terminate()
    try:
        processo.wait(timeout=5)
    except subprocess.TimeoutExpired:
        processo.kill()


async def esperar_pronto(llm: interface.ClienteDeLLM) -> bool:
    for _ in range(TENTATIVAS_DE_ESPERA):
        if (await llm.esta_disponivel()):
            return True
        await asyncio.sleep(INTERVALO_DE_ESPERA)
    return False
