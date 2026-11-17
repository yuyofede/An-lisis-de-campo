"""
Aplicación Streamlit para el diseño, cálculo y selección de muestras estadísticas.

Ejecutar con::

    streamlit run app.py

La lógica de cálculo vive en el paquete ``muestreo``; este archivo solo
orquesta la interfaz, el estado de la sesión y las exportaciones.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

from muestreo import datos as D
from muestreo import estadistica as E
from muestreo import graficos as G
from muestreo import i18n
from muestreo import muestreo as M

# ---------------------------------------------------------------------------
# Configuración general
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Diseño y selección de muestras",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

ESTILOS = """
<style>
  .block-container { padding-top: 1.2rem; padding-bottom: 3rem; }
  .hero {
    background: linear-gradient(135deg, #0f2a6b 0%, #1d4ed8 55%, #38bdf8 100%);
    padding: 1.4rem 1.7rem; border-radius: 18px; color: #fff;
    margin-bottom: 1.1rem; box-shadow: 0 10px 30px rgba(29, 78, 216, .18);
  }
  .hero h1 { font-size: 1.75rem; margin: 0 0 .35rem 0; color: #fff; line-height: 1.2; }
  .hero p { margin: 0; opacity: .92; font-size: .98rem; }
  div[data-testid="stMetric"] {
    background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px;
    padding: .7rem .9rem;
  }
  div[data-testid="stMetricValue"] { font-size: 1.55rem; }
  .nota { color: #475569; font-size: .87rem; }
  .chip {
    display: inline-block; background: #eff6ff; color: #1d4ed8;
    border: 1px solid #bfdbfe; border-radius: 999px;
    padding: .12rem .6rem; font-size: .78rem; margin-right: .3rem;
  }
  .stTabs [data-baseweb="tab-list"] { gap: .35rem; }
  .stTabs [data-baseweb="tab"] { padding: .45rem .85rem; }
</style>
"""
st.markdown(ESTILOS, unsafe_allow_html=True)

DESCRIPCION_METODOS = {
    "Aleatorio simple": "Sorteo puro: cada registro del marco tiene la misma probabilidad de ser elegido.",
    "Sistemático": "Se recorre el marco con un salto constante k = N/n a partir de un arranque aleatorio.",
    "Estratificado": "La población se divide en estratos y se sortea una muestra proporcional dentro de cada uno.",
    "Por conglomerados": "Se sortean grupos completos (sucursales, barrios, ciudades) y se censan todos sus registros.",
}

#: Claves de widgets que dependen de la base cargada. Se limpian al cambiarla.
CLAVES_DEPENDIENTES_BASE = [
    "n_seleccion",
    "t4_metodo",
    "t4_col_estr",
    "t4_col_cong",
    "t4_m",
    "t4_min_estrato",
    "t4_reemplazo",
    "t4_ordenar",
    "t4_auto",
    "t4_semilla",
    "t5_variable",
    "t5_nombre",
    "t5_estimacion",
]


# ---------------------------------------------------------------------------
# Utilidades de formato (convención española: 1.234,56)
# ---------------------------------------------------------------------------
def _decimal(valor: float, decimales: int = 2) -> str:
    texto = f"{float(valor):,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _entero(valor: float) -> str:
    return f"{int(round(float(valor))):,}".replace(",", ".")


def _pct(valor: float, decimales: int = 2) -> str:
    return f"{_decimal(valor * 100, decimales)} %"


def _nombre_archivo(texto: str) -> str:
    limpio = "".join(c if c.isalnum() or c in "-_ " else "" for c in texto).strip()
    return (limpio or "muestra").replace(" ", "_").lower()


# ---------------------------------------------------------------------------
# Estado de la sesión
# ---------------------------------------------------------------------------
def iniciar_estado() -> None:
    valores = {
        "df": None,
        "df_nombre": None,
        "df_meta": {},
        "resultado": None,
        "diseno": None,
        "n_sugerido": None,
        "uploader_ver": 0,
        "error_archivo": None,
        "t2_firma": None,
    }
    for clave, valor in valores.items():
        st.session_state.setdefault(clave, valor)


def limpiar_para_nueva_base() -> None:
    """Invalida resultados y controles que dependen de las columnas cargadas."""
    for clave in CLAVES_DEPENDIENTES_BASE:
        st.session_state.pop(clave, None)
    st.session_state["resultado"] = None
    st.session_state["t2_firma"] = None


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False, max_entries=6)
def _leer_cache(contenido: bytes, nombre: str):
    return D.leer_archivo(contenido, nombre)


def _al_cambiar_archivo(clave: str) -> None:
    archivo = st.session_state.get(clave)
    if archivo is None:
        return
    try:
        df, meta = _leer_cache(archivo.getvalue(), archivo.name)
    except Exception as exc:  # noqa: BLE001 - se informa en la interfaz
        st.session_state["error_archivo"] = str(exc)
        return

    limpiar_para_nueva_base()
    st.session_state["df"] = df
    st.session_state["df_nombre"] = archivo.name
    st.session_state["df_meta"] = meta
    st.session_state["error_archivo"] = None


def _cargar_ejemplo() -> None:
    df = D.generar_datos_ejemplo()
    limpiar_para_nueva_base()
    st.session_state["df"] = df
    st.session_state["df_nombre"] = "datos_ejemplo_sinteticos.csv"
    st.session_state["df_meta"] = {
        "nombre": "datos_ejemplo_sinteticos.csv",
        "formato": "Ejemplo",
        "filas": len(df),
        "columnas": df.shape[1],
    }
    st.session_state["uploader_ver"] += 1
    st.session_state["error_archivo"] = None


def _quitar_base() -> None:
    limpiar_para_nueva_base()
    st.session_state["df"] = None
    st.session_state["df_nombre"] = None
    st.session_state["df_meta"] = {}
    st.session_state["uploader_ver"] += 1


def _usar_n(n: int) -> None:
    st.session_state["n_seleccion"] = int(n)
    st.session_state["n_sugerido"] = int(n)


def _nueva_semilla() -> None:
    st.session_state["t4_semilla"] = M.generar_semilla()


# ---------------------------------------------------------------------------
# Encabezado
# ---------------------------------------------------------------------------
def encabezado() -> None:
    st.markdown(
        """
        <div class="hero">
          <h1>📊 Diseño y selección de muestras estadísticas</h1>
          <p>Calcule el tamaño de muestra, valide el margen de error real y seleccione
          muestras probabilísticas reproducibles desde su propia base de datos.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Barra lateral
# ---------------------------------------------------------------------------
def barra_lateral() -> None:
    with st.sidebar:
        idioma_selector = st.selectbox(
            "Idioma",
            list(i18n.ETIQUETAS_IDIOMA.keys()),
            format_func=lambda codigo: i18n.ETIQUETAS_IDIOMA[codigo],
            key="idioma_selector",
        )
        i18n.set_idioma(idioma_selector)
        st.markdown(f"### {i18n.t('panel')}")
        df = st.session_state.get("df")
        if df is not None:
            st.markdown(f"**{i18n.t('base')}:** `{st.session_state.get('df_nombre')}`")
            c1, c2 = st.columns(2)
            c1.metric("Registros", _entero(len(df)))
            c2.metric("Variables", _entero(len(df.columns)))
        else:
            st.caption(i18n.t("sin_base"))

        diseno = st.session_state.get("diseno")
        if diseno:
            st.divider()
            st.markdown(f"**{i18n.t('diseno_vigente')}**")
            st.write(
                f"Población: **{_entero(diseno['poblacion']) if diseno['poblacion'] else 'infinita'}**"
            )
            st.write(
                f"Confianza: **{_decimal(diseno['confianza'] * 100, 1)} %** "
                f"(Z = {_decimal(diseno['z'], 3)})"
            )
            st.write(f"Error: **±{_decimal(diseno['error'] * 100, 2)} %**")
            st.metric(i18n.t("muestra_necesaria"), _entero(diseno["n"]))

        resultado = st.session_state.get("resultado")
        if resultado is not None:
            st.divider()
            st.markdown(f"**{i18n.t('muestra_seleccionada')}**")
            st.write(f"{i18n.t('metodo')}: **{resultado.metodo}**")
            st.write(f"Registros: **{_entero(resultado.tamano_muestra)}**")
            if resultado.semilla is not None:
                st.caption(f"Semilla: {resultado.semilla}")

        st.divider()
        st.caption(
            "Los cálculos suponen muestreo aleatorio simple, porcentaje de "
            "respuesta completo y p = 0,5 cuando no se conoce la proporción."
        )


# ---------------------------------------------------------------------------
# Pestaña 1: tamaño de muestra
# ---------------------------------------------------------------------------
def tab_tamano() -> None:
    st.subheader(i18n.t("tamano_muestra"))
    st.caption(i18n.t("tamano_muestra_info"))

    diseno_anterior = st.session_state.get("diseno")

    izq, der = st.columns([1.05, 1], gap="large")

    with izq:
        tipo = st.radio(
            i18n.t("tipo_poblacion"),
            [i18n.t("finita"), i18n.t("infinita")],
            horizontal=True,
            key="t1_tipo",
        )
        poblacion: Optional[int] = None
        if tipo == i18n.t("finita"):
            poblacion = int(
                st.number_input(
                    "Tamaño de la población (N)",
                    min_value=2,
                    max_value=100_000_000,
                    value=10_000,
                    step=500,
                    key="t1_N",
                    help="Número total de elementos del marco muestral.",
                )
            )

        opcion_conf = st.selectbox(
            i18n.t("confianza"),
            [
                f"{i18n.t('conf_nivel_90')} %",
                f"{i18n.t('conf_nivel_95')} %",
                f"{i18n.t('conf_nivel_99')} %",
                i18n.t("conf_manual_z"),
            ],
            index=1,
            key="t1_conf",
        )
        z_manual: Optional[float] = None
        if opcion_conf == i18n.t("conf_manual_z"):
            z_manual = float(
                st.number_input(
                    "Valor Z (prueba de dos colas)",
                    min_value=0.50,
                    max_value=6.00,
                    value=1.96,
                    step=0.01,
                    format="%.3f",
                    key="t1_z",
                    help="Z = 1,645 (90 %), 1,960 (95 %), 2,576 (99 %).",
                )
            )
            confianza = E.confianza_para_z(z_manual)
        else:
            confianza = float(opcion_conf.replace(" %", "")) / 100.0

        error_pct = float(
            st.number_input(
                i18n.t("error_e"),
                min_value=0.1,
                max_value=50.0,
                value=5.0,
                step=0.5,
                format="%.2f",
                key="t1_error",
                help="Error absoluto máximo admisible para la proporción estimada.",
            )
        )

        p = float(
            st.slider(
                i18n.t("proporcion_esperada"),
                0.01,
                0.99,
                0.50,
                0.01,
                key="t1_p",
                help="Si no hay información previa, use 0,5 (escenario más conservador).",
            )
        )
        q = 1.0 - p
        st.caption(
            f"q = 1 − p = **{_decimal(q, 2)}**. Con p = q = 0,50 se obtiene el "
            "tamaño de muestra más grande posible."
        )

    try:
        res = E.calcular_tamano_muestra(
            poblacion=poblacion,
            error=error_pct / 100.0,
            confianza=confianza,
            z=z_manual,
            p=p,
            q=q,
        )
    except ValueError as exc:
        with der:
            st.error(f"Revise los parámetros: {exc}")
        return

    st.session_state["diseno"] = {
        "poblacion": res.poblacion,
        "confianza": res.confianza,
        "z": res.z,
        "p": res.p,
        "q": res.q,
        "error": res.error,
        "n": res.muestra,
        "n_infinita": res.n_infinita,
    }
    # Si el n de la selección seguía el diseño anterior, se actualiza solo.
    # Un n editado manualmente por el usuario se respeta.
    if (
        diseno_anterior
        and st.session_state.get("n_seleccion") == diseno_anterior.get("n")
        and st.session_state.get("n_seleccion") != res.muestra
    ):
        st.session_state["n_seleccion"] = res.muestra

    with der:
        st.metric(
            "Muestra necesaria (redondeada hacia arriba)",
            _entero(res.muestra),
            help="El resultado siempre se redondea con ⌈n⌉.",
        )
        c1, c2, c3 = st.columns(3)
        c1.metric("n (población infinita)", _decimal(res.n_infinita, 1))
        c2.metric("Factor de corrección", _decimal(res.factor_correccion, 3))
        c3.metric(
            "Fracción muestral",
            _pct(res.fraccion_muestral) if res.poblacion else "—",
        )

        with st.expander("Ver fórmulas y sustitución numérica", expanded=False):
            st.latex(
                r"n_0 = \frac{z^2 \cdot p \cdot q}{e^2} = "
                rf"\frac{{{_decimal(res.z, 3)}^2 \cdot {_decimal(res.p, 2)}"
                rf" \cdot {_decimal(res.q, 2)}}}{{{_decimal(res.error, 4)}^2}}"
                rf" = {_decimal(res.n_infinita, 2)}"
            )
            if res.poblacion:
                st.latex(
                    r"n = \frac{n_0}{1 + \frac{n_0 - 1}{N}} = "
                    rf"\frac{{{_decimal(res.n_infinita, 2)}}}"
                    rf"{{1 + \frac{{{_decimal(res.n_infinita, 2)} - 1}}"
                    rf"{{{_entero(res.poblacion)}}}}} = {_decimal(res.n_exacta, 2)}"
                )
                st.caption(
                    f"Se aplica corrección por población finita con N = {_entero(res.poblacion)}. "
                    f"El resultado se redondea hacia arriba: ⌈{_decimal(res.n_exacta, 2)}⌉ = "
                    f"**{_entero(res.muestra)}**."
                )
            else:
                st.caption(
                    f"Se asume población infinita o desconocida. El resultado se "
                    f"redondea hacia arriba: ⌈{_decimal(res.n_exacta, 2)}⌉ = "
                    f"**{_entero(res.muestra)}**."
                )

        st.button(
            "Usar este tamaño en la selección →",
            type="primary",
            width="stretch",
            on_click=_usar_n,
            args=(res.muestra,),
            disabled=st.session_state.get("df") is None,
            help="Guarda n y lo propone en la pestaña de selección. "
            "Requiere una base cargada.",
        )

        if res.poblacion and res.muestra >= res.poblacion:
            st.info(
                "La muestra calculada iguala el tamaño de la población: "
                "correspondería realizar un censo."
            )
        elif res.poblacion and res.fraccion_muestral > 0.10:
            st.info(
                "La muestra supera el 10 % de la población; la corrección por "
                "población finita reduce de forma apreciable el n requerido."
            )
        if abs(res.p - 0.5) > 1e-9:
            st.warning(
                "Con p distinto de 0,50 el cálculo deja de ser el escenario más "
                "conservador. Verifique que la proporción provenga de un estudio "
                "previo o de una prueba piloto."
            )

    st.divider()
    st.markdown("#### Sensibilidad del tamaño de muestra")
    st.caption(
        "Compare el costo de reducir el margen de error. Los valores usan el "
        "mismo nivel de confianza y las mismas proporciones del diseño."
    )
    filas = E.tabla_sensibilidad(
        poblacion=res.poblacion,
        confianza=res.confianza,
        p=res.p,
        q=res.q,
    )
    tabla = pd.DataFrame(
        {
            "Margen de error": [f"±{_decimal(f['margen_error'] * 100, 1)} %" for f in filas],
            "Muestra requerida": [int(f["muestra"]) for f in filas],
            "% de la población": [
                _pct(f["fraccion_muestral"]) if res.poblacion else "—" for f in filas
            ],
        }
    )
    st.dataframe(tabla, hide_index=True, width="stretch")


# ---------------------------------------------------------------------------
# Pestaña 2: margen de error real
# ---------------------------------------------------------------------------
def _sincronizar_inverso(diseno: Optional[Dict[str, Any]]) -> None:
    """Reinicia los valores de la calculadora cuando cambia el diseño."""
    if not diseno:
        st.session_state.setdefault("t2_plan", 384)
        st.session_state.setdefault("t2_real", 384)
        st.session_state.setdefault("t2_tipo", "Infinita o desconocida")
        st.session_state.setdefault("t2_conf", "95 %")
        st.session_state.setdefault("t2_p", 0.5)
        return

    firma = (
        diseno.get("n"),
        diseno.get("poblacion"),
        round(float(diseno.get("confianza", 0)), 6),
        round(float(diseno.get("p", 0)), 6),
        round(float(diseno.get("error", 0)), 6),
    )
    if st.session_state.get("t2_firma") == firma:
        return

    st.session_state["t2_firma"] = firma
    st.session_state["t2_plan"] = int(diseno["n"])
    st.session_state["t2_real"] = int(diseno["n"])
    st.session_state["t2_tipo"] = (
        "Finita (N conocida)" if diseno.get("poblacion") else "Infinita o desconocida"
    )
    st.session_state["t2_conf"] = "Mantener la del diseño"
    st.session_state["t2_p"] = round(float(diseno.get("p", 0.5)), 2)
    if diseno.get("poblacion"):
        st.session_state["t2_N"] = int(diseno["poblacion"])


def tab_margen_real() -> None:
    st.subheader("Margen de error real")
    st.caption(
        "¿Ya recolectó los datos? Compare la muestra planeada con la lograda y "
        "recalcule el margen de error efectivo manteniendo la confianza original."
    )

    diseno = st.session_state.get("diseno")
    _sincronizar_inverso(diseno)

    izq, der = st.columns([1.05, 1], gap="large")

    with izq:
        tipo2 = st.radio(
            "Tipo de población",
            ["Finita (N conocida)", "Infinita o desconocida"],
            horizontal=True,
            key="t2_tipo",
        )
        poblacion2: Optional[int] = None
        if tipo2.startswith("Finita"):
            poblacion2 = int(
                st.number_input(
                    "Tamaño de la población (N)",
                    min_value=2,
                    max_value=100_000_000,
                    value=10_000,
                    step=500,
                    key="t2_N",
                )
            )

        opcion_conf2 = st.selectbox(
            "Nivel de confianza",
            ["Mantener la del diseño", "90 %", "95 %", "99 %"],
            key="t2_conf",
            help="El margen real se recalcula conservando la confianza del diseño.",
        )
        z2: Optional[float] = None
        if opcion_conf2 == "Mantener la del diseño":
            if diseno:
                confianza2 = float(diseno["confianza"])
                z2 = float(diseno["z"])
            else:
                confianza2 = 0.95
        else:
            confianza2 = float(opcion_conf2.replace(" %", "")) / 100.0

        p2 = float(
            st.number_input(
                "Proporción esperada (p)",
                min_value=0.01,
                max_value=0.99,
                value=0.50,
                step=0.01,
                format="%.2f",
                key="t2_p",
                help="Use la misma proporción del diseño para comparar manzanas con manzanas.",
            )
        )

        max_muestra = poblacion2 if poblacion2 else 100_000_000
        for clave in ("t2_plan", "t2_real"):
            if st.session_state.get(clave, 1) > max_muestra:
                st.session_state[clave] = max_muestra
            if st.session_state.get(clave, 1) < 1:
                st.session_state[clave] = 1

        plan = int(
            st.number_input(
                "Muestra planeada (n)",
                min_value=1,
                max_value=max_muestra,
                value=384,
                step=1,
                key="t2_plan",
            )
        )
        real = int(
            st.number_input(
                "Muestra realmente recolectada (m)",
                min_value=1,
                max_value=max_muestra,
                value=384,
                step=1,
                key="t2_real",
            )
        )

    try:
        comp = E.comparar_muestras(
            muestra_planeada=plan,
            muestra_real=real,
            poblacion=poblacion2,
            confianza=confianza2,
            z=z2,
            p=p2,
            q=1.0 - p2,
        )
    except ValueError as exc:
        with der:
            st.error(f"Revise los datos: {exc}")
        return

    with der:
        c1, c2 = st.columns(2)
        c1.metric(
            "Error planeado",
            f"±{_decimal(comp.error_planeado * 100, 2)} %",
            help=f"Con n = {_entero(comp.muestra_planeada)} registros.",
        )
        c2.metric(
            "Error real",
            f"±{_decimal(comp.error_real * 100, 2)} %",
            delta=f"{comp.diferencia_error * 100:+.2f} pp",
            delta_color="inverse",
            help=f"Con m = {_entero(comp.muestra_real)} registros recolectados.",
        )

        st.progress(
            min(1.0, comp.logro_muestra),
            text=f"Muestra lograda: {_pct(comp.logro_muestra, 1)} del plan "
            f"({_entero(comp.muestra_real)} de {_entero(comp.muestra_planeada)})",
        )

        if comp.muestra_real >= comp.muestra_planeada:
            st.success(
                "La muestra recolectada alcanza o supera el plan: el margen de "
                "error es igual o menor al diseñado."
            )
        else:
            st.warning(
                f"Faltan **{_entero(comp.muestra_faltante)} registros** para cumplir "
                f"el plan. El margen de error aumentó en "
                f"**{_decimal(comp.diferencia_error * 100, 2)} puntos porcentuales**."
            )

        z_usado = z2 if z2 is not None else E.z_para_confianza(confianza2)
        st.caption(
            f"Confianza original: **{_decimal(confianza2 * 100, 2)} %** · "
            f"Z = {_decimal(z_usado, 3)} · "
            f"Confianza que alcanza el error planeado con la muestra real: "
            f"**{_decimal(comp.confianza_real * 100, 2)} %**."
        )

        st.info(
            "Interpretación: si la muestra real es menor que la planeada, el "
            "resultado sigue siendo válido pero con menor precisión. El intervalo "
            "de confianza se amplía alrededor de la proporción estimada.",
            icon="ℹ️",
        )

    st.divider()
    col_izq, col_der = st.columns([1.25, 1])
    with col_izq:
        fig = G.grafico_margen_error(
            muestra_planeada=comp.muestra_planeada,
            muestra_real=comp.muestra_real,
            poblacion=poblacion2,
            confianza=confianza2,
            z=z2,
            p=p2,
        )
        st.plotly_chart(fig, use_container_width=True)
    with col_der:
        st.markdown("#### Comparación del diseño")
        detalle = pd.DataFrame(
            {
                "Concepto": [
                    "Muestra planeada",
                    "Muestra recolectada",
                    "Margen planeado",
                    "Margen real",
                    "Diferencia",
                    "Confianza original",
                    "Registros faltantes",
                ],
                "Valor": [
                    _entero(comp.muestra_planeada),
                    _entero(comp.muestra_real),
                    f"±{_decimal(comp.error_planeado * 100, 2)} %",
                    f"±{_decimal(comp.error_real * 100, 2)} %",
                    f"{comp.diferencia_error * 100:+.2f} pp",
                    _decimal(confianza2 * 100, 1) + " %",
                    _entero(comp.muestra_faltante),
                ],
            }
        )
        st.dataframe(detalle, hide_index=True, width="stretch")
        st.caption(
            "Fórmula: e = Z · √(p·q/n) para población infinita y "
            "e = Z · √(p·q/n) · √((N−n)/(N−1)) para población finita."
        )


# ---------------------------------------------------------------------------
# Pestaña 3: base de datos
# ---------------------------------------------------------------------------
def tab_base() -> None:
    st.subheader("Base de datos (marco muestral)")
    st.caption(
        "Cargue un CSV o Excel con una fila por elemento de la población. "
        "También puede explorar la aplicación con datos sintéticos."
    )

    izq, der = st.columns([1.1, 1], gap="large")

    with izq:
        clave_uploader = f"uploader_{st.session_state['uploader_ver']}"
        st.file_uploader(
            "Archivo de datos",
            type=["csv", "txt", "xlsx", "xlsm"],
            key=clave_uploader,
            on_change=_al_cambiar_archivo,
            args=(clave_uploader,),
            help="CSV (UTF-8 o Latin-1, separador , ; o tabulador) o Excel .xlsx.",
        )
        c1, c2 = st.columns(2)
        c1.button(
            "Cargar datos de ejemplo",
            width="stretch",
            on_click=_cargar_ejemplo,
            help="Genera 3.000 clientes sintéticos con región, sucursal, edad y más.",
        )
        c2.button(
            "Quitar base",
            width="stretch",
            on_click=_quitar_base,
            disabled=st.session_state.get("df") is None,
        )

        if st.session_state.get("error_archivo"):
            st.error(st.session_state["error_archivo"])
            st.session_state["error_archivo"] = None

        st.markdown(
            '<p class="nota">Formatos admitidos: <b>.csv</b>, <b>.txt</b> y '
            "<b>.xlsx</b>. La primera fila debe contener los nombres de las "
            "columnas. Los encabezados vacíos se descartan automáticamente.</p>",
            unsafe_allow_html=True,
        )

    df = st.session_state.get("df")
    with der:
        if df is None:
            st.info(
                "Cargue un archivo o use los datos de ejemplo para habilitar la "
                "selección de muestras."
            )
        else:
            st.success(
                f"Base activa: **{st.session_state.get('df_nombre')}** "
                f"({st.session_state.get('df_meta', {}).get('formato', '—')})"
            )
            c1, c2, c3 = st.columns(3)
            c1.metric("Registros (N)", _entero(len(df)))
            c2.metric("Variables", _entero(df.shape[1]))
            c3.metric(
                "Faltantes",
                _pct(float(df.isna().to_numpy().mean()), 2) if len(df) else "—",
            )
            num = len(D.columnas_numericas(df))
            st.caption(
                f"{num} variable(s) numérica(s) y {df.shape[1] - num} no numérica(s). "
                "Los valores faltantes se informan en el perfil de columnas."
            )

    if df is None:
        return

    st.divider()
    vista, perfil = st.tabs(["Vista previa", "Perfil de columnas"])

    with vista:
        st.caption(
            f"Mostrando las primeras 10 filas de {_entero(len(df))}. Al generar "
            "una muestra se agrega `id_marco`, que identifica la posición de cada "
            "registro en el marco muestral."
        )
        st.dataframe(df.head(10), hide_index=True, width="stretch")

    with perfil:
        tabla_perfil = D.perfil_columnas(df)
        st.dataframe(tabla_perfil, hide_index=True, width="stretch")
        criticas = tabla_perfil[tabla_perfil["% faltantes"] > 20]
        if not criticas.empty:
            st.warning(
                "Estas columnas superan el 20 % de valores faltantes y podrían no "
                "ser confiables para estratificar: "
                + ", ".join(f"`{c}`" for c in criticas["columna"])
            )


# ---------------------------------------------------------------------------
# Pestaña 4: selección de la muestra
# ---------------------------------------------------------------------------
def _opciones_agrupacion(df: pd.DataFrame) -> list:
    """Columnas razonables para estratificar o conglomerar."""
    return [
        c
        for c in D.columnas_categoricas(df, max_unicos=60)
        if c != "id_marco" and df[c].nunique(dropna=True) >= 2
    ]


def _tabla_conteos(df: pd.DataFrame, columna: str) -> pd.DataFrame:
    conteos = (
        df[columna]
        .dropna()
        .map(lambda v: str(v))
        .value_counts()
        .rename_axis("Grupo")
        .reset_index(name="Registros")
    )
    return conteos


def tab_seleccion() -> None:
    st.subheader("Selección de la muestra")
    df = st.session_state.get("df")
    if df is None:
        st.info("Primero cargue una base de datos en la pestaña **Base de datos**.")
        return

    N = len(df)
    diseno = st.session_state.get("diseno")
    n_sugerido = st.session_state.get("n_seleccion")
    if n_sugerido is None:
        n_sugerido = int((diseno or {}).get("n", min(384, N)))
    n_sugerido = int(max(1, min(int(n_sugerido), N)))
    if st.session_state.get("n_seleccion") != n_sugerido:
        st.session_state["n_seleccion"] = n_sugerido

    with st.container(border=True):
        c1, c2, c3 = st.columns([1, 1.4, 1.1])
        with c1:
            n = int(
                st.number_input(
                    "Tamaño de la muestra (n)",
                    min_value=1,
                    max_value=N,
                    step=1,
                    key="n_seleccion",
                    help="Se propone el n calculado en la pestaña de diseño.",
                )
            )
        with c2:
            metodo = st.selectbox(
                "Método de muestreo",
                list(DESCRIPCION_METODOS.keys()),
                key="t4_metodo",
            )
            st.caption(DESCRIPCION_METODOS[metodo])
        with c3:
            automatica = st.checkbox(
                "Semilla automática",
                key="t4_auto",
                help="Si se desactiva, puede fijar una semilla para reproducir el sorteo.",
            )
            semilla: Optional[int] = None
            if automatica:
                st.caption("Cada sorteo será distinto (no reproducible).")
            else:
                if "t4_semilla" not in st.session_state:
                    st.session_state["t4_semilla"] = 2024
                semilla = int(
                    st.number_input(
                        "Semilla",
                        min_value=0,
                        max_value=2**32 - 1,
                        step=1,
                        key="t4_semilla",
                    )
                )
                st.button("Generar otra semilla", on_click=_nueva_semilla)

    if diseno and diseno.get("poblacion") and int(diseno["poblacion"]) != N:
        st.caption(
            f"Nota: el diseño usa N = {_entero(diseno['poblacion'])} y el marco "
            f"cargado tiene {_entero(N)} registros. Puede ajustar N en la pestaña "
            "**Tamaño de muestra** si corresponde."
        )

    reemplazo = False
    ordenar_marco = False
    col_estrat: Optional[str] = None
    col_congl: Optional[str] = None
    minimo_estrato = 1
    m_conglomerados = 1
    # El identificador de marco se agrega recién al muestrear para no ensuciar
    # la base original del usuario.
    marco_base = D.preparar_exportacion(df)
    marco = marco_base

    opciones = _opciones_agrupacion(df)

    with st.container(border=True):
        if metodo == "Aleatorio simple":
            st.markdown("**Parámetros del muestreo aleatorio simple**")
            reemplazo = st.checkbox(
                "Permitir duplicados (muestreo con reemplazo)",
                key="t4_reemplazo",
                help="Sin reemplazo, cada registro puede seleccionarse una sola vez.",
            )
            st.caption(
                f"Se sortearán {_entero(n)} registros de {_entero(N)}. "
                "Cada elemento tiene idéntica probabilidad de selección."
            )

        elif metodo == "Sistemático":
            k = N / n
            st.markdown("**Parámetros del muestreo sistemático**")
            ordenar_marco = st.checkbox(
                "Aleatorizar el orden del marco antes del sorteo",
                key="t4_ordenar",
                help="Recomendado si el archivo está ordenado por una variable "
                "relacionada con el estudio.",
            )
            st.caption(
                f"Intervalo de salto k = N/n = {_entero(N)}/{_entero(n)} = "
                f"**{_decimal(k, 3)}**. Se elegirá un arranque aleatorio entre 1 y k."
            )

        elif metodo == "Estratificado":
            st.markdown("**Parámetros del muestreo estratificado**")
            if not opciones:
                st.warning(
                    "No se detectaron columnas categóricas aptas para estratificar. "
                    "Cargue una base con variables como región, género o sucursal."
                )
            else:
                col_estrat = st.selectbox(
                    "Columna de estratificación",
                    opciones,
                    key="t4_col_estr",
                    help="Variables con pocos valores distintos (idealmente menos de 30).",
                )
                n_estratos = int(df[col_estrat].nunique(dropna=True))
                max_minimo = max(0, min(5, n // max(n_estratos, 1)))
                if st.session_state.get("t4_min_estrato", 1) > max_minimo:
                    st.session_state["t4_min_estrato"] = max_minimo
                minimo_estrato = int(
                    st.number_input(
                        "Mínimo de registros por estrato",
                        min_value=0,
                        max_value=max(1, max_minimo),
                        step=1,
                        key="t4_min_estrato",
                        help="Garantiza representación de estratos pequeños. "
                        "Use 0 para proporcionalidad estricta.",
                    )
                )
                conteos = df[col_estrat].dropna().map(lambda v: str(v)).value_counts()
                with st.expander(
                    f"Ver los {n_estratos} estratos y la afijación prevista",
                    expanded=False,
                ):
                    st.dataframe(
                        _tabla_conteos(df, col_estrat),
                        hide_index=True,
                        width="stretch",
                    )
                    try:
                        previa = M.afijacion_proporcional(
                            conteos, n, minimo_por_estrato=minimo_estrato
                        )
                        previa = previa.rename(
                            columns={
                                "estrato": "Estrato",
                                "N_h": "Población (N_h)",
                                "cuota": "Cuota exacta",
                                "n_h": "Muestra (n_h)",
                                "fraccion": "Fracción",
                                "peso": "Peso (N_h/n_h)",
                            }
                        )
                        st.markdown("**Afijación proporcional por estrato**")
                        st.dataframe(
                            previa,
                            hide_index=True,
                            width="stretch",
                            column_config={
                                "Cuota exacta": st.column_config.NumberColumn(format="%.2f"),
                                "Fracción": st.column_config.NumberColumn(format="%.3f"),
                                "Peso (N_h/n_h)": st.column_config.NumberColumn(format="%.2f"),
                            },
                        )
                    except ValueError as exc:
                        st.warning(str(exc))
                st.caption(
                    "La afijación es proporcional al tamaño de cada estrato, con "
                    "reparto por restos mayores para sumar exactamente n."
                )

        else:  # Por conglomerados
            st.markdown("**Parámetros del muestreo por conglomerados**")
            if not opciones:
                st.warning(
                    "No se detectaron columnas aptas para conglomerar. Cargue una "
                    "base con variables como sucursal, barrio o ciudad."
                )
            else:
                col_congl = st.selectbox(
                    "Columna de conglomeración",
                    opciones,
                    key="t4_col_cong",
                )
                grupos = df[col_congl].dropna().map(lambda v: str(v)).unique()
                n_grupos = len(grupos)
                sugerido = M.conglomerados_sugeridos(df, col_congl, n)
                if st.session_state.get("t4_m", sugerido) > n_grupos:
                    st.session_state["t4_m"] = n_grupos
                if st.session_state.get("t4_m", sugerido) < 1:
                    st.session_state["t4_m"] = 1
                m_conglomerados = int(
                    st.slider(
                        "Conglomerados a sortear",
                        min_value=1,
                        max_value=max(1, n_grupos),
                        value=int(max(1, min(sugerido, n_grupos))),
                        step=1,
                        key="t4_m",
                        help="Se incluirán todos los registros de los grupos elegidos.",
                    )
                )
                tam = df[col_congl].dropna().map(lambda v: str(v)).value_counts()
                st.caption(
                    f"{_entero(n_grupos)} conglomerados disponibles, con un tamaño "
                    f"medio de {_decimal(tam.mean(), 1)} registros. Con "
                    f"{_entero(m_conglomerados)} conglomerado(s) se esperan "
                    f"≈ {_entero(m_conglomerados * tam.mean())} registros "
                    f"(rango aproximado {_entero(tam.nsmallest(m_conglomerados).sum())} "
                    f"a {_entero(tam.nlargest(m_conglomerados).sum())})."
                )
                with st.expander("Ver tamaño de los conglomerados", expanded=False):
                    st.dataframe(
                        _tabla_conteos(df, col_congl), hide_index=True, width="stretch"
                    )

    if st.button("Seleccionar muestra", type="primary", width="stretch"):
        try:
            if metodo == "Aleatorio simple":
                resultado = M.aleatorio_simple(
                    marco_base, n, semilla=semilla, reemplazo=reemplazo
                )
            elif metodo == "Sistemático":
                marco = marco_base
                semilla_efectiva = semilla
                if ordenar_marco:
                    if semilla_efectiva is None:
                        semilla_efectiva = M.generar_semilla()
                    marco = marco_base.sample(
                        frac=1.0, random_state=int(semilla_efectiva) % (2**32)
                    )
                resultado = M.sistematico(marco, n, semilla=semilla_efectiva)
                resultado.detalles["orden_marco_aleatorizado"] = bool(ordenar_marco)
            elif metodo == "Estratificado":
                if col_estrat is None:
                    raise ValueError("Seleccione una columna de estratificación.")
                resultado = M.estratificado(
                    marco_base,
                    n,
                    columna=col_estrat,
                    semilla=semilla,
                    minimo_por_estrato=minimo_estrato,
                )
            else:
                if col_congl is None:
                    raise ValueError("Seleccione una columna de conglomeración.")
                resultado = M.conglomerados(
                    marco_base, col_congl, num_conglomerados=m_conglomerados, semilla=semilla
                )
        except ValueError as exc:
            st.error(f"No se pudo seleccionar la muestra: {exc}")
        else:
            st.session_state["resultado"] = resultado
            st.toast("Muestra seleccionada correctamente.", icon="✅")

    resultado = st.session_state.get("resultado")
    if resultado is None:
        return

    st.divider()
    st.markdown("#### Muestra generada")
    if resultado.metodo != metodo:
        st.info(
            f"La muestra guardada corresponde al método **{resultado.metodo}**. "
            f"Pulse **Seleccionar muestra** para generarla con el método actual "
            f"({metodo})."
        )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Método", resultado.metodo)
    c2.metric("Registros seleccionados", _entero(resultado.tamano_muestra))
    c3.metric("Fracción del marco", _pct(resultado.fraccion_muestral, 2))
    c4.metric(
        "Semilla",
        _entero(resultado.semilla) if resultado.semilla is not None else "automática",
    )

    excluidas = int(resultado.detalles.get("filas_excluidas", 0))
    if excluidas:
        st.warning(
            f"Se excluyeron {_entero(excluidas)} registros con valor faltante en la "
            "columna de agrupación. La muestra se extrajo del marco restante."
        )

    if resultado.metodo == "Estratificado":
        afijacion = resultado.detalles.get("afijacion")
        if isinstance(afijacion, pd.DataFrame):
            tabla = afijacion.rename(
                columns={
                    "estrato": "Estrato",
                    "N_h": "Población (N_h)",
                    "cuota": "Cuota exacta",
                    "n_h": "Muestra (n_h)",
                    "fraccion": "Fracción",
                    "peso": "Peso (N_h/n_h)",
                }
            )
            st.markdown("**Afijación ejecutada**")
            st.dataframe(
                tabla,
                hide_index=True,
                width="stretch",
                column_config={
                    "Cuota exacta": st.column_config.NumberColumn(format="%.2f"),
                    "Fracción": st.column_config.NumberColumn(format="%.3f"),
                    "Peso (N_h/n_h)": st.column_config.NumberColumn(format="%.2f"),
                },
            )
            st.plotly_chart(G.grafico_afijacion(afijacion), use_container_width=True)

    if resultado.metodo == "Sistemático":
        d = resultado.detalles
        c1, c2, c3 = st.columns(3)
        c1.metric("Intervalo k", _decimal(d.get("intervalo_k", 0), 3))
        c2.metric("Arranque", _decimal(d.get("arranque", 0), 2))
        c3.metric("Orden del marco", "aleatorizado" if d.get("orden_marco_aleatorizado") else "original")
        with st.expander("Ver posiciones sorteadas en el marco", expanded=False):
            st.write(
                ", ".join(str(p) for p in d.get("posiciones_marco", [])[:200])
                + ("…" if len(d.get("posiciones_marco", [])) > 200 else "")
            )

    if resultado.metodo == "Por conglomerados":
        seleccionados = resultado.detalles.get("conglomerados_seleccionados", [])
        st.markdown(
            "**Conglomerados sorteados:** "
            + ", ".join(f"`{c}`" for c in seleccionados)
        )

    with st.expander("Vista previa de los registros seleccionados", expanded=False):
        st.dataframe(resultado.datos.head(20), hide_index=True, width="stretch")

    st.caption(
        "La muestra quedó guardada. Continúe en la pestaña **Visualización y "
        "descarga** para comparar distribuciones y exportar los resultados."
    )


# ---------------------------------------------------------------------------
# Pestaña 5: visualización y descarga
# ---------------------------------------------------------------------------
def _resumen_exportacion(resultado: M.ResultadoMuestreo) -> pd.DataFrame:
    diseno = st.session_state.get("diseno") or {}
    parametros: Dict[str, Any] = {
        "Método de muestreo": resultado.metodo,
        "Población (N)": diseno.get("poblacion") or "Infinita / desconocida",
        "Nivel de confianza": (
            f"{_decimal(diseno['confianza'] * 100, 2)} %" if diseno else "—"
        ),
        "Valor Z": round(float(diseno["z"]), 4) if diseno else "—",
        "p (proporción esperada)": round(float(diseno["p"]), 4) if diseno else "—",
        "q = 1 - p": round(float(diseno["q"]), 4) if diseno else "—",
        "Margen de error planificado": (
            f"±{_decimal(diseno['error'] * 100, 2)} %" if diseno else "—"
        ),
        "Tamaño de muestra calculado": diseno.get("n", "—"),
    }

    detalles: Dict[str, Any] = {
        "Registros en el marco": resultado.tamano_marco,
        "Registros seleccionados": resultado.tamano_muestra,
        "Fracción muestral": _pct(resultado.fraccion_muestral, 2),
        "Semilla": (
            resultado.semilla if resultado.semilla is not None else "automática"
        ),
    }
    d = resultado.detalles
    if "reemplazo" in d:
        detalles["Muestreo con reemplazo"] = "Sí" if d["reemplazo"] else "No"
    if "intervalo_k" in d:
        detalles["Intervalo k = N/n"] = round(float(d["intervalo_k"]), 4)
        detalles["Arranque aleatorio"] = round(float(d["arranque"]), 4)
        detalles["Orden del marco"] = (
            "aleatorizado" if d.get("orden_marco_aleatorizado") else "original"
        )
    if "columna_estratificacion" in d:
        detalles["Columna de estratificación"] = d["columna_estratificacion"]
        detalles["Número de estratos"] = d.get("num_estratos")
        detalles["Mínimo por estrato"] = d.get("minimo_por_estrato")
    if "columna_conglomeracion" in d:
        detalles["Columna de conglomeración"] = d["columna_conglomeracion"]
        detalles["Conglomerados disponibles"] = len(d.get("conglomerados_disponibles", []))
        detalles["Conglomerados sorteados"] = list(d.get("conglomerados_seleccionados", []))
    if d.get("filas_excluidas"):
        detalles["Filas excluidas por valores faltantes"] = d["filas_excluidas"]

    return D.resumen_exportacion(parametros, detalles)


@st.cache_data(show_spinner=False, max_entries=8)
def _excel_cache(
    muestra: pd.DataFrame,
    resumen: pd.DataFrame,
    afijacion: Optional[pd.DataFrame] = None,
    conglomerados: Optional[pd.DataFrame] = None,
) -> bytes:
    hojas: Dict[str, pd.DataFrame] = {"Muestra": muestra}
    if afijacion is not None:
        hojas["Afijación"] = afijacion
    if conglomerados is not None:
        hojas["Conglomerados"] = conglomerados
    return D.a_excel_bytes(hojas, resumen=resumen)


def tab_resultados() -> None:
    st.subheader("Visualización y descarga")
    resultado = st.session_state.get("resultado")
    df = st.session_state.get("df")

    if resultado is None or df is None:
        st.info(
            "Genere una muestra en la pestaña **Selección de la muestra** para ver "
            "aquí la comparación con la población y descargar los registros."
        )
        return

    st.caption(
        f"Muestra del método **{resultado.metodo}** con "
        f"{_entero(resultado.tamano_muestra)} registros sobre un marco de "
        f"{_entero(resultado.tamano_marco)} "
        f"({_pct(resultado.fraccion_muestral, 2)})."
    )

    opciones = [c for c in df.columns if c != "id_marco"]
    if not opciones:
        st.error("La base no tiene variables para graficar.")
        return

    predeterminada = next(
        (
            c
            for c in opciones
            if 2 <= df[c].nunique(dropna=True) <= 15 and c != "id_cliente"
        ),
        opciones[0],
    )
    if st.session_state.get("t5_variable") not in opciones:
        st.session_state["t5_variable"] = predeterminada

    col_var = st.selectbox(
        "Variable para comparar población vs muestra",
        opciones,
        key="t5_variable",
        help="Puede elegir una variable numérica (histograma) o categórica (barras).",
    )

    st.plotly_chart(
        G.grafico_distribucion(df, resultado.datos, col_var),
        use_container_width=True,
    )

    grupo: Optional[str] = None
    if resultado.metodo == "Estratificado":
        grupo = resultado.detalles.get("columna_estratificacion")
    elif resultado.metodo == "Por conglomerados":
        grupo = resultado.detalles.get("columna_conglomeracion")
    if grupo:
        st.plotly_chart(
            G.grafico_grupos(df, resultado.datos, grupo),
            use_container_width=True,
        )

    with st.expander("Tabla comparativa de indicadores", expanded=False):
        tabla = G.tabla_comparacion(df, resultado.datos, col_var)
        st.dataframe(tabla, hide_index=True, width="stretch")
        if "Registros" in tabla.get("Indicador", pd.Series(dtype=str)).values:
            st.caption(
                "Los indicadores de la muestra permiten anticipar posibles sesgos "
                "de selección. En un muestreo probabilístico bien ejecutado, las "
                "diferencias deben ser compatibles con el azar."
            )

    # ------------------------------------------------------------------
    # Estimación puntual y su intervalo de confianza
    # ------------------------------------------------------------------
    with st.expander(f"**{i18n.t('estimacion_ic')}**", expanded=False):
        binarias = [
            c
            for c in df.columns
            if c != "id_marco" and D.es_proporcion_binaria(df[c])
        ]
        if not binarias:
            st.caption(
                "No se detectó una variable binaria (valores 0/1) en la base; no "
                "es posible calcular una estimación de proporción."
            )
        else:
            col_est = st.selectbox(
                i18n.t("variable_binaria"),
                binarias,
                key="t5_estimacion",
                help="Variable binaria usada para estimar la proporción de éxito.",
            )
            n_est = int(len(resultado.datos))
            exitos_est = (
                int(resultado.datos[col_est].fillna(0).sum())
                if col_est in resultado.datos.columns
                else 0
            )
            diseno_actual = st.session_state.get("diseno") or {}
            res_est = E.estimar_proporcion(
                n=n_est,
                exitos=exitos_est,
                poblacion=diseno_actual.get("poblacion"),
                confianza=float(diseno_actual.get("confianza") or 0.95),
                z=float(diseno_actual.get("z") or 0.0) or None,
            )

            c1, c2, c3, c4 = st.columns(4)
            c1.metric(i18n.t("estimacion_puntual"), _pct(res_est.proporcion))
            c2.metric(i18n.t("error"), _pct(res_est.error))
            c3.metric("Límite inferior", _pct(res_est.intervalo_inferior))
            c4.metric("Límite superior", _pct(res_est.intervalo_superior))

            st.caption(
                f"Estimación: **{_pct(res_est.proporcion)}** ± **{_pct(res_est.error)}** "
                f"→ Intervalo de confianza al "
                f"**{_decimal(res_est.nivel_confianza * 100, 2)} %** "
                f"(Z = {_decimal(res_est.z, 3)}): "
                f"**[{_pct(res_est.intervalo_inferior)}, {_pct(res_est.intervalo_superior)}]**"
            )
            st.info(
                "Se presenta la estimación puntual junto con su intervalo de "
                "confianza para no comunicar una precisión excesiva. El intervalo "
                "se construye con el margen de error calculado manteniendo el nivel "
                "de confianza del diseño."
            )

    st.divider()
    st.markdown("#### Descargar la muestra")

    muestra_exp = D.preparar_exportacion(resultado.datos)
    resumen = _resumen_exportacion(resultado)

    afijacion = resultado.detalles.get("afijacion")
    afijacion_exp: Optional[pd.DataFrame] = None
    if isinstance(afijacion, pd.DataFrame):
        afijacion_exp = afijacion.rename(
            columns={
                "estrato": "Estrato",
                "N_h": "Población (N_h)",
                "cuota": "Cuota exacta",
                "n_h": "Muestra (n_h)",
                "fraccion": "Fracción",
                "peso": "Peso (N_h/n_h)",
            }
        )

    conglomerados_exp: Optional[pd.DataFrame] = None
    tamanos = resultado.detalles.get("tamanos_conglomerados")
    if isinstance(tamanos, pd.DataFrame):
        seleccionados = set(resultado.detalles.get("conglomerados_seleccionados", []))
        conglomerados_exp = tamanos.copy()
        conglomerados_exp["Seleccionado"] = conglomerados_exp["conglomerado"].isin(
            seleccionados
        )
        conglomerados_exp = conglomerados_exp.rename(
            columns={"conglomerado": "Conglomerado", "registros": "Registros"}
        )

    c1, c2 = st.columns([1, 1])
    with c1:
        nombre = st.text_input(
            "Nombre del archivo (sin extensión)",
            value=f"muestra_{_nombre_archivo(resultado.metodo)}",
            key="t5_nombre",
        )
    with c2:
        st.caption(
            "El Excel incluye una hoja **Resumen** con los parámetros del diseño"
            + (", la afijación por estrato" if afijacion_exp is not None else "")
            + (", el detalle de conglomerados" if conglomerados_exp is not None else "")
            + "."
        )

    nombre = _nombre_archivo(nombre)
    csv_bytes = D.a_csv_bytes(muestra_exp)
    try:
        excel_bytes = _excel_cache(muestra_exp, resumen, afijacion_exp, conglomerados_exp)
        error_excel = None
    except Exception as exc:  # noqa: BLE001 - se informa y se mantiene el CSV
        excel_bytes = None
        error_excel = str(exc)

    d1, d2 = st.columns(2)
    with d1:
        st.download_button(
            "⬇️ Descargar CSV",
            data=csv_bytes,
            file_name=f"{nombre}.csv",
            mime="text/csv",
            width="stretch",
        )
    with d2:
        if excel_bytes is not None:
            st.download_button(
                "⬇️ Descargar Excel (.xlsx)",
                data=excel_bytes,
                file_name=f"{nombre}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
            )
        else:
            st.error(f"No se pudo generar el Excel: {error_excel}")

    with st.expander("Ver resumen que se incluye en la exportación", expanded=False):
        st.dataframe(resumen.astype(str), hide_index=True)

    with st.expander("Ver los registros seleccionados", expanded=False):
        st.dataframe(muestra_exp, hide_index=True, width="stretch", height=420)


# ---------------------------------------------------------------------------
# Pestaña 6: metodología
# ---------------------------------------------------------------------------
def tab_metodologia() -> None:
    st.subheader("Metodología y ayuda")

    with st.expander("Tamaño de muestra y margen de error", expanded=True):
        st.markdown(
            "Para estimar una **proporción** con un margen de error absoluto `e` "
            "y un nivel de confianza `1 − α`, se usa:"
        )
        st.latex(r"n_0 = \frac{z^2 \, p \, q}{e^2}")
        st.markdown(
            "Cuando la población es finita y se conoce `N`, se aplica la "
            "**corrección por población finita**:"
        )
        st.latex(r"n = \frac{n_0}{1 + \frac{n_0 - 1}{N}}")
        st.markdown(
            """
            * `z` = 1,645 (90 %), 1,960 (95 %) o 2,576 (99 %); también puede
              ingresarse manualmente.
            * `p` y `q` son las proporciones esperadas. Si no hay información
              previa se usa `p = q = 0,5`, que maximiza `p·q` y produce el n más
              conservador.
            * `e` es el margen de error **absoluto** expresado en proporción
              (0,05 equivale a ±5 puntos porcentuales).
            * El resultado se redondea **siempre hacia arriba** y nunca supera N.
            * La fórmula supone muestreo aleatorio simple, población grande o
              corrección por población finita, y ausencia de sesgo de respuesta.
            """
        )

        st.markdown("**Calculadora inversa (margen real):**")
        st.latex(r"e = z \sqrt{\frac{p\,q}{n}} \quad \text{(población infinita)}")
        st.latex(
            r"e = z \sqrt{\frac{p\,q}{n}} \sqrt{\frac{N-n}{N-1}} "
            r"\quad \text{(población finita)}"
        )
        st.markdown(
            "Al mantener fijo `z`, el margen real depende del tamaño efectivamente "
            "recolectado. Si `n` cae, `e` aumenta; el intervalo de confianza se "
            "ensancha y la estimación pierde precisión."
        )

    with st.expander("Métodos de selección implementados"):
        st.markdown(
            """
            **Aleatorio simple (MAS).** Se sortean `n` posiciones del marco sin
            reemplazo (opcionalmente con reemplazo). Todos los elementos tienen
            la misma probabilidad de selección.

            **Sistemático.** Se calcula `k = N / n`. Se sortea un arranque
            `u ~ U(0, k)` y se seleccionan las posiciones `⌊u + i·k⌋` para
            `i = 0, …, n−1`. Este intervalo fraccionario garantiza exactamente
            `n` registros aunque `N` no sea múltiplo de `n`. Si el marco está
            ordenado por una variable relevante, conviene aleatorizar el orden
            antes del sorteo.

            **Estratificado.** Se divide la población en estratos mutuamente
            excluyentes y exhaustivos (región, género, grupo de edad...). La
            afijación es proporcional: `n_h = n · N_h / N`. Las fracciones se
            redondean y el resto se reparte por el método de **restos mayores**,
            garantizando que `Σ n_h = n`, que `n_h ≤ N_h` y un mínimo por estrato
            si se solicita. Los registros con valor faltante en la columna de
            estratificación se excluyen y se informan.

            **Por conglomerados.** Se sortean `m` grupos completos y se incluyen
            **todos** sus registros (muestreo en una etapa). Es útil cuando no
            existe un listado de individuos pero sí de grupos (sucursales,
            barrios, aulas). El tamaño final es aleatorio: depende de los grupos
            sorteados. La inferencia requiere considerar el efecto de diseño, por
            lo que el margen de error calculado con la fórmula de MAS es una
            aproximación optimista.
            """
        )

    with st.expander("Supuestos, límites y buenas prácticas"):
        st.markdown(
            """
            * El archivo cargado se trata como **marco muestral completo**. Si la
              base ya es una muestra, el margen de error debe interpretarse con
              cautela.
            * El cálculo de `n` estima **una proporción**. Para estimar medias se
              necesita una desviación estándar esperada y una fórmula distinta.
            * El margen de error asume **muestreo probabilístico** y ausencia de
              error de cobertura, no respuesta o medición. La tasa de respuesta
              debe monitorearse: la calculadora inversa permite ajustar el margen
              cuando la muestra efectiva difiere del plan.
            * En poblaciones pequeñas, la corrección por población finita reduce
              el n. Nunca se seleccionan más registros que los disponibles.
            * Fije una **semilla** para auditoría y reproducibilidad. La semilla y
              el método quedan registrados en la hoja *Resumen* del Excel.
            * Los datos se procesan en memoria durante la sesión; la aplicación no
              envía archivos a servicios externos.
            """
        )

    with st.expander("Instalación y ejecución", expanded=False):
        st.markdown("**1. Crear y activar un entorno virtual** (macOS / Linux):")
        st.code(
            "cd muestreo_estadistico\n"
            "python3 -m venv .venv\n"
            "source .venv/bin/activate",
            language="bash",
        )
        st.markdown("En Windows (PowerShell):")
        st.code(
            "cd muestreo_estadistico\n"
            "python -m venv .venv\n"
            ".venv\\Scripts\\Activate.ps1",
            language="powershell",
        )
        st.markdown("**2. Instalar dependencias:**")
        st.code("pip install -r requirements.txt", language="bash")
        st.markdown("**3. Ejecutar la aplicación:**")
        st.code("streamlit run app.py", language="bash")
        st.markdown(
            "Se abrirá el navegador en `http://localhost:8501`. Para detenerla, "
            "presione `Ctrl + C` en la terminal."
        )
        st.markdown("**Contenido de `requirements.txt`:**")
        st.code(
            "streamlit>=1.49,<2.0\n"
            "pandas>=2.0,<3.0\n"
            "numpy>=1.24,<3.0\n"
            "openpyxl>=3.1,<4.0\n"
            "plotly>=5.18,<8.0",
            language="text",
        )

    with st.expander("Solución de problemas", expanded=False):
        st.markdown(
            """
            * **`streamlit: command not found`**: el entorno virtual no está
              activado o las dependencias no se instalaron. Repita el paso 2.
            * **Error al leer el CSV**: verifique que sea un archivo tabular con
              encabezados. La aplicación detecta separadores `,`, `;` y tabulador,
              y codificaciones UTF-8 y Latin-1.
            * **Excel no se descarga**: si el archivo es muy grande, use el CSV;
              Excel tiene un límite de 1.048.576 filas por hoja.
            * **El puerto 8501 está ocupado**: ejecute
              `streamlit run app.py --server.port 8502`.
            * **Los gráficos no aparecen**: actualice la página y verifique que la
              muestra se haya generado (pestaña *Selección de la muestra*).
            """
        )

    st.divider()
    st.caption(
        "Aplicación de apoyo docente y profesional. Los resultados dependen de la "
        "calidad del marco muestral y de los supuestos ingresados: valide siempre "
        "el diseño con el equipo metodológico del estudio."
    )


# ---------------------------------------------------------------------------
# Composición de la página
# ---------------------------------------------------------------------------
def main() -> None:
    iniciar_estado()
    encabezado()
    barra_lateral()

    (
        p1,
        p2,
        p3,
        p4,
        p5,
        p6,
    ) = st.tabs(
        [
            f"1 · {i18n.t('tab_tamano')}",
            f"2 · {i18n.t('tab_margen_real')}",
            f"3 · {i18n.t('tab_base')}",
            f"4 · {i18n.t('tab_seleccion')}",
            f"5 · {i18n.t('tab_resultados')}",
            f"6 · {i18n.t('tab_metodologia')}",
        ]
    )

    with p1:
        tab_tamano()
    with p2:
        tab_margen_real()
    with p3:
        tab_base()
    with p4:
        tab_seleccion()
    with p5:
        tab_resultados()
    with p6:
        tab_metodologia()


if __name__ == "__main__":
    main()
