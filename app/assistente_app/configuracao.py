"""Configuracao da camada nativa, lida do ambiente."""

from __future__ import annotations

import os
from dataclasses import dataclass

from assistente_app.dispensa import ESPERA_PADRAO

BACKEND_PADRAO = "ws://127.0.0.1:8765/ws"
IDIOMA_PADRAO = "pt-BR"


@dataclass(frozen=True)
class Configuracao:
    backend: str = BACKEND_PADRAO
    espera: float = ESPERA_PADRAO
    idioma: str = IDIOMA_PADRAO
    falar_resposta: bool = True

    @classmethod
    def do_ambiente(cls, ambiente: dict[str, str] | None = None) -> Configuracao:
        origem = os.environ if ambiente is None else ambiente
        return cls(
            backend=_texto(origem, "ASSISTENTE_BACKEND", BACKEND_PADRAO),
            espera=_numero(origem, "ASSISTENTE_TIMEOUT_CAIXA", ESPERA_PADRAO),
            idioma=_texto(origem, "ASSISTENTE_IDIOMA", IDIOMA_PADRAO),
            falar_resposta=_booleano(origem, "ASSISTENTE_FALAR", True),
        )


def _texto(ambiente: dict[str, str], chave: str, padrao: str) -> str:
    valor = (ambiente.get(chave) or "").strip()
    return valor or padrao


def _numero(ambiente: dict[str, str], chave: str, padrao: float) -> float:
    bruto = (ambiente.get(chave) or "").strip()
    if not bruto:
        return padrao
    try:
        valor = float(bruto)
    except ValueError as erro:
        raise ValueError(f"{chave} precisa ser um numero: {bruto!r}") from erro
    if valor <= 0:
        raise ValueError(f"{chave} precisa ser maior que zero: {bruto!r}")
    return valor


def _booleano(ambiente: dict[str, str], chave: str, padrao: bool) -> bool:
    bruto = (ambiente.get(chave) or "").strip().lower()
    if not bruto:
        return padrao
    return bruto in {"1", "sim", "true", "yes"}
