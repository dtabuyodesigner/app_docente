import sqlite3
import os
import shutil

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "app_evaluar.db")
BACKUP_PATH = os.path.join(os.path.dirname(__file__), "..", "app_evaluar.db.bak_usuarios")

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    shutil.copy2(DB_PATH, BACKUP_PATH)
    print(f"Backup created at {BACKUP_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Check if pregunta_seguridad already exists
    cur.execute("PRAGMA table_info(usuarios)")
    columns = [row[1] for row in cur.fetchall()]
    
    if "pregunta_seguridad" in columns:
        print("Database already migrated - usuarios table has security questions.")
        conn.close()
        return
        
    try:
        cur.execute("ALTER TABLE usuarios ADD COLUMN pregunta_seguridad TEXT")
        cur.execute("ALTER TABLE usuarios ADD COLUMN respuesta_seguridad_hash TEXT")
        conn.commit()
        print("Migration completed successfully: Added security question columns to usuarios.")
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
