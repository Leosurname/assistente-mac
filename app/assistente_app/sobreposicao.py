"""A caixa que aparece sobre a tela.

O detalhe que faz o produto funcionar: o painel **nao rouba o foco**. O usuario
continua digitando no aplicativo de baixo, e e essa digitacao que serve de
sinal para a caixa sumir. Um painel que ativa quebraria as duas coisas ao mesmo
tempo — o usuario perderia o cursor de onde estava, e o sinal de dispensa
nunca chegaria.

Daí `NSWindowStyleMaskNonactivatingPanel` e o `canBecomeKeyWindow` devolvendo
falso logo abaixo.
"""

from __future__ import annotations

from AppKit import (
    NSBackingStoreBuffered,
    NSColor,
    NSFont,
    NSMakeRect,
    NSPanel,
    NSScreen,
    NSTextField,
    NSView,
    NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSWindowCollectionBehaviorFullScreenAuxiliary,
    NSWindowStyleMaskBorderless,
    NSWindowStyleMaskNonactivatingPanel,
)

LARGURA = 620.0
ALTURA = 92.0
MARGEM_DO_TOPO = 160.0
CANTO = 18.0


class PainelSemFoco(NSPanel):
    """Painel que nunca vira janela principal."""

    def canBecomeKeyWindow(self) -> bool:  # noqa: N802 - nome exigido pelo AppKit
        return False

    def canBecomeMainWindow(self) -> bool:  # noqa: N802
        return False


class Sobreposicao:
    """A caixa, do ponto de vista do resto do programa."""

    def __init__(self) -> None:
        self._painel = self._criar_painel()
        self._rotulo = self._criar_rotulo()
        self._painel.contentView().addSubview_(self._rotulo)
        self._pensando = False

    def _criar_painel(self) -> PainelSemFoco:
        tela = NSScreen.mainScreen().frame()
        quadro = NSMakeRect(
            (tela.size.width - LARGURA) / 2,
            tela.size.height - MARGEM_DO_TOPO,
            LARGURA,
            ALTURA,
        )
        painel = PainelSemFoco.alloc().initWithContentRect_styleMask_backing_defer_(
            quadro,
            NSWindowStyleMaskBorderless | NSWindowStyleMaskNonactivatingPanel,
            NSBackingStoreBuffered,
            False,
        )
        painel.setOpaque_(False)
        painel.setBackgroundColor_(NSColor.clearColor())
        painel.setLevel_(25)  # acima de janelas normais, abaixo de alertas
        painel.setHidesOnDeactivate_(False)
        painel.setIgnoresMouseEvents_(True)
        painel.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces
            | NSWindowCollectionBehaviorFullScreenAuxiliary
        )

        fundo = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, LARGURA, ALTURA))
        fundo.setWantsLayer_(True)
        camada = fundo.layer()
        camada.setCornerRadius_(CANTO)
        camada.setBackgroundColor_(
            NSColor.colorWithCalibratedWhite_alpha_(0.10, 0.92).CGColor()
        )
        painel.setContentView_(fundo)
        return painel

    def _criar_rotulo(self) -> NSTextField:
        rotulo = NSTextField.alloc().initWithFrame_(
            NSMakeRect(24, 24, LARGURA - 48, ALTURA - 48)
        )
        rotulo.setBezeled_(False)
        rotulo.setDrawsBackground_(False)
        rotulo.setEditable_(False)
        rotulo.setSelectable_(False)
        rotulo.setFont_(NSFont.systemFontOfSize_(22))
        rotulo.setTextColor_(NSColor.whiteColor())
        rotulo.setStringValue_("")
        return rotulo

    # --- o que o coordenador chama ---------------------------------------

    def mostrar(self) -> None:
        # orderFrontRegardless, e nao makeKeyAndOrderFront: a caixa aparece sem
        # tirar o foco de quem esta na frente.
        self._painel.orderFrontRegardless()

    def ocultar(self) -> None:
        self._painel.orderOut_(None)

    def escrever(self, texto: str) -> None:
        self._rotulo.setStringValue_(texto or "Ouvindo…")

    def marcar_pensando(self, pensando: bool) -> None:
        self._pensando = pensando
        if pensando:
            self._rotulo.setTextColor_(
                NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.55)
            )
        else:
            self._rotulo.setTextColor_(NSColor.whiteColor())
