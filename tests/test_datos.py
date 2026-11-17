"""Pruebas de lectura, limpieza y exportación de datos."""

import io

import pandas as pd
import pytest

from muestreo import datos as D


def test_leer_csv_con_separador_punto_y_coma_y_decimales_coma():
    contenido = (
        "region;edad;ingreso\n"
        "Norte;34,5;1.250,50\n"
        "Sur;28,0;900,00\n"
    ).encode("utf-8")
    df, meta = D.leer_archivo(contenido, "datos.csv")
    assert meta["formato"] == "CSV"
    assert list(df.columns) == ["region", "edad", "ingreso"]
    assert df["edad"].tolist() == [34.5, 28.0]
    assert df["ingreso"].tolist() == [1250.5, 900.0]


def test_leer_csv_con_coma_y_punto_decimal():
    contenido = b"region,edad\nNorte,34.5\nSur,28.0\n"
    df, _ = D.leer_archivo(contenido, "datos.csv")
    assert pd.api.types.is_numeric_dtype(df["edad"])
    assert df["edad"].tolist() == [34.5, 28.0]


def test_leer_csv_latin1():
    contenido = "región;ciudad\nÑuble;Chillán\n".encode("latin-1")
    df, _ = D.leer_archivo(contenido, "datos.csv")
    assert df.loc[0, "región"] == "Ñuble"


def test_limpiar_dataframe():
    df = pd.DataFrame(
        {
            " nombre ": ["Ana", None, "Luis"],
            "Unnamed: 0": [1, 2, 3],
            "vacia": [None, None, None],
            "edad": [30, None, 40],
        }
    )
    limpio = D.limpiar_dataframe(df)
    assert "vacia" not in limpio.columns
    assert "Unnamed: 0" not in limpio.columns
    assert "nombre" in limpio.columns
    assert len(limpio) == 2


def test_preparar_exportacion_agrega_id_y_es_idempotente():
    df = pd.DataFrame({"x": [10, 20, 30]})
    con_id = D.preparar_exportacion(df)
    assert "id_marco" in con_id.columns
    assert con_id["id_marco"].tolist() == [1, 2, 3]
    otra_vez = D.preparar_exportacion(con_id)
    assert otra_vez["id_marco"].tolist() == [1, 2, 3]


def test_exportacion_csv_utf8_con_bom():
    df = pd.DataFrame({"ciudad": ["Córdoba", "Rosario"], "n": [1, 2]})
    contenido = D.a_csv_bytes(df)
    assert contenido.startswith(b"\xef\xbb\xbf")
    leido = pd.read_csv(io.BytesIO(contenido))
    assert leido["ciudad"].tolist() == ["Córdoba", "Rosario"]


def test_exportacion_excel_con_hojas_y_resumen():
    muestra = pd.DataFrame({"id_marco": [1, 2], "region": ["Norte", "Sur"]})
    extra = pd.DataFrame({"Estrato": ["Norte", "Sur"], "n_h": [1, 1]})
    resumen = D.resumen_exportacion({"Confianza": "95 %"}, {"Semilla": 42})
    contenido = D.a_excel_bytes(
        {"Muestra": muestra, "Afijación": extra}, resumen=resumen
    )
    hojas = pd.read_excel(io.BytesIO(contenido), sheet_name=None)
    assert set(hojas) == {"Resumen", "Muestra", "Afijación"}
    assert hojas["Muestra"]["region"].tolist() == ["Norte", "Sur"]
    assert "Concepto" in hojas["Resumen"].columns


def test_resumen_exportacion_no_genera_celdas_gigantes():
    lista = list(range(500))
    resumen = D.resumen_exportacion({}, {"Posiciones": lista})
    valor = resumen.loc[resumen["Concepto"] == "Posiciones", "Valor"].iloc[0]
    assert "500 en total" in valor
    assert len(valor) < 2000


def test_perfil_columnas():
    df = pd.DataFrame(
        {"a": [1, 2, None], "b": ["x", "x", "y"]}
    )
    perfil = D.perfil_columnas(df)
    assert len(perfil) == 2
    fila_a = perfil.set_index("columna").loc["a"]
    assert fila_a["faltantes"] == 1
    assert fila_a["valores_unicos"] == 2


def test_columnas_categoricas_y_numericas():
    df = pd.DataFrame(
        {
            "region": ["A", "B", "A"],
            "edad": [20, 30, 40],
            "id": ["x0", "x1", "x2"],
        }
    )
    assert "region" in D.columnas_categoricas(df)
    assert "edad" in D.columnas_categoricas(df)
    assert "id" not in D.columnas_categoricas(df)
    assert D.columnas_numericas(df) == ["edad"]


def test_formato_no_soportado():
    with pytest.raises(ValueError):
        D.leer_archivo(b"contenido", "archivo.pdf")


def test_datos_ejemplo_tienen_columnas_esperadas():
    df = D.generar_datos_ejemplo(n=200, semilla=1)
    assert len(df) == 200
    assert {"region", "sucursal", "genero", "edad", "canal_compra"} <= set(df.columns)
    assert df["edad"].between(18, 85).all()
    assert df["region"].nunique() == 5
