import math


DIRECCIONES_GRADOS = {
    "N": 0,
    "NE": 45,
    "E": 90,
    "SE": 135,
    "S": 180,
    "SO": 225,
    "O": 270,
    "NO": 315,
}


def calcular_distancia_m(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia aproximada entre dos puntos geográficos usando Haversine.
    Devuelve la distancia en metros.
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


def calcular_direccion_grados(lat1, lon1, lat2, lon2):
    """
    Calcula la dirección desde el fuego hacia la zona vulnerable.
    Devuelve grados: N=0, E=90, S=180, O=270.
    """
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlon_rad = math.radians(lon2 - lon1)

    x = math.sin(dlon_rad) * math.cos(lat2_rad)
    y = (
        math.cos(lat1_rad) * math.sin(lat2_rad)
        - math.sin(lat1_rad)
        * math.cos(lat2_rad)
        * math.cos(dlon_rad)
    )

    angulo = math.degrees(math.atan2(x, y))
    return (angulo + 360) % 360


def diferencia_signed_grados(direccion_objetivo, direccion_viento):
    """
    Calcula la diferencia angular firmada entre:
    - dirección del viento
    - dirección desde el fuego hacia la zona vulnerable

    Resultado en intervalo [-180, 180].
    """
    return (direccion_objetivo - direccion_viento + 180) % 360 - 180


def clasificar_cuadrante_documental(diferencia_signed):
    """
    Clasifica según los 4 cuadrantes del documento:

    - Riesgo: zona situada en el cuadrante hacia el que empuja el viento.
    - Alerta derecha / izquierda: cuadrantes laterales.
    - Sin riesgo: cuadrante opuesto al viento.

    Cada cuadrante ocupa 90º.
    """
    if -45 <= diferencia_signed <= 45:
        return "riesgo"

    if 45 < diferencia_signed <= 135:
        return "alerta_derecha"

    if -135 <= diferencia_signed < -45:
        return "alerta_izquierda"

    return "sin_riesgo"


def obtener_descripcion_cuadrante(cuadrante):
    descripciones = {
        "riesgo": (
            "La zona vulnerable está en el cuadrante de riesgo, hacia donde "
            "empuja el viento desde el punto del incendio."
        ),
        "alerta_derecha": (
            "La zona vulnerable está en un cuadrante de alerta lateral respecto "
            "a la dirección principal del viento."
        ),
        "alerta_izquierda": (
            "La zona vulnerable está en un cuadrante de alerta lateral respecto "
            "a la dirección principal del viento."
        ),
        "sin_riesgo": (
            "La zona vulnerable está en el cuadrante opuesto a la dirección "
            "principal del viento. No obstante, debe mantenerse vigilancia."
        ),
    }

    return descripciones[cuadrante]


def obtener_v0_combustible(tipo_combustible):
    """
    Velocidad base orientativa según tipo de combustible.
    Valores del documento Alerta Fuego.
    """
    valores = {
        "pastos_bajos": 3,
        "quercus": 4,
        "matorral_mediterraneo": 6,
        "pinar": 8,
    }

    return valores[tipo_combustible]


def obtener_factor_viento(velocidad_viento_kmh):
    """
    Factor FV según velocidad del viento.
    """
    if velocidad_viento_kmh < 10:
        return 1
    elif velocidad_viento_kmh < 20:
        return 1.5
    elif velocidad_viento_kmh < 30:
        return 2
    else:
        return 3


def obtener_factor_pendiente(pendiente_pct, sentido_ladera):
    """
    Factor FP según pendiente.

    sentido_ladera:
    - subiendo
    - llano
    - bajando
    """
    if sentido_ladera == "bajando":
        return 0.7

    if sentido_ladera == "llano":
        return 1

    if pendiente_pct < 20:
        return 1
    elif pendiente_pct <= 40:
        return 1.5
    else:
        return 2


def estimar_velocidad_propagacion(v0, factor_viento, factor_pendiente):
    """
    Calcula VPIF = V0 * FV * FP.
    Devuelve m/min.
    """
    return v0 * factor_viento * factor_pendiente


def calcular_tiempo_llegada_min(distancia_m, velocidad_propagacion_m_min):
    """
    Calcula el tiempo estimado de llegada del frente del incendio.
    """
    if velocidad_propagacion_m_min <= 0:
        return None

    return distancia_m / velocidad_propagacion_m_min


def formatear_tiempo(tiempo_min):
    """
    Convierte minutos en texto legible.
    """
    if tiempo_min is None:
        return "indeterminado"

    horas = int(tiempo_min // 60)
    minutos = int(round(tiempo_min % 60))

    if horas == 0:
        return f"{minutos} min"

    return f"{horas} h {minutos} min"


def clasificar_escenario_tiempo(tiempo_min):
    """
    Clasifica según los escenarios del protocolo.
    """
    if tiempo_min is None:
        return "indeterminado"

    if tiempo_min <= 30:
        return "30_min"
    elif tiempo_min <= 60:
        return "1_hora"
    elif tiempo_min <= 90:
        return "1_hora_y_media"
    else:
        return "vigilancia_preventiva"


def obtener_protocolo(escenario):
    """
    Devuelve protocolo orientativo según tiempo estimado de impacto.
    """
    protocolos = {
        "30_min": {
            "titulo": "SI EL INCENDIO TE ALCANZA EN 30 MINUTOS",
            "acciones": [
                "Mantén la calma y sigue las indicaciones de emergencias: 112, INFOEX o Protección Civil.",
                "Prepara documentación esencial: DNI, escrituras, seguros, tarjetas sanitarias, cartillas de animales, llaves y copias.",
                "Prepara medicación diaria si la necesitas.",
                "Prepara un kit básico: agua, linterna, botiquín, radio, teléfono, cargador, ropa de muda y ropa de algodón.",
                "Protege vías respiratorias y ojos frente al humo.",
                "Cierra llaves de gas y electricidad.",
                "Cierra puertas y ventanas.",
                "Retira cortinas y materiales combustibles visibles.",
                "Guarda mobiliario de jardín, toldos o elementos similares.",
                "Activa sistemas pasivos de defensa solo si no supone riesgo.",
                "Asegura animales y prepara su evacuación si es posible.",
                "Sal inmediatamente cuando lo indiquen las autoridades.",
                "Usa rutas seguras y evita caminos estrechos rodeados de vegetación.",
                "No regreses hasta autorización oficial.",
            ],
        },
        "1_hora": {
            "titulo": "SI EL INCENDIO TE ALCANZA EN 1 HORA",
            "acciones": [
                "Retira objetos inflamables: mobiliario de jardín, toldos, cortinas, leña, pinturas, barnices o combustibles.",
                "Revisa almacenes, maquinaria, infraestructuras ganaderas y vivienda.",
                "Activa sistemas pasivos de defensa o moja el entorno inmediato si es seguro.",
                "Retira biomasa forestal cercana si puede hacerse sin riesgo y en poco tiempo.",
                "Cierra depósitos de gas o combustibles.",
                "Comprueba por canales oficiales si se prevé evacuación o confinamiento.",
                "Deja libres los accesos para vehículos de emergencia.",
                "Avisa a familiares o vecinos vulnerables.",
                "Prepárate para evacuar o confinar siguiendo indicaciones oficiales.",
            ],
        },
        "1_hora_y_media": {
            "titulo": "SI EL INCENDIO TE ALCANZA EN 1 HORA Y MEDIA",
            "acciones": [
                "Aplica todo lo recomendado anteriormente si procede.",
                "Identifica la ruta de evacuación recomendada y un punto de encuentro seguro.",
                "Revisa que todas las personas del hogar saben qué hacer y a dónde dirigirse.",
                "Cierra depósitos de gas o combustibles.",
                "Mantente informado por fuentes oficiales.",
                "Prepara animales domésticos para un posible traslado.",
                "Asegura que el vehículo tiene combustible suficiente.",
                "Guarda documentos importantes en un lugar fácil de llevar.",
                "Retira muebles de exterior, cortinas o elementos que puedan favorecer la entrada de brasas, siempre que no suponga riesgo.",
                "Comprueba que personas dependientes o con movilidad reducida tienen apoyo garantizado.",
                "Sigue la evolución del incendio sin caer en rumores: solo fuentes oficiales.",
            ],
        },
        "vigilancia_preventiva": {
            "titulo": "VIGILANCIA PREVENTIVA",
            "acciones": [
                "Mantén vigilancia activa de la evolución del incendio.",
                "Comprueba cambios de viento y evolución del frente.",
                "Ten preparado un plan de evacuación de la finca.",
                "Prepara documentación, medicación, animales y vías de salida.",
                "Consulta solo fuentes oficiales.",
                "No uses esta estimación para apurar los tiempos.",
            ],
        },
        "alerta_lateral": {
            "titulo": "CUADRANTE DE ALERTA",
            "acciones": [
                "Mantén vigilancia activa.",
                "Revisa la evolución del viento para esa hora y las 3 siguientes.",
                "Prepara documentación, medicación, animales y vías de salida.",
                "Comprueba accesos y posibles rutas de evacuación.",
                "Consulta fuentes oficiales y avisos de emergencia.",
                "Si el viento cambia hacia tu zona, recalcula inmediatamente.",
            ],
        },
        "sin_riesgo": {
            "titulo": "CUADRANTE SIN RIESGO DIRECTO SEGÚN VIENTO ACTUAL",
            "acciones": [
                "Mantén vigilancia preventiva.",
                "No interpretes este resultado como ausencia absoluta de peligro.",
                "Revisa cambios de viento, pavesas y posibles focos secundarios.",
                "Consulta fuentes oficiales.",
                "Recalcula si cambia la dirección del viento.",
            ],
        },
        "indeterminado": {
            "titulo": "ESCENARIO INDETERMINADO",
            "acciones": [
                "No se puede estimar el tiempo de llegada con los datos actuales.",
                "Consulta fuentes oficiales.",
                "Llama al 112 si existe peligro inmediato.",
            ],
        },
    }

    return protocolos[escenario]


def evaluar_alerta_fuego(
    lat_fuego,
    lon_fuego,
    lat_zona,
    lon_zona,
    tipo_combustible,
    velocidad_viento_kmh,
    direccion_viento_hacia,
    pendiente_pct,
    sentido_ladera,
):
    """
    Evalúa el cuadrante de exposición y, si procede, el tiempo estimado de llegada.
    """

    distancia_m = calcular_distancia_m(
        lat_fuego,
        lon_fuego,
        lat_zona,
        lon_zona,
    )

    direccion_fuego_zona = calcular_direccion_grados(
        lat_fuego,
        lon_fuego,
        lat_zona,
        lon_zona,
    )

    direccion_viento_grados = DIRECCIONES_GRADOS[direccion_viento_hacia]

    diferencia_signed = diferencia_signed_grados(
        direccion_fuego_zona,
        direccion_viento_grados,
    )

    cuadrante = clasificar_cuadrante_documental(diferencia_signed)
    descripcion_cuadrante = obtener_descripcion_cuadrante(cuadrante)

    v0 = obtener_v0_combustible(tipo_combustible)
    fv = obtener_factor_viento(velocidad_viento_kmh)
    fp = obtener_factor_pendiente(pendiente_pct, sentido_ladera)

    vpif = estimar_velocidad_propagacion(v0, fv, fp)

    tiempo_llegada_min = calcular_tiempo_llegada_min(distancia_m, vpif)

    if cuadrante == "riesgo":
        escenario = clasificar_escenario_tiempo(tiempo_llegada_min)
    elif cuadrante in ["alerta_derecha", "alerta_izquierda"]:
        escenario = "alerta_lateral"
    else:
        escenario = "sin_riesgo"

    protocolo = obtener_protocolo(escenario)

    return {
        "distancia_m": distancia_m,
        "direccion_fuego_zona_grados": direccion_fuego_zona,
        "direccion_viento_grados": direccion_viento_grados,
        "diferencia_signed_grados": diferencia_signed,
        "cuadrante": cuadrante,
        "descripcion_cuadrante": descripcion_cuadrante,
        "v0": v0,
        "factor_viento": fv,
        "factor_pendiente": fp,
        "vpif_m_min": vpif,
        "tiempo_llegada_min": tiempo_llegada_min,
        "tiempo_llegada_texto": formatear_tiempo(tiempo_llegada_min),
        "escenario": escenario,
        "protocolo": protocolo,
    }


def main():
    resultado = evaluar_alerta_fuego(
        lat_fuego=40.1290,
        lon_fuego=-5.4610,
        lat_zona=40.1350,
        lon_zona=-5.4550,
        tipo_combustible="matorral_mediterraneo",
        velocidad_viento_kmh=20,
        direccion_viento_hacia="NE",
        pendiente_pct=30,
        sentido_ladera="subiendo",
    )

    print("ALERTA FUEGO - MVP 0.3")
    print("----------------------")
    print("Distancia:", round(resultado["distancia_m"], 2), "m")
    print("Dirección fuego-zona:", round(resultado["direccion_fuego_zona_grados"], 1), "°")
    print("Dirección viento:", resultado["direccion_viento_grados"], "°")
    print("Diferencia angular:", round(resultado["diferencia_signed_grados"], 1), "°")
    print("Cuadrante:", resultado["cuadrante"])
    print("VPIF:", round(resultado["vpif_m_min"], 2), "m/min")
    print("Tiempo estimado:", resultado["tiempo_llegada_texto"])
    print(resultado["protocolo"]["titulo"])


if __name__ == "__main__":
    main()