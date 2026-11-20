"""Paquete de cálculo y selección de muestras estadísticas.

Módulos
-------
estadistica
    Fórmulas de tamaño de muestra, margen de error y confianza.
muestreo
    Algoritmos de selección (aleatorio simple, sistemático, estratificado,
    conglomerados).
datos
    Lectura de CSV/Excel, datos de ejemplo y exportación.
graficos
    Figuras de Plotly para comparar población y muestra.
analisis
    Estadística descriptiva, regresión lineal múltiple y ANOVA de un factor.
"""

__version__ = "1.1.0"

__all__ = ["estadistica", "muestreo", "datos", "graficos", "analisis"]
