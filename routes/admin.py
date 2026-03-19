from flask import Blueprint, jsonify, session, request, send_file
import os
import glob
import datetime
import shutil
from utils.backup import create_backup, BACKUP_DIR, check_integrity
from utils.db import get_db_path

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
        shutil.copy2(backup_path, get_db_path())
        
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

@admin_bp.route('/api/admin/backup/restore/external', methods=['POST'])
def restore_external_backup():
    if 'file' not in request.files:
        return jsonify({"ok": False, "error": "No se ha proporcionado ningún archivo"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"ok": False, "error": "Nombre de archivo vacío"}), 400
    
    if not file.filename.endswith('.db'):
        return jsonify({"ok": False, "error": "El archivo debe ser una base de datos (.db)"}), 400

    # 1. Crear backup de seguridad antes de restaurar
    create_backup(label="pre_restore_ext")
    
    try:
        # 2. Guardar el archivo temporalmente y luego moverlo a la ruta de la BD
        db_path = get_db_path()
        file.save(db_path)
        
        # 3. Verificar integridad después de restaurar
        is_ok = check_integrity()
        
        if is_ok:
            return jsonify({
                "ok": True, 
                "message": "Copia externa restaurada con éxito. Reinicie la aplicación."
            })
        else:
            return jsonify({
                "ok": False, 
                "error": "El archivo restaurado parece estar corrupto o no es compatible."
            }), 500
            
    except Exception as e:
        return jsonify({"ok": False, "error": f"Error crítico al procesar el archivo: {str(e)}"}), 500

@admin_bp.route('/api/admin/integrity', methods=['GET'])
def get_integrity():
    is_ok = check_integrity()
    return jsonify({"ok": is_ok, "status": "ok" if is_ok else "error"})

@admin_bp.route('/api/admin/check_updates', methods=['GET'])
def check_updates():
    import requests
    from version import APP_VERSION

    github_repo = "dtabuyodesigner/app_docente"
    branch = "feature/refactor-evaluacion-curricular"

    try:
        # Obtener los últimos commits de la rama
        commits_url = f"https://api.github.com/repos/{github_repo}/commits?sha={branch}&per_page=5"
        r = requests.get(commits_url, timeout=5, headers={"Accept": "application/vnd.github.v3+json"})

        if r.status_code != 200:
            return jsonify({"ok": False, "error": f"Error GitHub: HTTP {r.status_code}"}), 500

        commits = r.json()

        # Obtener el SHA local actual via git
        import subprocess
        try:
            local_sha = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                stderr=subprocess.DEVNULL
            ).decode().strip()
        except Exception:
            local_sha = ""

        latest_sha = commits[0]["sha"] if commits else ""
        update_available = bool(latest_sha and local_sha and latest_sha != local_sha)

        # Construir lista de cambios pendientes
        cambios = []
        for c in commits:
            sha = c["sha"]
            msg = c["commit"]["message"].split("\n")[0]  # Solo primera línea
            fecha = c["commit"]["committer"]["date"][:10]
            cambios.append({"sha": sha[:7], "mensaje": msg, "fecha": fecha})
            if sha == local_sha:
                break

        return jsonify({
            "ok": True,
            "update_available": update_available,
            "current_version": APP_VERSION,
            "local_sha": local_sha[:7] if local_sha else "desconocido",
            "latest_sha": latest_sha[:7] if latest_sha else "desconocido",
            "cambios": cambios if update_available else []
        })

    except Exception as e:
        return jsonify({"ok": False, "error": f"Error de conexión: {str(e)}"}), 500


@admin_bp.route('/api/admin/apply_update', methods=['POST'])
def apply_update():
    """Hace git pull y reinicia la app."""
    import subprocess
    import threading

    project_dir = os.path.dirname(os.path.abspath(__file__))

    try:
        # Crear backup antes de actualizar
        create_backup(label="pre_update")

        # Ejecutar git pull
        result = subprocess.run(
            ["git", "pull"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return jsonify({
                "ok": False,
                "error": f"Error en git pull: {result.stderr}"
            }), 500

        output = result.stdout.strip()

        # Reiniciar en un hilo separado para que la respuesta llegue primero
        def restart():
            import time
            time.sleep(1.5)
            os.execv(__file__.replace('routes/admin.py', 'desktop.py'),
                     ['desktop.py'])

        threading.Thread(target=restart, daemon=True).start()

        return jsonify({
            "ok": True,
            "mensaje": "Actualización aplicada. La app se reiniciará en unos segundos.",
            "detalle": output
        })

    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "error": "Timeout — comprueba la conexión a Internet"}), 500
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@admin_bp.route('/api/admin/limpiar_alumnos_borrados', methods=['POST'])
def limpiar_alumnos_borrados():
    from utils.db import get_db
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        cur.execute("DELETE FROM alumnos WHERE deleted_at IS NOT NULL")
        eliminados = cur.rowcount
        conn.commit()
        return jsonify({"ok": True, "message": f"Se han eliminado definitivamente {eliminados} alumnos."})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": f"Error interno al limpiar alumnos: {str(e)}"}), 500
