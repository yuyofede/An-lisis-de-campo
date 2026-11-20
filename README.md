# 📊 Diseño y selección de muestras estadísticas

Aplicación web en **Python + Streamlit** para calcular tamaños de muestra,
evaluar el margen de error real de un estudio y seleccionar muestras
probabilísticas reproducibles a partir de un archivo **CSV** o **Excel**.

Pensada para investigación de mercados, encuestas, auditorías y trabajos
académicos: cubre el flujo completo desde el diseño hasta la exportación de la
muestra con trazabilidad (método, semilla y parámetros).

---

## Funcionalidades

### 1. Cálculo de tamaño de muestra
- Población **finita** (con corrección por población finita) o **infinita/desconocida**.
- Nivel de confianza con selector rápido **90 %, 95 %, 99 %** o **Z manual**.
- Margen de error configurable y proporciones esperadas `p` y `q` (0,50 por defecto).
- Redondeo **siempre hacia arriba** (`math.ceil`) y tope en `N`.
- Fórmulas visibles con la sustitución numérica y tabla de sensibilidad
  (muestra necesaria para distintos márgenes de error).

### 2. Calculadora inversa de margen de error
- Ingrese la muestra **planeada** y la **realmente recolectada**.
- Recalcula el margen de error efectivo manteniendo la confianza original.
- Informa diferencia en puntos porcentuales, muestra faltante, porcentaje de
  logro y confianza que realmente alcanza el error planeado.
- Gráfico interactivo de la curva `e(n)` con ambos puntos.

### 3. Selección automatizada de muestras
| Método | Implementación |
|---|---|
| **Aleatorio simple** | Sorteo puro de `n` registros, con opción de reemplazo. |
| **Sistemático** | Intervalo `k = N/n`, arranque aleatorio y posiciones `⌊u + i·k⌋` (garantiza exactamente `n`). Opción de aleatorizar el orden del marco. |
| **Estratificado** | Afijación proporcional por estrato, mínimo por estrato y reparto por **restos mayores** para sumar exactamente `n`. |
| **Por conglomerados** | Sortea `m` grupos completos y censa todos sus registros. Sugiere `m` según el tamaño medio del conglomerado. |

Todos los métodos permiten fijar una **semilla** para reproducir el sorteo y
registran las posiciones/parámetros utilizados.

### 4. Visualización y exportación
- Comparación población vs muestra con histogramas o barras (Plotly).
- Representatividad por estrato/conglomerado y tabla de indicadores.
- Exportación a **CSV** (UTF-8 con BOM) y **Excel (.xlsx)** con hoja
  *Resumen*, hoja *Muestra* y hojas adicionales de afijación o conglomerados.
- Cada fila conserva `id_marco`, el identificador de su posición en el marco.

### 5. Análisis estadístico
Módulo independiente (`muestreo/analisis.py`) que trabaja sobre la base
completa, sin depender de la muestra seleccionada:

- **Estadística descriptiva** (pandas): n válido, faltantes, media, desviación
  estándar, mínimo, cuartiles, mediana, máximo, asimetría, curtosis y
  coeficiente de variación para las variables numéricas elegidas.
- **Regresión lineal múltiple** (statsmodels): coeficientes con error estándar,
  `t`, `p` e intervalo de confianza al 95 %, `R²`, `R²` ajustado, `RMSE`,
  estadístico `F`, ecuación estimada y gráfico observado vs. ajustado. Admite
  predictores numéricos y categóricos (codificados con variables ficticias).
- **ANOVA de un factor** (SciPy): tabla completa (entre/dentro/total), `F`,
  `p-valor`, `η²` como tamaño del efecto, medias por grupo y diagrama de cajas.

Cada análisis valida las variables, informa valores faltantes y muestra
mensajes claros cuando no hay datos suficientes. El alcance puede ser la
**base completa** o la **muestra seleccionada**.

### 6. Interfaz multilingüe
Selector de idioma en la barra lateral con **español**, **inglés** y **noruego**.
Las etiquetas de la interfaz y de las tablas se resuelven desde
`muestreo/i18n.py`.

---

## Estructura del proyecto

```
muestreo_estadistico/
├── app.py                      # Interfaz Streamlit (7 pestañas)
├── requirements.txt            # Dependencias de ejecución
├── requirements-dev.txt        # Dependencias de pruebas
├── pytest.ini
├── README.md
├── .streamlit/config.toml      # Tema de la aplicación
├── muestreo/
│   ├── __init__.py
│   ├── estadistica.py          # Fórmulas: n, margen de error, confianza
│   ├── muestreo.py             # Algoritmos de los 4 métodos
│   ├── datos.py                # Lectura CSV/Excel, datos de ejemplo, exportación
│   ├── analisis.py             # Descriptiva, regresión lineal y ANOVA
│   ├── i18n.py                 # Traducciones español / inglés / noruego
│   └── graficos.py             # Figuras Plotly y tablas comparativas
├── tests/
│   ├── test_estadistica.py
│   ├── test_muestreo.py
│   ├── test_datos.py
│   ├── test_analisis.py
│   ├── test_graficos.py
│   ├── test_i18n.py
│   └── test_app.py             # Prueba de humo de la interfaz (AppTest)
└── datos_ejemplo/
    └── clientes_encuesta.csv   # 3.000 registros sintéticos para probar
```

La lógica estadística está separada de la interfaz para poder reutilizarla y
probarla sin Streamlit.

---

## Instalación y ejecución

Requisitos: **Python 3.9 o superior** (recomendado 3.10+) y `pip`.

### macOS / Linux

```bash
cd muestreo_estadistico
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

### Windows (PowerShell)

```powershell
cd muestreo_estadistico
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

La aplicación se abre en `http://localhost:8501`. Para detenerla: `Ctrl + C`.

> Si el puerto está ocupado:
> `streamlit run app.py --server.port 8502`

---

## Cómo usar la aplicación

1. **Tamaño de muestra.** Elija población finita o infinita, confianza, error y
   `p`. Revise el resultado, las fórmulas y la tabla de sensibilidad. Pulse
   **“Usar este tamaño en la selección”**.
2. **Margen real** (opcional, después del trabajo de campo). Indique la muestra
   planeada y la recolectada para ver el error efectivo.
3. **Base de datos.** Cargue su CSV/Excel o pulse **“Cargar datos de ejemplo”**
   para explorar con 3.000 clientes sintéticos.
4. **Selección.** Elija el método, ajuste `n`, la semilla y los parámetros
   propios del método. Pulse **“Seleccionar muestra”**.
5. **Visualización y descarga.** Compare la distribución de la muestra con la
   población y descargue el CSV o el Excel con el resumen metodológico.
6. **Análisis estadístico.** Describa variables numéricas, ajuste una regresión
   lineal múltiple o compare medias entre grupos con ANOVA. El idioma de la
   interfaz se elige en la barra lateral.

### Formato del archivo

- CSV (UTF-8 o Latin-1; separadores `,`, `;` o tabulador) o Excel `.xlsx`.
- Primera fila con nombres de columna; una fila por elemento de la población.
- Los decimales con coma (`1.250,50`) se detectan y convierten automáticamente.
- Para estratificar/conglomerar se necesitan columnas categóricas (región,
  sucursal, género, grupo de edad, etc.).

Ejemplo:

```csv
id_cliente,region,sucursal,genero,edad,ingreso_mensual
CL-00001,Centro,Sucursal Córdoba,Masculino,19,80000
CL-00002,Metropolitana,Sucursal Centro,Femenino,45,298900
```

---

## Metodología

**Tamaño de muestra (proporción, población infinita):**

```
n₀ = z² · p · q / e²
```

**Corrección por población finita:**

```
n = n₀ / (1 + (n₀ − 1) / N)
```

**Margen de error real:**

```
e = z · √(p·q / n)                         (población infinita)
e = z · √(p·q / n) · √((N − n)/(N − 1))    (población finita)
```

- `z` = 1,645 (90 %), 1,960 (95 %), 2,576 (99 %) o el valor manual ingresado.
- `p = q = 0,5` es el escenario más conservador (maximiza `p·q`).
- El resultado se redondea hacia arriba y nunca supera `N`.
- La confianza se mantiene fija al recalcular el margen real; lo que cambia es
  la precisión efectiva.

### Supuestos y límites

- La fórmula estima **una proporción**. Para medias se requiere la desviación
  estándar esperada y otra fórmula.
- Se asume muestreo aleatorio simple. En muestreo por conglomerados el margen
  calculado es una aproximación optimista (no incorpora el efecto de diseño).
- El archivo se trata como marco muestral completo; si ya es una muestra, la
  inferencia debe interpretarse con cautela.
- El margen de error no cubre sesgos de no respuesta, cobertura o medición.
- Los datos se procesan en memoria durante la sesión; no se envían a servicios
  externos.

### Análisis estadístico

**Regresión lineal múltiple (OLS):**

```
y = β₀ + β₁·x₁ + β₂·x₂ + … + ε
```

- Se estima por mínimos cuadrados ordinarios con `statsmodels`.
- Las variables categóricas se codifican como variables ficticias eliminando la
  primera categoría.
- Se informan `R²`, `R²` ajustado, `RMSE`, `F` global y, para cada coeficiente,
  error estándar, `t`, `p-valor` e intervalo de confianza al 95 %.

**ANOVA de un factor:**

```
F = MS_entre / MS_dentro        η² = SS_entre / SS_total
```

- Compara la media de una variable numérica entre dos o más grupos.
- Requiere al menos dos grupos y más observaciones que grupos.
- Un `p-valor < 0,05` indica diferencias estadísticamente significativas; `η²`
  cuantifica el tamaño del efecto.

> La significación estadística no implica relevancia práctica: interprete los
> resultados junto con el diseño del estudio y el tamaño del efecto.

---

## Pruebas

```bash
pip install -r requirements-dev.txt
pytest
```

Las pruebas cubren fórmulas, redondeo, corrección por población finita,
algoritmos de muestreo (tamaño exacto, unicidad, reproducibilidad, afijación),
lectura/exportación de archivos y una prueba de humo de la interfaz con
`streamlit.testing.v1.AppTest`.

---

## Despliegue en Vercel (Docker)

La aplicación puede desplegarse en Vercel usando el **Container Runtime** (requiere un `Dockerfile` en la raíz del proyecto):

```dockerfile
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=80
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 80
CMD ["sh", "-c", "streamlit run app.py --server.port ${PORT} --server.address 0.0.0.0 --server.headless true"]
```

Pasos:
1. Hacé commit y push de `Dockerfile`, `.dockerignore` y `vercel.json`.
2. En Vercel: **Settings → Framework Preset → Container**.
3. Deploy con `vercel deploy --prod` o push a `main`.

Alternativa recomendada para Streamlit: **Streamlit Community Cloud** (`share.streamlit.io`), que es el hosting nativo para Streamlit y no requiere Docker.

---

## Solución de problemas

| Problema | Solución |
|---|---|
| `streamlit: command not found` | Active el entorno virtual e instale `requirements.txt`. |
| Error al leer el CSV | Verifique encabezados y codificación; pruebe guardarlo como UTF-8. |
| No aparece el Excel | Use el CSV si la base es muy grande (Excel admite 1.048.576 filas por hoja). |
| El puerto 8501 está ocupado | `streamlit run app.py --server.port 8502`. |
| Cambié la base y no veo la muestra | Vuelva a generar la muestra: al cargar otra base se limpia el resultado anterior. |

---

## Tecnologías

Python 3.9+ · Streamlit · pandas · NumPy · SciPy · statsmodels · Plotly · openpyxl · pytest.
# An-lisis-de-campo
