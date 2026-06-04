def estimar_distancia(velocidad_avance_m_min, tiempo_min):
    """
    Estima la distancia recorrida por el frente del fuego.

    velocidad_avance_m_min: velocidad de avance en metros por minuto
    tiempo_min: tiempo transcurrido en minutos
    """
    distancia = velocidad_avance_m_min * tiempo_min
    return distancia


# Prueba inicial
velocidad = 2.5  # metros por minuto
tiempo = 30      # minutos

distancia = estimar_distancia(velocidad, tiempo)

print("Distancia estimada:", distancia, "metros")