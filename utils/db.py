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
        # Enable foreign keys
        g.db.execute("PRAGMA foreign_keys = ON;")
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
