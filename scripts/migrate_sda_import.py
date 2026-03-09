import sqlite3
import os
from datetime import datetime

DB_PATH = '/home/danito73/Documentos/APP_EVALUAR/app_evaluar.db'

def migrate():
    if not os.path.exists(DB_PATH):
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        cur.execute("PRAGMA table_info(sda)")
        sda_cols = [r[1] for r in cur.fetchall()]
        
        if "codigo_sda" not in sda_cols:
            print("Adding codigo_sda to sda...")
            cur.execute("ALTER TABLE sda ADD COLUMN codigo_sda TEXT")
            
        if "duracion_semanas" not in sda_cols:
            print("Adding duracion_semanas to sda...")
            cur.execute("ALTER TABLE sda ADD COLUMN duracion_semanas INTEGER")

        cur.execute("PRAGMA table_info(actividades_sda)")
        act_cols = [r[1] for r in cur.fetchall()]
        
        if "codigo_actividad" not in act_cols:
            print("Adding codigo_actividad to actividades_sda...")
            cur.execute("ALTER TABLE actividades_sda ADD COLUMN codigo_actividad TEXT")

        conn.commit()
        print("Migration for SDA Import completed successfully.")
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
