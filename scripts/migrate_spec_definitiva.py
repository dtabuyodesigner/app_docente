"""
Migración Spec Definitiva — Sistema Modular de Evaluación
Ejecutar: python scripts/migrate_spec_definitiva.py
"""
import sqlite3
import shutil
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'app_evaluar.db')
DB_PATH = os.path.abspath(DB_PATH)

def backup():
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    bak = DB_PATH + f'.bak_spec_def_{ts}'
    shutil.copy2(DB_PATH, bak)
    print(f"✅ Backup: {bak}")
    return bak

# ─────────────────────────────────────────────
# ÁREAS OFICIALES (según spec, sección 2.3)
# ─────────────────────────────────────────────
AREAS_OFICIALES = [
    # (nombre, etapa_nombre, modo_evaluacion, tipo_escala)
    # INFANTIL — 2º ciclo
    ("Crecimiento en Armonía",                        "Infantil",  "POR_CRITERIOS_DIRECTOS", "INFANTIL_NI_EP_C"),
    ("Descubrimiento y Exploración del Entorno",      "Infantil",  "POR_CRITERIOS_DIRECTOS", "INFANTIL_NI_EP_C"),
    ("Comunicación y Representación de la Realidad",  "Infantil",  "POR_CRITERIOS_DIRECTOS", "INFANTIL_NI_EP_C"),
    # PRIMARIA
    ("Lengua Castellana y Literatura",                "Primaria",  "POR_SA", "NUMERICA_1_4"),
    ("Matemáticas",                                   "Primaria",  "POR_SA", "NUMERICA_1_4"),
    ("Conocimiento del Medio Natural, Social y Cultural", "Primaria", "POR_SA", "NUMERICA_1_4"),
    ("Educación Artística",                           "Primaria",  "POR_SA", "NUMERICA_1_4"),
    ("Educación Física",                              "Primaria",  "POR_SA", "NUMERICA_1_4"),
    ("Primera Lengua Extranjera",                     "Primaria",  "POR_SA", "NUMERICA_1_4"),
    ("Segunda Lengua Extranjera",                     "Primaria",  "POR_SA", "NUMERICA_1_4"),
    ("Religión",                                      "Primaria",  "POR_SA", "NUMERICA_1_4"),
    ("Atención Educativa",                            "Primaria",  "POR_SA", "NUMERICA_1_4"),
    ("Educación en Valores Cívicos y Éticos",         "Primaria",  "POR_SA", "NUMERICA_1_4"),
]

def run():
    backup()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = OFF")

    # ── 1. Asegurar etapas ───────────────────────────────────────────────
    print("\n[1] Verificando etapas...")
    for nombre in ("Infantil", "Primaria", "Secundaria"):
        cur.execute("INSERT OR IGNORE INTO etapas (nombre, activa) VALUES (?, 1)", (nombre,))
    conn.commit()
    cur.execute("SELECT id, nombre FROM etapas")
    etapas = {row["nombre"]: row["id"] for row in cur.fetchall()}
    print(f"   Etapas: {etapas}")

    # ── 2. Añadir etapa_id a grupos si no existe ─────────────────────────
    print("\n[2] Añadiendo etapa_id a grupos...")
    cur.execute("PRAGMA table_info(grupos)")
    cols = [r["name"] for r in cur.fetchall()]
    if "etapa_id" not in cols:
        cur.execute("ALTER TABLE grupos ADD COLUMN etapa_id INTEGER REFERENCES etapas(id)")
        # Asignar por tipo_evaluacion existente
        cur.execute("UPDATE grupos SET etapa_id = ? WHERE tipo_evaluacion = 'infantil'", (etapas["Infantil"],))
        cur.execute("UPDATE grupos SET etapa_id = ? WHERE etapa_id IS NULL", (etapas["Primaria"],))
        conn.commit()
        print("   ✅ etapa_id añadido y asignado")
    else:
        print("   ⏭ etapa_id ya existe")

    # ── 3. Áreas oficiales: recargar según spec ──────────────────────────
    print("\n[3] Cargando áreas oficiales según spec...")
    # Obtener áreas que tienen criterios o evaluaciones (no se pueden borrar)
    cur.execute("""
        SELECT DISTINCT a.id FROM areas a
        LEFT JOIN criterios c ON c.area_id = a.id
        LEFT JOIN evaluacion_criterios ec ON ec.criterio_id = c.id
        LEFT JOIN evaluaciones ev ON ev.area_id = a.id
        WHERE c.id IS NOT NULL OR ec.id IS NOT NULL OR ev.id IS NOT NULL
    """)
    areas_con_datos = {r[0] for r in cur.fetchall()}
    
    # Obtener áreas actuales
    cur.execute("SELECT id, nombre, etapa_id, es_oficial FROM areas")
    areas_actuales = {(r["nombre"], r["etapa_id"]): r["id"] for r in cur.fetchall()}
    
    insertadas = 0
    for nombre, etapa_nombre, modo, escala in AREAS_OFICIALES:
        etapa_id = etapas[etapa_nombre]
        key = (nombre, etapa_id)
        if key not in areas_actuales:
            cur.execute("""
                INSERT INTO areas (nombre, etapa_id, es_oficial, es_personalizada, modo_evaluacion, tipo_escala, activa)
                VALUES (?, ?, 1, 0, ?, ?, 1)
            """, (nombre, etapa_id, modo, escala))
            insertadas += 1
        else:
            # Asegurar que está marcada como oficial y con los datos correctos
            area_id = areas_actuales[key]
            cur.execute("""
                UPDATE areas SET es_oficial=1, modo_evaluacion=?, tipo_escala=?, activa=1
                WHERE id=?
            """, (modo, escala, area_id))
    conn.commit()
    print(f"   ✅ {insertadas} áreas insertadas, existentes actualizadas")

    # ── 4. Añadir columna activo/oficial a criterios si falta ───────────
    print("\n[4] Verificando columnas en criterios...")
    cur.execute("PRAGMA table_info(criterios)")
    crit_cols = [r["name"] for r in cur.fetchall()]
    if "activo" not in crit_cols:
        cur.execute("ALTER TABLE criterios ADD COLUMN activo INTEGER DEFAULT 1")
    if "oficial" not in crit_cols:
        cur.execute("ALTER TABLE criterios ADD COLUMN oficial INTEGER DEFAULT 1")
    if "created_at" not in crit_cols:
        cur.execute("ALTER TABLE criterios ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
    if "updated_at" not in crit_cols:
        cur.execute("ALTER TABLE criterios ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")
    conn.commit()
    print("   ✅ Columnas de criterios verificadas")

    # ── 5. Recrear criterios_periodo con grupo_id ────────────────────────
    print("\n[5] Recreando criterios_periodo con grupo_id...")
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='criterios_periodo'")
    if cur.fetchone():
        # Ver si tiene grupo_id
        cur.execute("PRAGMA table_info(criterios_periodo)")
        cp_cols = [r["name"] for r in cur.fetchall()]
        if "grupo_id" not in cp_cols:
            cur.execute("DROP TABLE criterios_periodo")
            print("   Tabla antigua eliminada")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS criterios_periodo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            criterio_id INTEGER NOT NULL,
            grupo_id INTEGER NOT NULL,
            periodo TEXT NOT NULL,
            activo INTEGER DEFAULT 1,
            UNIQUE(criterio_id, grupo_id, periodo),
            FOREIGN KEY (criterio_id) REFERENCES criterios(id),
            FOREIGN KEY (grupo_id) REFERENCES grupos(id)
        )
    """)
    conn.commit()
    print("   ✅ criterios_periodo recreada con grupo_id y periodo TEXT")

    # ── 6. Verificar/Recrear evaluacion_criterios con UNIQUE correcto ────
    print("\n[6] Verificando evaluacion_criterios...")
    cur.execute("SELECT COUNT(*) FROM evaluacion_criterios")
    ec_count = cur.fetchone()[0]
    
    # Verificar si tiene columna 'periodo' como TEXT y UNIQUE correcto
    cur.execute("SELECT sql FROM sqlite_master WHERE name='evaluacion_criterios' AND type='table'")
    ec_sql = (cur.fetchone() or [None])[0] or ""
    
    needs_recreate = ec_count == 0 and "UNIQUE" not in ec_sql.upper()
    
    if needs_recreate or ec_count == 0:
        cur.execute("DROP TABLE IF EXISTS evaluacion_criterios")
        cur.execute("""
            CREATE TABLE evaluacion_criterios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alumno_id INTEGER NOT NULL,
                criterio_id INTEGER NOT NULL,
                periodo TEXT NOT NULL,
                nivel INTEGER NOT NULL,
                nota REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(alumno_id, criterio_id, periodo),
                FOREIGN KEY (alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE,
                FOREIGN KEY (criterio_id) REFERENCES criterios(id)
            )
        """)
        conn.commit()
        print("   ✅ evaluacion_criterios recreada con UNIQUE(alumno_id, criterio_id, periodo)")
    else:
        print(f"   ⏭ evaluacion_criterios ya tiene {ec_count} registros, no se toca")

    # ── 7. Añadir etapa_id a sda si no existe ───────────────────────────
    print("\n[7] Verificando sda.grupo_id...")
    cur.execute("PRAGMA table_info(sda)")
    sda_cols = [r["name"] for r in cur.fetchall()]
    if "grupo_id" not in sda_cols:
        cur.execute("ALTER TABLE sda ADD COLUMN grupo_id INTEGER REFERENCES grupos(id)")
        conn.commit()
        print("   ✅ grupo_id añadido a sda")
    else:
        print("   ⏭ sda.grupo_id ya existe")

    # ── 8. Asegurar es_oficial en áreas antiguas ─────────────────────────
    print("\n[8] Marcando áreas personalizadas (retrocompatibilidad)...")
    cur.execute("UPDATE areas SET es_personalizada=1, es_oficial=0 WHERE es_oficial IS NULL OR (es_oficial=0 AND es_personalizada IS NULL)")
    conn.commit()

    cur.execute("PRAGMA foreign_keys = ON")
    conn.close()

    print("\n" + "="*50)
    print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
    print("="*50)

    # Mostrar resumen
    conn2 = sqlite3.connect(DB_PATH)
    conn2.row_factory = sqlite3.Row
    c2 = conn2.cursor()
    c2.execute("SELECT e.nombre as etapa, COUNT(a.id) as num FROM areas a JOIN etapas e ON a.etapa_id=e.id WHERE a.activa=1 GROUP BY e.nombre")
    rows = c2.fetchall()
    print("\nÁreas activas por etapa:")
    for r in rows:
        print(f"  {r['etapa']}: {r['num']} áreas")
    c2.execute("SELECT COUNT(*) FROM grupos WHERE etapa_id IS NOT NULL")
    print(f"\nGrupos con etapa_id: {c2.fetchone()[0]}")
    conn2.close()

if __name__ == "__main__":
    run()
