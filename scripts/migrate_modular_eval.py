
import sqlite3
import os
import shutil
from datetime import datetime

DB_PATH = '/home/danito73/Documentos/APP_EVALUAR/app_evaluar.db'
BACKUP_PATH = f'/home/danito73/Documentos/APP_EVALUAR/app_evaluar.db.bak_modular_{datetime.now().strftime("%Y%m%d_%H%M%S")}'

def migrate():
    if not os.path.exists(DB_PATH):
        print("Database not found.")
        return

    print(f"Creating backup: {BACKUP_PATH}")
    shutil.copy2(DB_PATH, BACKUP_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        # 1. Create etapas table
        print("Creating etapas table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS etapas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                activa BOOLEAN DEFAULT 1
            )
        """)
        
        # Seed etapas
        for etapa in ["Infantil", "Primaria", "Secundaria"]:
            cur.execute("INSERT OR IGNORE INTO etapas (nombre) VALUES (?)", (etapa,))
        
        # Get etapa mapping
        cur.execute("SELECT id, nombre FROM etapas")
        etapa_map = {row["nombre"]: row["id"] for row in cur.fetchall()}

        # 2. Prepare new areas table
        print("Restructuring areas table...")
        cur.execute("ALTER TABLE areas RENAME TO areas_old")
        cur.execute("""
            CREATE TABLE areas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                etapa_id INTEGER NOT NULL,
                es_oficial BOOLEAN DEFAULT 0,
                es_personalizada BOOLEAN DEFAULT 1,
                modo_evaluacion TEXT DEFAULT 'POR_SA',
                tipo_escala TEXT DEFAULT 'NUMERICA_1_4',
                activa BOOLEAN DEFAULT 1,
                FOREIGN KEY (etapa_id) REFERENCES etapas(id),
                UNIQUE(nombre, etapa_id)
            )
        """)

        # 3. Migrate existing areas
        # We need to find all (area_name, stage) combinations from criteria
        cur.execute("""
            SELECT DISTINCT a.nombre, c.etapa 
            FROM criterios c 
            JOIN areas_old a ON c.area_id = a.id
        """)
        combinations = cur.fetchall()
        
        area_mapping = {} # (old_id, stage_name) -> new_id
        
        for comb in combinations:
            name = comb["nombre"]
            etapa_name = comb["etapa"]
            etapa_id = etapa_map.get(etapa_name)
            
            # Use default scale for Infantil if it's Infantil
            scale = "INFANTIL_NI_EP_C" if etapa_name == "Infantil" else "NUMERICA_1_4"
            
            cur.execute("""
                INSERT INTO areas (nombre, etapa_id, tipo_escala) 
                VALUES (?, ?, ?)
            """, (name, etapa_id, scale))
            new_id = cur.lastrowid
            
            # Map old area + stage to new area
            # Find old_id for this name (might be multiple if we are spliting, but we join by name)
            cur.execute("SELECT id FROM areas_old WHERE nombre = ?", (name,))
            old_ids = [r["id"] for r in cur.fetchall()]
            for old_id in old_ids:
                area_mapping[(old_id, etapa_name)] = new_id

        # 4. Restructure criterios table
        print("Restructuring criterios table...")
        cur.execute("ALTER TABLE criterios RENAME TO criterios_old")
        cur.execute("""
            CREATE TABLE criterios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                area_id INTEGER NOT NULL,
                activo BOOLEAN DEFAULT 1,
                oficial BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (area_id) REFERENCES areas(id),
                UNIQUE(codigo, area_id)
            )
        """)

        # Migrate criteria
        cur.execute("SELECT * FROM criterios_old")
        old_crits = cur.fetchall()
        crit_mapping = {} # old_id -> new_id
        for c in old_crits:
            new_area_id = area_mapping.get((c["area_id"], c["etapa"]))
            if not new_area_id:
                # Fallback: maybe the area didn't have any criteria combinations explored? 
                # Should not happen given step 3
                continue
            
            cur.execute("""
                INSERT INTO criterios (codigo, descripcion, area_id, activo, oficial, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (c["codigo"], c["descripcion"], new_area_id, c["activo"], c["oficial"], c["created_at"], c["updated_at"]))
            crit_mapping[c["id"]] = cur.lastrowid

        # 5. Create new tables
        print("Creating new modular tables...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS criterios_periodo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                criterio_id INTEGER NOT NULL,
                grupo_id INTEGER NOT NULL,
                periodo TEXT NOT NULL, -- T1, T2, T3
                activo BOOLEAN DEFAULT 1,
                FOREIGN KEY (criterio_id) REFERENCES criterios(id),
                FOREIGN KEY (grupo_id) REFERENCES grupos(id),
                UNIQUE(criterio_id, grupo_id, periodo)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS evaluacion_criterios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alumno_id INTEGER NOT NULL,
                criterio_id INTEGER NOT NULL,
                periodo TEXT NOT NULL, -- T1, T2, T3
                nivel INTEGER, -- 1-4
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (alumno_id) REFERENCES alumnos(id),
                FOREIGN KEY (criterio_id) REFERENCES criterios(id),
                UNIQUE(alumno_id, criterio_id, periodo)
            )
        """)

        # 6. Update foreign keys in other tables (evaluaciones, sda_criterios, etc.)
        # This is CRITICAL to maintain historical consistency
        print("Updating foreign keys in related tables...")
        
        # sda_criterios update
        cur.execute("SELECT * FROM sda_criterios")
        sda_crits = cur.fetchall()
        cur.execute("DELETE FROM sda_criterios")
        for sc in sda_crits:
            new_crit_id = crit_mapping.get(sc["criterio_id"])
            if new_crit_id:
                cur.execute("INSERT INTO sda_criterios (sda_id, criterio_id) VALUES (?, ?)", (sc["sda_id"], new_crit_id))

        # evaluaciones update
        cur.execute("SELECT * FROM evaluaciones")
        evals = cur.fetchall()
        cur.execute("DROP TABLE evaluaciones")
        cur.execute("""
            CREATE TABLE evaluaciones (
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
        """)
        for ev in evals:
            new_crit_id = crit_mapping.get(ev["criterio_id"])
            # The area_id might need update if the criterion's area changed due to splitting
            if new_crit_id:
                cur.execute("SELECT area_id FROM criterios WHERE id = ?", (new_crit_id,))
                new_area_id = cur.fetchone()["area_id"]
                cur.execute("""
                    INSERT INTO evaluaciones (id, alumno_id, area_id, trimestre, sda_id, criterio_id, nivel, nota, fecha)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (ev["id"], ev["alumno_id"], new_area_id, ev["trimestre"], ev["sda_id"], new_crit_id, ev["nivel"], ev["nota"], ev["fecha"]))

        # 7. Cleanup
        print("Cleaning up old tables...")
        cur.execute("DROP TABLE areas_old")
        cur.execute("DROP TABLE criterios_old")

        conn.commit()
        print("Migration completed successfully.")

    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
