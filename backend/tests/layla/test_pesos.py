"""Testes do download dos pesos. Nenhum deles baixa nada de verdade."""

from __future__ import annotations

import httpx
from assistente.layla import pesos


def _cliente_de_mentira(conteudo: bytes) -> httpx.Client:
    def responder(pedido: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, content=conteudo, headers={"Content-Length": str(len(conteudo))}
        )

    return httpx.Client(transport=httpx.MockTransport(responder))


def test_garantir_nao_baixa_se_o_arquivo_ja_existe(tmp_path):
    destino = tmp_path / "pesos.gguf"
    destino.write_bytes(b"ja esta aqui")

    caminho = pesos.garantir(str(destino), cliente_http=_cliente_de_mentira(b"novo"))

    assert caminho == str(destino)
    assert destino.read_bytes() == b"ja esta aqui"


def test_garantir_baixa_e_grava_o_arquivo_quando_falta(tmp_path):
    destino = tmp_path / "modelos" / "pesos.gguf"
    conteudo = b"conteudo do gguf de mentira"

    caminho = pesos.garantir(
        str(destino),
        url="http://layla.invalida/pesos.gguf",
        cliente_http=_cliente_de_mentira(conteudo),
    )

    assert caminho == str(destino)
    assert destino.read_bytes() == conteudo


def test_garantir_nao_deixa_arquivo_temporario_para_tras(tmp_path):
    destino = tmp_path / "pesos.gguf"

    pesos.garantir(str(destino), cliente_http=_cliente_de_mentira(b"dados"))

    temporario = destino.with_suffix(destino.suffix + ".tmp")
    assert not temporario.exists()


def test_caminho_do_ambiente_usa_a_variavel(monkeypatch):
    monkeypatch.setenv("LAYLA_PESOS_CAMINHO", "/tmp/outro/pesos.gguf")

    assert pesos.caminho_do_ambiente() == "/tmp/outro/pesos.gguf"


def test_caminho_do_ambiente_usa_o_padrao_sem_variavel(monkeypatch):
    monkeypatch.delenv("LAYLA_PESOS_CAMINHO", raising=False)

    assert pesos.caminho_do_ambiente() == pesos.CAMINHO_PADRAO
