import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import pydeck as pdk
import math

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from src.modelo import evaluar_alerta_fuego, DIRECCIONES_GRADOS
from src.meteo import obtener_viento_actual_open_meteo


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

CODIGO_A_LABEL_DIRECCION = {valor: clave for clave, valor in DIRECCIONES_VIENTO.items()}


def calcular_punto_desde_origen(lat, lon, direccion_grados, distancia_m):
    radio_tierra_m = 6371000

    angulo = math.radians(direccion_grados)
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)

    nueva_lat = math.asin(
        math.sin(lat_rad) * math.cos(distancia_m / radio_tierra_m)
        + math.cos(lat_rad) * math.sin(distancia_m / radio_tierra_m) * math.cos(angulo)
    )

    nueva_lon = lon_rad + math.atan2(
        math.sin(angulo) * math.sin(distancia_m / radio_tierra_m) * math.cos(lat_rad),
        math.cos(distancia_m / radio_tierra_m) - math.sin(lat_rad) * math.sin(nueva_lat),
    )

    return math.degrees(nueva_lat), math.degrees(nueva_lon)


def crear_sector(lat, lon, direccion_central, apertura_grados, radio_m, pasos=12):
    angulo_inicio = direccion_central - apertura_grados / 2
    angulo_fin = direccion_central + apertura_grados / 2

    puntos = [[lon, lat]]

    for i in range(pasos + 1):
        angulo = angulo_inicio + (angulo_fin - angulo_inicio) * i / pasos
        punto_lat, punto_lon = calcular_punto_desde_origen(
            lat,
            lon,
            angulo,
            radio_m,
        )
        puntos.append([punto_lon, punto_lat])

    puntos.append([lon, lat])

    return puntos


def mostrar_mapa_con_cuadrantes(
    lat_fuego,
    lon_fuego,
    lat_zona,
    lon_zona,
    direccion_viento_hacia,
    radio_cuadrantes_m,
):
    direccion_grados = DIRECCIONES_GRADOS[direccion_viento_hacia]

    lat_viento_fin, lon_viento_fin = calcular_punto_desde_origen(
        lat_fuego,
        lon_fuego,
        direccion_grados,
        radio_cuadrantes_m,
    )

    sectores_df = pd.DataFrame(
        [
            {
                "nombre": "Cuadrante de riesgo",
                "polygon": crear_sector(lat_fuego, lon_fuego, direccion_grados, 90, radio_cuadrantes_m),
                "color": [255, 0, 0, 80],
            },
            {
                "nombre": "Cuadrante de alerta",
                "polygon": crear_sector(lat_fuego, lon_fuego, direccion_grados + 90, 90, radio_cuadrantes_m),
                "color": [255, 180, 0, 65],
            },
            {
                "nombre": "Cuadrante de alerta",
                "polygon": crear_sector(lat_fuego, lon_fuego, direccion_grados - 90, 90, radio_cuadrantes_m),
                "color": [255, 180, 0, 65],
            },
            {
                "nombre": "Cuadrante sin riesgo directo",
                "polygon": crear_sector(lat_fuego, lon_fuego, direccion_grados + 180, 90, radio_cuadrantes_m),
                "color": [0, 180, 90, 55],
            },
        ]
    )

    puntos_df = pd.DataFrame(
        [
            {
                "lat": lat_fuego,
                "lon": lon_fuego,
                "nombre": "Incendio",
                "color": [255, 60, 0],
            },
            {
                "lat": lat_zona,
                "lon": lon_zona,
                "nombre": "Zona vulnerable",
                "color": [0, 90, 255],
            },
        ]
    )

    linea_finca_df = pd.DataFrame(
        [
            {
                "from_lon": lon_fuego,
                "from_lat": lat_fuego,
                "to_lon": lon_zona,
                "to_lat": lat_zona,
                "nombre": "Incendio → zona vulnerable",
                "color": [255, 230, 0],
            }
        ]
    )

    viento_df = pd.DataFrame(
        [
            {
                "from_lon": lon_fuego,
                "from_lat": lat_fuego,
                "to_lon": lon_viento_fin,
                "to_lat": lat_viento_fin,
                "nombre": "Dirección del viento",
                "color": [255, 0, 0],
            }
        ]
    )

    sectores_layer = pdk.Layer(
        "PolygonLayer",
        data=sectores_df,
        get_polygon="polygon",
        get_fill_color="color",
        get_line_color=[80, 80, 80],
        line_width_min_pixels=1,
        pickable=True,
        stroked=True,
        filled=True,
    )

    punto_layer = pdk.Layer(
        "ScatterplotLayer",
        data=puntos_df,
        get_position="[lon, lat]",
        get_fill_color="color",
        get_radius=70,
        pickable=True,
    )

    linea_finca_layer = pdk.Layer(
        "LineLayer",
        data=linea_finca_df,
        get_source_position="[from_lon, from_lat]",
        get_target_position="[to_lon, to_lat]",
        get_color="color",
        get_width=5,
        pickable=True,
    )

    viento_layer = pdk.Layer(
        "LineLayer",
        data=viento_df,
        get_source_position="[from_lon, from_lat]",
        get_target_position="[to_lon, to_lat]",
        get_color="color",
        get_width=8,
        pickable=True,
    )

    view_state = pdk.ViewState(
        latitude=(lat_fuego + lat_zona) / 2,
        longitude=(lon_fuego + lon_zona) / 2,
        zoom=12,
        pitch=0,
    )

    deck = pdk.Deck(
        layers=[
            sectores_layer,
            linea_finca_layer,
            viento_layer,
            punto_layer,
        ],
        initial_view_state=view_state,
        tooltip={"text": "{nombre}"},
    )

    st.pydeck_chart(deck)


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


st.markdown("## 3. Viento, combustible y pendiente")

usar_viento_automatico = st.checkbox(
    "Usar viento automático desde Open-Meteo",
    value=False,
)

direccion_viento_auto = None
velocidad_viento_auto = None
meteo_info = None

if usar_viento_automatico:
    try:
        meteo_info = obtener_viento_actual_open_meteo(lat_fuego, lon_fuego)

        velocidad_viento_auto = int(round(meteo_info["velocidad_kmh"]))
        direccion_viento_auto = meteo_info["direccion_hacia_cardinal"]

        st.success(
            f"Viento automático obtenido: {velocidad_viento_auto} km/h, "
            f"empujando hacia {direccion_viento_auto}."
        )

        with st.expander("Ver datos meteorológicos brutos"):
            st.write("Velocidad:", meteo_info["velocidad_kmh"], "km/h")
            st.write("Dirección meteorológica desde:", meteo_info["direccion_desde_grados"], "°")
            st.write("Dirección operativa hacia:", meteo_info["direccion_hacia_grados"], "°")
            st.write("Dirección cardinal hacia:", meteo_info["direccion_hacia_cardinal"])

    except Exception as error:
        st.error("No se pudo obtener el viento automático. Usa entrada manual.")
        st.write(error)
        usar_viento_automatico = False


if usar_viento_automatico and direccion_viento_auto in CODIGO_A_LABEL_DIRECCION:
    direccion_default_label = CODIGO_A_LABEL_DIRECCION[direccion_viento_auto]
else:
    direccion_default_label = "Hacia el nordeste ↗"

direccion_default_index = list(DIRECCIONES_VIENTO.keys()).index(direccion_default_label)

direccion_viento_label = st.selectbox(
    "Dirección hacia la que empuja el viento",
    list(DIRECCIONES_VIENTO.keys()),
    index=direccion_default_index,
    help="Usamos la dirección hacia la que el viento empuja el fuego, no de dónde viene.",
)

direccion_viento_hacia = DIRECCIONES_VIENTO[direccion_viento_label]

velocidad_viento_kmh = st.slider(
    "Velocidad del viento (km/h)",
    min_value=0,
    max_value=80,
    value=velocidad_viento_auto if velocidad_viento_auto is not None else 20,
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

st.markdown("## 4. Vista en mapa")

radio_cuadrantes_m = st.slider(
    "Radio visual de los cuadrantes (m)",
    min_value=500,
    max_value=5000,
    value=1500,
    step=100,
)

mostrar_mapa_con_cuadrantes(
    lat_fuego=lat_fuego,
    lon_fuego=lon_fuego,
    lat_zona=lat_zona,
    lon_zona=lon_zona,
    direccion_viento_hacia=direccion_viento_hacia,
    radio_cuadrantes_m=radio_cuadrantes_m,
)

st.caption(
    "Rojo transparente: cuadrante de riesgo. Amarillo: cuadrantes de alerta. Verde: cuadrante sin riesgo directo. "
    "Punto rojo: incendio. Punto azul: zona vulnerable. Línea amarilla: incendio → zona vulnerable. Línea roja: viento."
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
        st.write("Velocidad del viento usada:", velocidad_viento_kmh, "km/h")

        if meteo_info is not None:
            st.write("Fuente viento: Open-Meteo")
            st.write("Dirección meteorológica desde:", meteo_info["direccion_desde_grados"], "°")
            st.write("Dirección operativa hacia:", meteo_info["direccion_hacia_grados"], "°")
        else:
            st.write("Fuente viento: entrada manual")

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