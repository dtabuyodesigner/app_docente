#!/usr/bin/env python3
import os
import zipfile
import shutil
from datetime import datetime

# Directorio base de la app
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_NAME = f"APP_EVALUAR_Windows_Pilar_{datetime.now().strftime('%Y%m%d')}.zip"
OUTPUT_PATH = os.path.join(BASE_DIR, OUTPUT_NAME)

# Lista de carpetas o archivos a distribuir (whitelist/blacklist)
EXCLUDES = [
    ".git",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".idea",
    ".vscode",
    "node_modules",
    "app_evaluar.db",           # La BD del usuario actual se ignora
    "app_evaluar.db.bak",       # Backup de BD actual
    "app.db",                   # BD temporal antigua
    "notebook.db",              # DB temporal
    "database.db",              # DB temporal
    "evaluacion.db",            # DB temporal
    "logs",                     # Logs de sesión actuales
    "app.log",                  # Log principal
    "security.log",             # Log de seguridad
    "backups",                  # Backups locales
    "PROGRAMACIONES",            # Documentos del usuario
    "static/uploads",           # Fotos de alumnos, etc.
    "CRITERIOS_EVALUACION_INFANTIL", # Criterios específicos cargados
    "CRITERIOS_EVALUACION_PRIMARIA",  # Criterios específicos cargados
    OUTPUT_NAME,
    ".history",
    "build",                    # Carpetas de PyInstaller local
    "dist"                      # Carpetas de PyInstaller local
]

def should_exclude(curr_path):
    # Ruta relativa para comparar
    rel_path = os.path.relpath(curr_path, BASE_DIR)
    path_parts = rel_path.split(os.path.sep)
    
    # Comprobar si alguna parte del path está en EXCLUDES
    for part in path_parts:
        if part in EXCLUDES:
            return True
            
    # También comprobar el path completo relativo (para casos como static/uploads)
    if rel_path.replace("\\", "/") in EXCLUDES:
        return True

    # Extensiones prohibidas (excepto .spec que el usuario pidió no tocar)
    if curr_path.endswith(('.pyc', '.zip', '.sqlite3', '.log', '.pyd', '.pyo')):
        return True
        
    return False

def create_zip():
    print(f"--- Creando paquete Windows para Pilar ---")
    print(f"Destino: {OUTPUT_NAME}")
    
    files_added = 0
    with zipfile.ZipFile(OUTPUT_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(BASE_DIR):
            # Ignorar carpetas enteras para que no las recorra
            dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                if should_exclude(file_path):
                    continue
                
                # Calcular ruta relativa dentro del zip
                arcname = os.path.relpath(file_path, BASE_DIR)
                zipf.write(file_path, arcname)
                files_added += 1
                
    print(f"\n✅ Paquete creado con éxito ({files_added} archivos)")
    print(f"📦 Archivo: {OUTPUT_NAME}")
    print("\nEste ZIP contiene el código fuente 'limpio' y el script build_windows.bat.")
    print("Para generar el ejecutable (.exe) en Windows:")
    print("  1. Extraer el ZIP")
    print("  2. Abrir terminal en la carpeta")
    print("  3. Ejecutar: build_windows.bat")

if __name__ == "__main__":
    create_zip()
