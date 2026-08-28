"""
Ingesta de población (INE, tabla 29005) para Campazas.

Fuente:  https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/29005
Método:  DATOS_SERIE por Id individual devuelve 404 (probado en Fase 0),
         así que se descarga la tabla completa y se filtra por los
         códigos de serie de Campazas, ya confirmados y estables.

Códigos de serie Campazas (tabla 29005):
    DPOP10951 -> Total
    DPOP10952 -> Hombres
    DPOP10953 -> Mujeres

Código INE de municipio (provincia 24 = León): 24032
"""

import sqlite3
from datetime import datetime, timedelta, timezone

import requests

URL_TABLA = "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/29005"
DB_PATH = "data/campazas.db"

SERIES_CAMPAZAS = {
    "DPOP10951": "total",
    "DPOP10952": "hombres",
    "DPOP10953": "mujeres",
}

MUNICIPIO_COD_INE = "24032"


def obtener_datos():
    resp = requests.get(URL_TABLA, timeout=30)
    resp.raise_for_status()
    datos = resp.json()

    # NOTA: se asume que cada elemento trae un campo "COD" igual al que
    # devuelve SERIES_TABLA (ej. "DPOP10951"). Si esto falla o la tabla
    # viene vacía tras el filtro, imprime un elemento completo de `datos`
    # sin filtrar y ajusta aquí el nombre del campo real.
    filtrados = [d for d in datos if d.get("COD") in SERIES_CAMPAZAS]

    if not filtrados:
        raise RuntimeError(
            "El filtro por COD no encontró ninguna serie de Campazas. "
            "Revisa la estructura real de la respuesta (imprime datos[0]) "
            "y ajusta el campo de enlace en este script."
        )

    return filtrados


def guardar(filtrados):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS poblacion (
            municipio_cod TEXT NOT NULL,
            serie         TEXT NOT NULL,
            fecha         TEXT NOT NULL,
            valor         REAL,
            fuente        TEXT NOT NULL,
            actualizado   TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (municipio_cod, serie, fecha)
        )
        """
    )

    for serie in filtrados:
        etiqueta = SERIES_CAMPAZAS[serie["COD"]]
        for punto in serie.get("Data", []):
            # INE devuelve "Fecha" como epoch en milisegundos UTC, pero el
            # instante representa medianoche en España (CET = UTC+1). Sin
            # corregir el offset, la medianoche del 1 de enero se lee como
            # 31 de diciembre 23:00 UTC y el año sale mal en todas las filas.
            # Las fechas de referencia del padrón caen siempre en enero,
            # fuera del horario de verano, así que +1h es seguro sin
            # necesitar zoneinfo/tzdata.
            epoch_ms = punto.get("Fecha")
            if epoch_ms is not None:
                fecha_iso = (
                    datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc)
                    + timedelta(hours=1)
                ).strftime("%Y-%m-%d")
            else:
                fecha_iso = str(punto.get("Anyo"))

            cur.execute(
                """
                INSERT OR REPLACE INTO poblacion
                    (municipio_cod, serie, fecha, valor, fuente)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    MUNICIPIO_COD_INE,
                    etiqueta,
                    fecha_iso,
                    punto.get("Valor"),
                    "INE tabla 29005",
                ),
            )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    filtrados = obtener_datos()
    guardar(filtrados)
    print(f"Guardadas {len(filtrados)} series de población para Campazas.")
