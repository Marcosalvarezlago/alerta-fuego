import streamlit as st
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from src.modelo import evaluar_alerta_fuego


st.set_page_config(
    page_title="Alerta Fuego",
    page_icon="🔥",
    layout="centered"
)

st.title("🔥 Alerta Fuego")
st.subheader("Estimación orientativa de tiempo de llegada del incendio")

st.warning(
    "Herramienta orientativa. No sustituye indicaciones oficiales. "
    "En caso de peligro, llama al 112."
)

st.markdown("## 1. Ubicación del fuego")

lat_fuego = st.number_input("Latitud del fuego", value=40.1290, format="%.6f")
lon_fuego = st.number_input("Longitud del fuego", value=-5.4610, format="%.6f")

st.markdown("## 2. Ubicación vulnerable")

lat_zona = st.number_input("Latitud de la zona vulnerable", value=40.1350, format="%.6f")
lon_zona = st.number_input("Longitud de la zona vulnerable", value=-5.4550, format="%.6f")

st.markdown("## 3. Condiciones")

tipo_combustible = st.selectbox(
    "Tipo de combustible",
    [
        "pastos_bajos",
        "quercus",
        "matorral_mediterraneo",
        "pinar"
    ]
)

velocidad_viento_kmh = st.slider(
    "Velocidad del viento (km/h)",
    min_value=0,
    max_value=80,
    value=20,
    step=1
)

pendiente_pct = st.slider(
    "Pendiente aproximada (%)",
    min_value=0,
    max_value=100,
    value=30,
    step=1
)

sentido_ladera = st.selectbox(
    "Sentido respecto a la ladera",
    [
        "subiendo",
        "llano",
        "bajando"
    ]
)

st.markdown("---")

if st.button("Calcular alerta"):
    resultado = evaluar_alerta_fuego(
        lat_fuego=lat_fuego,
        lon_fuego=lon_fuego,
        lat_zona=lat_zona,
        lon_zona=lon_zona,
        tipo_combustible=tipo_combustible,
        velocidad_viento_kmh=velocidad_viento_kmh,
        pendiente_pct=pendiente_pct,
        sentido_ladera=sentido_ladera
    )

    st.markdown("## Resultado")

    st.metric(
        "Tiempo estimado de llegada",
        resultado["tiempo_llegada_texto"]
    )

    st.metric(
        "Distancia a zona vulnerable",
        f'{round(resultado["distancia_m"])} m'
    )

    st.metric(
        "Velocidad estimada de propagación",
        f'{round(resultado["velocidad_propagacion_m_min"], 2)} m/min'
    )

    st.markdown("## Escenario")
    st.error(resultado["protocolo"]["titulo"])

    st.markdown("## Protocolo orientativo")

    for accion in resultado["protocolo"]["acciones"]:
        st.write(f"- {accion}")

    st.markdown("---")
    st.warning(
        "Usa esta estimación para anticiparte, no para apurar los tiempos."
    )