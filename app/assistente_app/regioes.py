"""Nomes de regiao viram retangulos em pixels, aqui e so aqui.

O sistema de coordenadas e o da API de acessibilidade: origem no canto superior
esquerdo, y crescendo para baixo. E o mesmo que o backend assume ao conferir se
um retangulo cabe no monitor.
"""

from __future__ import annotations

from dataclasses import dataclass

# O catalogo e o mesmo do backend (backend/assistente/acoes.py). Se um lado
# mudar, o outro precisa mudar junto: uma regiao que a Layla pode escolher e a
# camada nativa nao sabe posicionar vira acao que nao acontece.
REGIOES: frozenset[str] = frozenset(
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


class RegiaoDesconhecida(ValueError):
    """A regiao pedida nao esta no catalogo."""


@dataclass(frozen=True)
class Retangulo:
    x: int
    y: int
    largura: int
    altura: int


@dataclass(frozen=True)
class AreaUtil:
    """A area do monitor onde uma janela pode ficar.

    Nao e o monitor inteiro: a barra de menu no topo e o Dock, quando visivel,
    ficam de fora. Posicionar uma janela debaixo da barra de menu e um jeito
    barato de esconder a barra de titulo dela.
    """

    x: int
    y: int
    largura: int
    altura: int


def calcular(regiao: str, area: AreaUtil) -> Retangulo:
    """Traduz um nome de regiao para coordenadas dentro da area util."""
    if regiao not in REGIOES:
        raise RegiaoDesconhecida(f"nao sei posicionar em {regiao!r}")

    x, y = area.x, area.y
    largura, altura = area.largura, area.altura
    meia_largura = largura // 2
    meia_altura = altura // 2
    terco = largura // 3

    match regiao:
        case "tela_cheia":
            return Retangulo(x, y, largura, altura)
        case "metade_esquerda":
            return Retangulo(x, y, meia_largura, altura)
        case "metade_direita":
            return Retangulo(x + meia_largura, y, largura - meia_largura, altura)
        case "metade_superior":
            return Retangulo(x, y, largura, meia_altura)
        case "metade_inferior":
            return Retangulo(x, y + meia_altura, largura, altura - meia_altura)
        case "terco_esquerdo":
            return Retangulo(x, y, terco, altura)
        case "terco_central":
            return Retangulo(x + terco, y, terco, altura)
        case "terco_direito":
            return Retangulo(x + 2 * terco, y, largura - 2 * terco, altura)
        case "canto_superior_esquerdo":
            return Retangulo(x, y, meia_largura, meia_altura)
        case "canto_superior_direito":
            return Retangulo(x + meia_largura, y, largura - meia_largura, meia_altura)
        case "canto_inferior_esquerdo":
            return Retangulo(x, y + meia_altura, meia_largura, altura - meia_altura)
        case "canto_inferior_direito":
            return Retangulo(
                x + meia_largura,
                y + meia_altura,
                largura - meia_largura,
                altura - meia_altura,
            )
        case "centro":
            # Deixa uma moldura em volta, para a janela nao encostar nas bordas.
            nova_largura = int(largura * 0.6)
            nova_altura = int(altura * 0.6)
            return Retangulo(
                x + (largura - nova_largura) // 2,
                y + (altura - nova_altura) // 2,
                nova_largura,
                nova_altura,
            )

    raise RegiaoDesconhecida(f"nao sei posicionar em {regiao!r}")  # pragma: no cover
