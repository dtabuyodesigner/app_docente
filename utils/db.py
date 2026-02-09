import sqlite3
import os

DB_PATH = "app_evaluar.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def nivel_a_nota(nivel):
    """Convierte un nivel (1-4) en una nota numérica (0-10)"""
    mapping = {1: 2.5, 2: 5.0, 3: 7.5, 4: 10.0}
    return mapping.get(nivel, 0.0)
