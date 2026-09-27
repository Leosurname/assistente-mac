# Os modos de trabalho: um nome que arruma a tela de uma vez. Modo e dado, nao codigo.

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class Modo:
    nome: str
    frases: tuple[str, ...]
    # Regiao None quer dizer so abrir, sem posicionar.
    passos: tuple[tuple[str, str | None], ...]


MODOS: Final[dict[str, Modo]] = {
    "revisao_pr": Modo(
        nome="revisão de PR",
        frases=("modo revisao de pr", "revisao de pr", "revisar pr"),
        passos=(("Safari", "metade_esquerda"), ("Terminal", "metade_direita")),
    ),
}
