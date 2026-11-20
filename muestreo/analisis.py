"""Análisis estadístico de los datos del estudio.

Este módulo concentra la lógica de análisis (sin Streamlit) para que la
interfaz solo se encargue de seleccionar variables y presentar resultados:

* Estadística descriptiva de variables numéricas (pandas).
* Regresión lineal múltiple con errores estándar, t, p e intervalos de
  confianza (statsmodels).
* ANOVA de un factor con tabla completa y tamaño del efecto (SciPy y
  statsmodels/pandas).

Convenciones
------------
``y`` : variable dependiente o de respuesta (numérica).
``X`` : variables predictoras (numéricas o categóricas; las categóricas se
        codifican con variables ficticias eliminando la primera categoría).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

from .datos import es_numerica

#: Claves canónicas de la tabla descriptiva (la interfaz las traduce).
COLUMNAS_DESCRIPTIVA: List[str] = [
    "columna",
    "n",
    "faltantes",
    "media",
    "desviacion",
    "minimo",
    "q1",
    "mediana",
    "q3",
    "maximo",
    "asimetria",
    "curtosis",
    "cv",
]


# ---------------------------------------------------------------------------
# Validaciones
# ---------------------------------------------------------------------------
def _validar_columnas(df: pd.DataFrame, columnas: Sequence[str]) -> List[str]:
    """Comprueba que las columnas existan y elimina duplicados conservando orden."""
    faltantes = [c for c in columnas if c not in df.columns]
    if faltantes:
        raise ValueError(f"Columnas inexistentes: {', '.join(faltantes)}.")
    vistos: List[str] = []
    for col in columnas:
        if col not in vistos:
            vistos.append(col)
    if not vistos:
        raise ValueError("Debe seleccionar al menos una variable.")
    return vistos


def _columna_numerica(df: pd.DataFrame, columna: str, papel: str) -> pd.Series:
    if columna not in df.columns:
        raise ValueError(f"La columna '{columna}' no existe.")
    if not es_numerica(df[columna]):
        raise ValueError(f"La variable {papel} '{columna}' debe ser numérica.")
    return pd.to_numeric(df[columna], errors="coerce")


# ---------------------------------------------------------------------------
# Estadística descriptiva
# ---------------------------------------------------------------------------
def estadistica_descriptiva(
    df: pd.DataFrame,
    columnas: Optional[Sequence[str]] = None,
) -> pd.DataFrame:
    """Resumen descriptivo de una o varias variables numéricas.

    Devuelve una fila por variable con n válido, faltantes, media, desviación
    estándar muestral, mínimo, cuartiles, mediana, máximo, asimetría,
    curtosis y coeficiente de variación.

    Parameters
    ----------
    df:
        Base de datos.
    columnas:
        Variables numéricas a resumir. Si se omite, se usan todas las
        columnas numéricas de la base.
    """
    if columnas is None:
        columnas = [c for c in df.columns if es_numerica(df[c])]
    columnas = _validar_columnas(df, columnas)

    filas: List[Dict[str, object]] = []
    for col in columnas:
        serie = pd.to_numeric(df[col], errors="coerce")
        validos = serie.dropna()
        n = int(validos.size)
        faltantes = int(serie.isna().sum())

        if n == 0:
            filas.append(
                {
                    "columna": col,
                    "n": 0,
                    "faltantes": faltantes,
                    "media": np.nan,
                    "desviacion": np.nan,
                    "minimo": np.nan,
                    "q1": np.nan,
                    "mediana": np.nan,
                    "q3": np.nan,
                    "maximo": np.nan,
                    "asimetria": np.nan,
                    "curtosis": np.nan,
                    "cv": np.nan,
                }
            )
            continue

        media = float(validos.mean())
        desviacion = float(validos.std(ddof=1)) if n > 1 else 0.0
        q1, mediana, q3 = (float(v) for v in validos.quantile([0.25, 0.5, 0.75]))

        filas.append(
            {
                "columna": col,
                "n": n,
                "faltantes": faltantes,
                "media": media,
                "desviacion": desviacion,
                "minimo": float(validos.min()),
                "q1": q1,
                "mediana": mediana,
                "q3": q3,
                "maximo": float(validos.max()),
                "asimetria": float(validos.skew()) if n > 2 else np.nan,
                "curtosis": float(validos.kurt()) if n > 3 else np.nan,
                "cv": (desviacion / abs(media)) if media != 0 else np.nan,
            }
        )

    return pd.DataFrame(filas, columns=COLUMNAS_DESCRIPTIVA)


# ---------------------------------------------------------------------------
# Regresión lineal múltiple
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ResultadoRegresion:
    """Resultado completo de un ajuste por mínimos cuadrados ordinarios."""

    variable_y: str
    predictores: List[str]
    n: int
    coeficientes: pd.DataFrame
    r2: float
    r2_ajustado: float
    rmse: float
    estadistico_f: float
    p_valor: float
    gl_modelo: int
    gl_residuo: int
    ecuacion: str
    observado: pd.Series
    ajustado: pd.Series
    residuos: pd.Series


def _matriz_diseno(
    datos: pd.DataFrame, predictores: Sequence[str]
) -> pd.DataFrame:
    """Construye la matriz de predictores codificando las categóricas.

    Las variables de texto se transforman en variables ficticias (dummies)
    eliminando la primera categoría para evitar colinealidad perfecta con el
    intercepto.
    """
    partes: List[pd.Series] = []
    for col in predictores:
        serie = datos[col]
        if es_numerica(serie):
            partes.append(pd.to_numeric(serie, errors="coerce").rename(col))
        else:
            dummies = pd.get_dummies(
                serie.astype("category"),
                prefix=col,
                drop_first=True,
                dtype=float,
            )
            partes.extend([dummies[c] for c in dummies.columns])

    if not partes:
        raise ValueError(
            "Los predictores elegidos no aportan variables utilizables. "
            "Seleccione otra combinación."
        )
    return pd.concat(partes, axis=1)


def regresion_lineal(
    df: pd.DataFrame,
    variable_y: str,
    predictores: Sequence[str],
) -> ResultadoRegresion:
    """Ajusta una regresión lineal múltiple por mínimos cuadrados ordinarios.

    Parameters
    ----------
    df:
        Base de datos.
    variable_y:
        Variable dependiente (numérica).
    predictores:
        Variables independientes (numéricas o categóricas).

    Returns
    -------
    ResultadoRegresion
        Coeficientes con error estándar, t, p e intervalo de confianza al
        95 %, bondad de ajuste, ecuación estimada y valores ajustados.
    """
    predictores = _validar_columnas(df, predictores)
    if variable_y in predictores:
        raise ValueError("La variable dependiente no puede ser también predictora.")

    y = _columna_numerica(df, variable_y, "dependiente")
    diseno = _matriz_diseno(df[predictores], predictores)
    datos = pd.concat([y.rename(variable_y), diseno], axis=1).dropna()

    if datos.empty:
        raise ValueError(
            "No quedan observaciones completas para ajustar el modelo. "
            "Revise los valores faltantes."
        )

    y_limpia = datos[variable_y].astype(float)
    x_limpia = datos.drop(columns=[variable_y]).astype(float)
    x_limpia = sm.add_constant(x_limpia, has_constant="add")

    if len(datos) <= x_limpia.shape[1]:
        raise ValueError(
            "Se necesitan más observaciones que parámetros para ajustar el "
            "modelo. Reduzca el número de predictores."
        )

    modelo = sm.OLS(y_limpia, x_limpia).fit()
    intervalos = modelo.conf_int(alpha=0.05)

    coeficientes = pd.DataFrame(
        {
            "variable": modelo.params.index,
            "coeficiente": modelo.params.values,
            "error_estandar": modelo.bse.values,
            "t": modelo.tvalues.values,
            "p_valor": modelo.pvalues.values,
            "ic_inferior": intervalos[0].values,
            "ic_superior": intervalos[1].values,
        }
    )

    terminos = []
    for nombre, coef in modelo.params.items():
        if nombre == "const":
            continue
        signo = "+" if coef >= 0 else "−"
        terminos.append(f"{signo} {abs(float(coef)):.4g}·{nombre}")
    intercepto = float(modelo.params.get("const", 0.0))
    ecuacion = f"{variable_y} = {intercepto:.4g} " + " ".join(terminos)

    ajustado = pd.Series(modelo.fittedvalues, index=datos.index, name="ajustado")
    residuos = pd.Series(modelo.resid, index=datos.index, name="residuo")

    return ResultadoRegresion(
        variable_y=variable_y,
        predictores=list(predictores),
        n=int(modelo.nobs),
        coeficientes=coeficientes,
        r2=float(modelo.rsquared),
        r2_ajustado=float(modelo.rsquared_adj),
        rmse=float(np.sqrt(np.mean(np.square(modelo.resid)))),
        estadistico_f=float(modelo.fvalue),
        p_valor=float(modelo.f_pvalue),
        gl_modelo=int(modelo.df_model),
        gl_residuo=int(modelo.df_resid),
        ecuacion=ecuacion.strip(),
        observado=y_limpia,
        ajustado=ajustado,
        residuos=residuos,
    )


# ---------------------------------------------------------------------------
# ANOVA de un factor
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ResultadoANOVA:
    """Resultado de un ANOVA de un factor entre grupos independientes."""

    variable_y: str
    variable_grupo: str
    n: int
    grupos: int
    tabla: pd.DataFrame
    medias: pd.DataFrame
    estadistico_f: float
    p_valor: float
    eta2: float

    @property
    def significativo(self) -> bool:
        """True si se rechaza la igualdad de medias al 5 %."""
        return bool(self.p_valor < 0.05)


def anova_una_via(
    df: pd.DataFrame,
    variable_y: str,
    variable_grupo: str,
) -> ResultadoANOVA:
    """ANOVA de un factor para comparar medias entre grupos.

    La tabla incluye suma de cuadrados, grados de libertad, media cuadrática,
    estadístico F y p-valor. También se informa η² (tamaño del efecto) y el
    resumen de medias por grupo.
    """
    if variable_y == variable_grupo:
        raise ValueError("La variable respuesta y el factor deben ser distintas.")

    y = _columna_numerica(df, variable_y, "respuesta")
    if variable_grupo not in df.columns:
        raise ValueError(f"La columna '{variable_grupo}' no existe.")

    datos = pd.DataFrame(
        {variable_y: y, variable_grupo: df[variable_grupo]}
    ).dropna()

    if datos.empty:
        raise ValueError("No hay observaciones completas para el ANOVA.")

    grupos = [
        serie[variable_y].astype(float)
        for _, serie in datos.groupby(variable_grupo, observed=True)
        if len(serie) > 0
    ]
    k = len(grupos)
    n_total = int(sum(len(g) for g in grupos))

    if k < 2:
        raise ValueError("El factor debe tener al menos dos grupos con datos.")
    if n_total <= k:
        raise ValueError(
            "Se necesitan más observaciones que grupos para estimar la "
            "varianza dentro de los grupos."
        )

    global_ = float(pd.concat(grupos).mean())
    ss_entre = float(sum(len(g) * (g.mean() - global_) ** 2 for g in grupos))
    ss_dentro = float(sum(((g - g.mean()) ** 2).sum() for g in grupos))
    ss_total = ss_entre + ss_dentro
    gl_entre = k - 1
    gl_dentro = n_total - k
    ms_entre = ss_entre / gl_entre if gl_entre else np.nan
    ms_dentro = ss_dentro / gl_dentro if gl_dentro else np.nan
    f_valor = ms_entre / ms_dentro if ms_dentro else np.nan
    p_valor = float(stats.f.sf(f_valor, gl_entre, gl_dentro)) if ms_dentro else np.nan

    tabla = pd.DataFrame(
        [
            {
                "fuente": "entre",
                "suma_cuadrados": ss_entre,
                "gl": gl_entre,
                "media_cuadratica": ms_entre,
                "f": f_valor,
                "p_valor": p_valor,
            },
            {
                "fuente": "dentro",
                "suma_cuadrados": ss_dentro,
                "gl": gl_dentro,
                "media_cuadratica": ms_dentro,
                "f": np.nan,
                "p_valor": np.nan,
            },
            {
                "fuente": "total",
                "suma_cuadrados": ss_total,
                "gl": n_total - 1,
                "media_cuadratica": np.nan,
                "f": np.nan,
                "p_valor": np.nan,
            },
        ]
    )

    medias = (
        datos.groupby(variable_grupo, observed=True)[variable_y]
        .agg(n="count", media="mean", desviacion="std")
        .reset_index()
        .rename(columns={variable_grupo: "grupo"})
    )
    medias["desviacion"] = medias["desviacion"].fillna(0.0)

    eta2 = ss_entre / ss_total if ss_total > 0 else np.nan

    return ResultadoANOVA(
        variable_y=variable_y,
        variable_grupo=variable_grupo,
        n=n_total,
        grupos=k,
        tabla=tabla,
        medias=medias,
        estadistico_f=float(f_valor),
        p_valor=p_valor,
        eta2=float(eta2),
    )


# ---------------------------------------------------------------------------
# Utilidad de presentación
# ---------------------------------------------------------------------------
def variables_analizables(df: pd.DataFrame) -> Dict[str, List[str]]:
    """Clasifica las columnas de la base para poblar los selectores.

    Devuelve ``{"numericas": [...], "categoricas": [...]}`` omitiendo
    identificadores (una fila distinta por registro) y columnas constantes.
    """
    numericas: List[str] = []
    categoricas: List[str] = []

    for col in df.columns:
        serie = df[col]
        n_validos = int(serie.notna().sum())
        n_unicos = int(serie.nunique(dropna=True))
        if n_unicos < 2:
            continue
        nombre = str(col).strip().lower()
        parece_identificador = nombre == "id" or nombre.startswith("id_")
        if (
            n_validos
            and n_unicos == n_validos
            and (serie.dtype == object or parece_identificador)
        ):
            # Identificador: un valor distinto por fila (id_cliente, id_marco...).
            continue
        if es_numerica(serie):
            numericas.append(col)
        elif n_unicos <= 50:
            categoricas.append(col)

    return {"numericas": numericas, "categoricas": categoricas}
