"""
add_indexes.py
==============
Agrega índices de rendimiento a las tablas más consultadas.
Es seguro ejecutarlo múltiples veces (usa IF NOT EXISTS).
"""
import sqlite3
import os
import shutil
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app_evaluar.db")

INDEXES = [
    # --- Evaluaciones (tabla más crítica, usada en cada carga de tabla) ---
    ("idx_eval_alumno_trim",   "evaluaciones",        "alumno_id, trimestre"),
    ("idx_eval_area",          "evaluaciones",        "area_id"),
    ("idx_eval_sda",           "evaluaciones",        "sda_id"),

    # --- Evaluacion criterios (modo Infantil) ---
    ("idx_eval_crit_alumno",   "evaluacion_criterios","alumno_id, periodo"),
    ("idx_eval_crit_criterio", "evaluacion_criterios","criterio_id"),

    # --- Alumnos ---
    ("idx_alumnos_grupo",      "alumnos",             "grupo_id"),

    # --- Asistencia (búsquedas por fecha y grupo) ---
    ("idx_asistencia_alumno_fecha", "asistencia",     "alumno_id, fecha"),

    # --- Currículum: SDA ---
    ("idx_sda_area",           "sda",                 "area_id"),
    ("idx_sda_grupo",          "sda",                 "grupo_id"),

    # --- Criterios ---
    ("idx_criterios_area",     "criterios",           "area_id, activo"),

    # --- Biblioteca ---
    ("idx_prestamos_alumno",   "prestamos_libros",    "alumno_id, estado"),
    ("idx_prestamos_libro",    "prestamos_libros",    "libro_id"),

    # --- Observaciones ---
    ("idx_obs_alumno",         "observaciones",       "alumno_id"),

    # --- Tareas ---
    ("idx_tareas_profesor",    "gestor_tareas",       "profesor_id, estado"),

    # --- Reuniones ---
    ("idx_reuniones_alumno",   "reuniones",           "alumno_id"),

    # --- Actividades SDA ---
    ("idx_actividades_sda",    "actividades_sda",     "sda_id"),
]

def run():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] No se encuentra la BD en {DB_PATH}")
        return

    # Backup rápido
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = f"{DB_PATH}.bak_indexes_{ts}"
    shutil.copy2(DB_PATH, bak)
    print(f"[BACKUP] → {bak}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    created = 0
    skipped = 0

    for idx_name, table, columns in INDEXES:
        try:
            cur.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({columns})")
            # Check if it was just created or already existed
            cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND name=?", (idx_name,))
            if cur.fetchone():
                print(f"  ✅ {idx_name} ON {table}({columns})")
                created += 1
        except sqlite3.OperationalError as e:
            print(f"  ⚠️  {idx_name}: {e}")
            skipped += 1

    conn.commit()

    # ANALYZE para que SQLite actualice sus estadísticas de cardinality
    print("\n[ANALYZE] Actualizando estadísticas del planificador de consultas...")
    cur.execute("ANALYZE")
    conn.commit()
    conn.close()

    print(f"\n✅ Completado: {created} índices creados/verificados, {skipped} omitidos.")

if __name__ == "__main__":
    run()
