"""Lectura, validación y exportación de la base de datos (marco muestral)."""

from __future__ import annotations

import io
import re
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

#: Extensiones aceptadas por la interfaz.
EXTENSIONES_CSV = (".csv", ".txt")
EXTENSIONES_EXCEL = (".xlsx", ".xlsm")

#: Números con coma decimal (1,5 / 1.234,56) para normalizarlos a punto.
_PATRON_DECIMAL_COMA = re.compile(r"^-?\d{1,3}(?:\.\d{3})*,\d+$|^-?\d+,\d+$")


# ---------------------------------------------------------------------------
# Lectura
# ---------------------------------------------------------------------------
def leer_csv(contenido: bytes, nombre: str = "") -> pd.DataFrame:
    """Lee un CSV detectando separador y codificación de forma tolerante.

    Se intenta primero UTF-8 y luego Latin-1 (habitual en exportaciones de
    Excel en español), y se autodetecta el separador (`,` `;` tabulador...).
    Los decimales con coma se convierten automáticamente.
    """
    errores = []
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            df = pd.read_csv(
                io.BytesIO(contenido),
                sep=None,
                engine="python",
                encoding=encoding,
            )
            return _normalizar_decimales_coma(df)
        except Exception as exc:  # noqa: BLE001 - se reintenta con otra codificación
            errores.append(f"{encoding}: {exc}")
    raise ValueError(
        "No se pudo leer el archivo CSV. Verifique que sea un archivo tabular "
        "válido.\n" + "\n".join(errores)
    )


def _normalizar_decimales_coma(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte columnas de texto con coma decimal a numéricas.

    Solo actúa cuando más del 90 % de los valores no nulos de una columna
    siguen el patrón ``1,5`` / ``1.234,56``; así no se dañan textos legítimos.
    """
    df = df.copy()
    for col in df.columns:
        serie = df[col]
        if serie.dtype != object:
            continue
        valores = serie.dropna().astype(str).str.strip()
        if valores.empty:
            continue
        proporcion = valores.str.match(_PATRON_DECIMAL_COMA).mean()
        if proporcion > 0.9:
            limpio = (
                valores.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
            )
            convertido = pd.to_numeric(limpio, errors="coerce")
            if convertido.notna().all():
                df[col] = pd.to_numeric(
                    serie.astype(str)
                    .str.replace(".", "", regex=False)
                    .str.replace(",", ".", regex=False),
                    errors="coerce",
                )
    return df


def leer_excel(contenido: bytes) -> pd.DataFrame:
    """Lee la primera hoja de un archivo Excel (.xlsx)."""
    try:
        return pd.read_excel(io.BytesIO(contenido), engine="openpyxl")
    except Exception as exc:  # noqa: BLE001
        raise ValueError(
            "No se pudo leer el archivo Excel. Asegúrese de que sea un .xlsx "
            "válido y que la primera hoja contenga los datos."
        ) from exc


def leer_archivo(
    contenido: bytes, nombre: str
) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """Lee un CSV o Excel y devuelve ``(dataframe, metadatos)``."""
    nombre_min = nombre.lower()
    if nombre_min.endswith(EXTENSIONES_EXCEL):
        df = leer_excel(contenido)
        formato = "Excel"
    elif nombre_min.endswith(EXTENSIONES_CSV):
        df = leer_csv(contenido, nombre)
        formato = "CSV"
    else:
        raise ValueError("Formato no soportado. Cargue un archivo .csv o .xlsx.")

    df = limpiar_dataframe(df)
    if df.empty:
        raise ValueError("El archivo no contiene registros legibles.")

    metadatos = {
        "nombre": nombre,
        "formato": formato,
        "filas": int(df.shape[0]),
        "columnas": int(df.shape[1]),
    }
    return df, metadatos


def limpiar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nombres de columnas y elimina filas/columnas vacías.

    No altera los valores: solo recorta espacios en los encabezados y descarta
    columnas ``Unnamed`` sin datos (típicas de exportaciones de Excel).
    """
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(axis=1, how="all")
    df = df.loc[:, [c for c in df.columns if not c.lower().startswith("unnamed")]]
    df = df.dropna(axis=0, how="all")
    df = df.reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# Datos de demostración
# ---------------------------------------------------------------------------
def generar_datos_ejemplo(n: int = 3000, semilla: int = 2024) -> pd.DataFrame:
    """Genera una base sintética realista para probar la aplicación.

    Incluye variables numéricas (edad, ingreso) y categóricas (región,
    sucursal, género, canal) con tamaños de conglomerado desiguales, para que
    los cuatro métodos de muestreo tengan sentido.
    """
    rng = np.random.default_rng(semilla)

    regiones = np.array(["Metropolitana", "Norte", "Centro", "Sur", "Litoral"])
    prob_region = np.array([0.38, 0.18, 0.20, 0.14, 0.10])

    sucursales = {
        "Metropolitana": ["Sucursal Centro", "Sucursal Palermo", "Sucursal Belgrano"],
        "Norte": ["Sucursal Tucumán", "Sucursal Salta"],
        "Centro": ["Sucursal Córdoba", "Sucursal Rosario"],
        "Sur": ["Sucursal Neuquén", "Sucursal Bariloche"],
        "Litoral": ["Sucursal Santa Fe", "Sucursal Paraná"],
    }
    region = rng.choice(regiones, size=n, p=prob_region)
    sucursal = np.array(
        [rng.choice(sucursales[r], p=None) if len(sucursales[r]) else "" for r in region],
        dtype=object,
    )

    genero = rng.choice(
        ["Femenino", "Masculino", "No binario / prefiero no decir"],
        size=n,
        p=[0.51, 0.46, 0.03],
    )

    # Edad correlacionada con la región (leve) y truncada a 18-85.
    edad_base = rng.normal(40, 13, size=n)
    edad = np.clip(np.round(edad_base + (region == "Sur") * 4), 18, 85).astype(int)

    ingreso = np.round(
        np.exp(rng.normal(12.35, 0.45, size=n)) * (1 + 0.006 * (edad - 40)), -2
    )
    ingreso = np.clip(ingreso, 80_000, 6_000_000)

    canal = rng.choice(
        ["Presencial", "Web", "App móvil", "Teléfono"],
        size=n,
        p=[0.34, 0.33, 0.25, 0.08],
    )

    satisfaccion = np.clip(
        np.round(
            7.1
            + 0.03 * (edad - 40)
            - 0.5 * (canal == "Teléfono")
            + rng.normal(0, 1.2, size=n),
            0,
        ),
        1,
        10,
    ).astype(int)

    compra = rng.choice([0, 1], size=n, p=[0.32, 0.68])

    return pd.DataFrame(
        {
            "id_cliente": [f"CL-{i:05d}" for i in range(1, n + 1)],
            "region": region,
            "sucursal": sucursal,
            "genero": genero,
            "edad": edad,
            "ingreso_mensual": ingreso.astype(int),
            "canal_compra": canal,
            "satisfaccion": satisfaccion,
            "compro_ultimo_mes": compra,
        }
    )


# ---------------------------------------------------------------------------
# Detección de variables
# ---------------------------------------------------------------------------
def es_numerica(serie: pd.Series) -> bool:
    return bool(pd.api.types.is_numeric_dtype(serie))


def columnas_numericas(df: pd.DataFrame) -> list:
    return [c for c in df.columns if es_numerica(df[c])]


def columnas_categoricas(df: pd.DataFrame, max_unicos: int = 100) -> list:
    """Columnas aptas para estratificar o conglomerar.

    Se aceptan variables de texto, booleanas, fechas y numéricas discretas con
    pocos valores únicos (p. ej. edad agrupada, código de sucursal).
    """
    resultado = []
    for col in df.columns:
        serie = df[col]
        n_unicos = int(serie.nunique(dropna=True))
        if n_unicos < 2 or n_unicos > max_unicos:
            continue
        # Un texto con un valor distinto por fila es un identificador, no un grupo.
        if serie.dtype == object and n_unicos == int(serie.notna().sum()):
            continue
        resultado.append(col)
    return resultado


def perfil_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Tabla descriptiva de las columnas: tipo, únicos y faltantes."""
    filas = []
    for col in df.columns:
        serie = df[col]
        faltantes = int(serie.isna().sum())
        filas.append(
            {
                "columna": col,
                "tipo": str(serie.dtype),
                "no_nulos": int(serie.notna().sum()),
                "faltantes": faltantes,
                "% faltantes": round(100 * faltantes / len(df), 2) if len(df) else 0.0,
                "valores_unicos": int(serie.nunique(dropna=True)),
            }
        )
    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# Exportación
# ---------------------------------------------------------------------------
def a_csv_bytes(df: pd.DataFrame) -> bytes:
    """CSV UTF-8 con BOM (se abre correctamente en Excel en español)."""
    return df.to_csv(index=False).encode("utf-8-sig")


def a_excel_bytes(
    hojas: Dict[str, pd.DataFrame],
    resumen: Optional[pd.DataFrame] = None,
) -> bytes:
    """Construye un .xlsx con varias hojas.

    Parameters
    ----------
    hojas:
        Diccionario ``nombre_hoja -> dataframe``.
    resumen:
        Si se entrega, se agrega como primera hoja "Resumen".
    """
    salida = io.BytesIO()
    with pd.ExcelWriter(salida, engine="openpyxl") as writer:
        if resumen is not None and not resumen.empty:
            resumen.to_excel(writer, sheet_name="Resumen", index=False)
        for nombre, df in hojas.items():
            # Excel limita los nombres de hoja a 31 caracteres.
            hoja = str(nombre)[:31]
            df.to_excel(writer, sheet_name=hoja, index=False)
            hoja_ws = writer.sheets[hoja]
            # Ancho de columnas razonable para lectura humana.
            for idx, col in enumerate(df.columns, start=1):
                ancho = max(
                    len(str(col)),
                    int(df[col].astype(str).str.len().quantile(0.9)) if len(df) else 0,
                )
                hoja_ws.column_dimensions[
                    hoja_ws.cell(row=1, column=idx).column_letter
                ].width = min(max(ancho + 2, 10), 45)
    salida.seek(0)
    return salida.getvalue()


def resumen_exportacion(
    parametros: Dict[str, object],
    resultado_resumen: Dict[str, object],
) -> pd.DataFrame:
    """Hoja "Resumen" con los parámetros del diseño y del sorteo."""
    filas = []
    filas.append(("PARÁMETROS DEL DISEÑO", ""))
    for clave, valor in parametros.items():
        filas.append((clave, valor))
    filas.append(("", ""))
    filas.append(("SELECCIÓN DE LA MUESTRA", ""))
    for clave, valor in resultado_resumen.items():
        if isinstance(valor, (list, tuple)):
            # Evita celdas gigantes (Excel limita a 32.767 caracteres por celda).
            valores = [str(v) for v in valor]
            if len(valores) > 40:
                valor = ", ".join(valores[:40]) + f" … ({len(valores)} en total)"
            else:
                valor = ", ".join(valores)
        filas.append((clave, valor))
    return pd.DataFrame(filas, columns=["Concepto", "Valor"])


def preparar_exportacion(df: pd.DataFrame, columna_id: str = "id_marco") -> pd.DataFrame:
    """Agrega un identificador de fila del marco si no existe.

    Permite auditar qué registros entraron a la muestra sin depender del
    índice de pandas.
    """
    salida = df.copy()
    if columna_id not in salida.columns:
        salida.insert(0, columna_id, np.arange(1, len(salida) + 1))
    return salida
