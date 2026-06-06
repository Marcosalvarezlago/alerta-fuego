import streamlit as st
import sys
from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from src.modelo import evaluar_alerta_fuego


COMBUSTIBLES = {
    "Pastos bajos": "pastos_bajos",
    "Bosque de Quercus / encinar / robledal": "quercus",
    "Matorral mediterráneo": "matorral_mediterraneo",
    "Pinar": "pinar",
}

DIRECCIONES_VIENTO = {
    "Hacia el norte ↑": "N",
    "Hacia el nordeste ↗": "NE",
    "Hacia el este →": "E",
    "Hacia el sudeste ↘": "SE",
    "Hacia el sur ↓": "S",
    "Hacia el suroeste ↙": "SO",
    "Hacia el oeste ←": "O",
    "Hacia el noroeste ↖": "NO",
}


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

with st.expander("Cómo obtener coordenadas desde Google Maps"):
    st.write(
        "1. Abre Google Maps.\n"
        "2. Mantén pulsado sobre el punto del incendio o de la finca.\n"
        "3. Copia las coordenadas que aparecen, por ejemplo: 40.1290, -5.4610.\n"
        "4. Introduce la primera cifra como latitud y la segunda como longitud."
    )

usar_ejemplo = st.checkbox("Usar ejemplo de prueba", value=True)

if usar_ejemplo:
    lat_fuego_default = 40.1290
    lon_fuego_default = -5.4610
    lat_zona_default = 40.1350
    lon_zona_default = -5.4550
else:
    lat_fuego_default = 40.0000
    lon_fuego_default = -5.0000
    lat_zona_default = 40.0000
    lon_zona_default = -5.0000


st.markdown("## 1. Ubicación del incendio")

lat_fuego = st.number_input(
    "Latitud del incendio",
    value=lat_fuego_default,
    format="%.6f",
)

lon_fuego = st.number_input(
    "Longitud del incendio",
    value=lon_fuego_default,
    format="%.6f",
)

st.markdown("## 2. Ubicación de la finca o zona vulnerable")

lat_zona = st.number_input(
    "Latitud de la finca o zona vulnerable",
    value=lat_zona_default,
    format="%.6f",
)

lon_zona = st.number_input(
    "Longitud de la finca o zona vulnerable",
    value=lon_zona_default,
    format="%.6f",
)

st.markdown("## 3. Vista rápida en mapa")

mapa_df = pd.DataFrame(
    [
        {"lat": lat_fuego, "lon": lon_fuego, "punto": "Incendio"},
        {"lat": lat_zona, "lon": lon_zona, "punto": "Zona vulnerable"},
    ]
)

st.map(
    mapa_df,
    latitude="lat",
    longitude="lon",
    zoom=12,
)

st.caption(
    "El mapa muestra los dos puntos introducidos. En esta versión todavía no dibuja cuadrantes ni frente de avance."
)

st.markdown("## 4. Viento, combustible y pendiente")

direccion_viento_label = st.selectbox(
    "Dirección hacia la que empuja el viento",
    list(DIRECCIONES_VIENTO.keys()),
    index=1,
    help="Usamos la dirección hacia la que el viento empuja el fuego, no de dónde viene.",
)

direccion_viento_hacia = DIRECCIONES_VIENTO[direccion_viento_label]

velocidad_viento_kmh = st.slider(
    "Velocidad del viento (km/h)",
    min_value=0,
    max_value=80,
    value=20,
    step=1,
)

combustible_legible = st.selectbox(
    "Tipo de combustible dominante",
    list(COMBUSTIBLES.keys()),
    index=2,
)

tipo_combustible = COMBUSTIBLES[combustible_legible]

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

    st.markdown("## 2. Resultado principal")

    st.metric(
        "Distancia incendio-zona vulnerable",
        f'{round(resultado["distancia_m"])} m',
    )

    if cuadrante == "riesgo":
        st.metric(
            "Tiempo estimado de alcance",
            resultado["tiempo_llegada_texto"],
        )
    elif cuadrante in ["alerta_derecha", "alerta_izquierda"]:
        st.info(
            "La zona no está en el cuadrante principal de riesgo, pero sí en alerta lateral. "
            "El tiempo se muestra solo como referencia prudencial si el frente derivase."
        )
        st.metric(
            "Tiempo orientativo",
            resultado["tiempo_llegada_texto"],
        )
    else:
        st.info(
            "Según la dirección actual del viento, la zona está fuera del cuadrante directo de riesgo. "
            "Mantén vigilancia: el viento puede cambiar y las pavesas pueden generar focos secundarios."
        )

    st.markdown("## 3. Protocolo orientativo")

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

    with st.expander("Ver detalles técnicos del cálculo"):
        st.write("Dirección seleccionada:", direccion_viento_label)
        st.write("Código interno de viento:", direccion_viento_hacia)
        st.write("Dirección incendio → zona vulnerable:", round(resultado["direccion_fuego_zona_grados"], 1), "°")
        st.write("Dirección del viento:", resultado["direccion_viento_grados"], "°")
        st.write("Diferencia angular:", round(resultado["diferencia_signed_grados"], 1), "°")
        st.write("V0 combustible:", resultado["v0"], "m/min")
        st.write("Factor viento FV:", resultado["factor_viento"])
        st.write("Factor pendiente FP:", resultado["factor_pendiente"])
        st.write("VPIF = V0 · FV · FP:", round(resultado["vpif_m_min"], 2), "m/min")

    st.markdown("---")

    st.warning(
        "Estimación grosera y orientativa. Úsala para anticiparte, no para apurar los tiempos."
    )