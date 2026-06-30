# Estado actual del proyecto Alerta Fuego

## Fecha

Verano 2026.

## Estado general

Existe un MVP funcional en Streamlit que digitaliza el modelo base de Alerta Fuego.

La aplicación permite introducir la ubicación aproximada del incendio y de la finca o zona vulnerable, calcular la distancia, determinar el cuadrante de exposición según la dirección del viento, estimar la velocidad de propagación del incendio forestal y obtener un tiempo aproximado de alcance.

## Funcionalidades que ya funcionan

- Ejecución local con Streamlit.
- Entrada manual de coordenadas del incendio.
- Entrada manual de coordenadas de la finca o zona vulnerable.
- Cálculo de distancia entre incendio y finca.
- Cálculo de cuadrantes:
  - cuadrante de riesgo;
  - cuadrantes de alerta;
  - cuadrante sin riesgo directo.
- Cálculo del modelo documental: VPIF = V0 · FV · FP.
- Selección manual de tipo de combustible.
- Selección manual de viento.
- Selección manual de pendiente.
- Consulta automática experimental de viento con Open-Meteo.
- Estimación automática provisional de pendiente.
- Visualización en mapa:
  - incendio;
  - finca;
  - línea incendio-finca;
  - dirección del viento;
  - cuadrantes.
- Resultado con nivel/protocolo orientativo.
- Código guardado en GitHub.

## Elementos experimentales

- Viento automático mediante Open-Meteo.
- Pendiente automática mediante elevación provisional.
- Visualización de cuadrantes sobre mapa.
- Acceso desde móvil en red local.
- SIGPAC investigado, pero no integrado.

## Elementos no implementados todavía

- Despliegue público estable.
- Selección de puntos directamente sobre el mapa.
- GPS automático robusto.
- Combustible automático.
- Perfil altimétrico con IGN/CNIG.
- Pronóstico de viento próximas 3 horas.
- Comparación Open-Meteo / MeteoBlue / AEMET.
- Modo usuario / modo técnico.
- Informe exportable.
- Diseño visual profesional.
- Versión PWA o Android.

## Criterio estratégico

El MVP debe seguir respetando el modelo documental original hasta que los socios fundadores y perfiles técnicos lo validen.

No se deben introducir modelos avanzados de propagación antes de validar:

- fórmula base;
- cuadrantes;
- interpretación del viento;
- protocolos asociados al tiempo estimado;
- lenguaje de seguridad.

## Próximo bloque de trabajo

Prioridad inmediata:

1. Desplegar demo en Streamlit.
2. Mejorar interfaz visual mínima.
3. Corregir coherencia entre entradas automáticas y manuales.
4. Preparar documentación para otoño/crowdfunding.