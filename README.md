# Alerta Fuego

Prototipo experimental de apoyo ciudadano para estimar, de forma orientativa, el riesgo de alcance de un incendio forestal a una finca o zona vulnerable.

## Estado del proyecto

Versión inicial demostrativa.

El objetivo actual es reproducir de forma digital el modelo documental base del grupo Alerta Fuego, sin modificar todavía sus supuestos principales.

Este repositorio contiene una demo experimental no oficial. No incluye datos reales de incendios, fincas ni personas.

## Modelo usado

La aplicación sigue el esquema:

1. Localización del incendio.
2. Localización de la finca o zona vulnerable.
3. Evaluación de cuadrantes según dirección del viento.
4. Estimación de velocidad de propagación:

```text
VPIF = V0 · FV · FP