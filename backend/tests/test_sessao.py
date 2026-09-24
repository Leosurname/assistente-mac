"""Testes da sessao: historico curto que expira junto com a caixa."""

from __future__ import annotations

from assistente.sessao import MAXIMO_DE_TURNOS, RegistroDeSessoes, Sessao


def test_sessao_nova_quando_nao_ha_identificador():
    registro = RegistroDeSessoes()

    primeira = registro.obter(None)
    segunda = registro.obter(None)

    assert primeira.identificador != segunda.identificador
    assert len(registro) == 2


def test_o_mesmo_identificador_devolve_a_mesma_sessao():
    registro = RegistroDeSessoes()

    primeira = registro.obter("caixa-1")
    primeira.registrar("quero terminal", "{}")
    segunda = registro.obter("caixa-1")

    assert segunda is primeira
    assert list(segunda.pedidos) == ["quero terminal"]


def test_sessao_expirada_vira_sessao_limpa():
    registro = RegistroDeSessoes(validade=0.0)
    antiga = registro.obter("caixa-1")
    antiga.registrar("quero terminal", "{}")
    antiga.atualizada_em -= 10

    nova = registro.obter("caixa-1")

    assert nova is not antiga
    assert list(nova.pedidos) == []


def test_encerrar_esquece_a_sessao():
    """A caixa sumiu, a conversa acabou."""
    registro = RegistroDeSessoes()
    registro.obter("caixa-1")

    registro.encerrar("caixa-1")

    assert len(registro) == 0


def test_limpar_descarta_so_as_vencidas():
    registro = RegistroDeSessoes(validade=60.0)
    vencida = registro.obter("velha")
    registro.obter("nova")
    vencida.atualizada_em -= 120

    assert registro.limpar() == 1
    assert len(registro) == 1


def test_o_historico_nao_cresce_sem_limite():
    sessao = Sessao(identificador="caixa-1")

    for i in range(MAXIMO_DE_TURNOS + 5):
        sessao.registrar(f"pedido {i}", "{}")

    assert len(sessao.pedidos) == MAXIMO_DE_TURNOS
    assert len(sessao.historico) == MAXIMO_DE_TURNOS * 2


def test_registrar_reinicia_a_contagem_de_validade():
    sessao = Sessao(identificador="caixa-1", validade=10.0)
    sessao.atualizada_em -= 100
    assert sessao.expirou()

    sessao.registrar("quero terminal", "{}")

    assert not sessao.expirou()
