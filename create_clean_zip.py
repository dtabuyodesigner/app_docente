#!/usr/bin/env python3
import os
import zipfile
from datetime import datetime

# Directorio raíz del proyecto (donde está este script)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_NAME = f"CuadernoDelTutor_Windows_{datetime.now().strftime('%Y%m%d')}.zip"
OUTPUT_PATH = os.path.join(BASE_DIR, OUTPUT_NAME)

# Carpetas y archivos a excluir
EXCLUDES = [
    ".git",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".idea",
    ".vscode",
    "node_modules",
    "dist",                      # Build anterior de PyInstaller
    "build",                     # Carpeta intermedia de PyInstaller
    "app_evaluar.db",            # BD del usuario actual
    "app_evaluar.db.bak",        # Backup de BD actual
    "app.db",
    "notebook.db",
    "database.db",
    "evaluacion.db",
    "logs",
    "app.log",
    "security.log",
    "backups",
    "PROGRAMACIONES",
    "static/uploads",
    "CRITERIOS_EVALUACION_INFANTIL",
    "CRITERIOS_EVALUACION_PRIMARIA",
    ".history",
    OUTPUT_NAME,                 # El propio zip que se está generando
]

def should_exclude(curr_path):
    rel_path = os.path.relpath(curr_path, BASE_DIR)
    path_parts = rel_path.split(os.path.sep)

    for part in path_parts:
        if part in EXCLUDES:
            return True

    # Path completo relativo (para casos como static/uploads)
    if rel_path.replace("\\", "/") in EXCLUDES:
        return True

    # Extensiones prohibidas
    if curr_path.endswith(('.pyc', '.zip', '.sqlite3', '.log')):
        return True

    return False

def create_zip():
    print(f"📦 Empaquetando aplicación para Windows en: {OUTPUT_NAME}")
    print(f"   Carpeta base: {BASE_DIR}\n")

    files_added = 0
    with zipfile.ZipFile(OUTPUT_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(BASE_DIR):
            # Excluir carpetas enteras para no recorrerlas
            dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]

            for file in files:
                file_path = os.path.join(root, file)
                if should_exclude(file_path):
                    continue
                arcname = os.path.relpath(file_path, BASE_DIR)
                zipf.write(file_path, arcname)
                files_added += 1
                print(f"   + {arcname}")

    print(f"\n✅ ¡ZIP creado con éxito! ({files_added} archivos)")
    print(f"📦 Archivo: {OUTPUT_PATH}")
    print()
    print("Pasos en Windows 11:")
    print("  1. Descomprime el ZIP")
    print("  2. Abre una terminal en esa carpeta")
    print("  3. pip install -r requirements.txt")
    print("  4. build_windows.bat")
    print("  5. Ejecuta dist/CuadernoDelTutor/CuadernoDelTutor.exe")

if __name__ == "__main__":
    create_zip()
