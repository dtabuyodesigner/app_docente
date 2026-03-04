import sqlite3
import json
import os
import sys

# Add project root to path for imports if needed
sys.path.append(os.getcwd())

DB_PATH = 'app_evaluar.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def test_migration_integrity():
    print("--- Testing Migration Integrity ---")
    conn = get_db()
    cur = conn.cursor()
    
    # Check tables exist
    tables = [t[0] for t in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    required = ['etapas', 'areas', 'criterios', 'criterios_periodo', 'evaluacion_criterios']
    for r in required:
        if r in tables: print(f"✅ Table {r} exists.")
        else: raise Exception(f"❌ Table {r} MISSING!")
    
    # Check stages seeded
    stages = cur.execute("SELECT nombre FROM etapas").fetchall()
    print(f"✅ Stages found: {[s['nombre'] for s in stages]}")
    conn.close()

def test_area_and_criteria_flow():
    print("\n--- Testing Area and Criteria Flow ---")
    conn = get_db()
    cur = conn.cursor()
    
    # 1. Create Stage if not exists (already there but safe check)
    cur.execute("INSERT OR IGNORE INTO etapas (nombre) VALUES ('Test Stage')")
    cur.execute("SELECT id FROM etapas WHERE nombre = 'Test Stage'")
    etapa_id = cur.fetchone()['id']
    
    # 2. Create Area
    cur.execute("""
        INSERT INTO areas (nombre, etapa_id, es_oficial, es_personalizada, modo_evaluacion, tipo_escala, activa)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("Area Test Modular", etapa_id, 0, 1, 'POR_CRITERIOS_DIRECTOS', 'NUMERICA_1_4', 1))
    area_id = cur.lastrowid
    print(f"✅ Created Area ID: {area_id}")
    
    # 3. Create Criteria
    cur.execute("""
        INSERT INTO criterios (codigo, descripcion, area_id, activo)
        VALUES (?, ?, ?, ?)
    """, ("MOD-1.1", "Criterio de prueba modular", area_id, 1))
    crit_id = cur.lastrowid
    print(f"✅ Created Criteria ID: {crit_id}")
    
    # 4. Activate for Period
    cur.execute("INSERT INTO criterios_periodo (area_id, periodo, criterio_id) VALUES (?, ?, ?)", (area_id, 1, crit_id))
    print(f"✅ Activated for Period 1")
    
    # 5. Check if listed for evaluation
    cur.execute("""
        SELECT c.id, c.codigo FROM criterios c 
        JOIN criterios_periodo cp ON c.id = cp.criterio_id
        WHERE cp.area_id = ? AND cp.periodo = ?
    """, (area_id, 1))
    res = cur.fetchall()
    if len(res) > 0: print(f"✅ Criterion listed for evaluation phase.")
    else: raise Exception("❌ Criterion NOT listed for evaluation!")
    
    # 6. Save Evaluation
    cur.execute("INSERT OR IGNORE INTO alumnos (nombre) VALUES ('Alumno Test 2024')")
    cur.execute("SELECT id FROM alumnos WHERE nombre = 'Alumno Test 2024'")
    alumno_id = cur.fetchone()['id']
    
    cur.execute("""
        INSERT INTO evaluacion_criterios (alumno_id, area_id, trimestre, criterio_id, nivel, nota)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (alumno_id, area_id, 1, crit_id, 3, 7.5)) # 3 out of 4 is 7.5
    print(f"✅ Evaluation saved (Nivel 3 -> 7.5)")
    
    # 7. Check Media
    cur.execute("SELECT AVG(nota) as media FROM evaluacion_criterios WHERE alumno_id = ? AND area_id = ? AND trimestre = ?", (alumno_id, area_id, 1))
    media = cur.fetchone()['media']
    print(f"✅ Average calculated: {media}")
    
    conn.rollback() # Clean up
    conn.close()

if __name__ == "__main__":
    try:
        test_migration_integrity()
        test_area_and_criteria_flow()
        print("\n🎉 ALL INTERNAL TESTS PASSED!")
    except Exception as e:
        print(f"\n💥 TEST FAILED: {e}")
        sys.exit(1)
