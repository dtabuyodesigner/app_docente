import sqlite3

DB_PATH = "app_evaluar.db"

def migrate():
    print("Starting migration...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    try:
        cur.execute("ALTER TABLE horario ADD COLUMN tipo TEXT DEFAULT 'clase'")
        conn.commit()
        print("SUCCESS: Added 'tipo' column.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("INFO: Column 'tipo' already exists.")
        else:
            print(f"ERROR: {e}")
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
