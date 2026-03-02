import sqlite3
import os

DB_PATH = "app_evaluar.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} no existe.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    print("Creando tabla material_entregado...")
    
    try:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS material_entregado (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alumno_id INTEGER NOT NULL,
            material_id INTEGER NOT NULL,
            entregado INTEGER DEFAULT 0, -- 0: No, 1: Sí
            fecha_entrega DATETIME,
            FOREIGN KEY(alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE,
            FOREIGN KEY(material_id) REFERENCES material_alumnado(id) ON DELETE CASCADE,
            UNIQUE(alumno_id, material_id)
        )
        """)
        
        conn.commit()
        print("Tabla material_entregado creada correctamente.")
    except Exception as e:
        conn.rollback()
        print(f"Error durante la migración: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
