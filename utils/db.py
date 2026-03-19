import sqlite3
import os
import sys
from flask import g

def get_app_data_dir():
    """Devuelve el directorio base para guardar los datos de la aplicación de forma persistente."""
    if sys.platform == "win32":
        # Windows: C:\Users\<Usuario>\AppData\Roaming\CuadernoDelTutor
        base_dir = os.environ.get("APPDATA", os.path.expanduser("~"))
        app_dir = os.path.join(base_dir, "CuadernoDelTutor")
    elif sys.platform == "darwin":
        # macOS: ~/Library/Application Support/CuadernoDelTutor
        base_dir = os.path.expanduser("~/Library/Application Support")
        app_dir = os.path.join(base_dir, "CuadernoDelTutor")
    else:
        # Linux / Otros: ~/.cuadernodeltutor
        app_dir = os.path.expanduser("~/.cuadernodeltutor")
        
    os.makedirs(app_dir, exist_ok=True)
    return app_dir

# For retrocompatibility during migration, we look first in the project folder
# Then we fallback to the persistent app data dir
_LEGACY_DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app_evaluar.db")
_NEW_DB = os.path.join(get_app_data_dir(), "app_evaluar.db")

# Move legacy DB to new location if it exists
if os.path.exists(_LEGACY_DB) and not os.path.exists(_NEW_DB):
    try:
        import shutil
        shutil.copy2(_LEGACY_DB, _NEW_DB)
        print(f"Migrando base de datos de {_LEGACY_DB} a {_NEW_DB}")
        # We rename the old one just in case as backup
        os.rename(_LEGACY_DB, _LEGACY_DB + ".bak")
    except Exception as e:
        print(f"Error migrando BD: {e}")

def get_db_path():
    return os.environ.get("DATABASE_PATH", _NEW_DB if os.path.exists(_NEW_DB) or not os.path.exists(_LEGACY_DB) else _LEGACY_DB)

def run_migrations():
    """Aplica migraciones automáticas para BDs antiguas."""
    path = get_db_path()
    if not os.path.exists(path):
        return
    
    conn = sqlite3.connect(path)
    migrated = []

    migrations = [
        # Columnas faltantes
        ("ALTER TABLE gestor_tareas ADD COLUMN completado INTEGER DEFAULT 0", "gestor_tareas.completado"),
        ("ALTER TABLE programacion_diaria ADD COLUMN completado INTEGER DEFAULT 0", "programacion_diaria.completado"),
        ("ALTER TABLE etapas ADD COLUMN activa INTEGER DEFAULT 1", "etapas.activa"),
        ("ALTER TABLE informe_grupo ADD COLUMN grupo_id INTEGER", "informe_grupo.grupo_id"),
        ("ALTER TABLE alumnos ADD COLUMN deleted_at DATETIME", "alumnos.deleted_at"),
        ("ALTER TABLE alumnos ADD COLUMN tiene_ayuda_material INTEGER DEFAULT 0", "alumnos.tiene_ayuda_material"),
        ("ALTER TABLE grupos ADD COLUMN equipo_docente TEXT", "grupos.equipo_docente"),
        # Tabla diplomas_entregados
        ("""CREATE TABLE IF NOT EXISTS diplomas_entregados (
            alumno_id INTEGER PRIMARY KEY,
            cantidad INTEGER DEFAULT 0,
            fecha_ultimo DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE
        )""", "tabla diplomas_entregados"),
    ]

    for sql, name in migrations:
        try:
            conn.execute(sql)
            conn.commit()
            migrated.append(name)
        except Exception:
            pass  # Ya existe o no aplica

    # Datos iniciales obligatorios
    try:
        conn.execute("INSERT OR IGNORE INTO etapas (id, nombre, activa) VALUES (1, 'Infantil', 1)")
        conn.execute("INSERT OR IGNORE INTO etapas (id, nombre, activa) VALUES (2, 'Primaria', 1)")
        conn.execute("INSERT OR IGNORE INTO etapas (id, nombre, activa) VALUES (3, 'Secundaria', 1)")
        conn.commit()
    except Exception:
        pass

    # Áreas por defecto si no hay ninguna
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM areas")
        count = cur.fetchone()[0]
        if count == 0:
            areas_infantil = [
                ("Conocimiento de sí mismo y autonomía personal", 1, "INFANTIL_NI_EP_C"),
                ("Conocimiento del entorno", 1, "INFANTIL_NI_EP_C"),
                ("Lenguajes: Comunicación y representación", 1, "INFANTIL_NI_EP_C"),
                ("Segunda Lengua Extranjera", 1, "INFANTIL_NI_EP_C"),
                ("Música", 1, "INFANTIL_NI_EP_C"),
            ]
            areas_primaria = [
                ("Conocimiento del Medio Natural, Social y Cultural", 2, "NUMERICA_1_4"),
                ("Lengua Castellana y Literatura", 2, "NUMERICA_1_4"),
                ("Matemáticas", 2, "NUMERICA_1_4"),
                ("Educación Artística", 2, "NUMERICA_1_4"),
                ("Educación Física", 2, "NUMERICA_1_4"),
                ("Segunda Lengua Extranjera", 2, "NUMERICA_1_4"),
                ("Religión", 2, "NUMERICA_1_4"),
                ("Atención Educativa", 2, "NUMERICA_1_4"),
            ]
            for nombre, etapa_id, escala in areas_infantil + areas_primaria:
                conn.execute(
                    "INSERT INTO areas (nombre, etapa_id, tipo_escala, es_oficial, activa) VALUES (?, ?, ?, 1, 1)",
                    (nombre, etapa_id, escala)
                )
            conn.commit()
            migrated.append("áreas por defecto")
    except Exception as e:
        pass

    if migrated:
        print(f"[Migraciones aplicadas]: {', '.join(migrated)}")

    conn.close()


def init_db_if_not_exists():
    """Initializes the SQLite database from schema.sql if it doesn't exist yet."""
    path = get_db_path()
    if not os.path.exists(path):
        print(f"[{path}] No existe. Inicializando base de datos en blanco...")
        conn = sqlite3.connect(path)
        
        # Determine the absolute path to schema.sql in the project root
        schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schema.sql')
        
        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_script = f.read()
                # Run the script
                conn.executescript(schema_script)
            print(f"[{path}] Base de datos inicializada correctamente con schema.sql.")
        else:
            print(f"[PELIGRO] Archivo schema.sql no encontrado en {schema_path}.")
            
        conn.commit()
        conn.close()

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(get_db_path())
        g.db.row_factory = sqlite3.Row  # Access columns by name
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def nivel_a_nota(nivel, escala=None):
    """Convierte un nivel en una nota numérica.
    
    Escala NUMERICA_1_4: 1→2.5, 2→5.0, 3→7.5, 4→10.0
    Escala INFANTIL_NI_EP_C: 1(NI)→1, 2(EP)→2, 3(C)→3
    """
    if escala == "INFANTIL_NI_EP_C":
        # Nivel 1=NI, 2=EP, 3=C — se guarda internamente como 1,2,3
        mapping = {1: 1, 2: 2, 3: 3}
    else:
        # Escala numérica 1-4 estándar
        mapping = {1: 2.5, 2: 5.0, 3: 7.5, 4: 10.0}
    return mapping.get(nivel, 0.0)

def infantil_nivel_a_texto(nivel):
    """Devuelve el texto legible para una evaluación Infantil (NI/EP/C)."""
    mapping = {1: "NI", 2: "EP", 3: "C"}
    return mapping.get(nivel, "—")
