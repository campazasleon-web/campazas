"""
Ingesta de observación horaria AEMET para Campazas.

Fuente: estación 2664B (Valencia de Don Juan), la estación AEMET más
cercana verificada a Campazas — 17,1 km en línea recta. Fase 0 AEMET
confirmada el 30/08/2026 (siguiente más cercana: Villafáfila, a 32,8 km).

Nota de transparencia: esto NO es el tiempo exacto de Campazas, es el
de una estación a 17 km. La web debe dejarlo claro, no dar a entender
que es una medición local.

Requiere la variable de entorno AEMET_API_KEY. NUNCA hardcodear la key
ni subirla al repo.
    - Local (PowerShell):     $env:AEMET_API_KEY = "tu_key"
    - Local (cmd):            set AEMET_API_KEY=tu_key
    - GitHub Actions:         Settings > Secrets and variables > Actions
                               -> New repository secret -> AEMET_API_KEY
"""

import os
import sqlite3

import requests

ESTACION = "2664B"
ESTACION_NOMBRE = "Valencia de Don Juan"
API_KEY = os.environ.get("AEMET_API_KEY")
DB_PATH = "data/campazas.db"

URL_BASE = (
    f"https://opendata.aemet.es/opendata/api/observacion/convencional/"
    f"datos/estacion/{ESTACION}"
)


def obtener_datos():
    if not API_KEY:
        raise RuntimeError(
            "Falta la variable de entorno AEMET_API_KEY. Revisa las "
            "instrucciones en la cabecera de este script."
        )

    resp = requests.get(URL_BASE, params={"api_key": API_KEY}, timeout=30)
    resp.raise_for_status()
    meta = resp.json()

    if meta.get("estado") != 200:
        raise RuntimeError(
            f"AEMET devolvió estado {meta.get('estado')}: {meta.get('descripcion')}"
        )

    url_datos = meta["datos"]
    resp_datos = requests.get(url_datos, timeout=30)
    resp_datos.raise_for_status()

    # AEMET sirve el JSON en ISO-8859-15 sin declararlo bien en la
    # cabecera HTTP. Sin forzar esto, los nombres con tildes/eñes
    # pueden llegar corruptos (mojibake).
    resp_datos.encoding = "ISO-8859-15"
    return resp_datos.json()


def guardar(lecturas):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS meteo_horaria (
            estacion          TEXT NOT NULL,
            fecha_hora        TEXT NOT NULL,
            temperatura       REAL,
            temp_min          REAL,
            temp_max          REAL,
            humedad           REAL,
            precipitacion     REAL,
            viento_medio      REAL,
            viento_racha      REAL,
            direccion_viento  REAL,
            fuente            TEXT NOT NULL,
            actualizado       TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (estacion, fecha_hora)
        )
        """
    )

    for l in lecturas:
        cur.execute(
            """
            INSERT OR REPLACE INTO meteo_horaria
                (estacion, fecha_hora, temperatura, temp_min, temp_max,
                 humedad, precipitacion, viento_medio, viento_racha,
                 direccion_viento, fuente)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                l.get("idema"),
                l.get("fint"),
                l.get("ta"),
                l.get("tamin"),
                l.get("tamax"),
                l.get("hr"),
                l.get("prec"),
                l.get("vv"),
                l.get("vmax"),
                l.get("dv"),
                f"AEMET OpenData - estación {ESTACION_NOMBRE} ({ESTACION})",
            ),
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    lecturas = obtener_datos()
    guardar(lecturas)
    print(f"Guardadas {len(lecturas)} lecturas horarias de AEMET ({ESTACION_NOMBRE}).")
