from __future__ import annotations

import pytest

from assistente_app.regioes import (
    REGIOES,
    AreaUtil,
    RegiaoDesconhecida,
    calcular,
)

AREA = AreaUtil(x=0, y=25, largura=1000, altura=600)


def test_metades_dividem_a_area_sem_sobra():
    esquerda = calcular("metade_esquerda", AREA)
    direita = calcular("metade_direita", AREA)

    assert esquerda.x == 0
    assert esquerda.largura + direita.largura == AREA.largura
    assert direita.x == esquerda.largura


def test_tela_cheia_respeita_a_area_util():
    # Nao e o monitor inteiro: a barra de menu e o Dock ficam de fora.
    cheia = calcular("tela_cheia", AREA)

    assert (cheia.x, cheia.y) == (0, 25)
    assert (cheia.largura, cheia.altura) == (1000, 600)


def test_tercos_cobrem_a_largura_inteira():
    esquerdo = calcular("terco_esquerdo", AREA)
    central = calcular("terco_central", AREA)
    direito = calcular("terco_direito", AREA)

    assert esquerdo.largura + central.largura + direito.largura == AREA.largura
    assert direito.x + direito.largura == AREA.x + AREA.largura


def test_largura_impar_nao_deixa_buraco():
    area = AreaUtil(x=0, y=0, largura=999, altura=501)

    esquerda = calcular("metade_esquerda", area)
    direita = calcular("metade_direita", area)

    assert direita.x == esquerda.largura
    assert direita.x + direita.largura == 999


def test_centro_fica_dentro_da_area():
    centro = calcular("centro", AREA)

    assert centro.x >= AREA.x
    assert centro.y >= AREA.y
    assert centro.x + centro.largura <= AREA.x + AREA.largura
    assert centro.y + centro.altura <= AREA.y + AREA.altura


@pytest.mark.parametrize("regiao", sorted(REGIOES))
def test_toda_regiao_do_catalogo_tem_calculo(regiao: str):
    # Uma regiao que a Layla pode escolher e a camada nativa nao sabe
    # posicionar vira acao que nao acontece.
    retangulo = calcular(regiao, AREA)

    assert retangulo.largura > 0
    assert retangulo.altura > 0


def test_regiao_fora_do_catalogo_e_recusada():
    with pytest.raises(RegiaoDesconhecida):
        calcular("atras_do_monitor", AREA)
