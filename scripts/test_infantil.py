import sqlite3
import os

def create_test_data():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app_evaluar.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # 1. Asegurar Admin (profesor)
    cur.execute("SELECT id FROM profesores LIMIT 1")
    prof = cur.fetchone()
    if not prof:
        cur.execute("INSERT INTO profesores (usuario_id, nombre) VALUES (1, 'Admin Test')")
        prof_id = cur.lastrowid
    else:
        prof_id = prof['id']
        
    # 2. Asegurar Etapa Infantil
    cur.execute("SELECT id FROM etapas WHERE nombre = 'Infantil'")
    etapa_inf = cur.fetchone()
    if not etapa_inf:
        cur.execute("INSERT INTO etapas (nombre) VALUES ('Infantil')")
        etapa_inf_id = cur.lastrowid
    else:
        etapa_inf_id = etapa_inf['id']

    grupos_data = [
        ("Test Infantil 3", "infantil_3"),
        ("Test Infantil 4", "infantil_4"),
        ("Test Infantil 5", "infantil_5")
    ]
    
    alumnos_data = {
        "infantil_3": ["Leo Martin", "Mia Gomez", "Hugo Ruiz"],
        "infantil_4": ["Lucas Vega", "Alba Rios", "Leo Mora"],
        "infantil_5": ["Mario Gil", "Sofia Diez", "Emma Cruz"]
    }

    try:
        cur.execute("BEGIN")
        for nombre_grupo, curso in grupos_data:
            cur.execute("INSERT INTO grupos (nombre, curso, profesor_id, etapa_id, tipo_evaluacion) VALUES (?, ?, ?, ?, ?)",
                        (nombre_grupo, curso, prof_id, etapa_inf_id, "infantil"))
            grupo_id = cur.lastrowid
            
            for nombre_alum in alumnos_data[curso]:
                cur.execute("INSERT INTO alumnos (nombre, grupo_id) VALUES (?, ?)",
                            (nombre_alum, grupo_id))
                            
        conn.commit()
        print("✅ Datos de prueba de Infantil insertados correctamente.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Error insertando datos: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    create_test_data()
