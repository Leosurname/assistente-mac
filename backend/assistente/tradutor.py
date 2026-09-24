"""O miolo: pedido em texto, acoes validadas na saida."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from assistente import prompt
from assistente.acoes import esquema_da_resposta
from assistente.layla.erros import ErroDaLLM, ErroDeResposta
from assistente.layla.interface import ClienteDeLLM, formato_json
from assistente.sessao import Sessao
from assistente.tela import RetratoDaTela
from assistente.validacao import AcaoValidada, Recusa, validar_acoes

registrador = logging.getLogger(__name__)

FALA_PADRAO = "concluído"
FALA_SEM_ACAO = "não entendi o pedido"


@dataclass(frozen=True)
class Traducao:
    acoes: tuple[AcaoValidada, ...]
    fala: str
    recusadas: tuple[Recusa, ...] = ()

    def para_dicionario(self) -> dict:
        return {
            "tipo": "acoes",
            "acoes": [acao.para_dicionario() for acao in self.acoes],
            "fala": self.fala,
        }


async def traduzir(
    transcricao: str,
    tela: RetratoDaTela,
    sessao: Sessao,
    llm: ClienteDeLLM,
) -> Traducao:
    """Manda o pedido para a Layla e devolve so o que passou pela validacao."""
    mensagens = prompt.montar(transcricao, tela, list(sessao.historico))

    bruta = await llm.conversar(
        mensagens,
        formato_resposta=formato_json("resposta_do_assistente", esquema_da_resposta()),
    )

    try:
        corpo = json.loads(bruta)
    except ValueError as erro:
        raise ErroDeResposta(f"A Layla nao devolveu JSON: {bruta!r}") from erro
    if not isinstance(corpo, dict):
        raise ErroDeResposta(f"A Layla devolveu {type(corpo).__name__}, nao um objeto")

    # O historico conta: "agora joga o Safari pra direita" se apoia no pedido
    # anterior, e o Safari continua sendo aplicativo que o usuario citou.
    falas_do_usuario = [*sessao.pedidos, transcricao]
    resultado = validar_acoes(
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
