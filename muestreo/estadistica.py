"""
Cálculos de diseño muestral.

Contiene la lógica estadística pura (sin Streamlit ni pandas) para poder
probarla de forma aislada:

* Tamaño de muestra para poblaciones finitas e infinitas.
* Margen de error real (calculadora inversa).
* Nivel de confianza alcanzado y utilidades de sensibilidad.

Convenciones
------------
N : tamaño de la población (``None`` si es desconocida o infinita).
n : tamaño de la muestra.
z : valor crítico de la distribución normal estándar.
p : proporción esperada del evento de interés; q = 1 - p.
e : margen de error absoluto (en proporción, p. ej. 0.05 para 5 %).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from statistics import NormalDist
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Valores z de uso frecuente (dos colas)
# ---------------------------------------------------------------------------
CONFIANZAS_ESTANDAR: Dict[float, float] = {
    0.90: 1.6448536269514722,
    0.95: 1.9599639845400540,
    0.99: 2.5758293035489004,
}

#: Etiquetas legibles para los selectores de la interfaz.
ETIQUETAS_CONFIANZA = {
    0.90: "90 %",
    0.95: "95 %",
    0.99: "99 %",
}


# ---------------------------------------------------------------------------
# Utilidades de validación
# ---------------------------------------------------------------------------
def _validar_error(error: float) -> float:
    """El margen de error debe estar en el intervalo (0, 1]."""
    try:
        error = float(error)
    except (TypeError, ValueError) as exc:
        raise ValueError("El margen de error debe ser un número.") from exc
    if not (0 < error <= 1):
        raise ValueError("El margen de error debe ser mayor que 0 y menor o igual a 1.")
    return error


def _validar_proporciones(p: float, q: Optional[float]) -> tuple:
    """Valida p y calcula q cuando no se entrega explícitamente."""
    try:
        p = float(p)
    except (TypeError, ValueError) as exc:
        raise ValueError("La proporción p debe ser un número.") from exc
    if not (0 < p < 1):
        raise ValueError("La proporción p debe estar estrictamente entre 0 y 1.")

    if q is None:
        q = 1.0 - p
    else:
        try:
            q = float(q)
        except (TypeError, ValueError) as exc:
            raise ValueError("La proporción q debe ser un número.") from exc
        if not (0 < q < 1):
            raise ValueError("La proporción q debe estar estrictamente entre 0 y 1.")
        if abs((p + q) - 1.0) > 1e-6:
            raise ValueError("Las proporciones deben cumplir p + q = 1.")

    return p, q


def _validar_poblacion(poblacion: Optional[int]) -> Optional[int]:
    """Normaliza y valida N. ``None`` representa una población infinita."""
    if poblacion is None:
        return None
    try:
        n_pob = int(poblacion)
    except (TypeError, ValueError) as exc:
        raise ValueError("El tamaño de la población debe ser un número entero.") from exc
    if n_pob < 1:
        raise ValueError("El tamaño de la población debe ser al menos 1.")
    return n_pob


def _validar_muestra(muestra: float) -> float:
    try:
        n = float(muestra)
    except (TypeError, ValueError) as exc:
        raise ValueError("El tamaño de la muestra debe ser un número.") from exc
    if n < 1:
        raise ValueError("El tamaño de la muestra debe ser al menos 1.")
    return n


# ---------------------------------------------------------------------------
# Nivel de confianza <-> z
# ---------------------------------------------------------------------------
def z_para_confianza(confianza: float) -> float:
    """Devuelve el valor crítico z (dos colas) para un nivel de confianza.

    Ejemplo: ``z_para_confianza(0.95) -> 1.9599...``
    """
    confianza = float(confianza)
    if not (0 < confianza < 1):
        raise ValueError("El nivel de confianza debe estar entre 0 y 1 (exclusivo).")
    if confianza in CONFIANZAS_ESTANDAR:
        return CONFIANZAS_ESTANDAR[confianza]
    return NormalDist().inv_cdf(0.5 + confianza / 2.0)


def confianza_para_z(z: float) -> float:
    """Nivel de confianza (dos colas) asociado a un valor crítico ``z``."""
    z = float(z)
    if z <= 0:
        raise ValueError("El valor z debe ser positivo.")
    return 2.0 * NormalDist().cdf(z) - 1.0


# ---------------------------------------------------------------------------
# Tamaño de muestra
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ResultadoTamanoMuestra:
    """Resultado completo del cálculo de tamaño de muestra."""

    poblacion: Optional[int]
    confianza: float
    z: float
    p: float
    q: float
    error: float
    n_infinita: float          # n0 antes de la corrección por población finita
    n_exacta: float            # n sin redondear
    muestra: int               # n final, siempre redondeado hacia arriba
    factor_correccion: float   # n / n0
    fraccion_muestral: float   # n / N (0.0 si N es desconocida)
    poblacion_infinita: bool

    def como_dict(self) -> Dict[str, object]:
        """Representación serializable (para tablas y exportaciones)."""
        return asdict(self)


def calcular_tamano_muestra(
    poblacion: Optional[int] = None,
    error: float = 0.05,
    confianza: float = 0.95,
    z: Optional[float] = None,
    p: float = 0.5,
    q: Optional[float] = None,
) -> ResultadoTamanoMuestra:
    """Calcula el tamaño de muestra necesario.

    Población infinita (o desconocida)::

        n0 = z² · p · q / e²

    Población finita (corrección por población finita)::

        n = n0 / (1 + (n0 - 1) / N)

    El resultado se redondea **siempre hacia arriba** (``math.ceil``) y se
    limita al tamaño de la población: no tiene sentido muestrear más
    registros de los que existen.

    Parameters
    ----------
    poblacion:
        N. ``None`` si es desconocida o infinita.
    error:
        Margen de error absoluto, en proporción (0.05 = ±5 %).
    confianza:
        Nivel de confianza (0.90, 0.95, 0.99...). Se ignora si se entrega ``z``.
    z:
        Valor crítico manual. Tiene prioridad sobre ``confianza``.
    p, q:
        Proporciones esperadas. Por defecto p = q = 0.5 (escenario más
        conservador, maximiza la varianza).
    """
    error = _validar_error(error)
    p, q = _validar_proporciones(p, q)
    N = _validar_poblacion(poblacion)

    if z is None:
        confianza = float(confianza)
        z = z_para_confianza(confianza)
    else:
        z = float(z)
        if z <= 0:
            raise ValueError("El valor z debe ser positivo.")
        confianza = confianza_para_z(z)

    n0 = (z ** 2) * p * q / (error ** 2)

    if N is None:
        n_exacta = n0
        factor = 1.0
        fraccion = 0.0
    else:
        n_exacta = n0 / (1.0 + (n0 - 1.0) / N)
        n_exacta = min(n_exacta, float(N))
        factor = n_exacta / n0 if n0 > 0 else 1.0

    muestra = int(math.ceil(n_exacta - 1e-9))  # el epsilon evita 384.0000001 -> 385
    if N is not None:
        muestra = min(muestra, N)
        fraccion = muestra / N

    return ResultadoTamanoMuestra(
        poblacion=N,
        confianza=confianza,
        z=z,
        p=p,
        q=q,
        error=error,
        n_infinita=n0,
        n_exacta=n_exacta,
        muestra=muestra,
        factor_correccion=factor,
        fraccion_muestral=fraccion,
        poblacion_infinita=N is None,
    )


# ---------------------------------------------------------------------------
# Margen de error (calculadora inversa)
# ---------------------------------------------------------------------------
def margen_error(
    muestra: float,
    poblacion: Optional[int] = None,
    confianza: float = 0.95,
    z: Optional[float] = None,
    p: float = 0.5,
    q: Optional[float] = None,
) -> float:
    """Margen de error absoluto para una muestra ya recolectada.

    Población infinita::

        e = z · sqrt(p·q / n)

    Población finita::

        e = z · sqrt(p·q / n) · sqrt((N - n) / (N - 1))

    Si la muestra cubre toda la población (censo), el error es 0.
    """
    n = _validar_muestra(muestra)
    p, q = _validar_proporciones(p, q)
    N = _validar_poblacion(poblacion)

    if N is None:
        if z is None:
            z = z_para_confianza(confianza)
        return float(z) * math.sqrt(p * q / n)

    if n >= N:
        return 0.0

    if z is None:
        z = z_para_confianza(confianza)

    fpc = math.sqrt((N - n) / (N - 1)) if N > 1 else 0.0
    return float(z) * math.sqrt(p * q / n) * fpc


def confianza_alcanzada(
    muestra: float,
    error: float,
    poblacion: Optional[int] = None,
    p: float = 0.5,
    q: Optional[float] = None,
) -> float:
    """Nivel de confianza que realmente alcanza una muestra con margen ``error``.

    Despeja z de la fórmula del margen de error y lo convierte a confianza
    de dos colas.
    """
    n = _validar_muestra(muestra)
    error = _validar_error(error)
    p, q = _validar_proporciones(p, q)
    N = _validar_poblacion(poblacion)

    if N is not None and n >= N:
        return 1.0

    fpc = 1.0
    if N is not None and N > 1:
        fpc = math.sqrt((N - n) / (N - 1))
    if fpc <= 0:
        return 1.0

    z_equivalente = error / (math.sqrt(p * q / n) * fpc)
    return min(confianza_para_z(z_equivalente), 1.0)


def tamano_para_error(
    error: float,
    poblacion: Optional[int] = None,
    confianza: float = 0.95,
    z: Optional[float] = None,
    p: float = 0.5,
    q: Optional[float] = None,
) -> int:
    """Tamaño de muestra requerido para lograr un margen de error objetivo."""
    return calcular_tamano_muestra(
        poblacion=poblacion, error=error, confianza=confianza, z=z, p=p, q=q
    ).muestra


@dataclass(frozen=True)
class ComparacionMuestras:
    """Comparación entre la muestra planeada y la realmente recolectada."""

    muestra_planeada: int
    muestra_real: int
    error_planeado: float
    error_real: float
    diferencia_error: float       # error_real - error_planeado (proporción)
    confianza_original: float
    confianza_real: float
    logro_muestra: float          # muestra_real / muestra_planeada
    muestra_faltante: int         # registros que faltan para el plan

    def como_dict(self) -> Dict[str, object]:
        return asdict(self)


def comparar_muestras(
    muestra_planeada: float,
    muestra_real: float,
    poblacion: Optional[int] = None,
    confianza: float = 0.95,
    z: Optional[float] = None,
    p: float = 0.5,
    q: Optional[float] = None,
) -> ComparacionMuestras:
    """Recalcula el margen de error real manteniendo la confianza original.

    Útil cuando se planeó recolectar ``n`` encuestas pero solo se obtuvieron
    ``m`` respuestas: el margen de error efectivo aumenta. También informa la
    confianza que realmente se alcanza con la muestra recolectada.
    """
    n_plan = int(math.ceil(_validar_muestra(muestra_planeada)))
    n_real = int(math.ceil(_validar_muestra(muestra_real)))

    if z is None:
        z = z_para_confianza(confianza)
    else:
        confianza = confianza_para_z(z)

    e_plan = margen_error(n_plan, poblacion, confianza=confianza, z=z, p=p, q=q)
    e_real = margen_error(n_real, poblacion, confianza=confianza, z=z, p=p, q=q)
    conf_real = confianza_alcanzada(n_real, e_plan, poblacion, p=p, q=q)

    return ComparacionMuestras(
        muestra_planeada=n_plan,
        muestra_real=n_real,
        error_planeado=e_plan,
        error_real=e_real,
        diferencia_error=e_real - e_plan,
        confianza_original=confianza,
        confianza_real=conf_real,
        logro_muestra=n_real / n_plan if n_plan else 0.0,
        muestra_faltante=max(n_plan - n_real, 0),
    )


# ---------------------------------------------------------------------------
# Tabla de sensibilidad
# ---------------------------------------------------------------------------
def tabla_sensibilidad(
    poblacion: Optional[int] = None,
    confianza: float = 0.95,
    p: float = 0.5,
    q: Optional[float] = None,
    errores: Optional[List[float]] = None,
) -> List[Dict[str, float]]:
    """Tamaño de muestra para distintos márgenes de error.

    Sirve como apoyo al investigador para negociar precisión frente a costo.
    """
    if errores is None:
        errores = [0.01, 0.02, 0.03, 0.04, 0.05, 0.075, 0.10]

    filas: List[Dict[str, float]] = []
    for e in errores:
        res = calcular_tamano_muestra(
            poblacion=poblacion, error=e, confianza=confianza, p=p, q=q
        )
        filas.append(
            {
                "margen_error": e,
                "muestra": res.muestra,
                "fraccion_muestral": res.fraccion_muestral,
            }
        )
    return filas
