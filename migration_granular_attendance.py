import sqlite3
import os

DB_PATH = "app_evaluar.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("Starting migration: Add tipo_ausencia and horas_ausencia to asistencia table...")

    try:
        # Add tipo_ausencia column
        try:
            cur.execute("ALTER TABLE asistencia ADD COLUMN tipo_ausencia TEXT DEFAULT 'dia'")
            print("SUCCESS: Added 'tipo_ausencia' column.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("INFO: Column 'tipo_ausencia' already exists.")
            else:
                raise e

        # Add horas_ausencia column
        try:
            cur.execute("ALTER TABLE asistencia ADD COLUMN horas_ausencia TEXT")
            print("SUCCESS: Added 'horas_ausencia' column.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("INFO: Column 'horas_ausencia' already exists.")
            else:
                raise e

        conn.commit()
        print("Migration completed successfully.")

    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
