from __future__ import annotations

from assistente.acoes import catalogo, validacao
from assistente.modos import arranjos, expansao
from assistente.tela import retrato

TELA = retrato.RetratoDaTela(
    monitores=(retrato.Monitor(largura=3456, altura=2234),),
    apps_abertos=("Finder", "Terminal", "Spotify"),
)


def test_modo_abre_o_que_falta_e_posiciona():
    assert expansao.expandir("revisao_pr", TELA) == [
        {"acao": "abrir_app", "app": "Safari"},
        {"acao": "posicionar", "app": "Safari", "regiao": "metade_esquerda"},
        {"acao": "posicionar", "app": "Terminal", "regiao": "metade_direita"},
    ]


def test_modo_nao_abre_app_que_ja_esta_aberto():
    acoes = expansao.expandir("revisao_pr", TELA)

    assert {"acao": "abrir_app", "app": "Terminal"} not in acoes


def test_modo_nunca_fecha_nem_minimiza():
    vazia = retrato.RetratoDaTela(monitores=TELA.monitores)
    for chave in arranjos.MODOS:
        acoes = {a["acao"] for a in expansao.expandir(chave, vazia)}
        assert acoes <= {catalogo.ABRIR_APP, catalogo.POSICIONAR}


def test_passos_de_todo_modo_usam_regiao_do_catalogo():
    for modo in arranjos.MODOS.values():
        for _, regiao in modo.passos:
            assert regiao is None or regiao in catalogo.REGIOES


def test_modo_citado_ignora_acento_e_caixa():
    assert expansao.modo_citado("revisao_pr", ["Modo REVISÃO de PR"])


def test_modo_que_o_usuario_nao_falou_nao_vale():
    assert not expansao.modo_citado("revisao_pr", ["abre o spotify"])
    assert not expansao.modo_citado("modo_inventado", ["modo inventado"])


def test_apps_do_modo_passam_na_validacao_e_o_resto_fica_onde_esta():
    acoes = [
        *expansao.expandir("revisao_pr", TELA),
        {"acao": "minimizar", "app": "Spotify"},
    ]

    resultado = validacao.validar_acoes(
        acoes,
        tela=TELA,
        textos_do_usuario=["modo revisão de PR"],
        apps_do_modo=expansao.apps_do_modo("revisao_pr"),
    )

    assert {a.app for a in resultado.aprovadas} == {"Safari", "Terminal"}
    assert "Spotify" in resultado.recusadas[0].motivo
