import streamlit as st
import sys
from pathlib import Path
import math
import re
from urllib.parse import unquote, urlparse, parse_qs

import folium
from folium.plugins import LocateControl
from streamlit_folium import st_folium
import requests

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

CENTRO_TRABAJO = [40.1290, -5.4610]
COORDENADAS_EJEMPLO = {
    "lat_fuego": 40.1290,
    "lon_fuego": -5.4610,
    "lat_zona": 40.1350,
    "lon_zona": -5.4550,
}


# -----------------------------------------------------------------------------
# Estado
# -----------------------------------------------------------------------------

def inicializar_estado():
    defaults = {
        "lat_fuego": None,
        "lon_fuego": None,
        "lat_zona": None,
        "lon_zona": None,
        "calculo_realizado": False,
        "ultimo_resultado": None,
        "ultimo_calculo": None,
        "ultimo_click_mapa": None,
    }
    for clave, valor in defaults.items():
        if clave not in st.session_state:
            st.session_state[clave] = valor


def reset_calculo():
    st.session_state["calculo_realizado"] = False
    st.session_state["ultimo_resultado"] = None
    st.session_state["ultimo_calculo"] = None


def set_coord(prefix, lat, lon):
    if prefix == "fuego":
        st.session_state["lat_fuego"] = float(lat)
        st.session_state["lon_fuego"] = float(lon)
    elif prefix == "zona":
        st.session_state["lat_zona"] = float(lat)
        st.session_state["lon_zona"] = float(lon)
    reset_calculo()


def cargar_ejemplo():
    for clave, valor in COORDENADAS_EJEMPLO.items():
        st.session_state[clave] = valor
    reset_calculo()


def vaciar_ubicaciones():
    for clave in ["lat_fuego", "lon_fuego", "lat_zona", "lon_zona"]:
        st.session_state[clave] = None
    reset_calculo()


def coords_completas():
    return all(
        st.session_state.get(clave) is not None
        for clave in ["lat_fuego", "lon_fuego", "lat_zona", "lon_zona"]
    )


# -----------------------------------------------------------------------------
# Estilos
# -----------------------------------------------------------------------------

def inyectar_estilos():
    st.markdown(
        """
        <style>
        :root {
            --af-border: #e2e8f0;
            --af-muted: #64748b;
            --af-slate-soft: #f8fafc;
            --af-red-soft: #fee2e2;
            --af-amber-soft: #fef3c7;
            --af-green-soft: #d1fae5;
            --af-blue-soft: #dbeafe;
        }
        .block-container {
            padding-top: 1.7rem;
            padding-bottom: 3rem;
            max-width: 1180px;
        }
        .af-hero {
            background: linear-gradient(135deg, #111827 0%, #7f1d1d 52%, #ea580c 100%);
            border-radius: 24px;
            padding: 30px 32px;
            color: white;
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.24);
            margin-bottom: 12px;
        }
        .af-kicker {
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            opacity: 0.86;
            font-weight: 750;
            margin-bottom: 8px;
        }
        .af-hero h1 {
            margin: 0;
            font-size: clamp(2.05rem, 5vw, 3.25rem);
            line-height: 1.04;
            font-weight: 900;
        }
        .af-hero p {
            margin: 12px 0 0 0;
            font-size: 1.05rem;
            line-height: 1.55;
            max-width: 880px;
            opacity: 0.94;
        }
        .af-note {
            border-left: 5px solid #f97316;
            background: #fff7ed;
            color: #7c2d12;
            border-radius: 14px;
            padding: 13px 15px;
            margin: 10px 0 18px 0;
            font-size: 0.95rem;
            line-height: 1.45;
        }
        .af-section-title {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 26px;
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
            font-weight: 850;
            font-size: 0.9rem;
        }
        .af-section-title h2 {
            margin: 0;
            font-size: 1.48rem;
            line-height: 1.2;
        }
        .af-help {
            border: 1px solid var(--af-border);
            background: var(--af-slate-soft);
            border-radius: 16px;
            padding: 13px 15px;
            color: #334155;
            font-size: 0.95rem;
            line-height: 1.45;
            margin-bottom: 12px;
        }
        .af-card {
            border: 1px solid var(--af-border);
            background: white;
            border-radius: 18px;
            padding: 17px 19px;
            box-shadow: 0 8px 28px rgba(15, 23, 42, 0.055);
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
        .af-mini-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 10px;
            margin: 10px 0 12px 0;
        }
        .af-mini-card {
            border: 1px solid var(--af-border);
            border-radius: 16px;
            padding: 13px 15px;
            background: white;
        }
        .af-mini-card .label {
            color: #64748b;
            font-size: .78rem;
            font-weight: 800;
            letter-spacing: .06em;
            text-transform: uppercase;
            margin-bottom: 5px;
        }
        .af-mini-card .value {
            color: #0f172a;
            font-size: 1.02rem;
            font-weight: 850;
            line-height: 1.25;
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
            max-width: 900px;
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
            font-size: 1.7rem;
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
        .af-dot { width: 13px; height: 13px; border-radius: 999px; flex: 0 0 auto; }
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
        .af-footer-warning strong { color: #fed7aa; }
        @media (max-width: 640px) {
            .af-hero { padding: 22px 20px; border-radius: 18px; }
            .af-section-title h2 { font-size: 1.22rem; }
            .af-status { padding: 18px 18px; border-radius: 18px; }
            .af-metric-value { font-size: 1.42rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# Componentes visuales
# -----------------------------------------------------------------------------

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


def mostrar_resumen_ubicaciones():
    def texto_coord(lat, lon):
        if lat is None or lon is None:
            return "Sin fijar"
        return f"{lat:.6f}, {lon:.6f}"

    st.markdown(
        f"""
        <div class="af-mini-grid">
            <div class="af-mini-card">
                <div class="label">Incendio</div>
                <div class="value">{texto_coord(st.session_state['lat_fuego'], st.session_state['lon_fuego'])}</div>
            </div>
            <div class="af-mini-card">
                <div class="label">Zona vulnerable</div>
                <div class="value">{texto_coord(st.session_state['lat_zona'], st.session_state['lon_zona'])}</div>
            </div>
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
# Coordenadas y enlaces
# -----------------------------------------------------------------------------

def numero_desde_texto(texto):
    if texto is None:
        return None
    texto = str(texto).strip().replace(",", ".")
    if not texto:
        return None
    try:
        return float(texto)
    except ValueError:
        return None


def validar_lat_lon(lat, lon):
    return lat is not None and lon is not None and -90 <= lat <= 90 and -180 <= lon <= 180


def intentar_resolver_url(texto):
    """Resuelve enlaces acortados de Google Maps si el servidor tiene acceso a internet."""
    if not texto or not re.search(r"https?://", texto):
        return texto

    posible_url = re.search(r"https?://\S+", texto)
    if not posible_url:
        return texto

    url = posible_url.group(0).strip()
    if not any(dominio in url for dominio in ["maps.app.goo.gl", "goo.gl/maps", "maps.google", "google.com/maps"]):
        return texto

    try:
        respuesta = requests.get(
            url,
            allow_redirects=True,
            timeout=6,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        if respuesta.url:
            return texto + "\n" + respuesta.url
    except Exception:
        return texto

    return texto


def extraer_par_lat_lon_de_texto(texto, permitir_resolver_url=True):
    """Extrae lat/lon desde coordenadas simples o enlaces de mapas.

    Evita el fallo típico de tomar números de zoom, fechas o identificadores como coordenadas.
    Para URLs, solo acepta patrones fuertes: @lat,lon, !3dLAT!4dLON, q/ll/query/etc.
    Para texto sin URL, acepta pares decimales separados por coma o punto y coma.
    """
    if not texto:
        return None

    texto_original = texto.strip()
    texto_trabajo = intentar_resolver_url(texto_original) if permitir_resolver_url else texto_original
    texto_trabajo = unquote(texto_trabajo).replace("%2C", ",")

    # 1) Google Maps: /@lat,lon,zoom
    coincidencia = re.search(r"@\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)", texto_trabajo)
    if coincidencia:
        lat = float(coincidencia.group(1))
        lon = float(coincidencia.group(2))
        if validar_lat_lon(lat, lon):
            return lat, lon

    # 2) Google Maps: !3dLAT!4dLON
    coincidencia = re.search(r"!3d(-?\d+(?:\.\d+)?)!4d(-?\d+(?:\.\d+)?)", texto_trabajo)
    if coincidencia:
        lat = float(coincidencia.group(1))
        lon = float(coincidencia.group(2))
        if validar_lat_lon(lat, lon):
            return lat, lon

    # 3) Google Maps: !2dLON!3dLAT
    coincidencia = re.search(r"!2d(-?\d+(?:\.\d+)?)!3d(-?\d+(?:\.\d+)?)", texto_trabajo)
    if coincidencia:
        lon = float(coincidencia.group(1))
        lat = float(coincidencia.group(2))
        if validar_lat_lon(lat, lon):
            return lat, lon

    # 4) Query params robustos: q=lat,lon / ll=lat,lon / query=lat,lon / destination=lat,lon
    for url in re.findall(r"https?://\S+", texto_trabajo):
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            for clave in ["q", "ll", "query", "center", "destination", "origin", "daddr", "saddr"]:
                for valor in params.get(clave, []):
                    par = re.search(r"(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)", valor)
                    if par:
                        lat = float(par.group(1))
                        lon = float(par.group(2))
                        if validar_lat_lon(lat, lon):
                            return lat, lon
        except Exception:
            pass

    # 5) Texto simple: "40.1290, -5.4610". Solo se usa como fallback si no parece URL.
    if "http://" not in texto_original and "https://" not in texto_original:
        coincidencia = re.search(r"(-?\d+(?:\.\d+)?)\s*[,;]\s*(-?\d+(?:\.\d+)?)", texto_original)
        if coincidencia:
            lat = float(coincidencia.group(1))
            lon = float(coincidencia.group(2))
            if validar_lat_lon(lat, lon):
                return lat, lon

    return None


# -----------------------------------------------------------------------------
# Geometría y mapa
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


def crear_sector_latlon(lat, lon, direccion_central, apertura_grados, radio_m, pasos=28):
    angulo_inicio = direccion_central - apertura_grados / 2
    angulo_fin = direccion_central + apertura_grados / 2

    puntos = [[lat, lon]]

    for i in range(pasos + 1):
        angulo = angulo_inicio + (angulo_fin - angulo_inicio) * i / pasos
        punto_lat, punto_lon = calcular_punto_desde_origen(lat, lon, angulo, radio_m)
        puntos.append([punto_lat, punto_lon])

    puntos.append([lat, lon])
    return puntos


def centro_mapa(lat_fuego, lon_fuego, lat_zona, lon_zona):
    puntos = []
    if validar_lat_lon(lat_fuego, lon_fuego):
        puntos.append((lat_fuego, lon_fuego))
    if validar_lat_lon(lat_zona, lon_zona):
        puntos.append((lat_zona, lon_zona))

    if len(puntos) == 2:
        return [(puntos[0][0] + puntos[1][0]) / 2, (puntos[0][1] + puntos[1][1]) / 2], 13
    if len(puntos) == 1:
        return [puntos[0][0], puntos[0][1]], 14
    return CENTRO_TRABAJO, 13


def crear_mapa_folium(
    lat_fuego,
    lon_fuego,
    lat_zona,
    lon_zona,
    mostrar_cuadrantes=False,
    direccion_viento_hacia=None,
    radio_cuadrantes_m=1500,
):
    centro, zoom = centro_mapa(lat_fuego, lon_fuego, lat_zona, lon_zona)

    mapa = folium.Map(
        location=centro,
        zoom_start=zoom,
        tiles=None,
        control_scale=True,
    )

    folium.TileLayer("OpenStreetMap", name="Mapa", control=True).add_to(mapa)
    folium.TileLayer("CartoDB positron", name="Claro", control=True).add_to(mapa)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community",
        name="Satélite",
        control=True,
    ).add_to(mapa)

    hay_fuego = validar_lat_lon(lat_fuego, lon_fuego)
    hay_zona = validar_lat_lon(lat_zona, lon_zona)

    if mostrar_cuadrantes and hay_fuego and direccion_viento_hacia in DIRECCIONES_GRADOS:
        direccion_grados = DIRECCIONES_GRADOS[direccion_viento_hacia]
        sectores = [
            ("Cuadrante de riesgo", direccion_grados, "#dc2626", 0.28),
            ("Cuadrante de alerta", direccion_grados + 90, "#f59e0b", 0.24),
            ("Cuadrante de alerta", direccion_grados - 90, "#f59e0b", 0.24),
            ("Cuadrante sin riesgo directo", direccion_grados + 180, "#10b981", 0.20),
        ]

        for nombre, direccion, color, opacidad in sectores:
            folium.Polygon(
                locations=crear_sector_latlon(lat_fuego, lon_fuego, direccion, 90, radio_cuadrantes_m),
                tooltip=nombre,
                color=color,
                weight=2,
                fill=True,
                fill_color=color,
                fill_opacity=opacidad,
            ).add_to(mapa)

        lat_viento_fin, lon_viento_fin = calcular_punto_desde_origen(
            lat_fuego,
            lon_fuego,
            direccion_grados,
            radio_cuadrantes_m,
        )
        folium.PolyLine(
            locations=[[lat_fuego, lon_fuego], [lat_viento_fin, lon_viento_fin]],
            color="#dc2626",
            weight=5,
            tooltip="Dirección del viento",
        ).add_to(mapa)

    if hay_fuego and hay_zona:
        folium.PolyLine(
            locations=[[lat_fuego, lon_fuego], [lat_zona, lon_zona]],
            color="#eab308",
            weight=5,
            tooltip="Incendio → zona vulnerable",
        ).add_to(mapa)

    if hay_fuego:
        folium.Marker(
            location=[lat_fuego, lon_fuego],
            tooltip="Incendio",
            popup=f"Incendio<br>{lat_fuego:.6f}, {lon_fuego:.6f}",
            icon=folium.Icon(color="red", icon="fire", prefix="fa"),
        ).add_to(mapa)

    if hay_zona:
        folium.Marker(
            location=[lat_zona, lon_zona],
            tooltip="Zona vulnerable",
            popup=f"Zona vulnerable<br>{lat_zona:.6f}, {lon_zona:.6f}",
            icon=folium.Icon(color="blue", icon="home", prefix="fa"),
        ).add_to(mapa)

    LocateControl(
        position="topleft",
        flyTo=True,
        strings={"title": "Mostrar mi ubicación", "popup": "Ubicación aproximada"},
    ).add_to(mapa)

    folium.LayerControl(position="topright", collapsed=True).add_to(mapa)
    return mapa


def mostrar_mapa_operativo(modo_ubicacion, objetivo_click):
    mostrar_cuadrantes = bool(st.session_state.get("calculo_realizado"))
    ultimo_calculo = st.session_state.get("ultimo_calculo") or {}

    mapa = crear_mapa_folium(
        lat_fuego=st.session_state["lat_fuego"],
        lon_fuego=st.session_state["lon_fuego"],
        lat_zona=st.session_state["lat_zona"],
        lon_zona=st.session_state["lon_zona"],
        mostrar_cuadrantes=mostrar_cuadrantes,
        direccion_viento_hacia=ultimo_calculo.get("direccion_viento_hacia"),
        radio_cuadrantes_m=ultimo_calculo.get("radio_cuadrantes_m", 1500),
    )

    mapa_data = st_folium(
        mapa,
        height=640,
        use_container_width=True,
        returned_objects=["last_clicked"],
        key="mapa_operativo_folium_v4",
    )

    if modo_ubicacion == "Seleccionar en mapa" and mapa_data and mapa_data.get("last_clicked"):
        click_lat = round(float(mapa_data["last_clicked"]["lat"]), 6)
        click_lon = round(float(mapa_data["last_clicked"]["lng"]), 6)
        firma_click = f"{objetivo_click}:{click_lat},{click_lon}"

        if firma_click != st.session_state.get("ultimo_click_mapa"):
            st.session_state["ultimo_click_mapa"] = firma_click
            if objetivo_click == "Incendio":
                set_coord("fuego", click_lat, click_lon)
                st.toast(f"Incendio actualizado: {click_lat}, {click_lon}")
            else:
                set_coord("zona", click_lat, click_lon)
                st.toast(f"Zona vulnerable actualizada: {click_lat}, {click_lon}")
            st.rerun()


# -----------------------------------------------------------------------------
# Interfaz principal
# -----------------------------------------------------------------------------

st.set_page_config(page_title="Alerta Fuego", page_icon="🔥", layout="wide")
inyectar_estilos()
inicializar_estado()

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

# -----------------------------------------------------------------------------
# 1. Mapa y ubicaciones: flujo principal
# -----------------------------------------------------------------------------

titulo_seccion(
    "1",
    "Mapa operativo y ubicaciones",
    "El mapa es ahora el punto de entrada principal. Primero fija el incendio y la zona vulnerable; los cuadrantes solo aparecen después de calcular la alerta.",
)

col_modo, col_acciones = st.columns([1.35, 1])
with col_modo:
    modo_ubicacion = st.radio(
        "Método de entrada de ubicaciones",
        ["Seleccionar en mapa", "Pegar enlace o coordenadas", "Editar coordenadas manualmente"],
        horizontal=False,
        key="modo_ubicacion",
    )

with col_acciones:
    st.write("")
    st.write("")
    col_ejemplo, col_vaciar = st.columns(2)
    with col_ejemplo:
        if st.button("Cargar ejemplo", use_container_width=True):
            cargar_ejemplo()
            st.rerun()
    with col_vaciar:
        if st.button("Vaciar", use_container_width=True):
            vaciar_ubicaciones()
            st.rerun()

objetivo_click = "Incendio"

if modo_ubicacion == "Seleccionar en mapa":
    objetivo_click = st.radio(
        "El próximo clic en el mapa se guardará como:",
        ["Incendio", "Zona vulnerable"],
        horizontal=True,
        key="objetivo_click_mapa",
    )
    st.caption("En este modo los campos manuales y el pegado de enlaces quedan ocultos. Usa el selector para decidir qué punto modificará el siguiente clic.")

elif modo_ubicacion == "Pegar enlace o coordenadas":
    with st.form("form_pegar_ubicacion"):
        destino_pegado = st.radio(
            "Asignar ubicación pegada a:",
            ["Incendio", "Zona vulnerable"],
            horizontal=True,
        )
        texto_ubicacion = st.text_area(
            "Coordenadas o enlace compartido",
            placeholder="Ejemplo coordenadas: 40.1290, -5.4610\nEjemplo Google Maps: https://www.google.com/maps/.../@40.1290,-5.4610,17z",
            height=92,
        )
        submit_pegado = st.form_submit_button("Aplicar ubicación pegada", use_container_width=True)

    if submit_pegado:
        coordenadas_extraidas = extraer_par_lat_lon_de_texto(texto_ubicacion)
        if coordenadas_extraidas is None:
            st.error(
                "No he podido extraer latitud/longitud. Si es un enlace acortado de Google Maps, "
                "prueba a abrirlo y copiar la URL completa, o pega directamente las coordenadas."
            )
        else:
            lat_extraida, lon_extraida = coordenadas_extraidas
            if destino_pegado == "Incendio":
                set_coord("fuego", lat_extraida, lon_extraida)
            else:
                set_coord("zona", lat_extraida, lon_extraida)
            st.success(f"{destino_pegado} actualizado: {lat_extraida:.6f}, {lon_extraida:.6f}")
            st.rerun()

elif modo_ubicacion == "Editar coordenadas manualmente":
    with st.form("form_manual_ubicaciones"):
        col_fuego, col_zona = st.columns(2)
        with col_fuego:
            st.markdown("**🔥 Incendio**")
            lat_fuego_txt = st.text_input(
                "Latitud del incendio",
                value="" if st.session_state["lat_fuego"] is None else f"{st.session_state['lat_fuego']:.6f}",
            )
            lon_fuego_txt = st.text_input(
                "Longitud del incendio",
                value="" if st.session_state["lon_fuego"] is None else f"{st.session_state['lon_fuego']:.6f}",
            )
        with col_zona:
            st.markdown("**🏡 Zona vulnerable**")
            lat_zona_txt = st.text_input(
                "Latitud de la zona vulnerable",
                value="" if st.session_state["lat_zona"] is None else f"{st.session_state['lat_zona']:.6f}",
            )
            lon_zona_txt = st.text_input(
                "Longitud de la zona vulnerable",
                value="" if st.session_state["lon_zona"] is None else f"{st.session_state['lon_zona']:.6f}",
            )
        submit_manual = st.form_submit_button("Aplicar coordenadas manuales", use_container_width=True)

    if submit_manual:
        lat_fuego_manual = numero_desde_texto(lat_fuego_txt)
        lon_fuego_manual = numero_desde_texto(lon_fuego_txt)
        lat_zona_manual = numero_desde_texto(lat_zona_txt)
        lon_zona_manual = numero_desde_texto(lon_zona_txt)

        if not validar_lat_lon(lat_fuego_manual, lon_fuego_manual):
            st.error("Coordenadas del incendio no válidas.")
        elif not validar_lat_lon(lat_zona_manual, lon_zona_manual):
            st.error("Coordenadas de la zona vulnerable no válidas.")
        else:
            st.session_state["lat_fuego"] = lat_fuego_manual
            st.session_state["lon_fuego"] = lon_fuego_manual
            st.session_state["lat_zona"] = lat_zona_manual
            st.session_state["lon_zona"] = lon_zona_manual
            reset_calculo()
            st.success("Coordenadas manuales aplicadas.")
            st.rerun()

mostrar_resumen_ubicaciones()

mostrar_mapa_operativo(modo_ubicacion, objetivo_click)

if st.session_state.get("calculo_realizado"):
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
else:
    st.caption("Antes del cálculo, el mapa muestra solo los puntos fijados y la línea entre ellos. Los cuadrantes aparecerán después de pulsar Calcular alerta.")

radio_cuadrantes_m = st.slider(
    "Radio visual de los cuadrantes tras el cálculo (m)",
    min_value=500,
    max_value=5000,
    value=1500,
    step=100,
    on_change=reset_calculo,
)

# -----------------------------------------------------------------------------
# 2. Viento
# -----------------------------------------------------------------------------

titulo_seccion(
    "2",
    "Viento",
    "El viento se interpreta como dirección hacia la que empuja el fuego. Si usas el modo automático, los campos manuales desaparecen.",
)

usar_viento_automatico = st.checkbox(
    "Usar viento automático desde Open-Meteo",
    value=False,
    key="usar_viento_automatico",
    on_change=reset_calculo,
)

meteo_info = None
fuente_viento = "manual"

if usar_viento_automatico:
    if not validar_lat_lon(st.session_state["lat_fuego"], st.session_state["lon_fuego"]):
        st.warning("Fija primero el punto del incendio para obtener el viento automático en esa ubicación.")
        direccion_viento_hacia = "NE"
        direccion_viento_label = CODIGO_A_LABEL_DIRECCION[direccion_viento_hacia]
        velocidad_viento_kmh = 20
        fuente_viento = "manual provisional"
    else:
        try:
            meteo_info = obtener_viento_actual_open_meteo(st.session_state["lat_fuego"], st.session_state["lon_fuego"])
            velocidad_viento_kmh = int(round(meteo_info["velocidad_kmh"]))
            direccion_viento_hacia = meteo_info["direccion_hacia_cardinal"]
            direccion_viento_label = CODIGO_A_LABEL_DIRECCION.get(direccion_viento_hacia, direccion_viento_hacia)
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
            st.error("No se pudo obtener el viento automático. Desactiva esta opción y usa entrada manual.")
            st.write(error)
            direccion_viento_hacia = "NE"
            direccion_viento_label = CODIGO_A_LABEL_DIRECCION[direccion_viento_hacia]
            velocidad_viento_kmh = 20
            fuente_viento = "manual provisional"
else:
    col_dir, col_vel = st.columns(2)
    with col_dir:
        direccion_viento_label = st.selectbox(
            "Dirección hacia la que empuja el viento",
            list(DIRECCIONES_VIENTO.keys()),
            index=list(DIRECCIONES_VIENTO.keys()).index("Hacia el nordeste ↗"),
            help="Usamos la dirección hacia la que el viento empuja el fuego, no de dónde viene.",
            key="direccion_viento_label",
            on_change=reset_calculo,
        )
        direccion_viento_hacia = DIRECCIONES_VIENTO[direccion_viento_label]

    with col_vel:
        velocidad_viento_kmh = st.slider(
            "Velocidad del viento (km/h)",
            min_value=0,
            max_value=80,
            value=20,
            step=1,
            key="velocidad_viento_kmh",
            on_change=reset_calculo,
        )

# -----------------------------------------------------------------------------
# 3. Combustible
# -----------------------------------------------------------------------------

titulo_seccion("3", "Combustible")

combustible_legible = st.selectbox(
    "Tipo de combustible dominante",
    list(COMBUSTIBLES.keys()),
    index=2,
    key="combustible_legible",
    on_change=reset_calculo,
)

tipo_combustible = COMBUSTIBLES[combustible_legible]
fuente_combustible = "manual"

# -----------------------------------------------------------------------------
# 4. Pendiente
# -----------------------------------------------------------------------------

titulo_seccion("4", "Pendiente")

usar_pendiente_automatica = st.checkbox(
    "Calcular pendiente automáticamente",
    value=False,
    key="usar_pendiente_automatica",
    on_change=reset_calculo,
)

pendiente_auto_info = None
fuente_pendiente = "manual"

if usar_pendiente_automatica:
    if not coords_completas():
        st.warning("Fija primero incendio y zona vulnerable para calcular la pendiente automática entre ambos puntos.")
        pendiente_pct = 30
        sentido_ladera = "subiendo"
        fuente_pendiente = "manual provisional"
    else:
        try:
            pendiente_auto_info = calcular_pendiente_entre_puntos(
                lat_fuego=st.session_state["lat_fuego"],
                lon_fuego=st.session_state["lon_fuego"],
                lat_zona=st.session_state["lat_zona"],
                lon_zona=st.session_state["lon_zona"],
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
            st.error("No se pudo calcular la pendiente automáticamente. Desactiva esta opción y usa entrada manual.")
            st.write(error)
            pendiente_pct = 30
            sentido_ladera = "subiendo"
            fuente_pendiente = "manual provisional"
else:
    col_pen, col_sentido = st.columns(2)
    with col_pen:
        pendiente_pct = st.slider(
            "Pendiente aproximada (%)",
            min_value=0,
            max_value=100,
            value=30,
            step=1,
            key="pendiente_pct",
            on_change=reset_calculo,
        )

    with col_sentido:
        sentidos = ["subiendo", "llano", "bajando"]
        sentido_ladera = st.selectbox(
            "Sentido de propagación respecto a la ladera",
            sentidos,
            index=sentidos.index("subiendo"),
            key="sentido_ladera",
            on_change=reset_calculo,
        )

# -----------------------------------------------------------------------------
# 5. Cálculo y salida
# -----------------------------------------------------------------------------

titulo_seccion("5", "Cálculo")
mostrar_fuentes(fuente_viento, fuente_combustible, fuente_pendiente)

if not coords_completas():
    st.warning("Falta fijar el incendio y/o la zona vulnerable. El cálculo se activará cuando ambos puntos estén definidos.")

calcular = st.button(
    "🔥 Calcular alerta",
    type="primary",
    use_container_width=True,
    disabled=not coords_completas(),
)

if calcular:
    resultado = evaluar_alerta_fuego(
        lat_fuego=st.session_state["lat_fuego"],
        lon_fuego=st.session_state["lon_fuego"],
        lat_zona=st.session_state["lat_zona"],
        lon_zona=st.session_state["lon_zona"],
        tipo_combustible=tipo_combustible,
        velocidad_viento_kmh=velocidad_viento_kmh,
        direccion_viento_hacia=direccion_viento_hacia,
        pendiente_pct=pendiente_pct,
        sentido_ladera=sentido_ladera,
    )

    st.session_state["ultimo_resultado"] = resultado
    st.session_state["ultimo_calculo"] = {
        "direccion_viento_hacia": direccion_viento_hacia,
        "radio_cuadrantes_m": radio_cuadrantes_m,
        "fuente_viento": fuente_viento,
        "fuente_combustible": fuente_combustible,
        "fuente_pendiente": fuente_pendiente,
        "velocidad_viento_kmh": velocidad_viento_kmh,
        "combustible_legible": combustible_legible,
        "pendiente_pct": pendiente_pct,
        "sentido_ladera": sentido_ladera,
        "direccion_viento_label": direccion_viento_label,
        "meteo_info": meteo_info,
        "pendiente_auto_info": pendiente_auto_info,
    }
    st.session_state["calculo_realizado"] = True
    st.rerun()

resultado_guardado = st.session_state.get("ultimo_resultado")
calculo_guardado = st.session_state.get("ultimo_calculo") or {}

if resultado_guardado is not None and st.session_state.get("calculo_realizado"):
    titulo_seccion("6", "Resultado")

    mostrar_estado_cuadrante(resultado_guardado)

    cuadrante = resultado_guardado["cuadrante"]
    distancia_texto = formatear_metros(resultado_guardado["distancia_m"])

    if cuadrante == "riesgo":
        tiempo_titulo = resultado_guardado["tiempo_llegada_texto"]
        tiempo_subtitulo = "Estimación principal porque la zona está en el cuadrante de riesgo."
    elif cuadrante in ["alerta_derecha", "alerta_izquierda"]:
        tiempo_titulo = resultado_guardado["tiempo_llegada_texto"]
        tiempo_subtitulo = "Referencia prudencial si el frente deriva lateralmente."
    else:
        tiempo_titulo = "No prioritario"
        tiempo_subtitulo = "No se muestra como alerta principal con la dirección actual del viento."

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        tarjeta_metrica("Distancia", distancia_texto, "Separación entre incendio y zona vulnerable.")
    with col_b:
        tarjeta_metrica("Tiempo", tiempo_titulo, tiempo_subtitulo)
    with col_c:
        tarjeta_metrica(
            "VPIF",
            f"{round(resultado_guardado['vpif_m_min'], 1)} m/min",
            "Velocidad estimada de propagación usada en el cálculo.",
        )

    st.markdown("### Datos usados")
    mostrar_fuentes(
        calculo_guardado.get("fuente_viento", fuente_viento),
        calculo_guardado.get("fuente_combustible", fuente_combustible),
        calculo_guardado.get("fuente_pendiente", fuente_pendiente),
    )

    col_d, col_e, col_f = st.columns(3)
    with col_d:
        tarjeta_metrica(
            "Viento",
            f"{calculo_guardado.get('velocidad_viento_kmh', velocidad_viento_kmh)} km/h",
            f"Dirección operativa: {calculo_guardado.get('direccion_viento_hacia', direccion_viento_hacia)}.",
        )
    with col_e:
        tarjeta_metrica(
            "Combustible",
            calculo_guardado.get("combustible_legible", combustible_legible),
            f"V0 = {resultado_guardado['v0']} m/min.",
        )
    with col_f:
        tarjeta_metrica(
            "Pendiente",
            f"{calculo_guardado.get('pendiente_pct', pendiente_pct)} %",
            f"Sentido: {calculo_guardado.get('sentido_ladera', sentido_ladera)}. FP = {resultado_guardado['factor_pendiente']}.",
        )

    st.markdown("### Protocolo orientativo")
    mostrar_protocolo(resultado_guardado)

    with st.expander("Ver detalles técnicos del cálculo"):
        st.write("Dirección seleccionada:", calculo_guardado.get("direccion_viento_label", direccion_viento_label))
        st.write("Código interno de viento:", calculo_guardado.get("direccion_viento_hacia", direccion_viento_hacia))
        st.write("Velocidad del viento usada:", calculo_guardado.get("velocidad_viento_kmh", velocidad_viento_kmh), "km/h")
        st.write("Fuente viento:", calculo_guardado.get("fuente_viento", fuente_viento))

        meteo_info_guardado = calculo_guardado.get("meteo_info")
        if meteo_info_guardado is not None:
            st.write("Dirección meteorológica desde:", meteo_info_guardado["direccion_desde_grados"], "°")
            st.write("Dirección operativa hacia:", meteo_info_guardado["direccion_hacia_grados"], "°")

        st.write("Combustible seleccionado:", calculo_guardado.get("combustible_legible", combustible_legible))
        st.write("Fuente combustible:", calculo_guardado.get("fuente_combustible", fuente_combustible))

        st.write("Pendiente usada:", calculo_guardado.get("pendiente_pct", pendiente_pct), "%")
        st.write("Sentido de ladera usado:", calculo_guardado.get("sentido_ladera", sentido_ladera))
        st.write("Fuente pendiente:", calculo_guardado.get("fuente_pendiente", fuente_pendiente))

        pendiente_auto_guardada = calculo_guardado.get("pendiente_auto_info")
        if pendiente_auto_guardada is not None:
            st.write("Elevación incendio:", pendiente_auto_guardada["elevacion_fuego_m"], "m")
            st.write("Elevación zona:", pendiente_auto_guardada["elevacion_zona_m"], "m")
            st.write("Desnivel:", round(pendiente_auto_guardada["desnivel_m"], 2), "m")

        st.write("Dirección incendio → zona vulnerable:", round(resultado_guardado["direccion_fuego_zona_grados"], 1), "°")
        st.write("Dirección del viento:", resultado_guardado["direccion_viento_grados"], "°")
        st.write("Diferencia angular:", round(resultado_guardado["diferencia_signed_grados"], 1), "°")
        st.write("V0 combustible:", resultado_guardado["v0"], "m/min")
        st.write("Factor viento FV:", resultado_guardado["factor_viento"])
        st.write("Factor pendiente FP:", resultado_guardado["factor_pendiente"])
        st.write("VPIF = V0 · FV · FP:", round(resultado_guardado["vpif_m_min"], 2), "m/min")

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
