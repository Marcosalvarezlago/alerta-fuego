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
from src.terreno import calcular_pendiente_entre_puntos


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


# -----------------------------------------------------------------------------
# Estilos visuales
# -----------------------------------------------------------------------------

def inyectar_estilos():
    st.markdown(
        """
        <style>
        :root {
            --af-bg: #0f172a;
            --af-bg-soft: #1e293b;
            --af-card: #ffffff;
            --af-text: #0f172a;
            --af-muted: #64748b;
            --af-border: #e2e8f0;
            --af-red: #dc2626;
            --af-red-soft: #fee2e2;
            --af-amber: #d97706;
            --af-amber-soft: #fef3c7;
            --af-green: #059669;
            --af-green-soft: #d1fae5;
            --af-blue: #2563eb;
            --af-blue-soft: #dbeafe;
            --af-slate-soft: #f8fafc;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1120px;
        }

        div[data-testid="stVerticalBlock"] > div:has(.af-hero) {
            gap: 0.6rem;
        }

        .af-hero {
            background: linear-gradient(135deg, #111827 0%, #7f1d1d 55%, #ea580c 100%);
            border-radius: 22px;
            padding: 28px 30px;
            color: white;
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.22);
            margin-bottom: 12px;
        }

        .af-kicker {
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            opacity: 0.86;
            font-weight: 700;
            margin-bottom: 8px;
        }

        .af-hero h1 {
            margin: 0;
            font-size: clamp(2rem, 5vw, 3.1rem);
            line-height: 1.05;
            font-weight: 850;
        }

        .af-hero p {
            margin: 12px 0 0 0;
            font-size: 1.05rem;
            line-height: 1.55;
            max-width: 820px;
            opacity: 0.94;
        }

        .af-section-title {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 28px;
            margin-bottom: 8px;
        }

        .af-section-title .num {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 30px;
            height: 30px;
            border-radius: 999px;
            background: #111827;
            color: white;
            font-weight: 800;
            font-size: 0.9rem;
        }

        .af-section-title h2 {
            margin: 0;
            font-size: 1.45rem;
            line-height: 1.2;
        }

        .af-help {
            border: 1px solid var(--af-border);
            background: var(--af-slate-soft);
            border-radius: 16px;
            padding: 14px 16px;
            color: #334155;
            font-size: 0.95rem;
            line-height: 1.45;
            margin-bottom: 12px;
        }

        .af-note {
            border-left: 5px solid #f97316;
            background: #fff7ed;
            color: #7c2d12;
            border-radius: 12px;
            padding: 13px 15px;
            margin: 10px 0 16px 0;
            font-size: 0.95rem;
            line-height: 1.45;
        }

        .af-card {
            border: 1px solid var(--af-border);
            background: white;
            border-radius: 18px;
            padding: 18px 20px;
            box-shadow: 0 8px 28px rgba(15, 23, 42, 0.06);
            margin: 10px 0;
        }

        .af-card h3 {
            margin: 0 0 6px 0;
            font-size: 1.05rem;
            color: #0f172a;
        }

        .af-card p {
            color: #475569;
            margin: 0;
            line-height: 1.45;
        }

        .af-source-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 8px 0 4px 0;
        }

        .af-chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            border-radius: 999px;
            padding: 7px 11px;
            background: #f1f5f9;
            border: 1px solid #e2e8f0;
            color: #334155;
            font-size: 0.86rem;
            font-weight: 650;
        }

        .af-chip-blue { background: var(--af-blue-soft); color: #1e3a8a; border-color: #bfdbfe; }
        .af-chip-green { background: var(--af-green-soft); color: #065f46; border-color: #a7f3d0; }
        .af-chip-amber { background: var(--af-amber-soft); color: #92400e; border-color: #fde68a; }

        .af-status {
            border-radius: 22px;
            padding: 22px 24px;
            margin: 14px 0 18px 0;
            border: 1px solid;
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
        }

        .af-status .label {
            font-size: 0.82rem;
            font-weight: 850;
            letter-spacing: 0.09em;
            text-transform: uppercase;
            margin-bottom: 6px;
        }

        .af-status .title {
            font-size: clamp(1.55rem, 4vw, 2.35rem);
            line-height: 1.1;
            font-weight: 900;
            margin-bottom: 8px;
        }

        .af-status .desc {
            font-size: 1rem;
            line-height: 1.5;
            max-width: 880px;
        }

        .af-risk { background: var(--af-red-soft); border-color: #fecaca; color: #7f1d1d; }
        .af-alert { background: var(--af-amber-soft); border-color: #fde68a; color: #78350f; }
        .af-safe { background: var(--af-green-soft); border-color: #a7f3d0; color: #064e3b; }

        .af-metric-card {
            border: 1px solid var(--af-border);
            background: white;
            border-radius: 18px;
            padding: 17px 18px;
            min-height: 112px;
            box-shadow: 0 8px 25px rgba(15, 23, 42, 0.055);
        }

        .af-metric-label {
            color: #64748b;
            font-size: 0.82rem;
            font-weight: 750;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 7px;
        }

        .af-metric-value {
            color: #0f172a;
            font-size: 1.75rem;
            font-weight: 900;
            line-height: 1.1;
            margin-bottom: 6px;
        }

        .af-metric-sub {
            color: #64748b;
            font-size: 0.9rem;
            line-height: 1.35;
        }

        .af-protocol {
            border-radius: 18px;
            padding: 18px 20px;
            margin-top: 14px;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
        }

        .af-protocol h3 {
            margin: 0 0 10px 0;
            color: #0f172a;
            font-size: 1.2rem;
        }

        .af-legend {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 8px;
            margin-top: 10px;
        }

        .af-legend-item {
            display: flex;
            align-items: center;
            gap: 9px;
            padding: 9px 10px;
            border-radius: 12px;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            font-size: 0.88rem;
            color: #334155;
        }

        .af-dot {
            width: 13px;
            height: 13px;
            border-radius: 999px;
            flex: 0 0 auto;
        }

        .af-dot-red { background: #ef4444; }
        .af-dot-blue { background: #2563eb; }
        .af-dot-yellow { background: #eab308; }
        .af-dot-green { background: #10b981; }
        .af-dot-orange { background: #f59e0b; }

        .af-footer-warning {
            border-radius: 16px;
            padding: 16px 18px;
            background: #111827;
            color: #f8fafc;
            margin-top: 18px;
            line-height: 1.45;
        }

        .af-footer-warning strong {
            color: #fed7aa;
        }

        @media (max-width: 640px) {
            .af-hero { padding: 22px 20px; border-radius: 18px; }
            .af-section-title h2 { font-size: 1.22rem; }
            .af-status { padding: 18px 18px; border-radius: 18px; }
            .af-metric-value { font-size: 1.45rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def titulo_seccion(numero, titulo, subtitulo=None):
    st.markdown(
        f"""
        <div class="af-section-title">
            <span class="num">{numero}</span>
            <h2>{titulo}</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if subtitulo:
        st.markdown(f'<div class="af-help">{subtitulo}</div>', unsafe_allow_html=True)


def tarjeta_metrica(etiqueta, valor, subtitulo):
    st.markdown(
        f"""
        <div class="af-metric-card">
            <div class="af-metric-label">{etiqueta}</div>
            <div class="af-metric-value">{valor}</div>
            <div class="af-metric-sub">{subtitulo}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def chip(texto, clase=""):
    return f'<span class="af-chip {clase}">{texto}</span>'


def mostrar_fuentes(fuente_viento, fuente_combustible, fuente_pendiente):
    st.markdown(
        f"""
        <div class="af-source-row">
            {chip('Viento: ' + fuente_viento, 'af-chip-blue')}
            {chip('Combustible: ' + fuente_combustible, 'af-chip-amber')}
            {chip('Pendiente: ' + fuente_pendiente, 'af-chip-green')}
        </div>
        """,
        unsafe_allow_html=True,
    )


def mostrar_estado_cuadrante(resultado):
    cuadrante = resultado["cuadrante"]

    if cuadrante == "riesgo":
        clase = "af-risk"
        etiqueta = "Exposición principal"
        titulo = "Cuadrante de riesgo"
    elif cuadrante in ["alerta_derecha", "alerta_izquierda"]:
        clase = "af-alert"
        etiqueta = "Exposición lateral"
        titulo = "Cuadrante de alerta"
    else:
        clase = "af-safe"
        etiqueta = "Exposición baja según viento actual"
        titulo = "Sin riesgo directo"

    st.markdown(
        f"""
        <div class="af-status {clase}">
            <div class="label">{etiqueta}</div>
            <div class="title">{titulo}</div>
            <div class="desc">{resultado['descripcion_cuadrante']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mostrar_protocolo(resultado):
    escenario = resultado["escenario"]
    protocolo = resultado["protocolo"]

    if escenario == "30_min":
        encabezado = "🚨 Prioridad inmediata"
    elif escenario in ["1_hora", "alerta_lateral"]:
        encabezado = "⚠️ Preparación urgente"
    elif escenario == "1_hora_y_media":
        encabezado = "🟠 Preparación preventiva"
    else:
        encabezado = "🟢 Vigilancia y seguimiento"

    st.markdown(
        f"""
        <div class="af-protocol">
            <h3>{encabezado}: {protocolo['titulo']}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for accion in protocolo["acciones"]:
        st.write(f"- {accion}")


def formatear_metros(distancia_m):
    if distancia_m >= 1000:
        return f"{distancia_m / 1000:.2f} km"
    return f"{round(distancia_m)} m"


# -----------------------------------------------------------------------------
# Geometría del mapa
# -----------------------------------------------------------------------------

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
                "color": [220, 38, 38, 78],
            },
            {
                "nombre": "Cuadrante de alerta",
                "polygon": crear_sector(lat_fuego, lon_fuego, direccion_grados + 90, 90, radio_cuadrantes_m),
                "color": [245, 158, 11, 68],
            },
            {
                "nombre": "Cuadrante de alerta",
                "polygon": crear_sector(lat_fuego, lon_fuego, direccion_grados - 90, 90, radio_cuadrantes_m),
                "color": [245, 158, 11, 68],
            },
            {
                "nombre": "Cuadrante sin riesgo directo",
                "polygon": crear_sector(lat_fuego, lon_fuego, direccion_grados + 180, 90, radio_cuadrantes_m),
                "color": [16, 185, 129, 54],
            },
        ]
    )

    puntos_df = pd.DataFrame(
        [
            {
                "lat": lat_fuego,
                "lon": lon_fuego,
                "nombre": "Incendio",
                "color": [239, 68, 68],
            },
            {
                "lat": lat_zona,
                "lon": lon_zona,
                "nombre": "Zona vulnerable",
                "color": [37, 99, 235],
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
                "color": [234, 179, 8],
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
                "color": [220, 38, 38],
            }
        ]
    )

    sectores_layer = pdk.Layer(
        "PolygonLayer",
        data=sectores_df,
        get_polygon="polygon",
        get_fill_color="color",
        get_line_color=[71, 85, 105],
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
        get_radius=75,
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

    st.pydeck_chart(deck, use_container_width=True)


# -----------------------------------------------------------------------------
# Interfaz principal
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="Alerta Fuego",
    page_icon="🔥",
    layout="wide",
)

inyectar_estilos()

st.markdown(
    """
    <div class="af-hero">
        <div class="af-kicker">Demo experimental</div>
        <h1>🔥 Alerta Fuego</h1>
        <p>
        Estimación orientativa de alcance de incendio forestal mediante cuadrantes de exposición,
        distancia, viento, pendiente y combustible según el modelo base del proyecto.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="af-note">
        <strong>Uso prudencial:</strong> esta demo no sustituye indicaciones oficiales ni decisiones de emergencia.
        En caso de peligro, llama al <strong>112</strong> y sigue las instrucciones de los servicios competentes.
    </div>
    """,
    unsafe_allow_html=True,
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


# -----------------------------------------------------------------------------
# Entradas
# -----------------------------------------------------------------------------

titulo_seccion(
    "1",
    "Ubicaciones",
    "Introduce el punto aproximado del incendio y la finca o zona vulnerable que quieres evaluar.",
)

col_fuego, col_zona = st.columns(2)

with col_fuego:
    st.markdown('<div class="af-card"><h3>🔥 Incendio</h3><p>Punto aproximado del frente o conato observado.</p></div>', unsafe_allow_html=True)
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

with col_zona:
    st.markdown('<div class="af-card"><h3>🏡 Zona vulnerable</h3><p>Finca, vivienda, corral, núcleo o punto que se desea proteger.</p></div>', unsafe_allow_html=True)
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


titulo_seccion(
    "2",
    "Viento",
    "El viento se interpreta como dirección hacia la que empuja el fuego. Si usas el modo automático, los campos manuales desaparecen.",
)

usar_viento_automatico = st.checkbox(
    "Usar viento automático desde Open-Meteo",
    value=False,
)

meteo_info = None
fuente_viento = "manual"

if usar_viento_automatico:
    try:
        meteo_info = obtener_viento_actual_open_meteo(lat_fuego, lon_fuego)

        velocidad_viento_kmh = int(round(meteo_info["velocidad_kmh"]))
        direccion_viento_hacia = meteo_info["direccion_hacia_cardinal"]
        direccion_viento_label = CODIGO_A_LABEL_DIRECCION.get(
            direccion_viento_hacia,
            direccion_viento_hacia,
        )
        fuente_viento = "Open-Meteo"

        st.markdown(
            f"""
            <div class="af-card">
                <h3>🌬️ Viento automático activo</h3>
                <p><strong>{velocidad_viento_kmh} km/h</strong>, empujando hacia <strong>{direccion_viento_hacia}</strong>.</p>
                <p>Los campos manuales de viento se ocultan para evitar incoherencias.</p>
            </div>
            """,
            unsafe_allow_html=True,
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
        fuente_viento = "manual"

if not usar_viento_automatico:
    col_dir, col_vel = st.columns(2)
    with col_dir:
        direccion_viento_label = st.selectbox(
            "Dirección hacia la que empuja el viento",
            list(DIRECCIONES_VIENTO.keys()),
            index=list(DIRECCIONES_VIENTO.keys()).index("Hacia el nordeste ↗"),
            help="Usamos la dirección hacia la que el viento empuja el fuego, no de dónde viene.",
        )
        direccion_viento_hacia = DIRECCIONES_VIENTO[direccion_viento_label]

    with col_vel:
        velocidad_viento_kmh = st.slider(
            "Velocidad del viento (km/h)",
            min_value=0,
            max_value=80,
            value=20,
            step=1,
        )

titulo_seccion(
    "3",
    "Combustible",
)

combustible_legible = st.selectbox(
    "Tipo de combustible dominante",
    list(COMBUSTIBLES.keys()),
    index=2,
)

tipo_combustible = COMBUSTIBLES[combustible_legible]
fuente_combustible = "manual"

titulo_seccion(
    "4",
    "Pendiente",
)

usar_pendiente_automatica = st.checkbox(
    "Calcular pendiente automáticamente",
    value=False,
)

pendiente_auto_info = None
fuente_pendiente = "manual"

if usar_pendiente_automatica:
    try:
        pendiente_auto_info = calcular_pendiente_entre_puntos(
            lat_fuego=lat_fuego,
            lon_fuego=lon_fuego,
            lat_zona=lat_zona,
            lon_zona=lon_zona,
        )

        pendiente_pct = int(round(pendiente_auto_info["pendiente_pct"]))
        pendiente_pct = max(0, min(100, pendiente_pct))
        sentido_ladera = pendiente_auto_info["sentido_ladera"]
        fuente_pendiente = pendiente_auto_info["fuente"]

        st.markdown(
            f"""
            <div class="af-card">
                <h3>⛰️ Pendiente automática activa</h3>
                <p><strong>{round(pendiente_auto_info['pendiente_pct'], 1)} %</strong>, sentido: <strong>{sentido_ladera}</strong>.</p>
                <p>Los campos manuales de pendiente se ocultan para evitar incoherencias.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("Ver datos de elevación"):
            st.write("Elevación incendio:", pendiente_auto_info["elevacion_fuego_m"], "m")
            st.write("Elevación zona vulnerable:", pendiente_auto_info["elevacion_zona_m"], "m")
            st.write("Desnivel:", round(pendiente_auto_info["desnivel_m"], 2), "m")
            st.write("Distancia usada:", round(pendiente_auto_info["distancia_m"], 2), "m")
            st.write("Fuente:", pendiente_auto_info["fuente"])

    except Exception as error:
        st.error("No se pudo calcular la pendiente automáticamente. Usa entrada manual.")
        st.write(error)
        usar_pendiente_automatica = False
        fuente_pendiente = "manual"

if not usar_pendiente_automatica:
    col_pen, col_sentido = st.columns(2)
    with col_pen:
        pendiente_pct = st.slider(
            "Pendiente aproximada (%)",
            min_value=0,
            max_value=100,
            value=30,
            step=1,
        )

    with col_sentido:
        sentidos = ["subiendo", "llano", "bajando"]
        sentido_ladera = st.selectbox(
            "Sentido de propagación respecto a la ladera",
            sentidos,
            index=sentidos.index("subiendo"),
        )

titulo_seccion(
    "5",
    "Mapa operativo",
)

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

st.markdown(
    """
    <div class="af-legend">
        <div class="af-legend-item"><span class="af-dot af-dot-red"></span>Incendio / cuadrante de riesgo</div>
        <div class="af-legend-item"><span class="af-dot af-dot-orange"></span>Cuadrantes de alerta</div>
        <div class="af-legend-item"><span class="af-dot af-dot-green"></span>Cuadrante sin riesgo directo</div>
        <div class="af-legend-item"><span class="af-dot af-dot-blue"></span>Zona vulnerable</div>
        <div class="af-legend-item"><span class="af-dot af-dot-yellow"></span>Línea incendio → zona vulnerable</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")


# -----------------------------------------------------------------------------
# Cálculo y salida visual
# -----------------------------------------------------------------------------

calcular = st.button("🔥 Calcular alerta", type="primary", use_container_width=True)

if calcular:
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

    titulo_seccion("6", "Resultado")

    mostrar_estado_cuadrante(resultado)

    cuadrante = resultado["cuadrante"]
    distancia_texto = formatear_metros(resultado["distancia_m"])

    if cuadrante == "riesgo":
        tiempo_titulo = resultado["tiempo_llegada_texto"]
        tiempo_subtitulo = "Estimación principal porque la zona está en el cuadrante de riesgo."
    elif cuadrante in ["alerta_derecha", "alerta_izquierda"]:
        tiempo_titulo = resultado["tiempo_llegada_texto"]
        tiempo_subtitulo = "Referencia prudencial si el frente deriva lateralmente."
    else:
        tiempo_titulo = "No prioritario"
        tiempo_subtitulo = "No se muestra como alerta principal con la dirección actual del viento."

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        tarjeta_metrica(
            "Distancia",
            distancia_texto,
            "Separación entre incendio y zona vulnerable.",
        )
    with col_b:
        tarjeta_metrica(
            "Tiempo",
            tiempo_titulo,
            tiempo_subtitulo,
        )
    with col_c:
        tarjeta_metrica(
            "VPIF",
            f"{round(resultado['vpif_m_min'], 1)} m/min",
            "Velocidad estimada de propagación usada en el cálculo.",
        )

    st.markdown("### Datos usados")
    mostrar_fuentes(fuente_viento, fuente_combustible, fuente_pendiente)

    col_d, col_e, col_f = st.columns(3)
    with col_d:
        tarjeta_metrica(
            "Viento",
            f"{velocidad_viento_kmh} km/h",
            f"Dirección operativa: {direccion_viento_hacia}.",
        )
    with col_e:
        tarjeta_metrica(
            "Combustible",
            combustible_legible,
            f"V0 = {resultado['v0']} m/min.",
        )
    with col_f:
        tarjeta_metrica(
            "Pendiente",
            f"{pendiente_pct} %",
            f"Sentido: {sentido_ladera}. FP = {resultado['factor_pendiente']}.",
        )

    st.markdown("### Protocolo orientativo")
    mostrar_protocolo(resultado)

    with st.expander("Ver detalles técnicos del cálculo"):
        st.write("Dirección seleccionada:", direccion_viento_label)
        st.write("Código interno de viento:", direccion_viento_hacia)
        st.write("Velocidad del viento usada:", velocidad_viento_kmh, "km/h")
        st.write("Fuente viento:", fuente_viento)

        if meteo_info is not None:
            st.write("Dirección meteorológica desde:", meteo_info["direccion_desde_grados"], "°")
            st.write("Dirección operativa hacia:", meteo_info["direccion_hacia_grados"], "°")

        st.write("Combustible seleccionado:", combustible_legible)
        st.write("Fuente combustible:", fuente_combustible)

        st.write("Pendiente usada:", pendiente_pct, "%")
        st.write("Sentido de ladera usado:", sentido_ladera)
        st.write("Fuente pendiente:", fuente_pendiente)

        if pendiente_auto_info is not None:
            st.write("Elevación incendio:", pendiente_auto_info["elevacion_fuego_m"], "m")
            st.write("Elevación zona:", pendiente_auto_info["elevacion_zona_m"], "m")
            st.write("Desnivel:", round(pendiente_auto_info["desnivel_m"], 2), "m")

        st.write("Dirección incendio → zona vulnerable:", round(resultado["direccion_fuego_zona_grados"], 1), "°")
        st.write("Dirección del viento:", resultado["direccion_viento_grados"], "°")
        st.write("Diferencia angular:", round(resultado["diferencia_signed_grados"], 1), "°")
        st.write("V0 combustible:", resultado["v0"], "m/min")
        st.write("Factor viento FV:", resultado["factor_viento"])
        st.write("Factor pendiente FP:", resultado["factor_pendiente"])
        st.write("VPIF = V0 · FV · FP:", round(resultado["vpif_m_min"], 2), "m/min")

    st.markdown(
        """
        <div class="af-footer-warning">
            <strong>Recordatorio:</strong> estimación grosera y orientativa. Úsala para anticiparte,
            retirarte antes y preparar decisiones prudentes, no para apurar tiempos ni justificar
            entrar o permanecer en zonas comprometidas.
        </div>
        """,
        unsafe_allow_html=True,
    )
