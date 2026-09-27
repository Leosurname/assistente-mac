# Garante que a Layla esta no ar antes do backend aceitar pedidos: se
# `LAYLA_URL` ja responde, nao mexe em nada; senao baixa os pesos na primeira
# vez e sobe o llama-server sozinho.

from __future__ import annotations

import logging

from assistente.ambiente import configuracao as configuracao_modulo
from assistente.layla import interface, pesos, processo

registrador = logging.getLogger(__name__)


async def garantir(
    configuracao: configuracao_modulo.ConfiguracaoLayla, llm: interface.ClienteDeLLM
) -> None:
    if (await llm.esta_disponivel()):
        return

    registrador.info("Layla fora do ar em %s, subindo sozinha", configuracao.url)
    caminho_dos_pesos = pesos.garantir()
    processo.subir(configuracao, caminho_dos_pesos)

    if not (await processo.esperar_pronto(llm)):
        raise RuntimeError("O llama-server não respondeu a tempo de subir")
