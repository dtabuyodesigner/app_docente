#!/usr/bin/env python3
"""
migrate_evaluacion_v3.py
========================
Migración de base de datos para la especificación técnica v3:

1. Tabla `areas`:
   - Añade `modo_evaluacion TEXT DEFAULT 'POR_SA'`
   - Añade `tipo_escala TEXT DEFAULT 'NUMERICA_1_4'`

2. Tabla `criterios`:
   - Añade `etapa TEXT`
   - Añade `materia_id INTEGER NULL` (por si en un futuro se separan áreas/materias)
   - Añade `activo BOOLEAN DEFAULT 1`
   - Añade `oficial BOOLEAN DEFAULT 1`
"""

import sqlite3
import os
import shutil
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app_evaluar.db")

def backup(db_path):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = db_path + f".bak_evalv3_{ts}"
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

    # 1. Nuevos campos en `areas`
    if not column_exists(cur, "areas", "modo_evaluacion"):
        cur.execute("ALTER TABLE areas ADD COLUMN modo_evaluacion TEXT DEFAULT 'POR_SA'")
        print("[OK] Columna modo_evaluacion añadida a areas.")
    
    if not column_exists(cur, "areas", "tipo_escala"):
        cur.execute("ALTER TABLE areas ADD COLUMN tipo_escala TEXT DEFAULT 'NUMERICA_1_4'")
        print("[OK] Columna tipo_escala añadida a areas.")

    # 2. Nuevos campos en `criterios`
    if not column_exists(cur, "criterios", "etapa"):
        cur.execute("ALTER TABLE criterios ADD COLUMN etapa TEXT")
        print("[OK] Columna etapa añadida a criterios.")

    if not column_exists(cur, "criterios", "materia_id"):
        cur.execute("ALTER TABLE criterios ADD COLUMN materia_id INTEGER")
        print("[OK] Columna materia_id añadida a criterios.")

    if not column_exists(cur, "criterios", "activo"):
        cur.execute("ALTER TABLE criterios ADD COLUMN activo BOOLEAN DEFAULT 1")
        print("[OK] Columna activo añadida a criterios.")

    if not column_exists(cur, "criterios", "oficial"):
        cur.execute("ALTER TABLE criterios ADD COLUMN oficial BOOLEAN DEFAULT 1")
        print("[OK] Columna oficial añadida a criterios.")

    conn.commit()
    conn.close()
    print("\n✅ Migración v3 completada correctamente.")
    return True

if __name__ == "__main__":
    migrate()
