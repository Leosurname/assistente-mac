"""A caixa que aparece sobre a tela.

O painel nao rouba o foco. O usuario continua digitando no aplicativo de baixo,
e e essa digitacao que serve de sinal para a caixa sumir: um painel que ativa
tiraria o cursor de onde estava e o sinal de dispensa nunca chegaria. Dai o
`NSWindowStyleMaskNonactivatingPanel` e o `canBecomeKeyWindow` falso.
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
    """Painel que nunca vira janela principal.

    So vira janela chave enquanto `aceita_teclado` esta ligado — o tempo em
    que o campo do Option+8 esta aberto. O estilo nonactivating e o que deixa
    isso acontecer sem tirar o app da frente do lugar nem o desativar.
    """

    aceita_teclado = False

    def canBecomeKeyWindow(self) -> bool:  # noqa: N802 - nome exigido pelo AppKit
        return self.aceita_teclado

    def canBecomeMainWindow(self) -> bool:  # noqa: N802
        return False


class Sobreposicao:
    """A caixa, do ponto de vista do resto do programa."""

    def __init__(self) -> None:
        self._painel = self._criar_painel()
        self._rotulo = self._criar_rotulo()
        self._campo = self._criar_campo()
        self._painel.contentView().addSubview_(self._rotulo)
        self._painel.contentView().addSubview_(self._campo)
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

    def _criar_campo(self) -> NSTextField:
        campo = NSTextField.alloc().initWithFrame_(
            NSMakeRect(24, 24, LARGURA - 48, ALTURA - 48)
        )
        campo.setBezeled_(False)
        campo.setDrawsBackground_(False)
        campo.setEditable_(True)
        campo.setSelectable_(True)
        campo.setFont_(NSFont.systemFontOfSize_(22))
        campo.setTextColor_(NSColor.whiteColor())
        campo.setStringValue_("")
        campo.setHidden_(True)
        return campo

    def mostrar(self) -> None:
        # orderFrontRegardless, e nao makeKeyAndOrderFront: a caixa aparece sem
        # tirar o foco de quem esta na frente.
        self._painel.orderFrontRegardless()

    def mostrar_para_digitar(self) -> None:
        """Option+8: mostra a caixa e poe o cursor no campo.

        `makeKeyWindow`, nunca `activateIgnoringOtherApps_`: e o que o painel
        nonactivating permite, aceitar teclado sem tirar o app da frente do
        lugar.
        """
        self.mostrar()
        self._rotulo.setHidden_(True)
        self._campo.setStringValue_("")
        self._campo.setHidden_(False)
        self._painel.aceita_teclado = True
        self._painel.makeKeyWindow()
        self._painel.makeFirstResponder_(self._campo)

    def texto_digitado(self) -> str:
        return str(self._campo.stringValue())

    def ocultar(self) -> None:
        self._painel.aceita_teclado = False
        self._painel.orderOut_(None)

    def escrever(self, texto: str) -> None:
        self._voltar_ao_rotulo()
        self._rotulo.setStringValue_(texto or "Ouvindo…")

    def marcar_pensando(self, pensando: bool) -> None:
        self._pensando = pensando
        if pensando:
            self._voltar_ao_rotulo()
            self._rotulo.setTextColor_(
                NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.55)
            )
        else:
            self._rotulo.setTextColor_(NSColor.whiteColor())

    def _voltar_ao_rotulo(self) -> None:
        # Some do modo de digitar: a resposta e a transcricao sempre aparecem
        # no rotulo, nunca editavel.
        self._campo.setHidden_(True)
        self._rotulo.setHidden_(False)
        self._painel.aceita_teclado = False
