# Fase 0 — Verificación de fuentes

Objetivo: confirmar qué datos son realmente accesibles antes de diseñar el modelo de datos o escribir un solo script de ingesta. Ningún dato entra en el esquema hasta que su fila aquí esté marcada como ✅.

No avances a Fase 1 (MVP) mientras haya bloques en ❌ o ⏳ que la afecten directamente.

---

## 1. INE — Población

- [x] ¿Existe la ficha municipal de Campazas en INE (aplicación "Cifras de población" / Alteraciones de municipios)?
- [x] ¿El dato de población total está disponible a nivel de municipio, o el municipio cae bajo secreto estadístico por tamaño de muestra?
- [x] ¿Hay serie histórica descargable (CSV/API) o solo se puede consultar de forma manual en su web?
- [x] ¿Existe API pública de INE (INEbase / API JSON) que permita automatizar la consulta, o hay que hacer scraping?
- [ ] Si hay secreto estadístico: ¿el Instituto de Estadística de Castilla y León ofrece el dato agregado que INE no da? — no aplica, no hay secreto estadístico.

**Estado:** ✅ confirmado
**Notas:**
- Tabla INE 29005 (padrón municipal). Código de municipio: 24032 (provincia 24 = León).
- Códigos de serie de Campazas: DPOP10951 (total), DPOP10952 (hombres), DPOP10953 (mujeres).
- El endpoint `DATOS_SERIE/{id}` da 404 con estos identificadores (probado con COD y con Id numérico). Método que sí funciona: descargar `DATOS_TABLA/29005` completa y filtrar por el campo `COD` de cada serie.
- Rango de datos disponible: 1996–2025, sin dato para 1997 (el padrón continuo con revisión anual no empezó hasta 1998; antes solo había censos en años concretos).
- Bug encontrado y corregido: INE devuelve `Fecha` como epoch en milisegundos UTC, pero representa medianoche en España (CET). Sin corregir el offset, la fecha salía con un año de menos. Fix: sumar 1h antes de extraer la fecha (seguro para estas fechas de referencia de enero, fuera de horario de verano).
- Ingesta y exportación a JSON validadas en local el 28/08/2026 (`ingest_ine_poblacion.py` + `export_poblacion.py`), y verificado visualmente el gráfico resultante en la web.

---

## 2. AEMET — Meteorología

- [x] ¿Cuál es la estación AEMET más cercana a Campazas con datos activos?
- [x] ¿A qué distancia está esa estación? (si es >15-20 km, el dato "de Campazas" es en realidad de otro sitio — decidir si se etiqueta así de forma honesta)
- [x] ¿Tienes ya una API key de AEMET OpenData, o hay que solicitarla?
- [x] ¿Qué variables ofrece esa estación en concreto (temperatura, precipitación, viento) y con qué frecuencia se actualizan?
- [ ] Alternativa Open-Meteo: no hizo falta, la estación de AEMET es lo bastante cercana.

**Estado:** ✅ confirmado
**Notas:**
- Estación AEMET: 2664B, Valencia de Don Juan. Distancia real a Campazas: 17,1 km (calculado por coordenadas, confirmado por la propia web del Ayuntamiento: "20 km a Valencia de Don Juan"). Siguiente estación más cercana: Villafáfila (Zamora), a 32,8 km — sin ambigüedad en la elección.
- Endpoint: `observacion/convencional/datos/estacion/2664B`. Devuelve una ventana móvil de lecturas horarias recientes (temperatura, min/max horaria, humedad, precipitación, viento medio y racha, dirección).
- La API sirve el JSON en ISO-8859-15 sin declararlo bien en la cabecera HTTP — hay que forzar `resp.encoding = "ISO-8859-15"` antes de parsear, si no los nombres con tildes llegan corruptos.
- La key de AEMET se gestiona como variable de entorno (`AEMET_API_KEY`), nunca en el código ni en el repo.
- Importante para la web: esto es el tiempo de Valencia de Don Juan, no una medición literal en Campazas. Debe quedar explícito en la interfaz, no solo en este documento.
- Ingesta validada en local el 31/08/2026 (`ingest_aemet_meteo.py`), guardando en tabla `meteo_horaria` de `campazas.db`.

---

## 3. Ayuntamiento de Campazas

- [ ] ¿Tiene web propia, o depende de una sede electrónica compartida (mancomunidad, diputación)?
- [ ] ¿Publica agenda de eventos, bandos o noticias en algún formato consultable (RSS, HTML estructurado, PDF)?
- [ ] ¿Hay tablón de anuncios digital o boletín que se pueda scrapear de forma estable (sin que cambie de estructura cada mes)?
- [ ] Si no hay canal digital: ¿existe contacto directo para pedir los datos manualmente, aunque sea de forma puntual?

**Estado:** ⏳ pendiente
**Notas:**

---

## 4. Catastro

- [ ] ¿La Sede Electrónica del Catastro permite consulta por municipio vía su servicio web (OVCSW / INSPIRE)?
- [ ] ¿Qué nivel de detalle es de acceso público sin certificado digital (referencia catastral, superficie) frente a lo que exige identificación?
- [ ] ¿Tiene sentido para el MVP, o se deja directamente para Fase 2 junto con vivienda y patrimonio?

**Estado:** ⏳ pendiente — candidato a aplazar a Fase 2
**Notas:**

---

## Criterio de salida de esta fase

Fase 0 se da por cerrada cuando INE y AEMET (los dos bloques que sostienen el MVP) están en ✅ con método de obtención decidido (API o scraping) y frecuencia de actualización clara. Ayuntamiento y Catastro pueden quedar en ⏳ sin bloquear el arranque del MVP, pero deben resolverse antes de abrir Fase 2.
