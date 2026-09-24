"""As tres regras de sumico da caixa.

Este arquivo e o que garante o produto: a caixa precisa sumir sozinha, e sumir
pelo motivo certo.
"""

from __future__ import annotations

from assistente_app.dispensa import Dispensa, Efeito, Estado


def test_atalho_mostra_a_caixa():
    dispensa = Dispensa()
    assert dispensa.atalho(agora=0.0) is Efeito.MOSTRAR
    assert dispensa.estado is Estado.ESCUTANDO
    assert dispensa.visivel


def test_atalho_com_a_caixa_aberta_nao_fecha():
    # Um atalho que alterna faria o usuario perder o pedido ao apertar duas
    # vezes por engano.
    dispensa = Dispensa()
    dispensa.atalho(agora=0.0)
    dispensa.concluido(agora=1.0)

    assert dispensa.atalho(agora=2.0) is Efeito.NADA
    assert dispensa.estado is Estado.ESCUTANDO
    assert dispensa.prazo is None


def test_some_depois_de_cinco_segundos_sem_pedido():
    dispensa = Dispensa(espera=5.0)
    dispensa.atalho(agora=0.0)
    dispensa.pedido_enviado()
    dispensa.concluido(agora=10.0)

    assert dispensa.tique(agora=14.9) is Efeito.NADA
    assert dispensa.tique(agora=15.0) is Efeito.OCULTAR
    assert dispensa.estado is Estado.OCULTA


def test_digitar_faz_sumir_na_hora():
    dispensa = Dispensa()
    dispensa.atalho(agora=0.0)

    assert dispensa.digitou() is Efeito.OCULTAR
    assert not dispensa.visivel


def test_digitar_faz_sumir_ate_esperando_o_backend():
    # Quem voltou a digitar ja saiu da conversa, mesmo com pedido em voo.
    dispensa = Dispensa()
    dispensa.atalho(agora=0.0)
    dispensa.pedido_enviado()

    assert dispensa.digitou() is Efeito.OCULTAR


def test_esc_faz_sumir():
    dispensa = Dispensa()
    dispensa.atalho(agora=0.0)

    assert dispensa.escape() is Efeito.OCULTAR


def test_nao_expira_enquanto_o_usuario_fala():
    dispensa = Dispensa(espera=5.0)
    dispensa.atalho(agora=0.0)
    dispensa.concluido(agora=1.0)

    dispensa.transcricao_parcial()

    assert dispensa.prazo is None
    assert dispensa.tique(agora=100.0) is Efeito.NADA
    assert dispensa.estado is Estado.ESCUTANDO


def test_nao_expira_enquanto_o_backend_pensa():
    # A Layla pode demorar. Sumir no meio deixaria o usuario sem resposta e com
    # as janelas mexendo sozinhas depois.
    dispensa = Dispensa(espera=5.0)
    dispensa.atalho(agora=0.0)
    dispensa.pedido_enviado()

    assert dispensa.prazo is None
    assert dispensa.tique(agora=999.0) is Efeito.NADA


def test_pedido_emendado_reinicia_a_contagem():
    dispensa = Dispensa(espera=5.0)
    dispensa.atalho(agora=0.0)
    dispensa.concluido(agora=10.0)

    dispensa.transcricao_parcial()
    dispensa.pedido_enviado()
    dispensa.concluido(agora=13.0)

    assert dispensa.tique(agora=17.0) is Efeito.NADA
    assert dispensa.tique(agora=18.0) is Efeito.OCULTAR


def test_eventos_com_a_caixa_oculta_nao_fazem_nada():
    dispensa = Dispensa()

    assert dispensa.digitou() is Efeito.NADA
    assert dispensa.escape() is Efeito.NADA
    assert dispensa.tique(agora=99.0) is Efeito.NADA
    assert dispensa.concluido(agora=99.0) is Efeito.NADA


def test_espera_configuravel():
    dispensa = Dispensa(espera=1.5)
    dispensa.atalho(agora=0.0)
    dispensa.concluido(agora=0.0)

    assert dispensa.tique(agora=1.4) is Efeito.NADA
    assert dispensa.tique(agora=1.5) is Efeito.OCULTAR
