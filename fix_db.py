import sqlite3
import os

DB_PATH = "app_evaluar.db"

def fix_db():
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Check schemas for TAREAS
    print("Checking TAREAS table...")
    cur.execute("PRAGMA table_info(tareas)")
    cols = [r[1] for r in cur.fetchall()]
    print("Columns:", cols)
    
    if "fecha" not in cols:
        print("Adding 'fecha' column to tareas...")
        try:
            cur.execute("ALTER TABLE tareas ADD COLUMN fecha TEXT")
            conn.commit()
            print("Column added.")
        except Exception as e:
            print("Error adding column:", e)
    else:
        print("'fecha' column already exists.")

    conn.close()

if __name__ == "__main__":
    fix_db()
