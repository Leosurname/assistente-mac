# Testes do retrato da tela.

from __future__ import annotations

from assistente.tela import retrato


def test_apps_conhecidos_nao_repete_o_mesmo_app():
    lido = retrato.RetratoDaTela(
        apps_abertos=("Safari", "Finder"),
        janelas=(retrato.Janela(app="Safari", x=0, y=0, largura=100, altura=100),),
        apps_instalados=("Safari", "Terminal"),
    )

    assert lido.apps_conhecidos == ("Safari", "Finder", "Terminal")
