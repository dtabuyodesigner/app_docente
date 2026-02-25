import sqlite3
import os

DB_PATH = "app_evaluar.db"

def migrate_db():
    print("Iniciando migración segura de Base de Datos a Multi-Grupo...")
    
    # 1. Crear backup
    import shutil
    from datetime import datetime
    backup_path = f"app_evaluar_backup_pre_migracion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(DB_PATH, backup_path)
    print(f"✅ Backup creado: {backup_path}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        cur.execute("BEGIN")

        # 2. Add New Tables if they don't exist
        print("2. Creando tablas profesores y grupos...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS profesores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER,
                nombre TEXT NOT NULL,
                FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS grupos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                curso TEXT,
                profesor_id INTEGER,
                FOREIGN KEY(profesor_id) REFERENCES profesores(id)
            )
        """)

        # 3. Create Default Professor linked to first admin user
        print("3. Configurando Profesor predeterminado...")
        cur.execute("SELECT id, username FROM usuarios WHERE role = 'admin' LIMIT 1")
        admin_user = cur.fetchone()
        
        if admin_user:
            admin_id = admin_user[0]
            admin_name = admin_user[1].capitalize()
        else:
            admin_id = None
            admin_name = "Profesor Principal"
        
        # Check if profesor already exists
        cur.execute("SELECT id FROM profesores LIMIT 1")
        prof = cur.fetchone()
        if not prof:
            cur.execute("INSERT INTO profesores (usuario_id, nombre) VALUES (?, ?)", (admin_id, admin_name))
            profesor_id = cur.lastrowid
            print(f"✅ Profesor '{admin_name}' creado (ID: {profesor_id}).")
        else:
            profesor_id = prof[0]
            print(f"✅ Profesor existente encontrado (ID: {profesor_id}).")

        # 4. Create Default Group
        print("4. Configurando Grupo predeterminado...")
        cur.execute("SELECT id FROM grupos LIMIT 1")
        grupo = cur.fetchone()
        if not grupo:
            cur.execute("INSERT INTO grupos (nombre, curso, profesor_id) VALUES (?, ?, ?)", 
                        ("Mi Primer Grupo", "Curso Actual", profesor_id))
            grupo_id = cur.lastrowid
            print(f"✅ Grupo 'Mi Primer Grupo' creado (ID: {grupo_id}).")
        else:
            grupo_id = grupo[0]
            print(f"✅ Grupo existente encontrado (ID: {grupo_id}).")

        # 5. Modify Alumnos Table (Add grupo_id column)
        print("5. Modificando tabla alumnos...")
        # SQLite checking mechanism for columns
        cur.execute("PRAGMA table_info(alumnos)")
        columns = [col[1] for col in cur.fetchall()]
        
        if "grupo_id" not in columns:
            cur.execute("ALTER TABLE alumnos ADD COLUMN grupo_id INTEGER")
            print("✅ Columna 'grupo_id' añadida a 'alumnos'.")
        else:
            print("✅ La columna 'grupo_id' ya existe.")

        # 6. Assign existing students to default group
        print("6. Asignando alumnos existentes al grupo predeterminado...")
        cur.execute("UPDATE alumnos SET grupo_id = ? WHERE grupo_id IS NULL OR grupo_id = ''", (grupo_id,))
        count = cur.rowcount
        print(f"✅ {count} alumnos asignados al Grupo (ID: {grupo_id}).")

        conn.commit()
        print("\n🚀 ¡MIGRACIÓN COMPLETADA CON ÉXITO!")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERROR FATAL DURANTE LA MIGRACIÓN: {e}")
        print("Los cambios han sido revertidos. Revise el error.")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_db()
