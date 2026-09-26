from __future__ import annotations

from types import SimpleNamespace

from assistente_app.ponte import Ponte


def despachar_na_hora(bloco) -> None:  # noqa: ANN001
    bloco()


def coordenador_falso():
    eventos = []
    return SimpleNamespace(
        eventos=eventos,
        ao_responder=lambda corpo: eventos.append(("responder", corpo)),
        ao_falhar=lambda erro: eventos.append(("falhar", erro)),
        ao_transcrever=lambda texto, final: eventos.append(("ouvir", texto, final)),
    )


def test_antes_do_coordenador_existir_tudo_e_ignorado():
    ponte = Ponte(despachar_na_hora)

    ponte.ao_responder({})
    ponte.ao_falhar(RuntimeError("x"))
    ponte.ao_transcrever("abre", False)


def test_depois_de_ligada_repassa_ao_coordenador():
    ponte = Ponte(despachar_na_hora)
    ponte.coordenador = coordenador_falso()
    erro = RuntimeError("x")

    ponte.ao_responder({"tipo": "ok"})
    ponte.ao_falhar(erro)
    ponte.ao_transcrever("abre o safari", True)

    assert ponte.coordenador.eventos == [
        ("responder", {"tipo": "ok"}),
        ("falhar", erro),
        ("ouvir", "abre o safari", True),
    ]


def test_transcricao_vai_pela_thread_principal():
    fila = []
    ponte = Ponte(fila.append)
    ponte.coordenador = coordenador_falso()

    ponte.ao_transcrever("abre", False)

    assert ponte.coordenador.eventos == []
    fila[0]()
    assert ponte.coordenador.eventos == [("ouvir", "abre", False)]
