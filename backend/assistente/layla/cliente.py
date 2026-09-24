"""Cliente HTTP da Layla.

A Layla e um conjunto de pesos GGUF servidos localmente pelo `llama-server` do
llama.cpp, que expoe uma API compativel com a da OpenAI. Nao ha chave de API: o
servidor esta no `localhost` e nao pede autenticacao.
"""

from __future__ import annotations

import asyncio
import logging
import random
from collections.abc import AsyncIterator, Sequence
from typing import Any

import httpx

from assistente.configuracao import ConfiguracaoLayla
from assistente.layla.erros import (
    ErroDeIndisponibilidade,
    ErroDeLimiteDeUso,
    ErroDeResposta,
    ErroDeTempoEsgotado,
)
from assistente.layla.interface import Mensagem
from assistente.layla.protocolo import (
    FIM,
    corpo_do_pedido,
    pedaco_do_evento,
    texto_da_resposta,
)

registrador = logging.getLogger(__name__)

ESPERA_INICIAL = 0.5
ESPERA_MAXIMA = 4.0
CODIGOS_QUE_MERECEM_NOVA_TENTATIVA = frozenset({429, 500, 502, 503, 504})


class ClienteLayla:
    """Implementacao de `ClienteDeLLM` que fala com o `llama-server` local."""

    def __init__(
        self,
        configuracao: ConfiguracaoLayla | None = None,
        cliente_http: httpx.AsyncClient | None = None,
    ) -> None:
        self.configuracao = configuracao or ConfiguracaoLayla()
        self._http_proprio = cliente_http is None
        self._http = cliente_http or httpx.AsyncClient(
            timeout=httpx.Timeout(self.configuracao.tempo_limite)
        )

    async def fechar(self) -> None:
        """Fecha o cliente HTTP, se fomos nos que o criamos."""
        if self._http_proprio:
            await self._http.aclose()

    async def __aenter__(self) -> ClienteLayla:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.fechar()

    async def _com_novas_tentativas(self, fazer_pedido: Any) -> httpx.Response:
        """Repete o pedido enquanto a falha for transitoria.

        Timeout, conexao recusada e respostas 429/5xx merecem outra tentativa:
        o `llama-server` pode ainda estar carregando o modelo, ou ocupado com
        outro pedido. Erro de formato ou 4xx de cliente, nao — repetir o mesmo
        pedido errado so gasta o orcamento de 3 segundos do produto.
        """
        ultima: Exception | None = None
        espera = ESPERA_INICIAL

        for tentativa in range(1, self.configuracao.tentativas + 1):
            try:
                resposta = await fazer_pedido()
            except httpx.TimeoutException as erro:
                ultima = ErroDeTempoEsgotado(
                    f"A Layla nao respondeu em {self.configuracao.tempo_limite}s"
                )
                registrador.warning(
                    "Tentativa %d: tempo esgotado (%s)", tentativa, erro
                )
            except httpx.HTTPError as erro:
                ultima = ErroDeIndisponibilidade(
                    f"Falha de conexao com a Layla: {erro}"
                )
                registrador.warning("Tentativa %d: sem conexao (%s)", tentativa, erro)
            else:
                if resposta.status_code in CODIGOS_QUE_MERECEM_NOVA_TENTATIVA:
                    ultima = self._erro_de_status(resposta)
                    registrador.warning(
                        "Tentativa %d: a Layla respondeu %d",
                        tentativa,
                        resposta.status_code,
                    )
                    await resposta.aclose()
                elif resposta.is_error:
                    erro_final = self._erro_de_status(resposta)
                    await resposta.aclose()
                    raise erro_final
                else:
                    return resposta

            if tentativa < self.configuracao.tentativas:
                # Um pouco de aleatoriedade evita que varios pedidos repitam em
                # bloco e derrubem de novo um servidor que acabou de voltar.
                await asyncio.sleep(espera + random.uniform(0, espera / 2))
                espera = min(espera * 2, ESPERA_MAXIMA)

        raise ultima or ErroDeIndisponibilidade("A Layla nao respondeu")

    @staticmethod
    def _erro_de_status(resposta: httpx.Response) -> Exception:
        if resposta.status_code == 429:
            return ErroDeLimiteDeUso("A Layla recusou por excesso de pedidos (429)")
        return ErroDeIndisponibilidade(f"A Layla respondeu {resposta.status_code}")

    async def conversar(
        self,
        mensagens: Sequence[Mensagem],
        *,
        temperatura: float | None = None,
        maximo_de_tokens: int | None = None,
        formato_resposta: dict[str, Any] | None = None,
    ) -> str:
        corpo = corpo_do_pedido(
            self.configuracao,
            mensagens,
            transmitir=False,
            temperatura=temperatura,
            maximo_de_tokens=maximo_de_tokens,
            formato_resposta=formato_resposta,
        )

        async def pedir() -> httpx.Response:
            return await self._http.post(self.configuracao.url_conversa, json=corpo)

        resposta = await self._com_novas_tentativas(pedir)
        try:
            dados = resposta.json()
        except ValueError as erro:
            raise ErroDeResposta(
                f"A Layla devolveu algo que nao e JSON: {erro}"
            ) from erro

        return texto_da_resposta(dados)

    async def transmitir(
        self,
        mensagens: Sequence[Mensagem],
        *,
        temperatura: float | None = None,
        maximo_de_tokens: int | None = None,
        formato_resposta: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """Devolve a resposta em pedacos, conforme o modelo vai gerando.

        O `llama-server` usa o mesmo formato de SSE da OpenAI: linhas `data: `
        com um JSON por pedaco, encerradas por `data: [DONE]`.
        """
        corpo = corpo_do_pedido(
            self.configuracao,
            mensagens,
            transmitir=True,
            temperatura=temperatura,
            maximo_de_tokens=maximo_de_tokens,
            formato_resposta=formato_resposta,
        )

        gerenciador = self._http.stream(
            "POST", self.configuracao.url_conversa, json=corpo
        )
        try:
            resposta = await gerenciador.__aenter__()
        except httpx.TimeoutException as erro:
            raise ErroDeTempoEsgotado(
                f"A Layla nao respondeu em {self.configuracao.tempo_limite}s"
            ) from erro
        except httpx.HTTPError as erro:
            raise ErroDeIndisponibilidade(
                f"Falha de conexao com a Layla: {erro}"
            ) from erro

        try:
            if resposta.is_error:
                raise self._erro_de_status(resposta)
            async for linha in resposta.aiter_lines():
                pedaco = pedaco_do_evento(linha)
                if pedaco is FIM:
                    break
                if pedaco:
                    yield pedaco
        except httpx.TimeoutException as erro:
            raise ErroDeTempoEsgotado("A Layla parou no meio da resposta") from erro
        finally:
            await gerenciador.__aexit__(None, None, None)

    async def esta_disponivel(self) -> bool:
        """Confere se o `llama-server` esta no ar, sem gerar texto."""
        try:
            resposta = await self._http.get(self.configuracao.url_modelos)
        except httpx.HTTPError:
            return False
        return not resposta.is_error
