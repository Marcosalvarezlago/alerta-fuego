import math


# -----------------------------
# 1. DISTANCIA ENTRE UBICACIONES
# -----------------------------

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


# -----------------------------
# 2. FACTORES DEL MODELO
# -----------------------------

def obtener_v0_combustible(tipo_combustible):
    """
    Valor base V0 según tipo de combustible.
    Valores orientativos tomados del protocolo Alerta Fuego.
    """
    valores = {
        "pastos_bajos": 3,
        "quercus": 4,
        "matorral_mediterraneo": 6,
        "pinar": 8
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
    - "subiendo"
    - "bajando"
    - "llano"
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


# -----------------------------
# 3. PROPAGACIÓN Y TIEMPO
# -----------------------------

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


# -----------------------------
# 4. CLASIFICACIÓN SEGÚN PROTOCOLO
# -----------------------------

def clasificar_escenario(tiempo_min):
    """
    Clasifica según los escenarios del protocolo:
    - 30 minutos
    - 1 hora
    - 1 hora y media
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
                "No regreses hasta autorización oficial."
            ]
        },
        "1_hora": {
            "titulo": "SI EL INCENDIO TE ALCANZA EN 1 HORA",
            "acciones": [
                "Todavía hay poco tiempo, pero permite preparar mejor la situación.",
                "Retira objetos inflamables: mobiliario de jardín, sillas, toldos, cortinas, leña, pinturas, barnices o combustibles.",
                "Revisa almacenes, maquinaria, infraestructuras ganaderas y vivienda.",
                "Activa sistemas pasivos de defensa o moja el entorno inmediato si es seguro.",
                "Retira biomasa forestal cercana si puede hacerse sin riesgo y en poco tiempo.",
                "Cierra depósitos de gas o combustibles.",
                "Comprueba por canales oficiales si se prevé evacuación o confinamiento.",
                "Deja libres los accesos para vehículos de emergencia.",
                "Avisa a familiares o vecinos vulnerables para que estén preparados.",
                "Prepárate para evacuar o confinar siguiendo indicaciones oficiales."
            ]
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
                "Guarda documentos u objetos importantes en un lugar fácil de llevar.",
                "Retira muebles de exterior, cortinas o elementos que puedan favorecer la entrada de brasas, siempre que no suponga riesgo.",
                "Comprueba que personas dependientes o con movilidad reducida tienen apoyo garantizado.",
                "Evita rumores y sigue solo fuentes oficiales."
            ]
        },
        "vigilancia_preventiva": {
            "titulo": "VIGILANCIA PREVENTIVA",
            "acciones": [
                "Mantén vigilancia activa de la evolución del incendio.",
                "Revisa cambios de viento, pendiente y dirección del frente.",
                "Ten preparado un plan de evacuación de la finca.",
                "Prepara documentación, medicación, animales y vías de salida.",
                "Consulta solo fuentes oficiales.",
                "No uses esta estimación para apurar los tiempos."
            ]
        },
        "indeterminado": {
            "titulo": "ESCENARIO INDETERMINADO",
            "acciones": [
                "No se puede estimar el tiempo de llegada con los datos actuales.",
                "Consulta fuentes oficiales.",
                "Llama al 112 si existe peligro inmediato."
            ]
        }
    }

    return protocolos[escenario]


# -----------------------------
# 5. FUNCIÓN PRINCIPAL DEL MODELO
# -----------------------------

def evaluar_alerta_fuego(
    lat_fuego,
    lon_fuego,
    lat_zona,
    lon_zona,
    tipo_combustible,
    velocidad_viento_kmh,
    pendiente_pct,
    sentido_ladera
):
    """
    Evalúa el tiempo estimado de llegada del incendio a una zona protegida.
    """

    distancia_m = calcular_distancia_m(
        lat_fuego,
        lon_fuego,
        lat_zona,
        lon_zona
    )

    v0 = obtener_v0_combustible(tipo_combustible)
    fv = obtener_factor_viento(velocidad_viento_kmh)
    fp = obtener_factor_pendiente(pendiente_pct, sentido_ladera)

    velocidad_propagacion = estimar_velocidad_propagacion(v0, fv, fp)

    tiempo_llegada_min = calcular_tiempo_llegada_min(
        distancia_m,
        velocidad_propagacion
    )

    escenario = clasificar_escenario(tiempo_llegada_min)
    protocolo = obtener_protocolo(escenario)

    resultado = {
        "distancia_m": distancia_m,
        "v0": v0,
        "factor_viento": fv,
        "factor_pendiente": fp,
        "velocidad_propagacion_m_min": velocidad_propagacion,
        "tiempo_llegada_min": tiempo_llegada_min,
        "tiempo_llegada_texto": formatear_tiempo(tiempo_llegada_min),
        "escenario": escenario,
        "protocolo": protocolo
    }

    return resultado


# -----------------------------
# 6. PRUEBA MANUAL
# -----------------------------

def main():
    resultado = evaluar_alerta_fuego(
        lat_fuego=40.1290,
        lon_fuego=-5.4610,
        lat_zona=40.1350,
        lon_zona=-5.4550,
        tipo_combustible="matorral_mediterraneo",
        velocidad_viento_kmh=20,
        pendiente_pct=30,
        sentido_ladera="subiendo"
    )

    print("ALERTA FUEGO - MVP 0.1")
    print("----------------------")
    print("Distancia a zona protegida:", round(resultado["distancia_m"], 2), "m")
    print("V0 combustible:", resultado["v0"], "m/min")
    print("Factor viento:", resultado["factor_viento"])
    print("Factor pendiente:", resultado["factor_pendiente"])
    print("Velocidad estimada de propagación:", round(resultado["velocidad_propagacion_m_min"], 2), "m/min")
    print("Tiempo estimado de llegada:", resultado["tiempo_llegada_texto"])
    print()
    print(resultado["protocolo"]["titulo"])
    print()
    print("Protocolo orientativo:")
    for accion in resultado["protocolo"]["acciones"]:
        print("-", accion)

    print()
    print("AVISO:")
    print("Estimación orientativa. No sustituye indicaciones oficiales ni llamadas al 112.")


if __name__ == "__main__":
    main()