"""O formato da API compativel com a da OpenAI: o corpo que vai e o que volta."""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from typing import Any

from assistente import configuracao as configuracao_modulo
from assistente.layla import erros, interface

registrador = logging.getLogger(__name__)

FIM = object()


def corpo_do_pedido(
    configuracao: configuracao_modulo.ConfiguracaoLayla,
    mensagens: Sequence[interface.Mensagem],
    *,
    transmitir: bool,
    temperatura: float | None,
    maximo_de_tokens: int | None,
    formato_resposta: dict[str, Any] | None,
) -> dict[str, Any]:
    cortadas = interface.limitar_contexto(mensagens, configuracao.limite_contexto)
    if len(cortadas) < len(mensagens):
        registrador.info(
            "Historico cortado para caber no contexto: %d de %d mensagens",
            len(cortadas),
            len(mensagens),
        )

    corpo: dict[str, Any] = {
        "messages": [mensagem.para_api() for mensagem in cortadas],
        "stream": transmitir,
        "temperature": (
            configuracao.temperatura if temperatura is None else temperatura
        ),
    }
    if configuracao.modelo:
        corpo["model"] = configuracao.modelo
    if maximo_de_tokens is not None:
        corpo["max_tokens"] = maximo_de_tokens
    if formato_resposta is not None:
        corpo["response_format"] = formato_resposta
    return corpo


def texto_da_resposta(dados: Any) -> str:
    """Extrai o texto da primeira escolha de uma resposta nao transmitida."""
    try:
        escolhas = dados["choices"]
        conteudo = escolhas[0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as erro:
        raise erros.ErroDeResposta(
            f"Resposta da Layla sem conteudo: {dados!r}"
        ) from erro
    if conteudo is None:
        raise erros.ErroDeResposta("A Layla devolveu uma resposta vazia")
    return str(conteudo)


def pedaco_do_evento(linha: str) -> Any:
    """Le uma linha de SSE e devolve o texto dela, `FIM`, ou string vazia."""
    linha = linha.strip()
    if not linha or not linha.startswith("data:"):
        return ""
    dado = linha[len("data:") :].strip()
    if dado == "[DONE]":
        return FIM
    try:
        evento = json.loads(dado)
    except ValueError as erro:
        raise erros.ErroDeResposta(
            f"Pedaco de streaming invalido: {dado!r}"
        ) from erro
    try:
        delta = evento["choices"][0].get("delta") or {}
    except (KeyError, IndexError, TypeError):
        return ""
    return delta.get("content") or ""
