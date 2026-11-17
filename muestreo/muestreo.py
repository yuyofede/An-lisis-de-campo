"""Algoritmos de selección de muestras probabilísticas.

Todos los métodos trabajan sobre un ``pandas.DataFrame`` que representa el
marco muestral (una fila = un elemento de la población) y devuelven un
:class:`ResultadoMuestreo` con la muestra, metadatos auditables y la semilla
utilizada para poder reproducir el sorteo.

Métodos implementados
---------------------
* Aleatorio simple (con o sin reemplazo).
* Sistemático con intervalo fraccionario (garantiza exactamente n registros).
* Estratificado con afijación proporcional y reparto por restos mayores.
* Por conglomerados (selección aleatoria de grupos completos).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Estructura de resultado
# ---------------------------------------------------------------------------
@dataclass
class ResultadoMuestreo:
    """Muestra seleccionada junto con su información de diseño."""

    datos: pd.DataFrame
    metodo: str
    detalles: Dict[str, Any] = field(default_factory=dict)
    semilla: Optional[int] = None
    tamano_marco: int = 0
    tamano_muestra: int = 0

    @property
    def fraccion_muestral(self) -> float:
        return self.tamano_muestra / self.tamano_marco if self.tamano_marco else 0.0

    def resumen(self) -> Dict[str, Any]:
        """Metadatos serializables (sin el DataFrame) para exportar."""
        datos = {k: v for k, v in self.detalles.items() if not isinstance(v, (pd.DataFrame, pd.Series))}
        return {
            "metodo": self.metodo,
            "semilla": self.semilla,
            "tamano_marco": self.tamano_marco,
            "tamano_muestra": self.tamano_muestra,
            "fraccion_muestral": self.fraccion_muestral,
            **datos,
        }


# ---------------------------------------------------------------------------
# Utilidades internas
# ---------------------------------------------------------------------------
def _rng(semilla: Optional[int]) -> np.random.Generator:
    """Generador reproducible. ``None`` produce una semilla aleatoria del sistema."""
    return np.random.default_rng(semilla)


def generar_semilla() -> int:
    """Devuelve una semilla entera de 32 bits para mostrar al usuario."""
    return int(np.random.SeedSequence().entropy % (2 ** 32))


def _validar_n(n: int, disponible: int, reemplazo: bool = False) -> int:
    n = int(n)
    if n < 1:
        raise ValueError("El tamaño de la muestra debe ser al menos 1.")
    if not reemplazo and n > disponible:
        raise ValueError(
            f"La muestra solicitada ({n}) supera el tamaño disponible ({disponible})."
        )
    return n


def _etiqueta(valor: Any) -> str:
    """Etiqueta legible y estable para valores de estratos/conglomerados."""
    if pd.isna(valor):
        return "(sin dato)"
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return str(valor)


def _orden_estable(valores: Sequence[Any]) -> List[Any]:
    """Ordena valores heterogéneos usando su representación textual."""
    return sorted(valores, key=_etiqueta)


# ---------------------------------------------------------------------------
# 1. Muestreo aleatorio simple
# ---------------------------------------------------------------------------
def aleatorio_simple(
    df: pd.DataFrame,
    n: int,
    semilla: Optional[int] = None,
    reemplazo: bool = False,
) -> ResultadoMuestreo:
    """Sorteo aleatorio puro de ``n`` registros del marco.

    Cada elemento tiene la misma probabilidad de selección. Sin reemplazo
    (por defecto) no hay duplicados; con reemplazo un registro puede repetirse
    y el tamaño de muestra puede superar N.
    """
    n = _validar_n(n, len(df), reemplazo=reemplazo)
    if len(df) == 0:
        raise ValueError("El marco muestral está vacío.")

    rng = _rng(semilla)
    posiciones = rng.choice(len(df), size=n, replace=reemplazo)
    # Cada sorteo es independiente: se conserva el orden de aparición.
    muestra = df.iloc[posiciones].copy()

    return ResultadoMuestreo(
        datos=muestra,
        metodo="Aleatorio simple",
        detalles={
            "reemplazo": reemplazo,
            "posiciones_marco": [int(p) + 1 for p in posiciones],
        },
        semilla=semilla,
        tamano_marco=len(df),
        tamano_muestra=len(muestra),
    )


# ---------------------------------------------------------------------------
# 2. Muestreo sistemático
# ---------------------------------------------------------------------------
def sistematico(
    df: pd.DataFrame,
    n: int,
    semilla: Optional[int] = None,
) -> ResultadoMuestreo:
    """Muestreo sistemático de ``n`` registros con intervalo ``k = N / n``.

    Para garantizar **exactamente n** registros incluso cuando N no es
    múltiplo de n se usa el intervalo fraccionario: se sortea un arranque
    ``u ~ U(0, k)`` y se toman las posiciones ``floor(u + i·k)`` para
    ``i = 0..n-1``. Las posiciones son distintas y siempre caen dentro del
    marco.

    Nota metodológica: si el marco tiene un orden cíclico relacionado con la
    variable de interés, conviene aleatorizar el orden antes de aplicar este
    método (opción disponible en la interfaz).
    """
    N = len(df)
    if N == 0:
        raise ValueError("El marco muestral está vacío.")
    n = _validar_n(n, N)
    k = N / n

    rng = _rng(semilla)
    arranque = float(rng.uniform(0.0, k))
    posiciones = [int(math.floor(arranque + i * k)) for i in range(n)]
    # Salvaguarda numérica: nunca salir del marco ni repetir posiciones.
    posiciones = [min(p, N - 1) for p in posiciones]
    if len(set(posiciones)) != n:
        raise ValueError(
            "No fue posible construir una muestra sistemática sin repeticiones; "
            "aumente el tamaño de la muestra o revise el marco."
        )

    muestra = df.iloc[posiciones].copy()
    pasos = np.diff(posiciones)

    return ResultadoMuestreo(
        datos=muestra,
        metodo="Sistemático",
        detalles={
            "intervalo_k": k,
            "arranque": arranque + 1.0,  # 1-based para mostrar al usuario
            "posiciones_marco": [p + 1 for p in posiciones],
            "paso_min": int(pasos.min()) if len(pasos) else 0,
            "paso_max": int(pasos.max()) if len(pasos) else 0,
        },
        semilla=semilla,
        tamano_marco=N,
        tamano_muestra=len(muestra),
    )


# ---------------------------------------------------------------------------
# 3. Muestreo estratificado
# ---------------------------------------------------------------------------
def afijacion_proporcional(
    conteos: pd.Series,
    n: int,
    minimo_por_estrato: int = 1,
) -> pd.DataFrame:
    """Reparte ``n`` entre estratos de forma proporcional a su tamaño.

    Pasos:
    1. Cuota exacta ``n_h = n · N_h / N``.
    2. Parte entera (redondeo hacia abajo).
    3. Se garantiza un mínimo por estrato (si hay presupuesto suficiente).
    4. El faltante/sobrante se ajusta por el método de **restos mayores**,
       respetando la capacidad de cada estrato (``n_h <= N_h``).

    Devuelve una tabla con ``estrato``, ``N_h``, ``cuota``, ``n_h``,
    ``fraccion`` y ``peso`` (N_h / n_h).
    """
    n = int(n)
    total = int(conteos.sum())
    if total <= 0:
        raise ValueError("No hay registros para estratificar.")
    if n < 1:
        raise ValueError("El tamaño de la muestra debe ser al menos 1.")
    if n > total:
        raise ValueError(
            f"La muestra ({n}) no puede superar el total de registros ({total})."
        )

    conteos = conteos[conteos > 0].copy()
    conteos.index = [_etiqueta(i) for i in conteos.index]
    N_h = conteos.to_numpy(dtype=float)
    cuotas = n * N_h / total
    asignado = np.floor(cuotas + 1e-9).astype(int)

    minimo = max(int(minimo_por_estrato), 0)
    minimo_efectivo = np.minimum(N_h.astype(int), minimo)
    if minimo_efectivo.sum() > n:
        raise ValueError(
            f"Con {len(conteos)} estratos y un mínimo de {minimo} por estrato "
            f"necesita al menos {int(minimo_efectivo.sum())} registros; "
            f"la muestra solicitada es {n}. Aumente n o reduzca el mínimo."
        )
    asignado = np.maximum(asignado, minimo_efectivo)

    # --- Ajuste del total por restos mayores -------------------------------
    diferencia = n - int(asignado.sum())
    while diferencia != 0:
        if diferencia > 0:
            # Prioridad a quien tiene mayor resto y todavía capacidad.
            restos = cuotas - asignado
            candidatos = np.where(asignado < N_h)[0]
            if len(candidatos) == 0:  # pragma: no cover - no debería ocurrir
                break
            elegido = candidatos[np.argmax(restos[candidatos])]
            asignado[elegido] += 1
            diferencia -= 1
        else:
            # Se retira a quien esté más sobre-asignado sin bajar del mínimo.
            excesos = asignado - cuotas
            candidatos = np.where(asignado > minimo_efectivo)[0]
            if len(candidatos) == 0:  # pragma: no cover
                break
            elegido = candidatos[np.argmax(excesos[candidatos])]
            asignado[elegido] -= 1
            diferencia += 1

    tabla = pd.DataFrame(
        {
            "estrato": conteos.index,
            "N_h": N_h.astype(int),
            "cuota": cuotas,
            "n_h": asignado,
        }
    )
    tabla["fraccion"] = tabla["n_h"] / tabla["N_h"]
    tabla["peso"] = np.where(tabla["n_h"] > 0, tabla["N_h"] / tabla["n_h"].replace(0, np.nan), np.nan)
    return tabla


def estratificado(
    df: pd.DataFrame,
    n: int,
    columna: str,
    semilla: Optional[int] = None,
    minimo_por_estrato: int = 1,
    orden_aleatorio_estratos: bool = False,
) -> ResultadoMuestreo:
    """Muestra aleatoria proporcional dentro de cada estrato.

    Los registros con valor faltante en ``columna`` se excluyen del marco y
    se informan en ``detalles["filas_excluidas"]``.
    """
    if columna not in df.columns:
        raise ValueError(f"La columna de estratificación '{columna}' no existe.")

    marco = df[df[columna].notna()]
    excluidas = int(len(df) - len(marco))
    if len(marco) == 0:
        raise ValueError("La columna seleccionada no tiene valores válidos.")

    n = _validar_n(n, len(marco))
    conteos = marco[columna].map(_etiqueta).value_counts()
    tabla = afijacion_proporcional(conteos, n, minimo_por_estrato)

    rng = _rng(semilla)
    partes = []
    for fila in tabla.itertuples(index=False):
        sub = marco[marco[columna].map(_etiqueta) == fila.estrato]
        elegidos = rng.choice(len(sub), size=int(fila.n_h), replace=False)
        partes.append(sub.iloc[elegidos])

    muestra = pd.concat(partes).sort_index()

    return ResultadoMuestreo(
        datos=muestra,
        metodo="Estratificado",
        detalles={
            "columna_estratificacion": columna,
            "afijacion": tabla,
            "num_estratos": int(len(tabla)),
            "minimo_por_estrato": minimo_por_estrato,
            "filas_excluidas": excluidas,
        },
        semilla=semilla,
        tamano_marco=len(marco),
        tamano_muestra=len(muestra),
    )


# ---------------------------------------------------------------------------
# 4. Muestreo por conglomerados
# ---------------------------------------------------------------------------
def conglomerados(
    df: pd.DataFrame,
    columna: str,
    num_conglomerados: int,
    semilla: Optional[int] = None,
) -> ResultadoMuestreo:
    """Selecciona ``m`` conglomerados al azar y toma **todos** sus registros.

    Es un muestreo por conglomerados en una etapa: primero se sortean los
    grupos (sucursales, barrios, ciudades...) y luego se censan por completo.
    """
    if columna not in df.columns:
        raise ValueError(f"La columna de conglomeración '{columna}' no existe.")

    marco = df[df[columna].notna()].copy()
    excluidas = int(len(df) - len(marco))
    if len(marco) == 0:
        raise ValueError("La columna seleccionada no tiene valores válidos.")

    grupos = marco[columna].map(_etiqueta)
    disponibles = _orden_estable(grupos.unique())
    m = int(num_conglomerados)
    if m < 1:
        raise ValueError("Debe seleccionar al menos un conglomerado.")
    if m > len(disponibles):
        raise ValueError(
            f"Solo hay {len(disponibles)} conglomerados disponibles y se solicitaron {m}."
        )

    rng = _rng(semilla)
    seleccionados = rng.choice(np.array(disponibles, dtype=object), size=m, replace=False)
    seleccionados = _orden_estable(list(seleccionados))
    mascara = grupos.isin(seleccionados)
    muestra = marco[mascara].sort_index()

    tamanos = (
        pd.DataFrame({"conglomerado": grupos, "registros": 1})
        .groupby("conglomerado", as_index=False)["registros"]
        .sum()
        .sort_values("registros", ascending=False)
    )

    return ResultadoMuestreo(
        datos=muestra,
        metodo="Por conglomerados",
        detalles={
            "columna_conglomeracion": columna,
            "conglomerados_disponibles": disponibles,
            "conglomerados_seleccionados": seleccionados,
            "num_conglomerados": m,
            "tamanos_conglomerados": tamanos,
            "filas_excluidas": excluidas,
        },
        semilla=semilla,
        tamano_marco=len(marco),
        tamano_muestra=len(muestra),
    )


def conglomerados_sugeridos(
    df: pd.DataFrame, columna: str, n_objetivo: int
) -> int:
    """Número aproximado de conglomerados para acercarse a ``n_objetivo``.

    Se usa el tamaño medio de los conglomerados: ``m ≈ n / tamaño_medio``.
    Es solo una sugerencia; el usuario decide el número final.
    """
    if columna not in df.columns:
        return 1
    tamanos = df[columna].dropna().map(_etiqueta).value_counts()
    if len(tamanos) == 0:
        return 1
    promedio = float(tamanos.mean())
    m = int(math.ceil(n_objetivo / promedio)) if promedio > 0 else 1
    return max(1, min(m, len(tamanos)))
