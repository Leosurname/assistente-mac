# Garante os pesos GGUF da Layla em disco, baixando na primeira vez.

from __future__ import annotations

import logging
import os
from pathlib import Path

import httpx

registrador = logging.getLogger(__name__)

CAMINHO_PADRAO = str(
    Path.home() / "modelos" / "mistral-7b-v0.1-layla-v4-chatml-Q4_K_M.gguf"
)
URL_PADRAO = (
    "https://huggingface.co/l3utterfly/mistral-7b-v0.1-layla-v4-chatml-gguf/"
    "resolve/main/mistral-7b-v0.1-layla-v4-chatml-Q4_K_M.gguf"
)
TAMANHO_DO_PEDACO = 1024 * 1024


def caminho_do_ambiente() -> str:
    return os.getenv("LAYLA_PESOS_CAMINHO") or CAMINHO_PADRAO


def url_do_ambiente() -> str:
    return os.getenv("LAYLA_PESOS_URL") or URL_PADRAO


def garantir(
    caminho: str | None = None,
    url: str | None = None,
    cliente_http: httpx.Client | None = None,
) -> str:
    """Baixa o GGUF se ele ainda nao existe. Devolve o caminho final."""
    destino = Path(caminho or caminho_do_ambiente())
    if (destino.exists()):
        return str(destino)

    origem = url or url_do_ambiente()
    destino.parent.mkdir(parents=True, exist_ok=True)
    # Baixa para um arquivo temporario e so troca de nome no fim: um download
    # interrompido nao pode parecer um GGUF completo na proxima vez.
    temporario = destino.with_suffix(destino.suffix + ".tmp")
    http = cliente_http or httpx.Client(timeout=None)

    registrador.info("Baixando pesos da Layla de %s", origem)
    with http.stream("GET", origem, follow_redirects=True) as resposta:
        resposta.raise_for_status()
        _baixar_para(resposta, temporario)

    temporario.rename(destino)
    registrador.info("Pesos da Layla prontos em %s", destino)
    return str(destino)


def _baixar_para(resposta: httpx.Response, temporario: Path) -> None:
    total = int(resposta.headers.get("Content-Length", 0))
    baixado = 0
    ultimo_marco = -1
    with open(temporario, "wb") as arquivo:
        for pedaco in resposta.iter_bytes(TAMANHO_DO_PEDACO):
            arquivo.write(pedaco)
            baixado += len(pedaco)
            marco = (baixado * 100 // total) // 10 if (total > 0) else -1
            if (marco > ultimo_marco):
                ultimo_marco = marco
                registrador.info("Download dos pesos: %d%%", marco * 10)
