from __future__ import annotations

import pytest

from assistente_app.protocolo import (
    ErroDoBackend,
    RespostaInvalida,
    ler_resposta,
    montar_encerramento,
    montar_pedido,
)


def test_pedido_leva_texto_e_tela():
    pedido = montar_pedido("quero terminal e safari", {"monitores": []})

    assert pedido["tipo"] == "pedido"
    assert pedido["texto"] == "quero terminal e safari"
    assert pedido["tela"] == {"monitores": []}
    assert "sessao" not in pedido


def test_pedido_emendado_leva_a_sessao():
    pedido = montar_pedido("agora joga o safari pra direita", {}, sessao="abc")

    assert pedido["sessao"] == "abc"


def test_encerramento():
    assert montar_encerramento("abc") == {"tipo": "encerrar", "sessao": "abc"}


def test_le_acoes():
    resposta = ler_resposta(
        {
            "tipo": "acoes",
            "acoes": [
                {"acao": "abrir_app", "app": "Terminal"},
                {"acao": "posicionar", "app": "Safari", "regiao": "metade_direita"},
            ],
            "fala": "concluído",
            "sessao": "s1",
        }
    )

    assert [a.acao for a in resposta.acoes] == ["abrir_app", "posicionar"]
    assert resposta.acoes[1].regiao == "metade_direita"
    assert resposta.fala == "concluído"
    assert resposta.sessao == "s1"


def test_acao_fora_do_catalogo_e_recusada():
    # O catalogo e fechado. Nao ha caminho em que texto de modelo vira comando.
    with pytest.raises(RespostaInvalida):
        ler_resposta(
            {
                "tipo": "acoes",
                "acoes": [{"acao": "rodar_shell", "app": "rm -rf /"}],
                "fala": "ok",
            }
        )


def test_regiao_fora_do_catalogo_e_recusada():
    with pytest.raises(RespostaInvalida):
        ler_resposta(
            {
                "tipo": "acoes",
                "acoes": [
                    {"acao": "posicionar", "app": "Safari", "regiao": "lugar_nenhum"}
                ],
                "fala": "ok",
            }
        )


def test_posicionar_sem_regiao_e_recusado():
    with pytest.raises(RespostaInvalida):
        ler_resposta(
            {
                "tipo": "acoes",
                "acoes": [{"acao": "posicionar", "app": "Safari"}],
                "fala": "ok",
            }
        )


def test_acao_sem_aplicativo_e_recusada():
    with pytest.raises(RespostaInvalida):
        ler_resposta(
            {"tipo": "acoes", "acoes": [{"acao": "focar", "app": "  "}], "fala": "ok"}
        )


def test_erro_do_backend_vira_excecao_com_mensagem():
    with pytest.raises(ErroDoBackend) as capturado:
        ler_resposta({"tipo": "erro", "mensagem": "não achei o Claude Code"})

    assert capturado.value.mensagem == "não achei o Claude Code"


def test_tipo_desconhecido_e_recusado():
    with pytest.raises(RespostaInvalida):
        ler_resposta({"tipo": "surpresa"})


def test_resposta_que_nao_e_objeto_e_recusada():
    with pytest.raises(RespostaInvalida):
        ler_resposta(["acoes"])


def test_fala_vazia_vira_o_padrao():
    resposta = ler_resposta({"tipo": "acoes", "acoes": [], "fala": "   "})

    assert resposta.fala == "concluído"
