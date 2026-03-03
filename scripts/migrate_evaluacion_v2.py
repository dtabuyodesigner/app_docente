#!/usr/bin/env python3
"""
migrate_evaluacion_v2.py
========================
Migración de base de datos para el sistema de evaluación v2:

1. Añade `grupo_id INTEGER` a la tabla `sda`
   → Las SA quedan vinculadas al grupo que las creó.
   → Las SA existentes quedan con grupo_id = NULL (compatibles con todos los grupos).

2. Añade `tipo_evaluacion TEXT DEFAULT 'primaria'` a la tabla `grupos`
   → Permite distinguir grupos de tipo 'primaria' (escala 1-4) e 'infantil' (NI/EP/C).

3. Hace `sda_id` nullable en la tabla `evaluaciones`
   → Permite registrar evaluaciones directas por criterio sin necesidad de SA (modo Infantil).
"""

import sqlite3
import os
import shutil
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app_evaluar.db")

def backup(db_path):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = db_path + f".bak_evalv2_{ts}"
    shutil.copy2(db_path, bak)
    print(f"[BACKUP] → {bak}")
    return bak

def column_exists(cur, table, column):
    cur.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cur.fetchall())

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] No se encuentra la BD en {DB_PATH}")
        return False

    backup(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ── 1. grupo_id en sda ─────────────────────────────────────────────────
    if not column_exists(cur, "sda", "grupo_id"):
        cur.execute("ALTER TABLE sda ADD COLUMN grupo_id INTEGER REFERENCES grupos(id)")
        print("[OK] Columna grupo_id añadida a sda.")
    else:
        print("[SKIP] grupo_id ya existe en sda.")

    # ── 2. tipo_evaluacion en grupos ───────────────────────────────────────
    if not column_exists(cur, "grupos", "tipo_evaluacion"):
        cur.execute("ALTER TABLE grupos ADD COLUMN tipo_evaluacion TEXT DEFAULT 'primaria'")
        print("[OK] Columna tipo_evaluacion añadida a grupos.")
    else:
        print("[SKIP] tipo_evaluacion ya existe en grupos.")

    # ── 3. sda_id nullable en evaluaciones ─────────────────────────────────
    # SQLite no soporta ALTER COLUMN, hay que recrear la tabla.
    cur.execute("PRAGMA table_info(evaluaciones)")
    cols = {row[1]: row for row in cur.fetchall()}
    sda_col = cols.get("sda_id")
    # Si la columna ya es nullable (notnull == 0) no hacemos nada
    if sda_col and sda_col[3] == 1:  # notnull flag
        print("[MIGRATING] Haciendo sda_id nullable en evaluaciones...")
        cur.executescript("""
            PRAGMA foreign_keys = OFF;
            BEGIN;

            CREATE TABLE evaluaciones_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alumno_id INTEGER NOT NULL,
                area_id INTEGER NOT NULL,
                trimestre INTEGER NOT NULL CHECK(trimestre BETWEEN 1 AND 3),
                sda_id INTEGER,
                criterio_id INTEGER NOT NULL,
                nivel INTEGER NOT NULL CHECK(nivel BETWEEN 1 AND 4),
                nota REAL NOT NULL,
                fecha DATE DEFAULT CURRENT_DATE,
                UNIQUE(alumno_id, criterio_id, sda_id, trimestre),
                FOREIGN KEY(alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE,
                FOREIGN KEY(area_id) REFERENCES areas(id),
                FOREIGN KEY(sda_id) REFERENCES sda(id),
                FOREIGN KEY(criterio_id) REFERENCES criterios(id)
            );

            INSERT INTO evaluaciones_new
                SELECT id, alumno_id, area_id, trimestre, sda_id, criterio_id, nivel, nota, fecha
                FROM evaluaciones;

            DROP TABLE evaluaciones;
            ALTER TABLE evaluaciones_new RENAME TO evaluaciones;

            COMMIT;
            PRAGMA foreign_keys = ON;
        """)
        print("[OK] sda_id ahora es nullable en evaluaciones.")
    else:
        print("[SKIP] sda_id ya es nullable en evaluaciones.")

    conn.commit()
    conn.close()
    print("\n✅ Migración completada correctamente.")
    return True

if __name__ == "__main__":
    migrate()
