#!/usr/bin/env python3
"""
fix_orphaned_sas.py
===================
Corrige la columna `area_id` de la tabla `sda` tras la migración modular.

El script `migrate_modular_eval.py` recreó la tabla `areas` asignando nuevos IDs,
pero nunca actualizó la columna `sda.area_id`. Como resultado, muchos SDAs apuntan
a IDs de área incorrectos.

Este script detecta automáticamente el mapeo entre el nombre del área y el ID
actual, y aplica la corrección usando el nombre de la primera área que encuentre
en el backup más antiguo disponible.

Mapeo manual de emergencia (basado en análisis):
  old_id=1 (Lengua Castellana y Literatura)  → new_id según nombre
  old_id=2 (Matemáticas)                     → new_id según nombre
  old_id=3 (Conocimiento del Medio)          → new_id según nombre

El script se puede re-ejecutar de forma segura (idempotente).
"""
import sqlite3
import os
import shutil
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app_evaluar.db")
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups")
OLDEST_BACKUP = os.path.join(BACKUP_DIR, "app_evaluar_backup_20260302_1301_manual.db")

def backup(db_path):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = os.path.join(BACKUP_DIR, f"app_evaluar.db.bak_fix_sas_{ts}")
    shutil.copy2(db_path, bak)
    print(f"[BACKUP] → {bak}")
    return bak

def run():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] No se encuentra la BD en {DB_PATH}")
        return

    backup(DB_PATH)

    conn_old = None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. Build a map: area_name -> current new area_id
    cur.execute("SELECT id, nombre FROM areas")
    current_areas = {row["nombre"]: row["id"] for row in cur.fetchall()}
    print(f"[INFO] Áreas actuales: {current_areas}")

    # 2. Open the oldest backup to get old area_id -> name mapping
    if not os.path.exists(OLDEST_BACKUP):
        print(f"[ERROR] Backup antiguo no encontrado en: {OLDEST_BACKUP}")
        conn.close()
        return

    conn_old = sqlite3.connect(OLDEST_BACKUP)
    conn_old.row_factory = sqlite3.Row
    cur_old = conn_old.cursor()
    cur_old.execute("SELECT id, nombre FROM areas")
    old_rows = cur_old.fetchall()
    conn_old.close()

    if not old_rows:
        print("[ERROR] No se pudieron leer áreas del backup.")
        conn.close()
        return

    # Build map: old_id -> current_new_id
    id_fix_map = {}
    print("\n[INFO] Mapeando IDs de área:")
    for row in old_rows:
        old_id = row["id"]
        nombre = row["nombre"]
        
        # Try exact name match first
        new_id = current_areas.get(nombre)
        if not new_id:
            # Try prefix match (e.g., "Conocimiento del Medio" → "Conocimiento del Medio Natural, Social y Cultural")
            for area_name, area_id in current_areas.items():
                if nombre.lower() in area_name.lower() or area_name.lower().startswith(nombre.lower()):
                    new_id = area_id
                    break
        
        if new_id:
            id_fix_map[old_id] = new_id
            print(f"  old_id={old_id} ('{nombre}') → new_id={new_id}")
        else:
            print(f"  [WARN] old_id={old_id} ('{nombre}') → No match found, skipping")

    if not id_fix_map:
        print("[ERROR] No se pudo construir ningún mapa de corrección.")
        conn.close()
        return

    # 3. Get all SDAs that currently point to IDs that no longer exist in areas
    cur.execute("SELECT id, nombre, area_id FROM sda")
    all_sdas = cur.fetchall()

    cur.execute("SELECT id FROM areas")
    valid_area_ids = {row["id"] for row in cur.fetchall()}

    print(f"\n[INFO] Procesando {len(all_sdas)} SDAs...")
    fixed = 0
    for sda in all_sdas:
        sda_id = sda["id"]
        old_area = sda["area_id"]
        if old_area not in valid_area_ids:
            # This SDA is orphaned – try to fix it
            new_area = id_fix_map.get(old_area)
            if new_area:
                cur.execute("UPDATE sda SET area_id = ? WHERE id = ?", (new_area, sda_id))
                print(f"  Fixed SDA id={sda_id} ('{sda['nombre']}'): area_id {old_area} → {new_area}")
                fixed += 1
            else:
                print(f"  [WARN] SDA id={sda_id} ('{sda['nombre']}'): area_id={old_area} orphaned but no fix mapping found")
        else:
            # Area still valid – but check if it was remapped (could be collateral)
            if old_area in id_fix_map and id_fix_map[old_area] != old_area:
                new_area = id_fix_map[old_area]
                cur.execute("UPDATE sda SET area_id = ? WHERE id = ?", (new_area, sda_id))
                print(f"  Remapped SDA id={sda_id} ('{sda['nombre']}'): area_id {old_area} → {new_area}")
                fixed += 1

    conn.commit()
    conn.close()
    print(f"\n✅ Corrección completada: {fixed} SDAs actualizados.")

if __name__ == "__main__":
    run()
