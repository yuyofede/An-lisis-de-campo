"""Pruebas de los algoritmos de selección de muestras."""

import numpy as np
import pandas as pd
import pytest

from muestreo import datos as D
from muestreo import muestreo as M


@pytest.fixture(scope="module")
def marco() -> pd.DataFrame:
    df = D.generar_datos_ejemplo(n=500, semilla=7)
    return D.preparar_exportacion(df)


# ---------------------------------------------------------------------------
# Aleatorio simple
# ---------------------------------------------------------------------------
def test_aleatorio_simple_tamano_y_sin_duplicados(marco):
    res = M.aleatorio_simple(marco, 60, semilla=42)
    assert res.tamano_muestra == 60
    assert len(res.datos) == 60
    assert res.datos["id_marco"].is_unique
    assert set(res.datos["id_marco"]).issubset(set(marco["id_marco"]))
    assert res.fraccion_muestral == pytest.approx(60 / len(marco))


def test_aleatorio_simple_reproducible(marco):
    a = M.aleatorio_simple(marco, 50, semilla=123)
    b = M.aleatorio_simple(marco, 50, semilla=123)
    c = M.aleatorio_simple(marco, 50, semilla=124)
    assert a.datos["id_marco"].tolist() == b.datos["id_marco"].tolist()
    assert a.datos["id_marco"].tolist() != c.datos["id_marco"].tolist()


def test_aleatorio_simple_con_reemplazo(marco):
    res = M.aleatorio_simple(marco, len(marco) + 50, semilla=5, reemplazo=True)
    assert len(res.datos) == len(marco) + 50
    assert res.datos["id_marco"].duplicated().any()


def test_aleatorio_simple_valida_n(marco):
    with pytest.raises(ValueError):
        M.aleatorio_simple(marco, len(marco) + 1)
    with pytest.raises(ValueError):
        M.aleatorio_simple(marco, 0)


# ---------------------------------------------------------------------------
# Sistemático
# ---------------------------------------------------------------------------
def test_sistematico_tamano_exacto_y_posiciones(marco):
    res = M.sistematico(marco, 73, semilla=11)
    assert len(res.datos) == 73
    assert res.datos["id_marco"].is_unique
    posiciones = res.detalles["posiciones_marco"]
    assert len(posiciones) == 73
    assert posiciones == sorted(posiciones)
    assert 1 <= min(posiciones) <= len(marco)
    assert max(posiciones) <= len(marco)
    assert res.detalles["intervalo_k"] == pytest.approx(len(marco) / 73)


def test_sistematico_reproducible(marco):
    a = M.sistematico(marco, 40, semilla=99)
    b = M.sistematico(marco, 40, semilla=99)
    assert a.detalles["posiciones_marco"] == b.detalles["posiciones_marco"]


def test_sistematico_con_muestra_igual_a_poblacion(marco):
    res = M.sistematico(marco, len(marco), semilla=1)
    assert res.detalles["posiciones_marco"] == list(range(1, len(marco) + 1))


# ---------------------------------------------------------------------------
# Estratificado
# ---------------------------------------------------------------------------
def test_afijacion_suma_exacta_y_capacidad():
    conteos = pd.Series({"A": 100, "B": 50, "C": 10, "D": 2})
    tabla = M.afijacion_proporcional(conteos, 25, minimo_por_estrato=1)
    assert tabla["n_h"].sum() == 25
    assert (tabla["n_h"] >= 1).all()
    assert (tabla["n_h"] <= tabla["N_h"]).all()
    # Estratos grandes reciben más muestra que los pequeños
    assert tabla.set_index("estrato").loc["A", "n_h"] >= tabla.set_index("estrato").loc["C", "n_h"]


def test_afijacion_minimo_imposible():
    conteos = pd.Series({"A": 1, "B": 1, "C": 1, "D": 1, "E": 1})
    with pytest.raises(ValueError):
        M.afijacion_proporcional(conteos, 3, minimo_por_estrato=1)


def test_estratificado_respeta_cuotas(marco):
    res = M.estratificado(marco, 120, columna="region", semilla=3)
    tabla = res.detalles["afijacion"]
    assert res.tamano_muestra == 120
    assert len(res.datos) == 120
    assert res.datos["id_marco"].is_unique
    assert tabla["n_h"].sum() == 120

    conteo_muestra = res.datos["region"].value_counts()
    for fila in tabla.itertuples(index=False):
        assert conteo_muestra.get(fila.estrato, 0) == fila.n_h


def test_estratificado_reproducible(marco):
    a = M.estratificado(marco, 80, columna="genero", semilla=8)
    b = M.estratificado(marco, 80, columna="genero", semilla=8)
    assert a.datos["id_marco"].tolist() == b.datos["id_marco"].tolist()


def test_estratificado_excluye_faltantes():
    df = pd.DataFrame(
        {"grupo": ["A", "A", "B", None, "B", "C"], "valor": range(6)}
    )
    res = M.estratificado(df, 3, columna="grupo", semilla=1)
    assert res.detalles["filas_excluidas"] == 1
    assert res.datos["grupo"].notna().all()
    assert res.tamano_marco == 5


# ---------------------------------------------------------------------------
# Conglomerados
# ---------------------------------------------------------------------------
def test_conglomerados_incluye_grupos_completos(marco):
    res = M.conglomerados(marco, "sucursal", num_conglomerados=3, semilla=21)
    seleccionados = res.detalles["conglomerados_seleccionados"]
    assert len(seleccionados) == 3
    assert set(res.datos["sucursal"].unique()) == set(seleccionados)
    esperado = marco[marco["sucursal"].isin(seleccionados)]
    assert len(res.datos) == len(esperado)
    assert set(res.datos["id_marco"]) == set(esperado["id_marco"])


def test_conglomerados_reproducible(marco):
    a = M.conglomerados(marco, "region", 2, semilla=77)
    b = M.conglomerados(marco, "region", 2, semilla=77)
    assert (
        a.detalles["conglomerados_seleccionados"]
        == b.detalles["conglomerados_seleccionados"]
    )


def test_conglomerados_valida_numero(marco):
    with pytest.raises(ValueError):
        M.conglomerados(marco, "region", num_conglomerados=0)
    with pytest.raises(ValueError):
        M.conglomerados(marco, "region", num_conglomerados=999)


def test_conglomerados_sugeridos_en_rango(marco):
    sugeridos = M.conglomerados_sugeridos(marco, "sucursal", 100)
    assert 1 <= sugeridos <= marco["sucursal"].nunique()


def test_resumen_sin_dataframes():
    res = M.estratificado(
        D.preparar_exportacion(D.generar_datos_ejemplo(100, semilla=2)),
        20,
        "region",
        semilla=1,
    )
    resumen = res.resumen()
    assert not any(isinstance(v, (pd.DataFrame, pd.Series)) for v in resumen.values())
    assert resumen["tamano_muestra"] == 20
