# Backlog técnico · Alerta Fuego

## Criterio actual

La versión presentable debe respetar el modelo documental de referencia:

- cuadrantes según dirección del viento;
- fórmula VPIF = V0 · FV · FP;
- tiempo estimado = distancia / VPIF;
- protocolos por tiempo estimado de impacto.

El documento base establece los cuadrantes a partir del vector de viento y usa después la fórmula VPIF = V0 · FV · FP cuando la finca está en el cuadrante de riesgo. :contentReference[oaicite:0]{index=0}

## Pendiente de validación con socios fundadores

- Redacción definitiva de avisos.
- Redacción definitiva de protocolos dentro de la app.
- Nombres oficiales de secciones.
- Criterios de prudencia comunicativa.
- Forma de presentar el mapa y los resultados.

## Mejoras técnicas futuras

### Ubicación

- Automatización fiable de ubicación GPS.
- Guardar ubicación habitual de finca/zona vulnerable.
- Selección de puntos directamente sobre mapa.

### Meteorología

- Pronóstico de viento actual y próximas 3 horas.
- Evaluación de cambios de cuadrante según previsión.
- Comparación entre viento actual y viento previsto.

### Topografía

- Sustituir elevación provisional por fuente IGN/CNIG.
- Calcular perfil altimétrico intermedio fuego → finca.
- Calcular pendiente media, pendiente máxima y tramos subiendo/bajando.

### Combustible / vegetación

- Investigar integración SIGPAC.
- Evaluar combustible en la línea fuego → finca.
- Evaluar combustible en buffer alrededor del eje de avance.
- Usar combustible predominante o escenario más desfavorable.

### Modelo

- Mantener fórmula documental en MVP.
- Explorar modelos más sofisticados solo después de validar el MVP con los socios fundadores.

### Producto

- Despliegue web estable.
- Versión Android instalable.
- Modo demo.
- Exportar informe breve del cálculo.