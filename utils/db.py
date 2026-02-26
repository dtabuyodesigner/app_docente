import sqlite3
import os
from flask import g

DB_PATH = "app_evaluar.db"

def init_db_if_not_exists():
    """Initializes the SQLite database from schema.sql if it doesn't exist yet."""
    if not os.path.exists(DB_PATH):
        print(f"[{DB_PATH}] No existe. Inicializando base de datos en blanco...")
        conn = sqlite3.connect(DB_PATH)
        
        # Determine the absolute path to schema.sql in the project root
        schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schema.sql')
        
        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_script = f.read()
                # Run the script
                conn.executescript(schema_script)
            print(f"[{DB_PATH}] Base de datos inicializada correctamente con schema.sql.")
        else:
            print(f"[PELIGRO] Archivo schema.sql no encontrado en {schema_path}.")
            
        conn.commit()
        conn.close()

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row  # Access columns by name
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def nivel_a_nota(nivel):
    """Convierte un nivel (1-4) en una nota numérica (0-10)"""
    mapping = {1: 2.5, 2: 5.0, 3: 7.5, 4: 10.0}
    return mapping.get(nivel, 0.0)
