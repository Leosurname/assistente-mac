# Manda um pedido ao backend por texto: o modo da beta, antes da voz.
#
# python scripts/pedido.py "quero terminal e safari"
# python scripts/pedido.py --executar "quero terminal e safari"

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

import websockets

TELA_DE_MENTIRA = {
    "monitores": [{"largura": 1920, "altura": 1080}],
    "apps_abertos": ["Finder", "Safari"],
    "janelas": [],
    "apps_instalados": ["Safari", "Terminal", "Finder"],
}


def endereco() -> str:
    return os.getenv("ASSISTENTE_BACKEND") or "ws://127.0.0.1:8765/ws"


# Retrato da máquina, ou um de mentira quando o PyObjC não está aqui.
def retrato(real: bool) -> dict:
    if not real:
        return TELA_DE_MENTIRA
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
    from assistente_app import contexto

    return contexto.montar()


async def conversar(texto: str, tela: dict) -> dict:
    async with websockets.connect(endereco()) as conexao:
        await conexao.send(json.dumps({"tipo": "pedido", "texto": texto, "tela": tela}))
        return json.loads(await conexao.recv())


def mostrar(resposta: dict) -> None:
    if resposta.get("tipo") == "erro":
        print(f"erro: {resposta.get('mensagem')}")
        return
    for acao in resposta.get("acoes", []):
        regiao = acao.get("regiao")
        print(
            f"  {acao['acao']:<12} {acao['app']}" + (f"  → {regiao}" if regiao else "")
        )
    if not resposta.get("acoes"):
        print("  (nenhuma ação)")
    print(f"fala: {resposta.get('fala')}")


def executar(resposta: dict) -> None:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
    from assistente_app.janelas import ExecutorDeJanelas
    from assistente_app.protocolo import ler_resposta

    falhas = ExecutorDeJanelas().executar(ler_resposta(resposta).acoes)
    for falha in falhas:
        print(f"  falhou: {falha}")


def principal() -> int:
    analisador = argparse.ArgumentParser(
        description="Manda um pedido ao backend por texto."
    )
    analisador.add_argument("texto", help="o pedido, em linguagem natural")
    analisador.add_argument(
        "--executar",
        action="store_true",
        help="mexe nas janelas de verdade; sem isso, só mostra o que faria",
    )
    analisador.add_argument(
        "--tela-falsa",
        action="store_true",
        help="usa um retrato fixo, para rodar fora do macOS",
    )
    argumentos = analisador.parse_args()

    try:
        resposta = asyncio.run(
            conversar(argumentos.texto, retrato(real=not argumentos.tela_falsa))
        )
    except OSError as erro:
        print(f"não consegui falar com o backend em {endereco()}: {erro}")
        return 1

    mostrar(resposta)
    if argumentos.executar:
        executar(resposta)
    return 0


if __name__ == "__main__":
    sys.exit(principal())
