import sqlite3
import os

def migrate_lectura(db_path="APP_EVALUAR.db"):
    # Determine the actual DB path, the app uses app_evaluar.db based on utils/db.py
    # or let's use the explicit one if passed. Usually it's app_evaluar.db
    actual_db_path = "app_evaluar.db"
    
    if not os.path.exists(actual_db_path):
        print(f"Database {actual_db_path} not found. Skipping migration.")
        return

    print(f"Connecting to database: {actual_db_path}")
    conn = sqlite3.connect(actual_db_path)
    cur = conn.cursor()

    print("Creating 'libros' table if it doesn't exist...")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS libros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        autor TEXT NOT NULL,
        isbn TEXT,
        editorial TEXT,
        año_publicacion INTEGER,
        nivel_lectura TEXT,
        genero TEXT,
        cantidad_disponible INTEGER DEFAULT 1,
        cantidad_total INTEGER DEFAULT 1,
        descripcion TEXT,
        portada TEXT,
        fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
        activo INTEGER DEFAULT 1
    )
    """)

    print("Creating 'prestamos_libros' table if it doesn't exist...")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS prestamos_libros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alumno_id INTEGER NOT NULL,
        libro_id INTEGER NOT NULL,
        fecha_prestamo DATE NOT NULL,
        fecha_devolucion DATE,
        estado TEXT DEFAULT 'activo', 
        observaciones TEXT,
        dias_retraso INTEGER DEFAULT 0,
        FOREIGN KEY (alumno_id) REFERENCES alumnos(id),
        FOREIGN KEY (libro_id) REFERENCES libros(id)
    )
    """)

    print("Creating 'generos_lectura' table if it doesn't exist...")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS generos_lectura (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE
    )
    """)

    print("Creating 'niveles_lectura' table if it doesn't exist...")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS niveles_lectura (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE,
        descripcion TEXT
    )
    """)

    conn.commit()
    conn.close()
    print("Migration for Reading Module completed successfully.")

if __name__ == "__main__":
    migrate_lectura()
