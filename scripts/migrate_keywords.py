from utils.db import get_db

def migrate():
    db = get_db()
    cur = db.cursor()
    
    print("Creando tabla criterios_keywords...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS criterios_keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            criterio_id INTEGER,
            keyword TEXT,
            FOREIGN KEY(criterio_id) REFERENCES criterios(id)
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_keywords_word ON criterios_keywords(keyword)")
    
    # Seeding some initial keywords from the example
    # We need to find real criterio IDs to seed.
    # I'll just seed a few based on common codes if they exist.
    
    keywords = [
        ("LCL3.1", "lectura"),
        ("LCL3.1", "cuento"),
        ("LCL3.1", "escuchar"),
        ("LCL3.1", "comprensión"),
        ("LCL3.2", "escribir"),
        ("LCL3.2", "redacción"),
        ("LCL3.3", "conversación"),
        ("MAT.1.1", "cálculo"),
        ("MAT.1.1", "sumas"),
        ("MAT.2.1", "problemas")
    ]
    
    print("Sembrando keywords de ejemplo...")
    for codigo, keyword in keywords:
        # Get criterio ID by code
        cur.execute("SELECT id FROM criterios WHERE codigo = ? LIMIT 1", (codigo,))
        row = cur.fetchone()
        if row:
            c_id = row["id"]
            # Check if already exists
            cur.execute("SELECT id FROM criterios_keywords WHERE criterio_id = ? AND keyword = ?", (c_id, keyword))
            if not cur.fetchone():
                cur.execute("INSERT INTO criterios_keywords (criterio_id, keyword) VALUES (?, ?)", (c_id, keyword))
                print(f"  + Added: {codigo} -> {keyword}")
    
    db.commit()
    print("Migración completada.")

if __name__ == "__main__":
    import os
    import sys
    # Add parent dir to path to import utils
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app import app
    with app.app_context():
        migrate()
