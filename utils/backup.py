import os
import shutil
import sqlite3
import datetime
import glob
import logging

# Configuración de logs para integridad y backups
LOG_FILE = "/home/danito73/Documentos/APP_EVALUAR/logs/integrity.log"
BACKUP_DIR = "/home/danito73/Documentos/APP_EVALUAR/backups"
DB_PATH = "/home/danito73/Documentos/APP_EVALUAR/app_evaluar.db"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def ensure_dirs():
    """Asegura que existan las carpetas necesarias."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

def check_integrity():
    """Ejecuta PRAGMA integrity_check en la base de datos."""
    if not os.path.exists(DB_PATH):
        logging.warning("No se encontró la base de datos para verificar integridad.")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchone()[0]
        conn.close()
        
        if result == "ok":
            logging.info("Chequeo de integridad: OK")
            return True
        else:
            logging.error(f"Error de integridad detectado: {result}")
            return False
    except Exception as e:
        logging.error(f"Error al ejecutar chequeo de integridad: {str(e)}")
        return False

def create_backup(label="auto"):
    """Crea un backup de la base de datos actual."""
    ensure_dirs()
    if not os.path.exists(DB_PATH):
        return False
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    backup_name = f"app_evaluar_backup_{timestamp}_{label}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    
    try:
        shutil.copy2(DB_PATH, backup_path)
        logging.info(f"Backup creado exitosamente: {backup_name}")
        rotate_backups()
        return True
    except Exception as e:
        logging.error(f"Error al crear backup: {str(e)}")
        return False

def rotate_backups():
    """Elimina backups con más de 30 días."""
    now = datetime.datetime.now()
    retention_days = 30
    
    files = glob.glob(os.path.join(BACKUP_DIR, "*.db"))
    for f in files:
        file_time = datetime.datetime.fromtimestamp(os.path.getmtime(f))
        if (now - file_time).days > retention_days:
            try:
                os.remove(f)
                logging.info(f"Backup antiguo eliminado (rotación): {os.path.basename(f)}")
            except Exception as e:
                logging.error(f"Error al eliminar backup antiguo {f}: {str(e)}")

def run_startup_tasks():
    """Ejecuta las tareas de blindaje al iniciar la app."""
    logging.info("--- Iniciando tareas de blindaje técnico ---")
    check_integrity()
    
    # Backup diario: comprobar si ya existe uno de hoy
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    existing_today = glob.glob(os.path.join(BACKUP_DIR, f"app_evaluar_backup_{today_str}_*.db"))
    
    if not existing_today:
        logging.info("No se encontró backup de hoy. Creando backup automático.")
        create_backup(label="startup")
    else:
        logging.info("Ya existe un backup del día de hoy.")
