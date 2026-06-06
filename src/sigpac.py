import math
import re
import html
import requests
import urllib3


SIGPAC_WMS_URL = "https://sigpac-hubcloud.es/wms"
LAYER_RECINTO = "AU.Sigpac:recinto"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def lonlat_a_webmercator(lon, lat):
    """
    Convierte lon/lat WGS84 a Web Mercator EPSG:3857.
    """
    radio = 6378137.0
    x = radio * math.radians(lon)
    y = radio * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    return x, y


def limpiar_html_basico(texto):
    """
    Limpia HTML de forma sencilla para diagnóstico.
    """
    texto = re.sub(r"<br\s*/?>", "\n", texto, flags=re.IGNORECASE)
    texto = re.sub(r"</tr>", "\n", texto, flags=re.IGNORECASE)
    texto = re.sub(r"</td>", " | ", texto, flags=re.IGNORECASE)
    texto = re.sub(r"<[^>]+>", "", texto)
    texto = html.unescape(texto)
    texto = re.sub(r"\n\s*\n+", "\n", texto)
    return texto.strip()


def extraer_tabla_html(texto_html):
    """
    Extrae pares campo-valor de una tabla HTML sencilla.
    Si no puede, devuelve texto limpio.
    """
    filas = re.findall(r"<tr[^>]*>(.*?)</tr>", texto_html, flags=re.IGNORECASE | re.DOTALL)

    resultado = {}

    for fila in filas:
        celdas = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", fila, flags=re.IGNORECASE | re.DOTALL)
        celdas_limpias = [limpiar_html_basico(celda).strip() for celda in celdas]

        if len(celdas_limpias) >= 2:
            clave = celdas_limpias[0]
            valor = celdas_limpias[1]
            if clave:
                resultado[clave] = valor

    if resultado:
        return resultado

    return {"texto": limpiar_html_basico(texto_html)}


def consultar_sigpac_punto(lat, lon, radio_mapa_m=250):
    """
    Consulta propiedades SIGPAC de un punto mediante WMS GetFeatureInfo.

    Se construye una pequeña ventana de mapa en EPSG:3857 alrededor del punto
    y se consulta el píxel central, imitando el ejemplo oficial de Leaflet/OpenLayers.
    """

    x, y = lonlat_a_webmercator(lon, lat)

    bbox = (
        f"{x - radio_mapa_m},"
        f"{y - radio_mapa_m},"
        f"{x + radio_mapa_m},"
        f"{y + radio_mapa_m}"
    )

    width = 101
    height = 101

    params = {
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": "GetFeatureInfo",
        "LAYERS": LAYER_RECINTO,
        "QUERY_LAYERS": LAYER_RECINTO,
        "CRS": "EPSG:3857",
        "SRS": "EPSG:3857",
        "BBOX": bbox,
        "WIDTH": width,
        "HEIGHT": height,
        "I": width // 2,
        "J": height // 2,
        "FORMAT": "image/png",
        "INFO_FORMAT": "text/html",
        "FEATURE_COUNT": 5,
        "STYLES": "",
        "TRANSPARENT": "true",
    }

    respuesta = requests.get(
        SIGPAC_WMS_URL,
        params=params,
        timeout=30,
        verify=False,
    )

    respuesta.raise_for_status()

    texto_html = respuesta.text
    datos = extraer_tabla_html(texto_html)

    return {
        "url": respuesta.url,
        "html": texto_html,
        "datos": datos,
    }


def sugerir_combustible_desde_sigpac(datos):
    """
    Intenta sugerir combustible a partir de campos SIGPAC.

    Esta equivalencia es provisional: SIGPAC no es un mapa forestal de combustible.
    """
    texto = " ".join(str(v) for v in datos.values()).lower()

    if any(p in texto for p in ["pastos", "pasto", "pastizal", "prado"]):
        return {
            "tipo_combustible": "pastos_bajos",
            "confianza": "media",
            "motivo": "El texto SIGPAC contiene referencias a pastos o pastizales.",
        }

    if any(p in texto for p in ["forestal", "matorral", "monte", "arbustivo"]):
        return {
            "tipo_combustible": "matorral_mediterraneo",
            "confianza": "baja",
            "motivo": "El texto SIGPAC sugiere uso forestal o monte, pero requiere confirmación visual.",
        }

    if any(p in texto for p in ["pinar", "pino", "conífera", "conifera"]):
        return {
            "tipo_combustible": "pinar",
            "confianza": "media",
            "motivo": "El texto SIGPAC contiene referencias a pinar o coníferas.",
        }

    if any(p in texto for p in ["encina", "roble", "quercus", "dehesa"]):
        return {
            "tipo_combustible": "quercus",
            "confianza": "media",
            "motivo": "El texto SIGPAC contiene referencias a Quercus, encinar, robledal o dehesa.",
        }

    return {
        "tipo_combustible": None,
        "confianza": "baja",
        "motivo": "No se ha podido asociar automáticamente el recinto a una categoría del modelo.",
    }


def main():
    lat = 40.1290
    lon = -5.4610

    print("Probando SIGPAC GetFeatureInfo")
    print("------------------------------")
    print("Capa:", LAYER_RECINTO)
    print("Latitud:", lat)
    print("Longitud:", lon)
    print()

    try:
        resultado = consultar_sigpac_punto(lat, lon)

        print("URL consultada:")
        print(resultado["url"])
        print()

        print("HTML crudo recibido:")
        print("-------------------")
        print(resultado["html"][:3000])
        print()

        print("Datos extraídos:")
        print("----------------")
        for clave, valor in resultado["datos"].items():
            print(f"{clave}: {valor}")

        print()
        print("Sugerencia de combustible:")
        print("--------------------------")
        sugerencia = sugerir_combustible_desde_sigpac(resultado["datos"])
        print(sugerencia)

    except Exception as error:
        print("Error consultando SIGPAC:")
        print(error)


if __name__ == "__main__":
    main()