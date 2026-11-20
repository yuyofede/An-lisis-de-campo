"""Pruebas del módulo de análisis estadístico."""

import numpy as np
import pandas as pd
import pytest

from muestreo import analisis as A


@pytest.fixture()
def base() -> pd.DataFrame:
    rng = np.random.default_rng(7)
    n = 120
    x1 = rng.normal(10, 2, size=n)
    x2 = rng.normal(5, 1, size=n)
    grupo = np.repeat(["A", "B", "C"], n // 3)
    y = 2.0 + 3.0 * x1 - 1.5 * x2 + rng.normal(0, 0.5, size=n)
    return pd.DataFrame(
        {
            "x1": x1,
            "x2": x2,
            "y": y,
            "grupo": grupo,
            "etiqueta": [f"id-{i}" for i in range(n)],
        }
    )


def test_estadistica_descriptiva_columnas_y_valores(base):
    tabla = A.estadistica_descriptiva(base, ["x1", "x2"])
    assert list(tabla["columna"]) == ["x1", "x2"]
    fila = tabla.set_index("columna").loc["x1"]
    assert fila["n"] == len(base)
    assert fila["faltantes"] == 0
    assert fila["media"] == pytest.approx(base["x1"].mean())
    assert fila["desviacion"] == pytest.approx(base["x1"].std(ddof=1))
    assert fila["minimo"] <= fila["q1"] <= fila["mediana"] <= fila["q3"]
    assert fila["q3"] <= fila["maximo"]
    assert fila["cv"] > 0


def test_estadistica_descriptiva_ignora_faltantes(base):
    base.loc[0, "x1"] = np.nan
    tabla = A.estadistica_descriptiva(base, ["x1"]).iloc[0]
    assert tabla["n"] == len(base) - 1
    assert tabla["faltantes"] == 1


def test_estadistica_descriptiva_validaciones(base):
    with pytest.raises(ValueError):
        A.estadistica_descriptiva(base, [])
    with pytest.raises(ValueError):
        A.estadistica_descriptiva(base, ["no_existe"])


def test_regresion_lineal_recupera_coeficientes(base):
    res = A.regresion_lineal(base, "y", ["x1", "x2"])
    coef = res.coeficientes.set_index("variable")["coeficiente"]
    assert coef["const"] == pytest.approx(2.0, abs=0.8)
    assert coef["x1"] == pytest.approx(3.0, abs=0.1)
    assert coef["x2"] == pytest.approx(-1.5, abs=0.15)
    assert 0.9 < res.r2 <= 1.0
    assert 0.9 < res.r2_ajustado <= 1.0
    assert res.n == len(base)
    assert res.rmse > 0
    assert res.p_valor < 0.001
    assert "y =" in res.ecuacion
    assert len(res.observado) == len(res.ajustado) == len(res.residuos)


def test_regresion_lineal_admite_predictor_categorico(base):
    res = A.regresion_lineal(base, "y", ["x1", "grupo"])
    assert any("grupo_" in nombre for nombre in res.coeficientes["variable"])
    assert 0.9 < res.r2 <= 1.0


def test_regresion_lineal_validaciones(base):
    with pytest.raises(ValueError):
        A.regresion_lineal(base, "y", ["y"])
    with pytest.raises(ValueError):
        A.regresion_lineal(base, "grupo", ["x1"])
    with pytest.raises(ValueError):
        A.regresion_lineal(base, "y", ["etiqueta"])


def test_anova_una_via_detecta_diferencias():
    df = pd.DataFrame(
        {
            "valor": [1, 2, 3, 10, 11, 12, 20, 21, 22],
            "grupo": ["A"] * 3 + ["B"] * 3 + ["C"] * 3,
        }
    )
    res = A.anova_una_via(df, "valor", "grupo")
    assert res.grupos == 3
    assert res.n == 9
    assert res.estadistico_f > 1
    assert res.p_valor < 0.05
    assert 0 < res.eta2 <= 1
    assert res.significativo is True
    assert set(res.tabla["fuente"]) == {"entre", "dentro", "total"}
    assert len(res.medias) == 3
    assert res.medias.set_index("grupo").loc["A", "media"] == pytest.approx(2.0)


def test_anova_una_via_sin_diferencias():
    df = pd.DataFrame(
        {
            "valor": [1, 2, 3, 1, 2, 3, 1, 2, 3],
            "grupo": ["A"] * 3 + ["B"] * 3 + ["C"] * 3,
        }
    )
    res = A.anova_una_via(df, "valor", "grupo")
    assert res.estadistico_f == pytest.approx(0.0, abs=1e-9)
    assert res.significativo is False


def test_anova_una_via_validaciones(base):
    with pytest.raises(ValueError):
        A.anova_una_via(base, "grupo", "grupo")
    with pytest.raises(ValueError):
        A.anova_una_via(base, "y", "no_existe")
    with pytest.raises(ValueError):
        A.anova_una_via(base, "y", "etiqueta")  # un grupo por fila


def test_variables_analizables_omite_identificadores(base):
    base = base.copy()
    base.insert(0, "id_marco", range(1, len(base) + 1))
    clasificacion = A.variables_analizables(base)
    assert "x1" in clasificacion["numericas"]
    assert "y" in clasificacion["numericas"]
    assert "grupo" in clasificacion["categoricas"]
    assert "etiqueta" not in clasificacion["numericas"]
    assert "etiqueta" not in clasificacion["categoricas"]
    assert "id_marco" not in clasificacion["numericas"]
