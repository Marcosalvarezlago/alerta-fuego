def estimar_distancia(velocidad_avance_m_min, tiempo_min):
    """
    Estima la distancia recorrida por el frente del fuego.

    Parámetros:
    velocidad_avance_m_min: velocidad de avance en metros por minuto
    tiempo_min: tiempo transcurrido en minutos
    """
    return velocidad_avance_m_min * tiempo_min


def main():
    velocidad = 2.5  # metros por minuto
    tiempo = 30      # minutos

    distancia = estimar_distancia(velocidad, tiempo)

    print("Modelo inicial de propagación")
    print("-----------------------------")
    print("Velocidad de avance:", velocidad, "m/min")
    print("Tiempo:", tiempo, "min")
    print("Distancia estimada:", distancia, "m")


if __name__ == "__main__":
    main()