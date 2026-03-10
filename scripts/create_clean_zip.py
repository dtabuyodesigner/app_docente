#!/usr/bin/env python3
import os
import zipfile
import shutil
from datetime import datetime

# Directorio base de la app
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_NAME = f"APP_EVALUAR_Limpio_{datetime.now().strftime('%Y%m%d')}.zip"
OUTPUT_PATH = os.path.join(BASE_DIR, OUTPUT_NAME)

# Lista de carpetas o archivos a exclusir o ignorar
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
    "logs",                     # Logs de sesión actuales
    "backups",                  # Backups locales (ahora van fuera, pero por si acaso)
    OUTPUT_NAME,
    "APP_EVALUAR_20260310.zip", # Zips anteriores
    ".history"
]

def should_exclude(curr_path):
    path_parts = curr_path.replace(BASE_DIR, "").strip(os.path.sep).split(os.path.sep)
    for part in path_parts:
        if part in EXCLUDES or part.endswith('.pyc') or part.endswith('.zip') or part.endswith('.sqlite3'):
            return True
    return False

def create_zip():
    print(f"Empaquetando aplicación 'limpia' en: {OUTPUT_NAME}")
    
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
                
    print("\n✅ ¡Paquete creado con éxito!")
    print(f"📦 Archivo: {OUTPUT_PATH}")
    print("Este archivo ZIP está limpio y listo para compartir. Al ejecutarlo en otro ordenador, ")
    print("la app solicitará crear el primer usuario administrativo.")

if __name__ == "__main__":
    create_zip()
