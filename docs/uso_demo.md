# Uso demo · Alerta Fuego

## Objetivo de la demo

Mostrar una versión mínima funcional de la herramienta Alerta Fuego, respetando el modelo documental de referencia.

La app permite estimar de forma orientativa el tiempo de alcance de un incendio forestal a una finca o zona vulnerable.

## Flujo de uso

1. Introducir coordenadas del incendio.
2. Introducir coordenadas de la finca o zona vulnerable.
3. Seleccionar o automatizar viento.
4. Seleccionar tipo de combustible dominante.
5. Introducir o estimar pendiente.
6. Visualizar cuadrantes.
7. Calcular alerta.
8. Revisar protocolo orientativo.

## Datos de entrada

- Latitud y longitud del incendio.
- Latitud y longitud de la zona vulnerable.
- Dirección hacia la que empuja el viento.
- Velocidad del viento.
- Tipo de combustible dominante.
- Pendiente aproximada.
- Sentido de propagación respecto a la ladera.

## Datos de salida

- Cuadrante de exposición.
- Distancia entre incendio y zona vulnerable.
- VPIF estimada.
- Tiempo estimado de alcance.
- Protocolo orientativo.

## Limitaciones

Esta herramienta no sustituye al 112, INFOEX, Protección Civil, bomberos ni autoridades competentes.

Es una estimación orientativa. El documento base advierte que es una “estimación grosera, no un modelo profesional” y que los cálculos sirven “para decidir retirarse antes, no para apurar más”. :contentReference[oaicite:1]{index=1}

## Estado actual

Versión demostrativa local.

Funcionalidades activas:

- mapa con cuadrantes;
- viento automático opcional;
- pendiente automática provisional;
- cálculo documental VPIF;
- protocolos por tiempo estimado.

Funcionalidades no incluidas todavía:

- GPS fiable;
- SIGPAC automático;
- perfil topográfico avanzado;
- pronóstico horario;
- simulación dinámica.