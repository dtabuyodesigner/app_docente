
import sqlite3
from datetime import date

DB_PATH = 'app_evaluar.db'

def fix_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    fecha_hoy = date.today().isoformat()
    print(f"Fixing evaluations for {fecha_hoy}...")
    
    # 1. Move T1 evals from today to T2
    cur.execute("""
        UPDATE evaluaciones 
        SET trimestre = 2 
        WHERE fecha = ? AND trimestre = 1 AND sda_id IS NULL
    """, (fecha_hoy,))
    print(f"Updated {cur.rowcount} evaluations to Trimestre 2.")
    
    # 2. Get all criteria evaluated today
    cur.execute("""
        SELECT DISTINCT e.criterio_id, a.grupo_id 
        FROM evaluaciones e
        JOIN alumnos a ON e.alumno_id = a.id
        WHERE e.fecha = ? AND e.sda_id IS NULL
    """, (fecha_hoy,))
    
    rows = cur.fetchall()
    count = 0
    for row in rows:
        cur.execute("""
            INSERT INTO criterios_periodo (criterio_id, grupo_id, periodo, activo)
            VALUES (?, ?, 'T2', 1)
            ON CONFLICT(criterio_id, grupo_id, periodo) DO UPDATE SET activo = 1
        """, (row['criterio_id'], row['grupo_id']))
        count += 1
    
    print(f"Ensured {count} criteria are active in T2 for their respective groups.")
    
    conn.commit()
    conn.close()
    print("Data correction complete.")

if __name__ == '__main__':
    fix_data()
