import streamlit as st
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from src.modelo import evaluar_alerta_fuego


st.set_page_config(
    page_title="Alerta Fuego",
    page_icon="🔥",
    layout="centered",
)


st.title("🔥 Alerta Fuego")
st.subheader("Estimación orientativa de riesgo y tiempo de alcance")

st.warning(
    "Herramienta orientativa. No sustituye indicaciones oficiales. "
    "En caso de peligro, llama al 112."
)

st.markdown("## 1. Ubicación del incendio")

lat_fuego = st.number_input(
    "Latitud del incendio",
    value=40.1290,
    format="%.6f",
)

lon_fuego = st.number_input(
    "Longitud del incendio",
    value=-5.4610,
    format="%.6f",
)

st.markdown("## 2. Ubicación de la finca o zona vulnerable")

lat_zona = st.number_input(
    "Latitud de la finca o zona vulnerable",
    value=40.1350,
    format="%.6f",
)

lon_zona = st.number_input(
    "Longitud de la finca o zona vulnerable",
    value=-5.4550,
    format="%.6f",
)

st.markdown("## 3. Viento, combustible y pendiente")

direccion_viento_hacia = st.selectbox(
    "Dirección hacia la que empuja el viento",
    ["N", "NE", "E", "SE", "S", "SO", "O", "NO"],
    index=1,
)

velocidad_viento_kmh = st.slider(
    "Velocidad del viento (km/h)",
    min_value=0,
    max_value=80,
    value=20,
    step=1,
)

tipo_combustible = st.selectbox(
    "Tipo de combustible dominante",
    [
        "pastos_bajos",
        "quercus",
        "matorral_mediterraneo",
        "pinar",
    ],
)

pendiente_pct = st.slider(
    "Pendiente aproximada (%)",
    min_value=0,
    max_value=100,
    value=30,
    step=1,
)

sentido_ladera = st.selectbox(
    "Sentido de propagación respecto a la ladera",
    [
        "subiendo",
        "llano",
        "bajando",
    ],
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
        direccion_viento_hacia=direccion_viento_hacia,
        pendiente_pct=pendiente_pct,
        sentido_ladera=sentido_ladera,
    )

    st.markdown("## 1. Cuadrante de exposición")

    cuadrante = resultado["cuadrante"]

    if cuadrante == "riesgo":
        st.error("CUADRANTE DE RIESGO")
    elif cuadrante in ["alerta_derecha", "alerta_izquierda"]:
        st.warning("CUADRANTE DE ALERTA")
    else:
        st.success("CUADRANTE SIN RIESGO DIRECTO")

    st.write(resultado["descripcion_cuadrante"])

    st.write(
        "Diferencia angular respecto al eje del viento:",
        round(resultado["diferencia_signed_grados"], 1),
        "°",
    )

    st.markdown("## 2. Datos de cálculo")

    st.metric(
        "Distancia incendio-zona vulnerable",
        f'{round(resultado["distancia_m"])} m',
    )

    st.write("Dirección incendio → zona vulnerable:", round(resultado["direccion_fuego_zona_grados"], 1), "°")
    st.write("Dirección del viento:", resultado["direccion_viento_grados"], "°")
    st.write("V0 combustible:", resultado["v0"], "m/min")
    st.write("Factor viento FV:", resultado["factor_viento"])
    st.write("Factor pendiente FP:", resultado["factor_pendiente"])
    st.write("VPIF = V0 · FV · FP:", round(resultado["vpif_m_min"], 2), "m/min")

    st.markdown("## 3. Tiempo estimado")

    if cuadrante == "riesgo":
        st.metric(
            "Tiempo estimado de alcance",
            resultado["tiempo_llegada_texto"],
        )
    elif cuadrante in ["alerta_derecha", "alerta_izquierda"]:
        st.info(
            "La zona no está en el cuadrante principal de riesgo, pero sí en alerta lateral. "
            "El tiempo estimado se muestra solo como referencia prudencial."
        )
        st.metric(
            "Tiempo orientativo si el frente derivase hacia la zona",
            resultado["tiempo_llegada_texto"],
        )
    else:
        st.info(
            "Según la dirección actual del viento, la zona está fuera del cuadrante directo de riesgo. "
            "No se debe interpretar como ausencia absoluta de peligro."
        )

    st.markdown("## 4. Protocolo orientativo")

    if resultado["escenario"] == "30_min":
        st.error(resultado["protocolo"]["titulo"])
    elif resultado["escenario"] in ["1_hora", "alerta_lateral"]:
        st.warning(resultado["protocolo"]["titulo"])
    elif resultado["escenario"] == "1_hora_y_media":
        st.info(resultado["protocolo"]["titulo"])
    else:
        st.success(resultado["protocolo"]["titulo"])

    for accion in resultado["protocolo"]["acciones"]:
        st.write(f"- {accion}")

    st.markdown("---")

    st.warning(
        "Estimación grosera y orientativa. Úsala para anticiparte, no para apurar los tiempos."
    )