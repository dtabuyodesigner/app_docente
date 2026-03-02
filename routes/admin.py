from flask import Blueprint, jsonify, session, request, send_file
import os
import glob
import datetime
import shutil
from utils.backup import create_backup, BACKUP_DIR, DB_PATH, check_integrity

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
def require_admin():
    if not session.get('logged_in'):
        return jsonify({"ok": False, "error": "No autorizado"}), 401
    if session.get('role') != 'admin':
        return jsonify({"ok": False, "error": "Requiere privilegios de administrador"}), 403

@admin_bp.route('/api/admin/backups', methods=['GET'])
def list_backups():
    files = glob.glob(os.path.join(BACKUP_DIR, "*.db"))
    backups = []
    for f in files:
        stat = os.stat(f)
        backups.append({
            "name": os.path.basename(f),
            "size": stat.st_size,
            "mtime": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        })
    # Sort by mtime descending
    backups.sort(key=lambda x: x['mtime'], reverse=True)
    return jsonify(backups)

@admin_bp.route('/api/admin/backup/manual', methods=['POST'])
def manual_backup():
    success = create_backup(label="manual")
    if success:
        return jsonify({"ok": True, "message": "Backup manual creado con éxito"})
    else:
        return jsonify({"ok": False, "error": "Error al crear el backup"}), 500

@admin_bp.route('/api/admin/restore', methods=['POST'])
def restore_backup():
    data = request.json
    filename = data.get('filename')
    
    if not filename:
        return jsonify({"ok": False, "error": "Nombre de archivo no proporcionado"}), 400
    
    backup_path = os.path.join(BACKUP_DIR, filename)
    if not os.path.exists(backup_path):
        return jsonify({"ok": False, "error": "El archivo de backup no existe"}), 404
    
    # 1. Crear backup de seguridad antes de restaurar
    create_backup(label="pre_restore")
    
    try:
        # 2. Restaurar el archivo (reemplazar la base de datos actual)
        # Nota: En SQLite, shutil.copy2 es suficiente si no hay conexiones activas escribiendo.
        # Flask-SQLAlchemy o similares podrían requerir cerrar conexiones, pero aquí usamos sqlite3 directo.
        shutil.copy2(backup_path, DB_PATH)
        
        # 3. Verificar integridad después de restaurar
        is_ok = check_integrity()
        
        if is_ok:
            return jsonify({
                "ok": True, 
                "message": "Restauración completada con éxito. Reinicie la aplicación para asegurar consistencia."
            })
        else:
            return jsonify({
                "ok": False, 
                "error": "La base de datos restaurada parece estar corrupta. Se recomienda restaurar otro backup."
            }), 500
            
    except Exception as e:
        return jsonify({"ok": False, "error": f"Error crítico durante la restauración: {str(e)}"}), 500

@admin_bp.route('/api/admin/integrity', methods=['GET'])
def get_integrity():
    is_ok = check_integrity()
    return jsonify({"ok": is_ok, "status": "ok" if is_ok else "error"})
