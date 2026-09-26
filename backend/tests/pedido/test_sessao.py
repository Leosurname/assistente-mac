"""Testes da sessao: historico curto que expira junto com a caixa."""

from __future__ import annotations

from assistente.pedido import sessao


def test_sessao_nova_quando_nao_ha_identificador():
    registro = sessao.RegistroDeSessoes()

    primeira = registro.obter(None)
    segunda = registro.obter(None)

    assert primeira.identificador != segunda.identificador
    assert len(registro) == 2


def test_o_mesmo_identificador_devolve_a_mesma_sessao():
    registro = sessao.RegistroDeSessoes()

    primeira = registro.obter("caixa-1")
    primeira.registrar("quero terminal", "{}")
    segunda = registro.obter("caixa-1")

    assert segunda is primeira
    assert list(segunda.pedidos) == ["quero terminal"]


def test_sessao_expirada_vira_sessao_limpa():
    registro = sessao.RegistroDeSessoes(validade=0.0)
    antiga = registro.obter("caixa-1")
    antiga.registrar("quero terminal", "{}")
    antiga.atualizada_em -= 10

    nova = registro.obter("caixa-1")

    assert nova is not antiga
    assert list(nova.pedidos) == []


def test_encerrar_esquece_a_sessao():
    """A caixa sumiu, a conversa acabou."""
    registro = sessao.RegistroDeSessoes()
    registro.obter("caixa-1")

    registro.encerrar("caixa-1")

    assert len(registro) == 0


def test_limpar_descarta_so_as_vencidas():
    registro = sessao.RegistroDeSessoes(validade=60.0)
    vencida = registro.obter("velha")
    registro.obter("nova")
    vencida.atualizada_em -= 120

    assert registro.limpar() == 1
    assert len(registro) == 1


def test_o_historico_nao_cresce_sem_limite():
    atual = sessao.Sessao(identificador="caixa-1")

    for i in range(sessao.MAXIMO_DE_TURNOS + 5):
        atual.registrar(f"pedido {i}", "{}")

    assert len(atual.pedidos) == sessao.MAXIMO_DE_TURNOS
    assert len(atual.historico) == sessao.MAXIMO_DE_TURNOS * 2


def test_registrar_reinicia_a_contagem_de_validade():
    atual = sessao.Sessao(identificador="caixa-1", validade=10.0)
    atual.atualizada_em -= 100
    assert atual.expirou()

    atual.registrar("quero terminal", "{}")

    assert not atual.expirou()
