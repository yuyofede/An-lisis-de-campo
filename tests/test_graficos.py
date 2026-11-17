"""Pruebas de los gráficos y tablas comparativas."""

import pandas as pd
import plotly.graph_objects as go
import pytest

from muestreo import datos as D
from muestreo import graficos as G
from muestreo import muestreo as M


@pytest.fixture(scope="module")
def escenario():
    marco = D.preparar_exportacion(D.generar_datos_ejemplo(n=300, semilla=3))
    muestra = M.aleatorio_simple(marco, 60, semilla=2).datos
    return marco, muestra


def test_grafico_distribucion_numerica(escenario):
    marco, muestra = escenario
    fig = G.grafico_distribucion(marco, muestra, "edad")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2


def test_grafico_distribucion_categorica(escenario):
    marco, muestra = escenario
    fig = G.grafico_distribucion(marco, muestra, "region")
    assert isinstance(fig, go.Figure)
    assert fig.layout.barmode == "group"


def test_grafico_grupos(escenario):
    marco, muestra = escenario
    fig = G.grafico_grupos(marco, muestra, "sucursal")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2


def test_grafico_afijacion():
    tabla = pd.DataFrame(
        {"estrato": ["A", "B"], "N_h": [100, 200], "n_h": [10, 20]}
    )
    fig = G.grafico_afijacion(tabla)
    assert isinstance(fig, go.Figure)


def test_grafico_margen_error():
    fig = G.grafico_margen_error(384, 250, poblacion=10_000, confianza=0.95)
    assert isinstance(fig, go.Figure)
    # Curva + dos puntos (planeada y real)
    assert len(fig.data) == 3
    assert fig.data[1].x[0] == 384
    assert fig.data[2].x[0] == 250


def test_tabla_comparacion_numerica(escenario):
    marco, muestra = escenario
    tabla = G.tabla_comparacion(marco, muestra, "ingreso_mensual")
    assert "Indicador" in tabla.columns
    assert "Población" in tabla.columns
    assert "Muestra" in tabla.columns
    assert "Media" in tabla["Indicador"].tolist()


def test_tabla_comparacion_categorica(escenario):
    marco, muestra = escenario
    tabla = G.tabla_comparacion(marco, muestra, "region")
    assert "Categoría" in tabla.columns
    assert "% Población" in tabla.columns
    assert "% Muestra" in tabla.columns
    assert len(tabla) == marco["region"].nunique()
