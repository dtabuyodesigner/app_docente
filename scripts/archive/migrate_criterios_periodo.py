import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'app_evaluar.db')

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    print("Creating table criterios_periodo...")
    cur.execute('''
    CREATE TABLE IF NOT EXISTS criterios_periodo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        criterio_id INTEGER NOT NULL,
        grupo_id INTEGER NOT NULL,
        periodo TEXT NOT NULL,
        activo INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (criterio_id) REFERENCES criterios(id) ON DELETE CASCADE,
        FOREIGN KEY (grupo_id) REFERENCES grupos(id) ON DELETE CASCADE,
        UNIQUE(criterio_id, grupo_id, periodo)
    );
    ''')
    
    conn.commit()
    conn.close()
    print("Migration successful: Added criterios_periodo table.")

if __name__ == '__main__':
    migrate()
