import requests
import math


def calcular_distancia_m(lat1, lon1, lat2, lon2):
    """
    Calcula distancia aproximada entre dos puntos usando Haversine.
    """
    radio_tierra_m = 6371000

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return radio_tierra_m * c


def obtener_elevacion_open_meteo(lat, lon):
    """
    Obtiene elevación aproximada para unas coordenadas.
    Implementación provisional para MVP.
    """
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m",
        "timezone": "auto",
    }

    respuesta = requests.get(url, params=params, timeout=10)
    respuesta.raise_for_status()

    datos = respuesta.json()

    if "elevation" not in datos:
        raise ValueError("La respuesta no contiene elevación.")

    return datos["elevation"]


def calcular_pendiente_entre_puntos(lat_fuego, lon_fuego, lat_zona, lon_zona):
    """
    Calcula pendiente aproximada entre incendio y zona vulnerable.

    Devuelve:
    - elevación fuego
    - elevación zona
    - desnivel
    - distancia
    - pendiente %
    - sentido de ladera para el modelo documental
    """
    elevacion_fuego = obtener_elevacion_open_meteo(lat_fuego, lon_fuego)
    elevacion_zona = obtener_elevacion_open_meteo(lat_zona, lon_zona)

    distancia_m = calcular_distancia_m(
        lat_fuego,
        lon_fuego,
        lat_zona,
        lon_zona,
    )

    desnivel_m = elevacion_zona - elevacion_fuego

    if distancia_m == 0:
        pendiente_pct = 0
    else:
        pendiente_pct = abs(desnivel_m) / distancia_m * 100

    if abs(desnivel_m) < 5:
        sentido_ladera = "llano"
    elif desnivel_m > 0:
        sentido_ladera = "subiendo"
    else:
        sentido_ladera = "bajando"

    return {
        "elevacion_fuego_m": elevacion_fuego,
        "elevacion_zona_m": elevacion_zona,
        "desnivel_m": desnivel_m,
        "distancia_m": distancia_m,
        "pendiente_pct": pendiente_pct,
        "sentido_ladera": sentido_ladera,
        "fuente": "Open-Meteo elevation provisional",
    }


def main():
    resultado = calcular_pendiente_entre_puntos(
        lat_fuego=40.1290,
        lon_fuego=-5.4610,
        lat_zona=40.1350,
        lon_zona=-5.4550,
    )

    print("Pendiente automática")
    print("--------------------")
    print("Elevación incendio:", resultado["elevacion_fuego_m"], "m")
    print("Elevación zona:", resultado["elevacion_zona_m"], "m")
    print("Desnivel:", round(resultado["desnivel_m"], 2), "m")
    print("Distancia:", round(resultado["distancia_m"], 2), "m")
    print("Pendiente:", round(resultado["pendiente_pct"], 2), "%")
    print("Sentido:", resultado["sentido_ladera"])
    print("Fuente:", resultado["fuente"])


if __name__ == "__main__":
    main()