"""
Exporta la tabla `meteo_horaria` de campazas.db a data/meteo.json,
con dos bloques: el dato más reciente (actual) y una tendencia diaria
agregada (media/min/max de temperatura, precipitación total por día).

Se ejecuta DESPUÉS de ingest_aemet_meteo.py.
"""

import json
import sqlite3
from collections import defaultdict

DB_PATH = "data/campazas.db"
OUT_PATH = "data/meteo.json"

ESTACION_NOMBRE = "Valencia de Don Juan"
ESTACION_DISTANCIA_KM = 17.1


def exportar():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT fecha_hora, temperatura, temp_min, temp_max, humedad,
               precipitacion, viento_medio, viento_racha, direccion_viento
        FROM meteo_horaria
        ORDER BY fecha_hora ASC
        """
    )
    filas = cur.fetchall()
    conn.close()

    if not filas:
        raise RuntimeError("No hay datos en meteo_horaria todavía.")

    # --- Dato actual: la lectura más reciente ---
    ultima = filas[-1]
    actual = {
        "fecha_hora": ultima[0],
        "temperatura": ultima[1],
        "humedad": ultima[4],
        "precipitacion": ultima[5],
        "viento_medio": ultima[6],
        "viento_racha": ultima[7],
    }

    # --- Tendencia diaria: agregado por fecha (día) ---
    por_dia = defaultdict(list)
    for fecha_hora, temp, tmin, tmax, hr, prec, vv, vmax, dv in filas:
        dia = fecha_hora[:10]  # "2026-08-31T09:00:00+0000" -> "2026-08-31"
        por_dia[dia].append((temp, tmin, tmax, prec))

    tendencia = []
    for dia, valores in sorted(por_dia.items()):
        temps = [v[0] for v in valores if v[0] is not None]
        tmins = [v[1] for v in valores if v[1] is not None]
        tmaxs = [v[2] for v in valores if v[2] is not None]
        precs = [v[3] for v in valores if v[3] is not None]
        tendencia.append(
            {
                "fecha": dia,
                "temp_media": round(sum(temps) / len(temps), 1) if temps else None,
                "temp_min": min(tmins) if tmins else None,
                "temp_max": max(tmaxs) if tmaxs else None,
                "precipitacion_total": round(sum(precs), 1) if precs else None,
            }
        )

    salida = {
        "fuente": "AEMET OpenData",
        "estacion": {
            "nombre": ESTACION_NOMBRE,
            "distancia_km": ESTACION_DISTANCIA_KM,
        },
        "actual": actual,
        "tendencia": tendencia,
    }

    with open(OUT_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)

    print(f"Exportado dato actual + {len(tendencia)} días de tendencia a {OUT_PATH}")


if __name__ == "__main__":
    exportar()
