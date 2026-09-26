"""Ponto de entrada do backend. Roda com `python main.py`."""

from __future__ import annotations

import logging

import uvicorn
from assistente import configuracao, registro, servidor, sessao
from assistente.layla import cliente

registrador = logging.getLogger(__name__)


def principal() -> None:
    registro.configurar()

    llm = cliente.ClienteLayla(configuracao.ConfiguracaoLayla.do_ambiente())
    validade = configuracao.validade_da_sessao_do_ambiente(sessao.VALIDADE_PADRAO)
    sessoes = sessao.RegistroDeSessoes(validade)
    aplicativo = servidor.criar_aplicativo(llm, sessoes)

    porta = configuracao.porta_do_ambiente(servidor.PORTA_PADRAO)
    registrador.info("Assistente Mac ouvindo em %s:%d", servidor.ENDERECO_PADRAO, porta)
    uvicorn.run(aplicativo, host=servidor.ENDERECO_PADRAO, port=porta, log_config=None)


if (__name__ == "__main__"):
    principal()
