"""O catalogo fechado de acoes e o esquema que a Layla e obrigada a seguir.

Este modulo e a fronteira do que o assistente sabe fazer. Uma acao que nao esta
aqui nao existe: nao ha caminho em que um texto vindo do modelo vire comando de
shell ou chamada arbitraria. Aumentar o catalogo e mexer neste arquivo, de
proposito, e nao um efeito colateral de um prompt bem escrito.
"""

from __future__ import annotations

from typing import Any, Final

ABRIR_APP: Final = "abrir_app"
FECHAR_APP: Final = "fechar_app"
POSICIONAR: Final = "posicionar"
FOCAR: Final = "focar"
MINIMIZAR: Final = "minimizar"

CATALOGO: Final[frozenset[str]] = frozenset(
    {ABRIR_APP, FECHAR_APP, POSICIONAR, FOCAR, MINIMIZAR}
)

# As regioes sao nomes, nao coordenadas, porque quem sabe o tamanho real da
# tela e a camada nativa. A Layla escolhe "metade_esquerda"; a conversao para
# pixels acontece com o retrato da tela em maos.
REGIOES: Final[frozenset[str]] = frozenset(
    {
        "tela_cheia",
        "metade_esquerda",
        "metade_direita",
        "metade_superior",
        "metade_inferior",
        "terco_esquerdo",
        "terco_central",
        "terco_direito",
        "canto_superior_esquerdo",
        "canto_superior_direito",
        "canto_inferior_esquerdo",
        "canto_inferior_direito",
        "centro",
    }
)

DESCRICAO_DAS_ACOES: Final[dict[str, str]] = {
    ABRIR_APP: "Abre um aplicativo que ainda nao esta aberto.",
    FECHAR_APP: "Fecha um aplicativo. So quando o usuario pedir explicitamente.",
    POSICIONAR: "Move e redimensiona a janela de um aplicativo para uma regiao.",
    FOCAR: "Traz a janela de um aplicativo para a frente.",
    MINIMIZAR: "Minimiza a janela de um aplicativo.",
}


def esquema_da_resposta() -> dict[str, Any]:
    """JSON Schema da resposta que a Layla deve devolver.

    Vai para o `llama-server` no campo `response_format`, que deriva dele uma
    gramatica e restringe a decodificacao. Os fine-tunes layla sao voltados a
    conversa, e sem essa restricao erram o formato com frequencia.
    """
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["acoes", "fala"],
        "properties": {
            "acoes": {
                "type": "array",
                "maxItems": 12,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["acao", "app"],
                    "properties": {
                        "acao": {"type": "string", "enum": sorted(CATALOGO)},
                        "app": {"type": "string", "minLength": 1, "maxLength": 80},
                        "regiao": {"type": "string", "enum": sorted(REGIOES)},
                    },
                },
            },
            "fala": {"type": "string", "maxLength": 200},
        },
    }
