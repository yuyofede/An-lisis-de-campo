"""Prueba de humo de la interfaz Streamlit (sin navegador)."""

import pytest

pytest.importorskip("streamlit")

from streamlit.testing.v1 import AppTest  # noqa: E402


def _boton(at: AppTest, etiqueta: str):
    for boton in at.button:
        if boton.label == etiqueta:
            return boton
    raise AssertionError(f"No se encontró el botón '{etiqueta}'")


def test_flujo_completo_con_datos_de_ejemplo():
    at = AppTest.from_file("app.py", default_timeout=90)
    at.run()
    assert not at.exception, at.exception

    # 1. Cargar la base sintética.
    _boton(at, "Cargar datos de ejemplo").click().run()
    assert not at.exception, at.exception
    assert at.session_state["df"] is not None
    assert len(at.session_state["df"]) == 3000

    # 2. Seleccionar la muestra con el n calculado por el diseño por defecto.
    _boton(at, "Seleccionar muestra").click().run()
    assert not at.exception, at.exception

    resultado = at.session_state["resultado"]
    diseno = at.session_state["diseno"]
    assert resultado is not None
    assert diseno is not None
    assert resultado.tamano_muestra == diseno["n"]
    assert resultado.datos["id_marco"].is_unique

    # 3. Volver a ejecutar sin errores (la pestaña de descarga se renderiza).
    at.run()
    assert not at.exception, at.exception


def test_calculo_inverso_refleja_menor_muestra():
    at = AppTest.from_file("app.py", default_timeout=90)
    at.run()
    assert not at.exception, at.exception

    def errores() -> dict:
        salida = {}
        for metrica in at.metric:
            if metrica.label in ("Error planeado", "Error real"):
                texto = (
                    str(metrica.value)
                    .replace("±", "")
                    .replace(" %", "")
                    .replace(".", "")
                    .replace(",", ".")
                )
                salida[metrica.label] = float(texto)
        return salida

    antes = errores()
    # La muestra real es la mitad de la planeada: el margen debe subir.
    real = next(w for w in at.number_input if w.label.startswith("Muestra realmente"))
    plan = next(w for w in at.number_input if w.label.startswith("Muestra planeada"))
    real.set_value(max(1, int(plan.value) // 2)).run()
    assert not at.exception, at.exception

    despues = errores()
    assert despues["Error real"] > antes["Error real"]
    assert despues["Error real"] > despues["Error planeado"]
    assert any("Faltan" in w.value for w in at.warning)


@pytest.mark.parametrize(
    "metodo",
    ["Sistemático", "Estratificado", "Por conglomerados"],
)
def test_metodos_de_seleccion_en_la_interfaz(metodo):
    at = AppTest.from_file("app.py", default_timeout=90)
    at.run()
    assert not at.exception, at.exception

    _boton(at, "Cargar datos de ejemplo").click().run()
    selector = next(s for s in at.selectbox if s.label == "Método de muestreo")
    selector.set_value(metodo).run()
    assert not at.exception, at.exception

    _boton(at, "Seleccionar muestra").click().run()
    assert not at.exception, at.exception

    resultado = at.session_state["resultado"]
    assert resultado.metodo == metodo
    assert resultado.tamano_muestra == len(resultado.datos)
    assert resultado.tamano_muestra > 0
    assert resultado.datos["id_marco"].is_unique


def test_n_de_seleccion_sigue_al_diseno():
    at = AppTest.from_file("app.py", default_timeout=90)
    at.run()
    _boton(at, "Cargar datos de ejemplo").click().run()
    assert not at.exception, at.exception

    n_inicial = at.session_state["n_seleccion"]
    assert n_inicial == at.session_state["diseno"]["n"]

    poblacion = next(
        w for w in at.number_input if w.label == "Tamaño de la población (N)"
    )
    poblacion.set_value(50_000).run()
    assert not at.exception, at.exception

    assert at.session_state["n_seleccion"] == at.session_state["diseno"]["n"]
    assert at.session_state["n_seleccion"] != n_inicial


def test_cambio_de_idioma_es_en_no():
    at = AppTest.from_file("app.py", default_timeout=90)
    at.run()
    assert not at.exception, at.exception

    selector = next(s for s in at.selectbox if s.label == "Idioma")
    selector.set_value("en").run()
    assert not at.exception, at.exception
    texto_app = " ".join(m.value for m in at.markdown)
    assert any(
        "Sample size and statistical sampling design" in m.value for m in at.markdown
    )

    selector = next(s for s in at.selectbox if s.label == "Idioma")
    selector.set_value("no").run()
    assert not at.exception, at.exception
    texto_app = " ".join(m.value for m in at.markdown)
    assert any(
        "Størrelsesdesign og statistisk utvelsning" in m.value for m in at.markdown
    )


