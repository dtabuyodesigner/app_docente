import sqlite3
import os
import sys

# Ensure werkzeug is accessible from the project venv
try:
    from werkzeug.security import generate_password_hash
except ImportError:
    print("Error: No se pudo cargar 'werkzeug.security'. Asegúrate de ejecutar este script desde el entorno virtual.")
    sys.exit(1)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "app_evaluar.db")

def recover_admin():
    print("=========================================")
    print("   RECUPERACION DE ACCESO ADMINISTRADOR  ")
    print("=========================================\n")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: No se encontró la base de datos en {DB_PATH}.")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Look for users with admin role or specific names
        cur.execute("SELECT id, username FROM usuarios WHERE role = 'admin' OR username IN ('admin', 'daniel')")
        admins = cur.fetchall()
        
        if not admins:
            print("❌ Error: No se encontraron usuarios administradores en la base de datos.")
            return
            
        new_password = "1234"
        hashed = generate_password_hash(new_password)
        
        print("Se han encontrado los siguientes administradores:")
        for admin in admins:
            user_id = admin[0]
            username = admin[1]
            
            # Reset password
            cur.execute("UPDATE usuarios SET password_hash = ? WHERE id = ?", (hashed, user_id))
            print(f" -> Usuario: '{username}'. Contraseña restablecida.")
            
        conn.commit()
        conn.close()
        
        print("\n✅ RECUPERACION COMPLETADA CON EXITO")
        print(f"Tu nueva contraseña de emergencia es: {new_password}")
        print("Por favor, entra en la aplicación y cambia esta contraseña desde")
        print("el menú de Gestión de Usuarios lo antes posible por seguridad.")
        
    except Exception as e:
        print(f"\n❌ Ocurrió un error al intentar modificar la base de datos: {e}")

if __name__ == "__main__":
    recover_admin()
