"""Gráficos de apoyo para el diseño y la validación de la muestra.

Se usa Plotly porque permite interactividad (zoom, tooltips) y se integra de
forma nativa con Streamlit. Todas las funciones devuelven una ``Figure``.
"""

from __future__ import annotations

import math
from typing import Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .datos import es_numerica
from .estadistica import margen_error

COLOR_POBLACION = "#94a3b8"  # gris azulado
COLOR_MUESTRA = "#2563eb"    # azul
COLOR_ACENTO = "#f97316"     # naranja

PLANTILLA = "plotly_white"


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def _etiquetas(serie: pd.Series) -> pd.Series:
    """Convierte valores (incluidos NaN) en etiquetas legibles."""
    return serie.map(lambda v: "(sin dato)" if pd.isna(v) else str(v))


def _layout(fig: go.Figure, titulo: str, alto: int = 380) -> go.Figure:
    fig.update_layout(
        template=PLANTILLA,
        title=dict(text=titulo, x=0.01, xanchor="left", font=dict(size=15)),
        height=alto,
        margin=dict(l=10, r=10, t=55, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1),
    )
    return fig


# ---------------------------------------------------------------------------
# Distribución de una variable: población vs muestra
# ---------------------------------------------------------------------------
def grafico_distribucion(
    poblacion: pd.DataFrame,
    muestra: pd.DataFrame,
    columna: str,
) -> go.Figure:
    """Compara la distribución de ``columna`` en la población y en la muestra.

    * Variables numéricas con muchos valores: histogramas normalizados (%).
    * Variables categóricas o discretas: barras agrupadas de porcentajes.
    """
    if columna not in poblacion.columns:
        raise ValueError(f"La columna '{columna}' no existe en la población.")

    pob = poblacion[columna]
    mus = muestra[columna] if columna in muestra.columns else pd.Series(dtype=pob.dtype)

    if es_numerica(pob) and pob.nunique(dropna=True) > 12:
        return _histograma_comparado(pob, mus, columna)
    return _barras_categoricas(pob, mus, columna)


def _histograma_comparado(
    pob: pd.Series, mus: pd.Series, columna: str
) -> go.Figure:
    datos = pd.concat(
        [
            pd.DataFrame({"valor": pob.dropna(), "conjunto": "Población"}),
            pd.DataFrame({"valor": mus.dropna(), "conjunto": "Muestra"}),
        ],
        ignore_index=True,
    )
    nbins = int(min(50, max(10, round(math.sqrt(max(len(datos), 1))))))
    fig = px.histogram(
        datos,
        x="valor",
        color="conjunto",
        barmode="overlay",
        histnorm="percent",
        nbins=nbins,
        opacity=0.6,
        color_discrete_map={"Población": COLOR_POBLACION, "Muestra": COLOR_MUESTRA},
        labels={"valor": columna, "conjunto": "", "percent": "% de registros"},
    )
    # Líneas de media para lectura rápida del sesgo.
    for serie, color, nombre in (
        (pob.dropna(), COLOR_POBLACION, "Media población"),
        (mus.dropna(), COLOR_MUESTRA, "Media muestra"),
    ):
        if len(serie):
            fig.add_vline(
                x=float(serie.mean()),
                line_dash="dash",
                line_color=color,
                annotation_text=f"{nombre}: {serie.mean():,.1f}",
                annotation_position="top",
            )
    _layout(fig, f"Distribución de «{columna}»: población vs muestra")
    fig.update_yaxes(title="% de registros")
    fig.update_layout(bargap=0.05)
    return fig


def _barras_categoricas(
    pob: pd.Series, mus: pd.Series, columna: str, max_categorias: int = 12
) -> go.Figure:
    pob_et = _etiquetas(pob)
    mus_et = _etiquetas(mus)

    orden = pob_et.value_counts().head(max_categorias).index.tolist()
    tabla = pd.DataFrame(
        {
            "categoria": orden,
            "Población": [100 * (pob_et == c).mean() for c in orden],
            "Muestra": [100 * (mus_et == c).mean() if len(mus_et) else 0.0 for c in orden],
        }
    )
    largo = tabla.melt(
        id_vars="categoria", var_name="conjunto", value_name="porcentaje"
    )
    fig = px.bar(
        largo,
        x="categoria",
        y="porcentaje",
        color="conjunto",
        barmode="group",
        color_discrete_map={"Población": COLOR_POBLACION, "Muestra": COLOR_MUESTRA},
        labels={"categoria": columna, "porcentaje": "% de registros", "conjunto": ""},
        text=largo["porcentaje"].map(lambda v: f"{v:.1f}%"),
    )
    fig.update_traces(textposition="outside", textfont_size=10)
    _layout(fig, f"Composición de «{columna}»: población vs muestra")
    fig.update_yaxes(range=[0, min(105, max(10, largo["porcentaje"].max() * 1.18))])
    if len(orden) > 6:
        fig.update_xaxes(tickangle=-30)
    return fig


# ---------------------------------------------------------------------------
# Comparación por estratos / conglomerados
# ---------------------------------------------------------------------------
def grafico_grupos(
    poblacion: pd.DataFrame,
    muestra: pd.DataFrame,
    columna: str,
    max_grupos: int = 15,
) -> go.Figure:
    """Barras agrupadas con el peso de cada grupo en población y muestra."""
    pob = _etiquetas(poblacion[columna])
    mus = _etiquetas(muestra[columna]) if columna in muestra.columns else pd.Series(dtype=str)

    orden = pob.value_counts().head(max_grupos).index.tolist()
    tabla = pd.DataFrame(
        {
            "grupo": orden,
            "Población": [100 * (pob == g).mean() for g in orden],
            "Muestra": [100 * (mus == g).mean() if len(mus) else 0.0 for g in orden],
        }
    )
    largo = tabla.melt(id_vars="grupo", var_name="conjunto", value_name="porcentaje")
    fig = px.bar(
        largo,
        y="grupo",
        x="porcentaje",
        color="conjunto",
        barmode="group",
        orientation="h",
        color_discrete_map={"Población": COLOR_POBLACION, "Muestra": COLOR_MUESTRA},
        labels={"grupo": columna, "porcentaje": "% de registros", "conjunto": ""},
    )
    fig.update_layout(yaxis=dict(autorange="reversed"))
    _layout(
        fig,
        f"Representatividad por «{columna}»: población vs muestra",
        alto=max(360, 26 * len(orden) + 120),
    )
    return fig


def grafico_afijacion(tabla: pd.DataFrame) -> go.Figure:
    """Barras población vs muestra por estrato (valores absolutos)."""
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=tabla["estrato"],
            y=tabla["N_h"],
            name="Población (N_h)",
            marker_color=COLOR_POBLACION,
        )
    )
    fig.add_trace(
        go.Bar(
            x=tabla["estrato"],
            y=tabla["n_h"],
            name="Muestra (n_h)",
            marker_color=COLOR_MUESTRA,
            text=tabla["n_h"],
            textposition="outside",
        )
    )
    fig.update_layout(barmode="group")
    _layout(fig, "Afijación proporcional por estrato")
    fig.update_xaxes(tickangle=-30)
    return fig


# ---------------------------------------------------------------------------
# Curva de margen de error
# ---------------------------------------------------------------------------
def grafico_margen_error(
    muestra_planeada: int,
    muestra_real: int,
    poblacion: Optional[int] = None,
    confianza: float = 0.95,
    z: Optional[float] = None,
    p: float = 0.5,
    max_muestra: Optional[int] = None,
) -> go.Figure:
    """Curva ``e(n)`` con los puntos de la muestra planeada y la real."""
    if max_muestra is None:
        max_muestra = max(muestra_planeada, muestra_real) * 2
        if poblacion is not None:
            max_muestra = min(max_muestra, poblacion)
    max_muestra = max(int(max_muestra), 2)

    if poblacion is not None:
        n_max = min(max_muestra, poblacion)
        valores = np.unique(
            np.linspace(1, n_max, num=min(250, n_max)).round().astype(int)
        )
    else:
        valores = np.unique(np.linspace(1, max_muestra, num=250).round().astype(int))

    errores = np.array(
        [
            margen_error(int(n), poblacion, confianza=confianza, z=z, p=p) * 100
            for n in valores
        ]
    )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=valores,
            y=errores,
            mode="lines",
            name="Margen de error",
            line=dict(color=COLOR_MUESTRA, width=3),
            hovertemplate="n = %{x:,}<br>error = ±%{y:.2f} %<extra></extra>",
        )
    )

    puntos = [
        (muestra_planeada, "Planeada", COLOR_POBLACION),
        (muestra_real, "Real", COLOR_ACENTO),
    ]
    for n_punto, etiqueta, color in puntos:
        if n_punto < 1:
            continue
        e_punto = margen_error(n_punto, poblacion, confianza=confianza, z=z, p=p) * 100
        fig.add_trace(
            go.Scatter(
                x=[n_punto],
                y=[e_punto],
                mode="markers+text",
                name=f"Muestra {etiqueta.lower()} (n={n_punto:,})",
                marker=dict(size=12, color=color, line=dict(width=1, color="white")),
                text=[f"±{e_punto:.2f} %"],
                textposition="top center",
                hovertemplate=f"{etiqueta}: n = %{{x:,}}<br>error = ±%{{y:.2f}} %<extra></extra>",
            )
        )

    _layout(fig, "Margen de error según el tamaño de muestra")
    fig.update_xaxes(title="Tamaño de muestra (n)")
    fig.update_yaxes(title="Margen de error (± %)", rangemode="tozero")
    return fig


# ---------------------------------------------------------------------------
# Tabla comparativa
# ---------------------------------------------------------------------------
def tabla_comparacion(
    poblacion: pd.DataFrame, muestra: pd.DataFrame, columna: str
) -> pd.DataFrame:
    """Indicadores descriptivos de la variable en población y muestra."""
    pob = poblacion[columna]
    mus = muestra[columna] if columna in muestra.columns else pd.Series(dtype=pob.dtype)

    if es_numerica(pob) and pob.nunique(dropna=True) > 12:
        indicadores = {
            "Registros": lambda s: len(s.dropna()),
            "Media": lambda s: s.mean(),
            "Mediana": lambda s: s.median(),
            "Desv. estándar": lambda s: s.std(),
            "Mínimo": lambda s: s.min(),
            "Máximo": lambda s: s.max(),
        }
        filas = []
        for nombre, funcion in indicadores.items():
            try:
                v_pob = funcion(pob)
                v_mus = funcion(mus)
            except Exception:  # noqa: BLE001 - columnas no numéricas
                continue
            filas.append(
                {"Indicador": nombre, "Población": v_pob, "Muestra": v_mus}
            )
        tabla = pd.DataFrame(filas)
        for col in ("Población", "Muestra"):
            tabla[col] = pd.to_numeric(tabla[col], errors="coerce").round(2)
        return tabla

    pob_et = _etiquetas(pob)
    mus_et = _etiquetas(mus)
    orden = pob_et.value_counts().head(12).index.tolist()
    return pd.DataFrame(
        {
            "Categoría": orden,
            "% Población": [round(100 * (pob_et == c).mean(), 2) for c in orden],
            "% Muestra": [
                round(100 * (mus_et == c).mean(), 2) if len(mus_et) else 0.0
                for c in orden
            ],
        }
    )


# ---------------------------------------------------------------------------
# Diagnóstico de regresión
# ---------------------------------------------------------------------------
def grafico_regresion(
    observado: pd.Series,
    ajustado: pd.Series,
    variable_y: str = "",
) -> go.Figure:
    """Dispersión de valores observados frente a los ajustados por el modelo.

    La línea diagonal representa el ajuste perfecto: cuanto más cerca estén los
    puntos, mejor reproduce el modelo los valores observados.
    """
    obs = pd.to_numeric(observado, errors="coerce")
    aju = pd.to_numeric(ajustado, errors="coerce")
    datos = pd.DataFrame({"observado": obs, "ajustado": aju}).dropna()

    fig = go.Figure()
    if not datos.empty:
        minimo = float(min(datos["observado"].min(), datos["ajustado"].min()))
        maximo = float(max(datos["observado"].max(), datos["ajustado"].max()))
        fig.add_trace(
            go.Scatter(
                x=[minimo, maximo],
                y=[minimo, maximo],
                mode="lines",
                name="Ajuste perfecto",
                line=dict(color=COLOR_POBLACION, dash="dash", width=1.5),
                hoverinfo="skip",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=datos["observado"],
                y=datos["ajustado"],
                mode="markers",
                name="Observado vs. ajustado",
                marker=dict(size=7, color=COLOR_MUESTRA, opacity=0.65),
                hovertemplate=(
                    "observado = %{x:.4g}<br>ajustado = %{y:.4g}<extra></extra>"
                ),
            )
        )

    _layout(fig, "Valores observados frente a los ajustados")
    fig.update_xaxes(title=variable_y or "Observado")
    fig.update_yaxes(title="Ajustado por el modelo")
    return fig


# ---------------------------------------------------------------------------
# Comparación de grupos (ANOVA)
# ---------------------------------------------------------------------------
def grafico_anova(
    datos: pd.DataFrame,
    variable_y: str,
    variable_grupo: str,
) -> go.Figure:
    """Diagrama de cajas de la variable respuesta por grupo."""
    if variable_y not in datos.columns or variable_grupo not in datos.columns:
        raise ValueError("Las columnas indicadas no existen en los datos.")

    limpio = datos[[variable_y, variable_grupo]].copy()
    limpio[variable_y] = pd.to_numeric(limpio[variable_y], errors="coerce")
    limpio = limpio.dropna()

    fig = px.box(
        limpio,
        x=variable_grupo,
        y=variable_y,
        color=variable_grupo,
        points="outliers",
        template=PLANTILLA,
    )
    fig.update_layout(showlegend=False)
    _layout(fig, f"{variable_y} según {variable_grupo}", alto=420)
    fig.update_xaxes(title=variable_grupo)
    fig.update_yaxes(title=variable_y)
    return fig
