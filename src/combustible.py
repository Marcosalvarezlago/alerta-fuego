def sugerir_combustible_por_uso(uso_texto):
    """
    Sugiere una categoría de combustible del modelo a partir de un texto de uso.

    Esta función es provisional.
    Más adelante se conectará con SIGPAC u otra fuente cartográfica.
    """

    uso = uso_texto.lower().strip()

    if any(palabra in uso for palabra in ["pasto", "pastizal", "prado", "herbáceo", "herbaceo"]):
        return {
            "tipo_combustible": "pastos_bajos",
            "confianza": "media",
            "motivo": "El uso parece corresponder a pastos o vegetación herbácea."
        }

    if any(palabra in uso for palabra in ["quercus", "encina", "roble", "dehesa", "alcornocal"]):
        return {
            "tipo_combustible": "quercus",
            "confianza": "media",
            "motivo": "El uso parece corresponder a bosque o dehesa de Quercus."
        }

    if any(palabra in uso for palabra in ["matorral", "jaral", "retama", "monte bajo", "arbustivo"]):
        return {
            "tipo_combustible": "matorral_mediterraneo",
            "confianza": "media",
            "motivo": "El uso parece corresponder a matorral o vegetación arbustiva."
        }

    if any(palabra in uso for palabra in ["pino", "pinar", "conífera", "conifera"]):
        return {
            "tipo_combustible": "pinar",
            "confianza": "media",
            "motivo": "El uso parece corresponder a pinar o coníferas."
        }

    return {
        "tipo_combustible": None,
        "confianza": "baja",
        "motivo": "No se ha podido asociar el uso a una categoría del modelo."
    }


def main():
    ejemplos = [
        "pastizal",
        "dehesa de encinas",
        "matorral mediterráneo",
        "pinar",
        "olivar",
    ]

    for ejemplo in ejemplos:
        print(ejemplo, "→", sugerir_combustible_por_uso(ejemplo))


if __name__ == "__main__":
    main()