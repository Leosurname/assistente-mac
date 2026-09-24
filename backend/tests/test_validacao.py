"""Testes da validacao. E aqui que mora a promessa do produto."""

from __future__ import annotations

import pytest
from assistente.tela import Janela, Monitor, RetratoDaTela
from assistente.validacao import app_foi_citado, normalizar, validar_acoes

TELA = RetratoDaTela(
    monitores=(Monitor(largura=3456, altura=2234),),
    apps_abertos=("Finder", "Safari", "Terminal", "Claude Code", "Spotify"),
    janelas=(Janela(app="Safari", x=100, y=80, largura=1200, altura=900),),
)

PEDIDO = ["quero terminal e safari, e ja deixa o claude code aberto"]


def _validar(acoes, textos=PEDIDO, tela=TELA):
    return validar_acoes(acoes, tela=tela, textos_do_usuario=textos)


# ── catalogo fechado ─────────────────────────────────────────────────────────


def test_acao_fora_do_catalogo_e_recusada():
    resultado = _validar([{"acao": "rodar_shell", "app": "Terminal"}])

    assert resultado.aprovadas == ()
    assert "catalogo" in resultado.recusadas[0].motivo


def test_todas_as_acoes_do_catalogo_passam():
    acoes = [
        {"acao": "abrir_app", "app": "Terminal"},
        {"acao": "focar", "app": "Safari"},
        {"acao": "minimizar", "app": "Safari"},
        {"acao": "posicionar", "app": "Terminal", "regiao": "metade_esquerda"},
    ]

    resultado = _validar(acoes)

    assert len(resultado.aprovadas) == 4
    assert not resultado.houve_recusa


def test_acao_que_nao_e_objeto_e_recusada():
    resultado = _validar(["abrir o terminal", None, 42])

    assert resultado.aprovadas == ()
    assert len(resultado.recusadas) == 3


def test_lista_que_nao_e_lista_e_recusada():
    resultado = _validar({"acao": "abrir_app", "app": "Terminal"})

    assert resultado.aprovadas == ()
    assert resultado.houve_recusa


# ── so se mexe no que foi pedido ─────────────────────────────────────────────


def test_app_nao_citado_no_pedido_e_recusado():
    """O Spotify esta aberto, mas ninguem falou dele. Fica onde esta."""
    resultado = _validar([{"acao": "minimizar", "app": "Spotify"}])

    assert resultado.aprovadas == ()
    assert "nao foi citado" in resultado.recusadas[0].motivo


def test_fechar_app_nao_citado_e_recusado():
    resultado = _validar([{"acao": "fechar_app", "app": "Finder"}])

    assert resultado.aprovadas == ()


def test_app_citado_passa_e_o_nao_citado_cai_na_mesma_lista():
    acoes = [
        {"acao": "abrir_app", "app": "Terminal"},
        {"acao": "minimizar", "app": "Spotify"},
    ]

    resultado = _validar(acoes)

    assert [a.app for a in resultado.aprovadas] == ["Terminal"]
    assert len(resultado.recusadas) == 1


def test_o_historico_da_sessao_conta_como_citacao():
    """ "agora joga o Safari pra direita" se apoia no pedido anterior."""
    anteriores = ["quero terminal e safari"]
    acoes = [{"acao": "posicionar", "app": "Safari", "regiao": "metade_direita"}]

    resultado = _validar(acoes, textos=[*anteriores, "agora joga ele pra direita"])

    assert len(resultado.aprovadas) == 1


def test_sem_nenhuma_fala_do_usuario_nada_passa():
    resultado = _validar([{"acao": "abrir_app", "app": "Terminal"}], textos=[])

    assert resultado.aprovadas == ()


@pytest.mark.parametrize(
    ("app", "pedido"),
    [
        ("Terminal", "abre o terminal"),
        ("Safari", "quero o SAFARI"),
        ("Claude Code", "ja deixa o claude code aberto"),
        ("Google Chrome", "abre o chrome"),
        ("Visual Studio Code", "abre o vscode"),
        ("Música", "poe a musica"),
    ],
)
def test_reconhece_o_app_pelo_nome_e_pelos_apelidos(app: str, pedido: str):
    assert app_foi_citado(app, [pedido])


def test_nao_confunde_app_que_nao_foi_falado():
    assert not app_foi_citado("Spotify", ["quero terminal e safari"])


def test_normalizar_tira_acento_e_caixa():
    assert normalizar("  Música  DO  Usuário ") == "musica do usuario"


# ── aplicativos que existem ──────────────────────────────────────────────────


def test_app_desconhecido_pela_maquina_e_recusado():
    tela = RetratoDaTela(
        monitores=(Monitor(1920, 1080),),
        apps_abertos=("Finder",),
        apps_instalados=("Safari", "Terminal"),
    )

    resultado = _validar(
        [{"acao": "abrir_app", "app": "Photoshop"}],
        textos=["abre o photoshop"],
        tela=tela,
    )

    assert resultado.aprovadas == ()
    assert "nao encontrei" in resultado.recusadas[0].motivo


def test_abrir_app_que_ainda_nao_esta_aberto_passa():
    """E o caso normal de `abrir_app`: o Terminal esta instalado, nao aberto."""
    tela = RetratoDaTela(
        monitores=(Monitor(1920, 1080),),
        apps_abertos=("Finder",),
        apps_instalados=("Finder", "Safari", "Terminal"),
    )

    resultado = _validar(
        [{"acao": "abrir_app", "app": "Terminal"}],
        textos=["abre o terminal"],
        tela=tela,
    )

    assert len(resultado.aprovadas) == 1


def test_sem_retrato_a_checagem_de_existencia_fica_com_a_camada_nativa():
    """O backend nao enxerga /Applications; quem enxerga e o app nativo."""
    resultado = _validar(
        [{"acao": "abrir_app", "app": "Photoshop"}],
        textos=["abre o photoshop"],
        tela=RetratoDaTela(),
    )

    assert len(resultado.aprovadas) == 1


# ── coordenadas e regioes ────────────────────────────────────────────────────


def test_posicionar_sem_regiao_e_recusado():
    resultado = _validar([{"acao": "posicionar", "app": "Safari"}])

    assert "sem dizer a regiao" in resultado.recusadas[0].motivo


def test_regiao_inventada_e_recusada():
    acoes = [{"acao": "posicionar", "app": "Safari", "regiao": "flutuando"}]

    resultado = _validar(acoes)

    assert "nao existe" in resultado.recusadas[0].motivo


def test_coordenadas_que_nao_cabem_na_tela_sao_recusadas():
    acoes = [
        {
            "acao": "posicionar",
            "app": "Safari",
            "regiao": "metade_direita",
            "x": 3000,
            "y": 0,
            "largura": 2000,
            "altura": 900,
        }
    ]

    resultado = _validar(acoes)

    assert "nao cabem na tela" in resultado.recusadas[0].motivo


def test_coordenadas_que_cabem_passam():
    acoes = [
        {
            "acao": "posicionar",
            "app": "Safari",
            "regiao": "metade_direita",
            "x": 1728,
            "y": 0,
            "largura": 1728,
            "altura": 2234,
        }
    ]

    resultado = _validar(acoes)

    assert len(resultado.aprovadas) == 1


def test_coordenadas_negativas_sao_recusadas():
    acoes = [
        {
            "acao": "posicionar",
            "app": "Safari",
            "regiao": "centro",
            "x": -10,
            "y": 0,
            "largura": 100,
            "altura": 100,
        }
    ]

    assert _validar(acoes).aprovadas == ()


def test_regiao_em_acao_que_nao_posiciona_e_recusada():
    acoes = [{"acao": "abrir_app", "app": "Terminal", "regiao": "tela_cheia"}]

    assert _validar(acoes).aprovadas == ()


def test_a_acao_aprovada_so_carrega_campos_do_catalogo():
    """Campo extra inventado pela Layla nao chega ao executor."""
    acoes = [
        {"acao": "abrir_app", "app": "Terminal", "comando": "rm -rf /", "shell": True}
    ]

    resultado = _validar(acoes)

    assert resultado.aprovadas[0].para_dicionario() == {
        "acao": "abrir_app",
        "app": "Terminal",
    }
