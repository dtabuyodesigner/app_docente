import sqlite3
import os

DB_PATH = "app_evaluar.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} no existe.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    print("Creando tablas para listado de material...")
    
    try:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS material_alumnado (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grupo_id INTEGER NOT NULL,
            categoria TEXT NOT NULL, -- 'AYUDA' or 'TODO'
            unidades INTEGER DEFAULT 1,
            material TEXT NOT NULL,
            FOREIGN KEY(grupo_id) REFERENCES grupos(id) ON DELETE CASCADE
        )
        """)
        
        cur.execute("""
        CREATE TABLE IF NOT EXISTS material_info (
            grupo_id INTEGER PRIMARY KEY,
            centro TEXT,
            curso_escolar TEXT,
            nivel_curso TEXT,
            observaciones TEXT,
            FOREIGN KEY(grupo_id) REFERENCES grupos(id) ON DELETE CASCADE
        )
        """)
        
        conn.commit()
        print("Tablas creadas correctamente.")
    except Exception as e:
        conn.rollback()
        print(f"Error durante la migración: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
