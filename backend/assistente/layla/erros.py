"""Erros da camada de conversa com o modelo.

Todos carregam uma `mensagem_amigavel` pronta para ser mostrada ao usuario, com
acento e tudo, porque quem le o erro na caixa de sobreposicao e uma pessoa. O
`detalhe`, esse sim tecnico, fica para o log.
"""

from __future__ import annotations


class ErroDaLLM(Exception):
    """Raiz de tudo que pode dar errado ao falar com o modelo."""

    mensagem_amigavel = "Não consegui falar com a Layla."

    def __init__(self, detalhe: str = "", mensagem_amigavel: str | None = None) -> None:
        super().__init__(detalhe or self.mensagem_amigavel)
        self.detalhe = detalhe
        if mensagem_amigavel is not None:
            self.mensagem_amigavel = mensagem_amigavel


class ErroDeTempoEsgotado(ErroDaLLM):
    """A Layla demorou mais do que o tempo limite para responder."""

    mensagem_amigavel = "A Layla demorou demais para responder."


class ErroDeIndisponibilidade(ErroDaLLM):
    """A Layla nao esta no ar, ou recusou a conexao."""

    mensagem_amigavel = "A Layla não está respondendo. Ela está rodando?"


class ErroDeLimiteDeUso(ErroDaLLM):
    """A Layla respondeu 429: ha pedidos demais em andamento."""

    mensagem_amigavel = "A Layla está ocupada. Tente de novo em instantes."


class ErroDeResposta(ErroDaLLM):
    """A Layla respondeu, mas o corpo nao tem o formato esperado."""

    mensagem_amigavel = "Não entendi a resposta da Layla."
