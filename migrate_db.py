import sqlite3
import os
import shutil

DB_PATH = "app_evaluar.db"
BACKUP_PATH = "app_evaluar.db.bak"

def migrate():
    shutil.copy2(DB_PATH, BACKUP_PATH)
    print(f"Backup created at {BACKUP_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Check if ON DELETE CASCADE already exists in asistencia to avoid running twice
    cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='asistencia'")
    row = cur.fetchone()
    if row and "ON DELETE CASCADE" in row['sql']:
        print("Database already migrated.")
        return
        
    cur.execute("PRAGMA foreign_keys = OFF")
    
    new_schemas = {
        "asistencia": """
            CREATE TABLE asistencia_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alumno_id INTEGER NOT NULL,
                fecha TEXT NOT NULL,
                estado TEXT CHECK (estado IN ('presente', 'retraso', 'falta_justificada', 'falta_no_justificada')) NOT NULL,
                comedor INTEGER DEFAULT 1,
                observacion TEXT, 
                tipo_ausencia TEXT DEFAULT 'dia', 
                horas_ausencia TEXT,
                UNIQUE (alumno_id, fecha),
                FOREIGN KEY (alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE
            )
        """,
        "evaluaciones": """
            CREATE TABLE evaluaciones_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alumno_id INTEGER NOT NULL,
                area_id INTEGER NOT NULL,
                trimestre INTEGER NOT NULL CHECK(trimestre BETWEEN 1 AND 3),
                sda_id INTEGER NOT NULL,
                criterio_id INTEGER NOT NULL,
                nivel INTEGER NOT NULL CHECK(nivel BETWEEN 1 AND 4),
                nota REAL NOT NULL,
                fecha DATE DEFAULT CURRENT_DATE,
                UNIQUE(alumno_id, criterio_id, sda_id, trimestre),
                FOREIGN KEY(alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE,
                FOREIGN KEY(area_id) REFERENCES areas(id),
                FOREIGN KEY(sda_id) REFERENCES sda(id),
                FOREIGN KEY(criterio_id) REFERENCES criterios(id)
            )
        """,
        "informe_individual": """
            CREATE TABLE informe_individual_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alumno_id INTEGER NOT NULL,
                trimestre INTEGER NOT NULL,
                texto TEXT,
                fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(alumno_id, trimestre),
                FOREIGN KEY(alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE
            )
        """,
        "encargados": """
            CREATE TABLE encargados_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                fecha DATE NOT NULL UNIQUE, 
                alumno_id INTEGER NOT NULL, 
                FOREIGN KEY(alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE
            )
        """,
        "reuniones": """
            CREATE TABLE reuniones_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alumno_id INTEGER,
                fecha TEXT,
                asistentes TEXT,
                temas TEXT,
                acuerdos TEXT, 
                tipo TEXT DEFAULT 'PADRES', 
                ciclo_id INTEGER REFERENCES config_ciclo(id),
                FOREIGN KEY(alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE
            )
        """,
        "observaciones": """
            CREATE TABLE observaciones_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alumno_id INTEGER NOT NULL,
                fecha TEXT NOT NULL,
                texto TEXT NOT NULL, 
                area_id INTEGER REFERENCES areas(id),
                FOREIGN KEY (alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE
            )
        """,
        "ficha_alumno": """
            CREATE TABLE ficha_alumno_new (
                alumno_id INTEGER,
                fecha_nacimiento TEXT,
                direccion TEXT,
                madre_nombre BLOB,
                madre_telefono BLOB,
                padre_nombre TEXT,
                padre_telefono TEXT,
                observaciones_generales TEXT, 
                personas_autorizadas TEXT, 
                madre_email TEXT, 
                padre_email TEXT,
                PRIMARY KEY(alumno_id),
                FOREIGN KEY(alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE
            )
        """
    }

    try:
        # Start transaction
        conn.execute("BEGIN TRANSACTION")
        
        for table, create_sql in new_schemas.items():
            print(f"Migrating table: {table}")
            new_table = f"{table}_new"
            
            # 1. Create new table
            cur.execute(create_sql)
            
            # 2. Copy data
            cur.execute(f"INSERT INTO {new_table} SELECT * FROM {table}")
            
            # 3. Drop old table
            cur.execute(f"DROP TABLE {table}")
            
            # 4. Rename new table to old name
            cur.execute(f"ALTER TABLE {new_table} RENAME TO {table}")
            
        conn.execute("COMMIT")
        print("Migration completed successfully.")
        
    except Exception as e:
        conn.execute("ROLLBACK")
        print(f"Migration failed: {e}")
        shutil.copy2(BACKUP_PATH, DB_PATH)
        print("Restored from backup.")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
