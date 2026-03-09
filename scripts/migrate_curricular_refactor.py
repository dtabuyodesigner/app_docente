import sqlite3
import os

def migrate():
    db_path = 'app_evaluar.db'
    if not os.path.exists(db_path):
        print("Database not found.")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        cur.execute("BEGIN")

        # 1. New table: etapas
        cur.execute("""
            CREATE TABLE IF NOT EXISTS etapas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL
            )
        """)
        
        # Seed stages
        for etapa in ["Infantil", "Primaria", "Secundaria"]:
            cur.execute("INSERT OR IGNORE INTO etapas (nombre) VALUES (?)", (etapa,))

        # 2. Update areas table
        # We need to recreate it or add columns if they don't exist
        cur.execute("PRAGMA table_info(areas)")
        columns = [row[1] for row in cur.fetchall()]
        
        if 'etapa_id' not in columns:
            print("Adding columns to areas table...")
            # Recreate pattern recommended for SQLite
            cur.execute("ALTER TABLE areas ADD COLUMN etapa_id INTEGER")
            cur.execute("ALTER TABLE areas ADD COLUMN es_oficial INTEGER DEFAULT 1")
            cur.execute("ALTER TABLE areas ADD COLUMN activa INTEGER DEFAULT 1")
            cur.execute("ALTER TABLE areas ADD COLUMN tipo_escala TEXT DEFAULT 'NUMERICA_1_4'")
            cur.execute("ALTER TABLE areas ADD COLUMN modo_evaluacion TEXT DEFAULT 'POR_SA'")
            
            # Map existing areas to stages based on their names or previous logic if possible
            # For now, we'll try to find a stage ID for the areas if the app had some implicit logic
            cur.execute("SELECT id, nombre FROM etapas")
            etapas = {r["nombre"]: r["id"] for r in cur.fetchall()}
            
            # Default to Primaria if unsure, but we can check if they have 'Infantil' in the name
            # Or better, look at the groups that use these areas if we had that link
            infantil_id = etapas.get("Infantil")
            primaria_id = etapas.get("Primaria")
            
            cur.execute("UPDATE areas SET etapa_id = ? WHERE lower(nombre) LIKE '%infantil%'", (infantil_id,))
            cur.execute("UPDATE areas SET etapa_id = ? WHERE etapa_id IS NULL", (primaria_id,))

        # 3. New table: criterios_periodo
        cur.execute("""
            CREATE TABLE IF NOT EXISTS "criterios_periodo" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                criterio_id INTEGER NOT NULL,
                grupo_id INTEGER NOT NULL,
                periodo TEXT NOT NULL, -- T1, T2, T3
                activo INTEGER DEFAULT 1,
                FOREIGN KEY (criterio_id) REFERENCES criterios(id) ON DELETE CASCADE,
                FOREIGN KEY (grupo_id) REFERENCES grupos(id) ON DELETE CASCADE,
                UNIQUE(criterio_id, grupo_id, periodo)
            )
        """)

        # 4. Refactor programacion_diaria
        cur.execute("PRAGMA table_info(programacion_diaria)")
        pd_columns = [row[1] for row in cur.fetchall()]
        
        if 'actividad_id' not in pd_columns:
            print("Refactoring programacion_diaria table...")
            # We rename the old one
            cur.execute("ALTER TABLE programacion_diaria RENAME TO programacion_diaria_old")
            
            # Create the new one
            cur.execute("""
                CREATE TABLE programacion_diaria (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    fecha DATE NOT NULL, 
                    sda_id INTEGER, 
                    actividad_id INTEGER,
                    numero_sesion INTEGER,
                    descripcion TEXT,
                    material TEXT,
                    evaluable INTEGER DEFAULT 0,
                    tipo TEXT DEFAULT 'clase', 
                    color TEXT DEFAULT '#3788d8', 
                    FOREIGN KEY(sda_id) REFERENCES sda(id),
                    FOREIGN KEY(actividad_id) REFERENCES actividades_sda(id)
                )
            """)
            
            # Migrate data (trying to match activity name to actividades_sda if possible)
            cur.execute("SELECT * FROM programacion_diaria_old")
            old_rows = cur.fetchall()
            for row in old_rows:
                # Find activity_id
                act_name = row['actividad']
                sda_id = row['sda_id']
                cur.execute("SELECT id FROM actividades_sda WHERE nombre = ? AND sda_id = ?", (act_name, sda_id))
                act_row = cur.fetchone()
                act_id = act_row[0] if act_row else None
                
                cur.execute("""
                    INSERT INTO programacion_diaria (id, fecha, sda_id, actividad_id, descripcion, tipo, color)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (row['id'], row['fecha'], row['sda_id'], act_id, row['actividad'], row['tipo'], row['color']))
            
            cur.execute("DROP TABLE programacion_diaria_old")

        # 5. Add indices
        print("Adding performance indices...")
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_sda_area ON sda(area_id)",
            "CREATE INDEX IF NOT EXISTS idx_sda_grupo ON sda(grupo_id)",
            "CREATE INDEX IF NOT EXISTS idx_criterios_area ON criterios(area_id)",
            "CREATE INDEX IF NOT EXISTS idx_eval_alumno ON evaluaciones(alumno_id)",
            "CREATE INDEX IF NOT EXISTS idx_eval_criterio ON evaluaciones(criterio_id)",
            "CREATE INDEX IF NOT EXISTS idx_asistencia_fecha ON asistencia(fecha)"
        ]
        for idx in indices:
            cur.execute(idx)

        conn.commit()
        print("Migration completed successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
