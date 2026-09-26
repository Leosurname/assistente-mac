"""O miolo: pedido em texto, acoes validadas na saida."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from assistente import acoes, prompt, validacao
from assistente import sessao as sessao_modulo
from assistente import tela as tela_modulo
from assistente.layla import erros, interface

registrador = logging.getLogger(__name__)

FALA_PADRAO = "concluído"
FALA_SEM_ACAO = "não entendi o pedido"

# Reexportado: servidor.py trata ErroDaLLM como erro conhecido de traducao.
ErroDaLLM = erros.ErroDaLLM


@dataclass(frozen=True)
class Traducao:
    acoes: tuple[validacao.AcaoValidada, ...]
    fala: str
    recusadas: tuple[validacao.Recusa, ...] = ()

    def para_dicionario(self) -> dict:
        return {
            "tipo": "acoes",
            "acoes": [acao.para_dicionario() for acao in self.acoes],
            "fala": self.fala,
        }


async def traduzir(
    transcricao: str,
    tela: tela_modulo.RetratoDaTela,
    sessao: sessao_modulo.Sessao,
    llm: interface.ClienteDeLLM,
) -> Traducao:
    """Manda o pedido para a Layla e devolve so o que passou pela validacao."""
    mensagens = prompt.montar(transcricao, tela, list(sessao.historico))

    formato_resposta = interface.formato_json(
        "resposta_do_assistente", acoes.esquema_da_resposta()
    )
    bruta = await llm.conversar(mensagens, formato_resposta=formato_resposta)

    try:
        corpo = json.loads(bruta)
    except ValueError as erro:
        raise erros.ErroDeResposta(f"A Layla nao devolveu JSON: {bruta!r}") from erro
    if not isinstance(corpo, dict):
        raise erros.ErroDeResposta(
            f"A Layla devolveu {type(corpo).__name__}, nao um objeto"
        )

    # O historico conta: "agora joga o Safari pra direita" se apoia no pedido
    # anterior, e o Safari continua sendo aplicativo que o usuario citou.
    falas_do_usuario = [*sessao.pedidos, transcricao]
    resultado = validacao.validar_acoes(
        corpo.get("acoes"), tela=tela, textos_do_usuario=falas_do_usuario
    )

    for recusa in resultado.recusadas:
        registrador.warning("Acao recusada (%s): %r", recusa.motivo, recusa.bruta)

    fala = corpo.get("fala")
    if not isinstance(fala, str) or not fala.strip():
        fala = FALA_PADRAO
    if not resultado.aprovadas:
        fala = FALA_SEM_ACAO

    sessao.registrar(transcricao, bruta)

    return Traducao(
        acoes=resultado.aprovadas,
        fala=fala.strip()[:200],
        recusadas=resultado.recusadas,
    )


__all__ = ["ErroDaLLM", "Traducao", "traduzir"]
