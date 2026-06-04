def estimar_velocidad_avance(velocidad_base, factor_viento, factor_pendiente, factor_combustible):
    """
    Estima la velocidad de avance del frente del fuego.

    Todos los factores son multiplicadores simples.
    """
    return velocidad_base * factor_viento * factor_pendiente * factor_combustible


def estimar_distancia(velocidad_avance_m_min, tiempo_min):
    """
    Estima la distancia recorrida por el frente del fuego.
    """
    return velocidad_avance_m_min * tiempo_min


def main():
    velocidad_base = 1.0       # m/min en condiciones neutras
    factor_viento = 2.0        # el viento duplica el avance
    factor_pendiente = 1.3     # la pendiente aumenta un 30 %
    factor_combustible = 1.5   # combustible más favorable al fuego
    tiempo = 30                # minutos

    velocidad_avance = estimar_velocidad_avance(
        velocidad_base,
        factor_viento,
        factor_pendiente,
        factor_combustible
    )

    distancia = estimar_distancia(velocidad_avance, tiempo)

    print("Modelo inicial de propagación")
    print("-----------------------------")
    print("Velocidad base:", velocidad_base, "m/min")
    print("Factor viento:", factor_viento)
    print("Factor pendiente:", factor_pendiente)
    print("Factor combustible:", factor_combustible)
    print("Velocidad estimada:", velocidad_avance, "m/min")
    print("Tiempo:", tiempo, "min")
    print("Distancia estimada:", distancia, "m")


if __name__ == "__main__":
    main()