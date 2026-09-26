"""Configuracao do backend, lida sempre de variaveis de ambiente.

Nenhum valor sensivel mora no codigo.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

# A Layla-Server e um empacotamento do `llama-server` do llama.cpp e serve uma
# API compativel com a da OpenAI. O padrao do proprio projeto e a porta 8080.
URL_PADRAO_LAYLA = "http://127.0.0.1:8080"

TEMPO_LIMITE_PADRAO = 30.0
TENTATIVAS_PADRAO = 3
LIMITE_CONTEXTO_PADRAO = 4096


def _ler_float(nome: str, padrao: float) -> float:
    bruto = os.getenv(nome)
    if bruto is None or not bruto.strip():
        return padrao
    try:
        return float(bruto)
    except ValueError as erro:
        raise ValueError(f"{nome} precisa ser um numero: {bruto!r}") from erro


def _ler_int(nome: str, padrao: int) -> int:
    bruto = os.getenv(nome)
    if bruto is None or not bruto.strip():
        return padrao
    try:
        return int(bruto)
    except ValueError as erro:
        raise ValueError(f"{nome} precisa ser um numero inteiro: {bruto!r}") from erro


@dataclass(frozen=True)
class ConfiguracaoLayla:
    url: str = URL_PADRAO_LAYLA
    modelo: str | None = None
    tempo_limite: float = TEMPO_LIMITE_PADRAO
    tentativas: int = TENTATIVAS_PADRAO
    limite_contexto: int = LIMITE_CONTEXTO_PADRAO
    temperatura: float = 0.2

    @property
    def url_base(self) -> str:
        """URL sem barra final e sem o caminho do endpoint, para montar rotas."""
        base = self.url.strip().rstrip("/")
        for sufixo in ("/v1/chat/completions", "/chat/completions", "/v1"):
            if base.endswith(sufixo):
                base = base[: -len(sufixo)]
                break
        return base.rstrip("/")

    @property
    def url_conversa(self) -> str:
        return f"{self.url_base}/v1/chat/completions"

    @property
    def url_modelos(self) -> str:
        return f"{self.url_base}/v1/models"

    @classmethod
    def do_ambiente(cls) -> ConfiguracaoLayla:
        modelo = os.getenv("LAYLA_MODEL")
        return cls(
            url=os.getenv("LAYLA_URL") or URL_PADRAO_LAYLA,
            modelo=modelo.strip() if modelo and modelo.strip() else None,
            tempo_limite=_ler_float("LAYLA_TIMEOUT", TEMPO_LIMITE_PADRAO),
            tentativas=_ler_int("LAYLA_TENTATIVAS", TENTATIVAS_PADRAO),
            limite_contexto=_ler_int("LAYLA_LIMITE_CONTEXTO", LIMITE_CONTEXTO_PADRAO),
            temperatura=_ler_float("LAYLA_TEMPERATURA", 0.2),
        )


def validade_da_sessao_do_ambiente(padrao: float) -> float:
    return _ler_float("ASSISTENTE_VALIDADE_SESSAO", padrao)


def porta_do_ambiente(padrao: int) -> int:
    # Sem mensagem propria: um valor invalido aqui sempre levantou o ValueError
    # cru do int().
    return int(os.getenv("ASSISTENTE_PORTA") or padrao)
