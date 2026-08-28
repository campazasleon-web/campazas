"""
Exporta la tabla `poblacion` de campazas.db a data/poblacion.json,
en el formato que consume index.html.

Se ejecuta DESPUÉS de ingest_ine_poblacion.py, cada vez que hay datos
nuevos. El JSON resultante es lo único que la web estática necesita
leer — nunca lee el .db directamente.
"""

import json
import sqlite3
from collections import defaultdict

DB_PATH = "data/campazas.db"
OUT_PATH = "data/poblacion.json"


def exportar():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT fecha, serie, valor FROM poblacion ORDER BY fecha ASC")

    por_anio = defaultdict(dict)
    for fecha, serie, valor in cur.fetchall():
        anio = fecha[:4]  # "2025-01-01" -> "2025"
        por_anio[anio][serie] = valor

    conn.close()

    salida = [
        {
            "anio": int(anio),
            "total": datos.get("total"),
            "hombres": datos.get("hombres"),
            "mujeres": datos.get("mujeres"),
        }
        for anio, datos in sorted(por_anio.items())
    ]

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {
                "fuente": "INE, tabla 29005",
                "municipio_cod": "24032",
                "actualizado": None,  # se puede rellenar con la fecha de ejecución del Action
                "datos": salida,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Exportados {len(salida)} años a {OUT_PATH}")


if __name__ == "__main__":
    exportar()
