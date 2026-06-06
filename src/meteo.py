import requests


def grados_a_direccion_cardinal(grados):
    """
    Convierte grados en una dirección cardinal de 8 rumbos.

    Convención:
    N  = 0º
    NE = 45º
    E  = 90º
    SE = 135º
    S  = 180º
    SO = 225º
    O  = 270º
    NO = 315º
    """
    direcciones = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
    indice = round(grados / 45) % 8
    return direcciones[indice]


def direccion_desde_a_hacia(grados_desde):
    """
    Convierte dirección meteorológica en dirección operativa.

    Las APIs meteorológicas suelen dar la dirección DESDE donde viene el viento.
    Para el modelo necesitamos la dirección HACIA donde empuja el fuego.

    Ejemplo:
    - viento desde el oeste: 270º
    - empuja hacia el este: 90º
    """
    return (grados_desde + 180) % 360


def obtener_viento_actual_open_meteo(lat, lon):
    """
    Obtiene viento actual aproximado desde Open-Meteo.

    Devuelve:
    - velocidad_kmh
    - direccion_desde_grados
    - direccion_hacia_grados
    - direccion_hacia_cardinal
    """

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "wind_speed_10m,wind_direction_10m",
        "wind_speed_unit": "kmh",
        "timezone": "auto",
    }

    respuesta = requests.get(url, params=params, timeout=10)
    respuesta.raise_for_status()

    datos = respuesta.json()

    if "current" not in datos:
        raise ValueError("La respuesta de Open-Meteo no contiene datos actuales.")

    actual = datos["current"]

    velocidad_kmh = actual["wind_speed_10m"]
    direccion_desde_grados = actual["wind_direction_10m"]

    direccion_hacia_grados = direccion_desde_a_hacia(direccion_desde_grados)
    direccion_hacia_cardinal = grados_a_direccion_cardinal(direccion_hacia_grados)

    return {
        "velocidad_kmh": velocidad_kmh,
        "direccion_desde_grados": direccion_desde_grados,
        "direccion_hacia_grados": direccion_hacia_grados,
        "direccion_hacia_cardinal": direccion_hacia_cardinal,
    }


def main():
    print("Probando servicio meteorológico Open-Meteo...")
    print("--------------------------------------------")

    lat = 40.1290
    lon = -5.4610

    print("Coordenadas de prueba:")
    print("Latitud:", lat)
    print("Longitud:", lon)
    print()

    try:
        viento = obtener_viento_actual_open_meteo(lat, lon)

        print("Datos de viento obtenidos:")
        print("Velocidad:", viento["velocidad_kmh"], "km/h")
        print("Dirección meteorológica desde:", viento["direccion_desde_grados"], "º")
        print("Dirección operativa hacia:", viento["direccion_hacia_grados"], "º")
        print("Dirección cardinal hacia:", viento["direccion_hacia_cardinal"])

    except requests.exceptions.RequestException as error:
        print("Error de conexión con Open-Meteo:")
        print(error)

    except Exception as error:
        print("Error inesperado:")
        print(error)


if __name__ == "__main__":
    main()