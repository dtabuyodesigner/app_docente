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
