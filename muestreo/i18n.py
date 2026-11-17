"""Internacionalización de la interfaz (español, inglés y noruego).

El idioma se elige desde la barra lateral mediante el selector de la
aplicación; las etiquetas se resuelven con la clave ``key`` del diccionario
``TR``.
"""

from __future__ import annotations

from typing import Optional

#: Idiomas disponibles para la interfaz.
IDIOMAS = ("es", "en", "no")

#: Etiquetas legibles del selector de idioma.
ETIQUETAS_IDIOMA: dict = {
    "es": "Español",
    "en": "English",
    "no": "Norsk",
}

#: Traducciones por idioma. Claves descriptivas, p. ej. ``"tab_tamano"``.
TR: dict = {
    "es": {
        "app_titulo": "Diseño y selección de muestras estadísticas",
        "app_subtitulo": (
            "Calcule el tamaño de muestra, valide el margen de error real y "
            "seleccione muestras probabilísticas reproducibles desde su propia base de datos."
        ),
        "panel": "Panel del estudio",
        "diseno_vigente": "Diseño vigente",
        "muestra_seleccionada": "Muestra seleccionada",
        "sin_base": "Aún no hay una base de datos cargada.",
        "tab_tamano": "Tamaño de muestra",
        "tab_margen_real": "Margen de error real",
        "tab_base": "Base de datos (marco muestral)",
        "tab_seleccion": "Selección de la muestra",
        "tab_resultados": "Visualización y descarga",
        "tab_metodologia": "Metodología y ayuda",
        "tamano_muestra": "Tamaño de muestra",
        "muestra_necesaria": "Muestra necesaria (redondeada hacia arriba)",
        "tamano_muestra_info": (
            "Determine cuántos registros necesita para estimar una proporción con un margen de error y un nivel de confianza dados."
        ),
        "n_infinita": "n (población infinita)",
        "n_poblacion": "Tamaño de la población (N)",
        "tipo_poblacion": "Tipo de población",
        "finita": "Finita (N conocida)",
        "infinita": "Infinita o desconocida",
        "factor_correccion": "Factor de corrección",
        "fraccion_muestral": "Fracción muestral",
        "error": "Margen de error",
        "sensibilidad": "Sensibilidad del tamaño de muestra",
        "confianza": "Nivel de confianza",
        "error_planeado": "Error planeado",
        "error_real": "Error real",
        "muestra_lograda": "Muestra lograda",
        "planeada": "Muestra planeada (n)",
        "recolectada": "Muestra realmente recolectada (m)",
        "base_datos": "Base de datos (marco muestral)",
        "generada": "Muestra generada",
        "metodo": "Método",
        "archivo": "Archivo (sin extensión)",
    },
    "en": {
        "app_titulo": "Sample size and statistical sampling design",
        "app_subtitulo": (
            "Calculate the sample size, validate the real error margin and select "
            "reproducible probabilistic samples from your own database."
        ),
        "panel": "Study panel",
        "diseno_vigente": "Current design",
        "muestra_seleccionada": "Selected sample",
        "sin_base": "No data base has been loaded yet.",
        "tab_tamano": "Sample size",
        "tab_margen_real": "Real error margin",
        "tab_base": "Data base (sampling frame)",
        "tab_seleccion": "Sample selection",
        "tab_resultados": "Visualization and download",
        "tab_metodologia": "Methodology and help",
        "tamano_muestra": "Sample size",
        "muestra_necesaria": "Required sample size (rounded up)",
        "tamano_muestra_info": (
            "Determine how many records you need to estimate a proportion with a margin of error and a confidence level."
        ),
        "n_infinita": "n (infinite population)",
        "n_poblacion": "Population size (N)",
        "tipo_poblacion": "Population type",
        "finita": "Finite (N known)",
        "infinita": "Infinite or unknown",
        "factor_correccion": "Correction factor",
        "fraccion_muestral": "Sampling fraction",
        "error": "Error margin",
        "sensibilidad": "Sample size sensitivity",
        "confianza": "Confidence level",
        "error_planeado": "Planned error",
        "error_real": "Real error",
        "muestra_lograda": "Sample achieved",
        "planeada": "Planned sample (n)",
        "recolectada": "Collected sample (m)",
        "base_datos": "Data base (sampling frame)",
        "generada": "Generated sample",
        "metodo": "Method",
        "archivo": "File name (without extension)",
        "sin_base": "No data base has been loaded yet.",
        "estimacion_ic": "Point estimate and its confidence interval",
        "variable_binaria": "Estimation variable (binary proportion)",
        "estimacion_puntual": "Point estimate (p̂)",
    },
    "no": {
        "app_titulo": "Størrelsesdesign og statistisk utvelsning",
        "app_subtitulo": (
            "Bere størrelsesample, valider den reelle marginkutt og velg "
            "gjenværende probabilistiske utvelsninger fra din egen database."
        ),
        "panel": "Studiepanel",
        "diseno_vigente": "Nåværende design",
        "muestra_seleccionada": "Valgt utvelsning",
        "sin_base": "Ingen databasemotor er lastet enn.",
        "tab_tamano": "Størrelse",
        "tab_margen_real": "Riktig marginkutt",
        "tab_base": "Databasemotor (stikkordbar ramme)",
        "tab_seleccion": "Størrelsesvalg",
        "tab_resultados": "Visualisering og nedlasting",
        "tab_metodologia": "Metode og hjelp",
        "tamano_muestra": "Størrelse",
        "muestra_necesaria": "Nødvendig størrelse (rundet opp)",
        "tamano_muestra_info": (
            "Bere hvor mange registreringer du trenger for å estimere en andel med en marginkutt og et konfidensnivå."
        ),
        "n_infinita": "n (uendret befolkning)",
        "n_poblacion": "Populasjonsstørrelse (N)",
        "tipo_poblacion": "Populasjons type",
        "finita": "Bemannet (N kjent)",
        "infinita": "Uendret eller ukjent",
        "factor_correccion": "Korrigeringsfaktor",
        "fraccion_muestral": "Stikkordsandel",
        "error": "Marginkutt",
        "sensibilidad": "Størrelsesamplefølsomhet",
        "confianza": "Konfidensnivå",
        "error_planeado": "Planlagt marginkutt",
        "error_real": "Riktig marginkutt",
        "muestra_lograda": "Størrelse oppnådd",
        "planeada": "Planlagt størrelse (n)",
        "recolectada": "Innsamlet størrelse (m)",
        "base_datos": "Databasemotor (stikkordbar ramme)",
        "generada": "Generert størrelse",
        "metodo": "Metode",
        "archivo": "Filnavn (uten filtype)",
        "sin_base": "Ingen databasemotor er lastet enn.",
        "estimacion_ic": "Estimert punkt og dets konfidensintervall",
        "variable_binaria": "Estimeringsvariabel (binær proportion)",
        "estimacion_puntual": "Estimert punkt (p̂)",
    },
}

#: Idioma actualmente seleccionado en la interfaz.
_IDIOMA_ACTUAL = "es"


def set_idioma(codigo: str) -> None:
    """Fija el idioma de la interfaz (``es``, ``en`` o ``no``)."""
    global _IDIOMA_ACTUAL
    _IDIOMA_ACTUAL = codigo if codigo in IDIOMAS else "es"


def idioma_actual() -> str:
    """Devuelve el código del idioma activo."""
    return _IDIOMA_ACTUAL


def t(key: str, idioma: Optional[str] = None) -> str:
    """Devuelve la etiqueta traducida para la clave indicada."""
    codigo = idioma or _IDIOMA_ACTUAL
    tabla = TR.get(codigo) or TR["es"]
    return tabla.get(key, key)
