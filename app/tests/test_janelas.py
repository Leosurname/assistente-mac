# O executor com o macOS de mentira: nenhuma janela de verdade se mexe.

from __future__ import annotations

from types import SimpleNamespace

import pytest

pytest.importorskip("AppKit")

from assistente_app import janelas  # noqa: E402
from assistente_app.protocolo import Acao  # noqa: E402
from assistente_app.regioes import AreaUtil  # noqa: E402


class AppFalso:
    def __init__(self, nome: str, mac: MacFalso) -> None:
        self.nome = nome
        self._mac = mac

    def activateWithOptions_(self, _: int) -> None:  # noqa: N802
        self._mac.feito.append(("focar", self.nome))

    def terminate(self) -> None:
        self._mac.feito.append(("fechar", self.nome))


class MacFalso:
    def __init__(self, abertos=(), instalados=(), com_janela=()) -> None:
        self.abertos = set(abertos)
        self.instalados = set(abertos) | set(instalados)
        self.com_janela = set(com_janela)
        self.feito: list[tuple] = []

    def rodando(self, nome: str):
        return AppFalso(nome, self) if (nome in self.abertos) else None

    def caminho(self, nome: str):
        return f"/Applications/{nome}.app" if (nome in self.instalados) else None

    def primeira_janela(self, nome: str, esperar: bool = False):
        return f"janela de {nome}" if (nome in self.com_janela) else None

    def mudar(self, janela: str, atributo: str, valor) -> None:
        self.feito.append((atributo, janela.removeprefix("janela de "), valor))

    def abrir(self, url, _configuracao, _pronto) -> None:
        self.feito.append(("abrir", url))

    @property
    def apps_tocados(self) -> set[str]:
        return {
            f[1].removeprefix("/Applications/").removesuffix(".app") for f in self.feito
        }


class AreaDeTrabalho:
    def __init__(self, mac: MacFalso) -> None:
        self.openApplicationAtURL_configuration_completionHandler_ = mac.abrir


@pytest.fixture
def mac(monkeypatch: pytest.MonkeyPatch) -> MacFalso:
    falso = MacFalso(
        abertos={"Safari", "Spotify"},
        instalados={"Terminal"},
        com_janela={"Safari", "Spotify"},
    )
    monkeypatch.setattr(janelas, "rodando", falso.rodando)
    monkeypatch.setattr(janelas, "caminho_do_aplicativo", falso.caminho)
    monkeypatch.setattr(janelas, "primeira_janela", falso.primeira_janela)
    monkeypatch.setattr(janelas, "AXUIElementSetAttributeValue", falso.mudar)
    monkeypatch.setattr(janelas, "AXValueCreate", lambda _tipo, valor: valor)
    area = SimpleNamespace(sharedWorkspace=lambda: AreaDeTrabalho(falso))
    monkeypatch.setattr(janelas, "NSWorkspace", area)
    monkeypatch.setattr(janelas, "NSURL", SimpleNamespace(fileURLWithPath_=str))
    monkeypatch.setattr(
        janelas.contexto,
        "area_util",
        lambda: AreaUtil(x=0, y=25, largura=1000, altura=600),
    )
    return falso


def executar(*acoes: Acao) -> list[str]:
    return janelas.ExecutorDeJanelas().executar(acoes)


def test_abrir_app_ja_aberto_so_traz_para_frente(mac: MacFalso):
    assert executar(Acao("abrir_app", "Safari")) == []
    assert mac.feito == [("focar", "Safari")]


def test_abrir_app_fechado_abre_o_pacote_do_disco(mac: MacFalso):
    assert executar(Acao("abrir_app", "Terminal")) == []
    assert mac.feito == [("abrir", "/Applications/Terminal.app")]


def test_abrir_app_que_nao_existe_avisa_e_nao_abre_nada(mac: MacFalso):
    assert executar(Acao("abrir_app", "Photoshop")) == ["não achei o Photoshop"]
    assert mac.feito == []


def test_focar_app_fechado_avisa_que_ele_nao_esta_aberto(mac: MacFalso):
    assert executar(Acao("focar", "Terminal")) == ["o Terminal não está aberto"]


def test_fechar_app_que_ja_esta_fechado_nao_e_falha(mac: MacFalso):
    assert executar(Acao("fechar_app", "Terminal")) == []
    assert mac.feito == []


def test_minimizar_app_sem_janela_avisa(mac: MacFalso):
    falhas = executar(Acao("minimizar", "Terminal"))

    assert falhas == ["o Terminal não tem janela para minimizar"]


def test_posicionar_move_antes_de_redimensionar(mac: MacFalso):
    executar(Acao("posicionar", "Safari", "metade_direita"))

    assert mac.feito == [
        (janelas.kAXPositionAttribute, "Safari", (500.0, 25.0)),
        (janelas.kAXSizeAttribute, "Safari", (500.0, 600.0)),
    ]


def test_regiao_desconhecida_nao_toca_na_janela(mac: MacFalso):
    falhas = executar(Acao("posicionar", "Safari", "diagonal"))

    assert len(falhas) == 1
    assert mac.feito == []


def test_acao_fora_do_catalogo_vira_falha_e_nao_executa(mac: MacFalso):
    assert executar(Acao("apagar_tudo", "Safari")) == ["não sei fazer 'apagar_tudo'"]
    assert mac.feito == []


def test_uma_acao_que_quebra_nao_impede_as_seguintes(
    mac: MacFalso, monkeypatch: pytest.MonkeyPatch
):
    def quebrar(_janela, _atributo, _valor):
        raise RuntimeError("acessibilidade negada")

    monkeypatch.setattr(janelas, "AXUIElementSetAttributeValue", quebrar)

    falhas = executar(
        Acao("posicionar", "Safari", "tela_cheia"), Acao("abrir_app", "Terminal")
    )

    assert len(falhas) == 1
    assert "acessibilidade negada" in falhas[0]
    assert mac.feito == [("abrir", "/Applications/Terminal.app")]


def test_so_mexe_nos_apps_citados_nas_acoes(mac: MacFalso):
    executar(
        Acao("abrir_app", "Terminal"),
        Acao("posicionar", "Safari", "metade_esquerda"),
    )

    assert mac.apps_tocados == {"Terminal", "Safari"}
