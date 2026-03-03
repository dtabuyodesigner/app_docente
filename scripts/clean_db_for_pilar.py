import sqlite3
import os
import shutil
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "app_evaluar.db")
CLEAN_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "app_evaluar_pilar.db")

def create_clean_db():
    print(f"Creating a clean database for Pilar at: {CLEAN_DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print(f"Error: Original database {DB_PATH} not found.")
        return

    # Create a copy safely
    shutil.copy2(DB_PATH, CLEAN_DB_PATH)
    
    conn = sqlite3.connect(CLEAN_DB_PATH)
    cur = conn.cursor()
    
    # We will disable foreign keys momentarily to truncate tables easily
    cur.execute("PRAGMA foreign_keys = OFF")
    
    # Tables to clear entirely
    tables_to_clear = [
        "alumnos", "asistencia", "evaluaciones", "informe_individual",
        "encargados", "reuniones", "observaciones", "ficha_alumno",
        "informe_observaciones", "material_entregado", "material_alumnado",
        "material_info", "grupos", "profesores", "informe_grupo",
        "programacion_diaria", "actividades_sda", "horario", "gestor_tareas"
    ]
    
    for table in tables_to_clear:
        try:
            cur.execute(f"DELETE FROM {table}")
            print(f"Cleared table: {table}")
        except Exception as e:
            print(f"Warning: could not clear table {table} ({e})")
            
    # For usuarios, we keep only 'admin' or create it if missing, and delete the rest
    try:
        cur.execute("DELETE FROM usuarios WHERE username != 'admin'")
        cur.execute("SELECT id FROM usuarios WHERE username = 'admin'")
        admin_exists = cur.fetchone()
        
        if not admin_exists:
            pwd_hash = generate_password_hash("admin") # Password provided via .env normally, but let's give it a default
            cur.execute("INSERT INTO usuarios (username, password_hash, role) VALUES ('admin', ?, 'admin')", (pwd_hash,))
            print("Recreated 'admin' user.")
        else:
            print("Retained 'admin' user.")
            
    except Exception as e:
        print(f"Error cleaning usuarios table: {e}")
        
    conn.commit()
    cur.execute("PRAGMA foreign_keys = ON")
    
    # VACUUM to shrink file size after deletions
    cur.execute("VACUUM")
    conn.close()
    
    print("\nClean database generated successfully!")
    print(f"You can now send this file to Pilar: {CLEAN_DB_PATH}")

if __name__ == "__main__":
    create_clean_db()
