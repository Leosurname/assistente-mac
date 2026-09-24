"""O atalho global e a deteccao de digitacao.

Os dois saem do mesmo lugar: um event tap do Quartz, que ve o teclado do
sistema inteiro. E por isso que o aplicativo exige permissao de Acessibilidade
— sem ela o macOS nao entrega evento de teclado de outros aplicativos, e o
`Option + 9` simplesmente nao acontece.

O tap consome o `Option + 9` (devolve `None`) para que o caractere nao seja
digitado no aplicativo que esta na frente. Qualquer outra tecla passa adiante
intacta: este modulo observa, nao intercepta.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from Quartz import (
    CFMachPortCreateRunLoopSource,
    CFRunLoopAddSource,
    CFRunLoopGetCurrent,
    CGEventGetIntegerValueField,
    CGEventTapCreate,
    CGEventTapEnable,
    kCFRunLoopCommonModes,
    kCGEventKeyDown,
    kCGEventMaskForAllEvents,
    kCGEventTapOptionDefault,
    kCGHeadInsertEventTap,
    kCGKeyboardEventKeycode,
    kCGSessionEventTap,
)

registrador = logging.getLogger(__name__)

TECLA_9 = 25
TECLA_ESC = 53
MASCARA_OPTION = 0x00080000


class PermissaoNegada(RuntimeError):
    """O macOS nao deixou criar o event tap."""


class Teclado:
    """Escuta o teclado do sistema e avisa quem interessa."""

    def __init__(
        self,
        ao_atalho: Callable[[], None],
        ao_digitar: Callable[[], None],
        ao_escape: Callable[[], None],
    ) -> None:
        self._ao_atalho = ao_atalho
        self._ao_digitar = ao_digitar
        self._ao_escape = ao_escape
        self._tap = None

    def instalar(self) -> None:
        """Liga o tap no run loop atual."""
        self._tap = CGEventTapCreate(
            kCGSessionEventTap,
            kCGHeadInsertEventTap,
            kCGEventTapOptionDefault,
            kCGEventMaskForAllEvents & (1 << kCGEventKeyDown),
            self._tratar,
            None,
        )
        if self._tap is None:
            raise PermissaoNegada(
                "não consegui ouvir o teclado. Conceda Acessibilidade ao "
                "aplicativo em Ajustes do Sistema ▸ Privacidade e Segurança "
                "e abra-o de novo."
            )

        fonte = CFMachPortCreateRunLoopSource(None, self._tap, 0)
        CFRunLoopAddSource(CFRunLoopGetCurrent(), fonte, kCFRunLoopCommonModes)
        CGEventTapEnable(self._tap, True)
        registrador.info("Teclado sob escuta: Option+9 ativo")

    def _tratar(self, proxy, tipo, evento, referencia):  # noqa: ANN001, ARG002
        try:
            codigo = CGEventGetIntegerValueField(evento, kCGKeyboardEventKeycode)
            modificadores = _modificadores(evento)

            if codigo == TECLA_9 and modificadores & MASCARA_OPTION:
                self._ao_atalho()
                # Devolver None engole a tecla: sem isto o "ª" do Option+9
                # apareceria no aplicativo que esta na frente.
                return None

            if codigo == TECLA_ESC:
                self._ao_escape()
                return evento

            self._ao_digitar()
        except Exception:  # noqa: BLE001 - um erro aqui derrubaria o tap
            registrador.exception("Falha ao tratar tecla")
        return evento

    def desligar(self) -> None:
        if self._tap is not None:
            CGEventTapEnable(self._tap, False)
            self._tap = None


def _modificadores(evento) -> int:  # noqa: ANN001
    from Quartz import CGEventGetFlags

    return int(CGEventGetFlags(evento))
