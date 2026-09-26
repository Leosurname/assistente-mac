"""O fluxo inteiro, do atalho ate a caixa sumindo.

Sem janela, sem microfone e sem backend no ar: a caixa, o microfone e o
executor entram como dublês, e o relogio e uma variavel.
"""

from __future__ import annotations

from typing import Any

from assistente_app.coordenador import MENSAGEM_DE_FALHA, Coordenador
from assistente_app.dispensa import Estado


class CaixaFalsa:
    def __init__(self) -> None:
        self.visivel = False
        self.texto = ""
        self.pensando = False
        self.historico: list[str] = []

    def mostrar(self) -> None:
        self.visivel = True

    def ocultar(self) -> None:
        self.visivel = False

    def escrever(self, texto: str) -> None:
        self.texto = texto
        self.historico.append(texto)

    def marcar_pensando(self, pensando: bool) -> None:
        self.pensando = pensando


class MicrofoneFalso:
    def __init__(self) -> None:
        self.ouvindo = False

    def ouvir(self) -> None:
        self.ouvindo = True

    def parar(self) -> None:
        self.ouvindo = False


class ExecutorFalso:
    def __init__(self, falhas: list[str] | None = None) -> None:
        self.executadas: list[Any] = []
        self.falhas = falhas or []

    def executar(self, acoes) -> list[str]:  # noqa: ANN001
        self.executadas.extend(acoes)
        return list(self.falhas)


class ExecutorQueQuebra:
    def executar(self, acoes) -> list[str]:  # noqa: ANN001, ARG002
        raise RuntimeError("a API de acessibilidade recusou")


class Relogio:
    def __init__(self) -> None:
        self.agora = 0.0

    def __call__(self) -> float:
        return self.agora


def montar(executor=None, falhas=None):  # noqa: ANN001
    caixa = CaixaFalsa()
    microfone = MicrofoneFalso()
    relogio = Relogio()
    enviados: list[dict] = []

    coordenador = Coordenador(
        caixa=caixa,
        microfone=microfone,
        executor=executor or ExecutorFalso(falhas),
        retrato=lambda: {"monitores": [{"largura": 1000, "altura": 600}]},
        enviar=enviados.append,
        relogio=relogio,
        espera=5.0,
    )
    return coordenador, caixa, microfone, relogio, enviados


RESPOSTA = {
    "tipo": "acoes",
    "acoes": [
        {"acao": "abrir_app", "app": "Terminal"},
        {"acao": "posicionar", "app": "Safari", "regiao": "metade_direita"},
    ],
    "fala": "concluído",
    "sessao": "s1",
}


def test_atalho_mostra_a_caixa_e_liga_o_microfone():
    coordenador, caixa, microfone, _, _ = montar()

    coordenador.ao_atalho()

    assert caixa.visivel
    assert microfone.ouvindo
    assert coordenador.estado is Estado.ESCUTANDO


def test_transcricao_parcial_aparece_na_caixa_sem_enviar_nada():
    coordenador, caixa, _, _, enviados = montar()
    coordenador.ao_atalho()

    coordenador.ao_transcrever("quero terminal e", final=False)

    assert caixa.texto == "quero terminal e"
    assert enviados == []


def test_fim_da_fala_manda_o_pedido_com_o_retrato_da_tela():
    coordenador, _, _, _, enviados = montar()
    coordenador.ao_atalho()

    coordenador.ao_transcrever("quero terminal e safari", final=True)

    assert len(enviados) == 1
    assert enviados[0]["tipo"] == "pedido"
    assert enviados[0]["texto"] == "quero terminal e safari"
    assert enviados[0]["tela"]["monitores"][0]["largura"] == 1000
    assert coordenador.estado is Estado.PENSANDO


def test_fluxo_completo_ate_a_caixa_sumir():
    coordenador, caixa, microfone, relogio, _ = montar()
    executor = ExecutorFalso()
    coordenador.executor = executor

    coordenador.ao_atalho()
    coordenador.ao_transcrever("quero terminal e safari", final=True)
    coordenador.ao_responder(RESPOSTA)

    assert [a.app for a in executor.executadas] == ["Terminal", "Safari"]
    assert caixa.texto == "concluído"
    assert coordenador.estado is Estado.AGUARDANDO

    relogio.agora = 4.9
    coordenador.ao_tique()
    assert caixa.visivel

    relogio.agora = 5.0
    coordenador.ao_tique()
    assert not caixa.visivel
    assert not microfone.ouvindo


def test_silencio_depois_da_fala_manda_o_pedido():
    coordenador, _, _, relogio, enviados = montar()
    coordenador.ao_atalho()
    coordenador.ao_transcrever("coloca o safari na direita", final=False)

    relogio.agora = 1.1
    coordenador.ao_tique()
    assert enviados == []

    relogio.agora = 1.2
    coordenador.ao_tique()
    assert [e["texto"] for e in enviados] == ["coloca o safari na direita"]
    assert coordenador.estado is Estado.PENSANDO


def test_falar_de_novo_reinicia_a_contagem_do_silencio():
    coordenador, _, _, relogio, enviados = montar()
    coordenador.ao_atalho()
    coordenador.ao_transcrever("coloca o safari", final=False)

    relogio.agora = 1.0
    coordenador.ao_transcrever("coloca o safari na direita", final=False)
    relogio.agora = 2.0
    coordenador.ao_tique()

    assert enviados == []


def test_fala_enquanto_a_layla_pensa_nao_vira_outro_pedido():
    coordenador, caixa, _, relogio, enviados = montar()
    coordenador.ao_atalho()
    coordenador.ao_transcrever("coloca o safari na direita", final=True)

    coordenador.ao_transcrever("e o terminal", final=True)
    relogio.agora = 5.0
    coordenador.ao_tique()

    assert len(enviados) == 1
    assert caixa.texto == "coloca o safari na direita"

def test_digitar_faz_sumir_e_encerra_a_sessao():
    coordenador, caixa, _, _, enviados = montar()
    coordenador.ao_atalho()
    coordenador.ao_transcrever("quero terminal", final=True)
    coordenador.ao_responder(RESPOSTA)

    coordenador.ao_digitar()

    assert not caixa.visivel
    assert enviados[-1] == {"tipo": "encerrar", "sessao": "s1"}
    assert coordenador.sessao is None


def test_esc_faz_sumir():
    coordenador, caixa, _, _, _ = montar()
    coordenador.ao_atalho()

    coordenador.ao_escape()

    assert not caixa.visivel


def test_pedido_emendado_reusa_a_sessao():
    coordenador, _, _, _, enviados = montar()
    coordenador.ao_atalho()
    coordenador.ao_transcrever("quero terminal e safari", final=True)
    coordenador.ao_responder(RESPOSTA)

    coordenador.ao_atalho()
    coordenador.ao_transcrever("agora joga o safari pra direita", final=True)

    assert enviados[-1]["sessao"] == "s1"


def test_microfone_desliga_ao_mandar_e_nao_ouve_o_concluido_da_caixa():
    coordenador, _, microfone, _, enviados = montar()
    coordenador.ao_atalho()
    coordenador.ao_transcrever("abre o terminal", final=True)

    assert not microfone.ouvindo
    coordenador.ao_responder(RESPOSTA)
    assert not microfone.ouvindo
    assert len(enviados) == 1


def test_erro_do_backend_aparece_na_caixa():
    coordenador, caixa, _, _, _ = montar()
    coordenador.ao_atalho()
    coordenador.ao_transcrever("abre o claude code", final=True)

    coordenador.ao_responder({"tipo": "erro", "mensagem": "não achei o Claude Code"})

    assert caixa.texto == "não achei o Claude Code"
    assert coordenador.estado is Estado.AGUARDANDO


def test_resposta_fora_do_contrato_nao_derruba_a_caixa():
    coordenador, caixa, _, _, _ = montar()
    coordenador.ao_atalho()
    coordenador.ao_transcrever("abre o safari", final=True)

    coordenador.ao_responder({"tipo": "acoes", "acoes": [{"acao": "rodar_shell"}]})

    assert caixa.texto == MENSAGEM_DE_FALHA
    assert coordenador.estado is Estado.AGUARDANDO


def test_backend_fora_do_ar_avisa_o_usuario():
    coordenador, caixa, _, _, _ = montar()
    coordenador.ao_atalho()

    coordenador.ao_falhar(ConnectionRefusedError())

    assert caixa.texto == MENSAGEM_DE_FALHA


def test_falha_ao_mexer_nas_janelas_vira_mensagem():
    coordenador, caixa, _, _, _ = montar(falhas=["o Claude Code não está aberto"])
    coordenador.ao_atalho()
    coordenador.ao_transcrever("foca o claude code", final=True)

    coordenador.ao_responder(RESPOSTA)

    assert caixa.texto == "o Claude Code não está aberto"


def test_executor_que_quebra_nao_derruba_o_aplicativo():
    coordenador, caixa, _, _, _ = montar(executor=ExecutorQueQuebra())
    coordenador.ao_atalho()
    coordenador.ao_transcrever("abre o safari", final=True)

    coordenador.ao_responder(RESPOSTA)

    assert caixa.texto == "não consegui mexer nas janelas"
    assert coordenador.estado is Estado.AGUARDANDO


def test_resposta_atrasada_depois_de_sumir_e_ignorada():
    # O usuario ja voltou ao trabalho. Mexer nas janelas agora seria pior que
    # nao fazer nada.
    coordenador, caixa, _, _, _ = montar()
    executor = ExecutorFalso()
    coordenador.executor = executor
    coordenador.ao_atalho()
    coordenador.ao_transcrever("quero terminal", final=True)
    coordenador.ao_digitar()

    coordenador.ao_responder(RESPOSTA)

    assert executor.executadas == []
    assert not caixa.visivel


def test_transcricao_com_a_caixa_oculta_e_ignorada():
    coordenador, caixa, _, _, enviados = montar()

    coordenador.ao_transcrever("oi", final=True)

    assert enviados == []
    assert not caixa.visivel
