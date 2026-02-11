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

    # 2. Check and initialize config_ciclo
    print("Checking config_ciclo table...")
    cur.execute("SELECT COUNT(*) FROM config_ciclo")
    count = cur.fetchone()[0]
    
    if count == 0 or (count == 1 and "Primaria" in [r[1] for r in cur.execute("SELECT * FROM config_ciclo").fetchall()]):
        print("Initializing standard Primary Cycles...")
        standard_cycles = [
            ("Primer Ciclo", "[]"),
            ("Segundo Ciclo", "[]"),
            ("Tercer Ciclo", "[]")
        ]
        # Clear if it only has the previous placeholder "Primaria"
        cur.execute("DELETE FROM config_ciclo WHERE nombre = 'Primaria'")
        cur.executemany("INSERT INTO config_ciclo (nombre, asistentes_defecto) VALUES (?, ?)", standard_cycles)
        conn.commit()
        print("Cycles initialized.")
    else:
        print(f"config_ciclo already has {count} entries.")

    conn.close()

if __name__ == "__main__":
    fix_db()
