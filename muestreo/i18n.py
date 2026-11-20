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
        "base": "Base",
        "estimacion_ic": "Estimación puntual e intervalo de confianza",
        "variable_binaria": "Variable de estimación (proporción binaria)",
        "estimacion_puntual": "Estimación puntual (p̂)",
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
        "conf_nivel_90": "90 %",
        "conf_nivel_95": "95 %",
        "conf_nivel_99": "99 %",
        "conf_manual_z": "Manual (definir Z)",
        "error_e": "Margen de error (e, en %)",
        "proporcion_esperada": "Proporción esperada (p)",
        "error_planeado": "Error planeado",
        "error_real": "Error real",
        "muestra_lograda": "Muestra lograda",
        "planeada": "Muestra planeada (n)",
        "recolectada": "Muestra realmente recolectada (m)",
        "base_datos": "Base de datos (marco muestral)",
        "generada": "Muestra generada",
        "metodo": "Método",
        "archivo": "Archivo (sin extensión)",
        "usar_n": "Usar este tamaño en la selección →",
        "error_revise": "Revise los parámetros ingresados.",
        "error_parametros": "Revise los parámetros: {exc}",
        "error_muestra": "No se pudo seleccionar la muestra: {exc}",
        "error_carga": "No se pudo leer el archivo: {exc}",
        "error_diseno": "No se pudo calcular el tamaño de muestra: {exc}",
        "error_resultado": "No se pudo procesar la muestra: {exc}",
        "error_exportacion": "No se pudo exportar la muestra: {exc}",
        "error_variable": "Seleccione una variable válida.",
        "tab_analisis": "Análisis estadístico",
        "analisis_titulo": "Análisis estadístico",
        "analisis_info": (
            "Explore la base completa con estadística descriptiva, regresión "
            "lineal múltiple y ANOVA de un factor."
        ),
        "analisis_alcance": "Datos a analizar",
        "analisis_base_completa": "Base completa",
        "analisis_muestra": "Muestra seleccionada",
        "analisis_sin_numericas": (
            "La base no tiene variables numéricas suficientes para el análisis."
        ),
        "analisis_desc": "Estadística descriptiva",
        "analisis_desc_info": (
            "Resumen de tendencia central, dispersión y forma de las variables numéricas."
        ),
        "analisis_desc_cols": "Variables numéricas a describir",
        "analisis_desc_sin_cols": "Seleccione al menos una variable para describir.",
        "analisis_descargar": "Descargar tabla descriptiva (CSV)",
        "analisis_reg": "Regresión lineal",
        "analisis_reg_info": (
            "Ajuste una regresión lineal múltiple por mínimos cuadrados ordinarios."
        ),
        "analisis_reg_y": "Variable dependiente (Y)",
        "analisis_reg_x": "Predictores (X)",
        "analisis_reg_sin_x": (
            "Seleccione al menos un predictor para ajustar el modelo."
        ),
        "analisis_reg_resultados": "Resultados del modelo",
        "analisis_r2": "R²",
        "analisis_r2_ajustado": "R² ajustado",
        "analisis_rmse": "RMSE",
        "analisis_f": "Estadístico F",
        "analisis_p": "p-valor",
        "analisis_n": "Observaciones",
        "analisis_coeficientes": "Coeficientes estimados",
        "analisis_ecuacion": "Ecuación estimada",
        "analisis_reg_plot": "Diagnóstico observado vs. ajustado",
        "analisis_anova": "ANOVA de un factor",
        "analisis_anova_info": (
            "Compare la media de una variable numérica entre dos o más grupos."
        ),
        "analisis_anova_y": "Variable respuesta (Y)",
        "analisis_anova_grupo": "Factor o grupo",
        "analisis_anova_sin_grupo": (
            "La base no tiene variables categóricas aptas como factor."
        ),
        "analisis_anova_tabla": "Tabla ANOVA",
        "analisis_fuente": "Fuente",
        "analisis_medias": "Medias por grupo",
        "analisis_eta2": "η² (tamaño del efecto)",
        "analisis_significativo": "Diferencia significativa al 5 %",
        "analisis_no_significativo": "Sin diferencias significativas al 5 %",
        "analisis_grupos": "Grupos",
        "analisis_error": "No se pudo completar el análisis: {exc}",
        "analisis_columna": "Variable",
        "analisis_faltantes": "Faltantes",
        "analisis_media": "Media",
        "analisis_desviacion": "Desv. estándar",
        "analisis_minimo": "Mínimo",
        "analisis_mediana": "Mediana",
        "analisis_maximo": "Máximo",
        "analisis_asimetria": "Asimetría",
        "analisis_curtosis": "Curtosis",
        "analisis_cv": "CV",
        "analisis_suma_cuadrados": "Suma de cuadrados",
        "analisis_gl": "gl",
        "analisis_media_cuadratica": "Media cuadrática",
        "analisis_entre": "Entre grupos",
        "analisis_dentro": "Dentro de grupos",
        "analisis_total": "Total",
        "analisis_grupo": "Grupo",
        "analisis_coeficiente": "Coeficiente",
        "analisis_error_estandar": "Error estándar",
        "analisis_ic_inferior": "IC 95 % inferior",
        "analisis_ic_superior": "IC 95 % superior",
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
        "base": "Base",
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
        "conf_nivel_90": "90 %",
        "conf_nivel_95": "95 %",
        "conf_nivel_99": "99 %",
        "conf_manual_z": "Custom (define Z)",
        "error_e": "Error margin (e, in %)",
        "proporcion_esperada": "Expected proportion (p)",
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
        "usar_n": "Use this sample size in the selection →",
        "error_revise": "Please review the entered parameters.",
        "error_parametros": "Please review the parameters: {exc}",
        "error_muestra": "The sample could not be selected: {exc}",
        "error_carga": "The file could not be read: {exc}",
        "error_diseno": "The sample size could not be calculated: {exc}",
        "error_resultado": "The sample could not be processed: {exc}",
        "error_exportacion": "The sample could not be exported: {exc}",
        "error_variable": "Please select a valid variable.",
        "tab_analisis": "Statistical analysis",
        "analisis_titulo": "Statistical analysis",
        "analisis_info": (
            "Explore the full data base with descriptive statistics, multiple "
            "linear regression and one-way ANOVA."
        ),
        "analisis_alcance": "Data to analyze",
        "analisis_base_completa": "Full data base",
        "analisis_muestra": "Selected sample",
        "analisis_sin_numericas": (
            "The data base does not have enough numeric variables for analysis."
        ),
        "analisis_desc": "Descriptive statistics",
        "analisis_desc_info": (
            "Summary of central tendency, dispersion and shape of numeric variables."
        ),
        "analisis_desc_cols": "Numeric variables to describe",
        "analisis_desc_sin_cols": "Select at least one variable to describe.",
        "analisis_descargar": "Download descriptive table (CSV)",
        "analisis_reg": "Linear regression",
        "analisis_reg_info": (
            "Fit a multiple linear regression by ordinary least squares."
        ),
        "analisis_reg_y": "Dependent variable (Y)",
        "analisis_reg_x": "Predictors (X)",
        "analisis_reg_sin_x": "Select at least one predictor to fit the model.",
        "analisis_reg_resultados": "Model results",
        "analisis_r2": "R²",
        "analisis_r2_ajustado": "Adjusted R²",
        "analisis_rmse": "RMSE",
        "analisis_f": "F statistic",
        "analisis_p": "p-value",
        "analisis_n": "Observations",
        "analisis_coeficientes": "Estimated coefficients",
        "analisis_ecuacion": "Estimated equation",
        "analisis_reg_plot": "Observed vs. fitted diagnostic",
        "analisis_anova": "One-way ANOVA",
        "analisis_anova_info": (
            "Compare the mean of a numeric variable across two or more groups."
        ),
        "analisis_anova_y": "Response variable (Y)",
        "analisis_anova_grupo": "Factor or group",
        "analisis_anova_sin_grupo": (
            "The data base has no categorical variables suitable as a factor."
        ),
        "analisis_anova_tabla": "ANOVA table",
        "analisis_fuente": "Source",
        "analisis_medias": "Means by group",
        "analisis_eta2": "η² (effect size)",
        "analisis_significativo": "Significant difference at 5 %",
        "analisis_no_significativo": "No significant differences at 5 %",
        "analisis_grupos": "Groups",
        "analisis_error": "The analysis could not be completed: {exc}",
        "analisis_columna": "Variable",
        "analisis_faltantes": "Missing",
        "analisis_media": "Mean",
        "analisis_desviacion": "Std. deviation",
        "analisis_minimo": "Minimum",
        "analisis_mediana": "Median",
        "analisis_maximo": "Maximum",
        "analisis_asimetria": "Skewness",
        "analisis_curtosis": "Kurtosis",
        "analisis_cv": "CV",
        "analisis_suma_cuadrados": "Sum of squares",
        "analisis_gl": "df",
        "analisis_media_cuadratica": "Mean square",
        "analisis_entre": "Between groups",
        "analisis_dentro": "Within groups",
        "analisis_total": "Total",
        "analisis_grupo": "Group",
        "analisis_coeficiente": "Coefficient",
        "analisis_error_estandar": "Standard error",
        "analisis_ic_inferior": "95 % CI lower",
        "analisis_ic_superior": "95 % CI upper",
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
        "base": "Base",
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
        "conf_nivel_90": "90 %",
        "conf_nivel_95": "95 %",
        "conf_nivel_99": "99 %",
        "conf_manual_z": "Manuell (definer Z)",
        "error_e": "Marginkutt (e, i %)",
        "proporcion_esperada": "Forventet andel (p)",
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
        "usar_n": "Bruk denne størrelsen i utvelsningen →",
        "error_revise": "Vennligst kontroller de valgte parameterne.",
        "error_parametros": "Vennligst kontroller parameterne: {exc}",
        "error_muestra": "Størrelsen kunne ikke velges: {exc}",
        "error_carga": "Filen kunne ikke leses: {exc}",
        "error_diseno": "Størrelsen kunne ikke beregnes: {exc}",
        "error_resultado": "Størrelsen kunne ikke behandles: {exc}",
        "error_exportacion": "Størrelsen kunne ikke eksporteres: {exc}",
        "error_variable": "Vennligst velg en gyldig variabel.",
        "tab_analisis": "Statistisk analyse",
        "analisis_titulo": "Statistisk analyse",
        "analisis_info": (
            "Utforsk hele databasen med beskrivende statistikk, multippel "
            "lineær regresjon og enveis ANOVA."
        ),
        "analisis_alcance": "Data som skal analyseres",
        "analisis_base_completa": "Hele databasen",
        "analisis_muestra": "Valgt utvalg",
        "analisis_sin_numericas": (
            "Databasen har ikke nok numeriske variabler for analyse."
        ),
        "analisis_desc": "Beskrivende statistikk",
        "analisis_desc_info": (
            "Sammendrag av sentraltendens, spredning og form for numeriske variabler."
        ),
        "analisis_desc_cols": "Numeriske variabler som skal beskrives",
        "analisis_desc_sin_cols": "Velg minst én variabel å beskrive.",
        "analisis_descargar": "Last ned beskrivende tabell (CSV)",
        "analisis_reg": "Lineær regresjon",
        "analisis_reg_info": (
            "Tilpass en multippel lineær regresjon med minste kvadrater."
        ),
        "analisis_reg_y": "Avhengig variabel (Y)",
        "analisis_reg_x": "Prediktorer (X)",
        "analisis_reg_sin_x": "Velg minst én prediktor for å tilpasse modellen.",
        "analisis_reg_resultados": "Modellresultater",
        "analisis_r2": "R²",
        "analisis_r2_ajustado": "Justert R²",
        "analisis_rmse": "RMSE",
        "analisis_f": "F-statistikk",
        "analisis_p": "p-verdi",
        "analisis_n": "Observasjoner",
        "analisis_coeficientes": "Estimerte koeffisienter",
        "analisis_ecuacion": "Estimert ligning",
        "analisis_reg_plot": "Observert vs. tilpasset diagnostikk",
        "analisis_anova": "Enveis ANOVA",
        "analisis_anova_info": (
            "Sammenlign gjennomsnittet av en numerisk variabel på tvers av to eller flere grupper."
        ),
        "analisis_anova_y": "Responsvariabel (Y)",
        "analisis_anova_grupo": "Faktor eller gruppe",
        "analisis_anova_sin_grupo": (
            "Databasen har ingen kategoriske variabler som egner seg som faktor."
        ),
        "analisis_anova_tabla": "ANOVA-tabell",
        "analisis_fuente": "Kilde",
        "analisis_medias": "Gjennomsnitt per gruppe",
        "analisis_eta2": "η² (effektstørrelse)",
        "analisis_significativo": "Signifikant forskjell ved 5 %",
        "analisis_no_significativo": "Ingen signifikante forskjeller ved 5 %",
        "analisis_grupos": "Grupper",
        "analisis_error": "Analysen kunne ikke fullføres: {exc}",
        "analisis_columna": "Variabel",
        "analisis_faltantes": "Manglende",
        "analisis_media": "Gjennomsnitt",
        "analisis_desviacion": "Std. avvik",
        "analisis_minimo": "Minimum",
        "analisis_mediana": "Median",
        "analisis_maximo": "Maksimum",
        "analisis_asimetria": "Skjevhet",
        "analisis_curtosis": "Kurtose",
        "analisis_cv": "CV",
        "analisis_suma_cuadrados": "Kvadratsum",
        "analisis_gl": "df",
        "analisis_media_cuadratica": "Gjennomsnittskvadrat",
        "analisis_entre": "Mellom grupper",
        "analisis_dentro": "Innen grupper",
        "analisis_total": "Totalt",
        "analisis_grupo": "Gruppe",
        "analisis_coeficiente": "Koeffisient",
        "analisis_error_estandar": "Standardfeil",
        "analisis_ic_inferior": "95 % KI nedre",
        "analisis_ic_superior": "95 % KI øvre",
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
