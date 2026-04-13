from flask import Blueprint, jsonify, session, request, send_file
import os
import glob
import datetime
import shutil
from utils.backup import create_backup, BACKUP_DIR, check_integrity
from utils.db import get_db_path
import subprocess
import requests

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

    import tempfile
    import shutil

    try:
        # 1. Guardar temporalmente para validar antes de reemplazar
        tmp_fd, tmp_path = tempfile.mkstemp(suffix='.db')
        os.close(tmp_fd)
        file.save(tmp_path)

        # 2. Validar que es un SQLite válido con el esquema esperado
        import sqlite3
        conn_tmp = sqlite3.connect(tmp_path)
        cur_tmp = conn_tmp.cursor()

        # Verificar que tiene las tablas esenciales
        cur_tmp.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cur_tmp.fetchall()}
        required_tables = {'usuarios', 'alumnos', 'grupos', 'areas', 'criterios', 'etapas'}
        missing = required_tables - tables
        if missing:
            conn_tmp.close()
            os.unlink(tmp_path)
            return jsonify({"ok": False, "error": f"El archivo no es una BD válida de APP_EVALUAR. Faltan tablas: {', '.join(missing)}"}), 400

        # Verificar integridad SQLite
        cur_tmp.execute("PRAGMA integrity_check")
        integrity = cur_tmp.fetchone()[0]
        conn_tmp.close()
        if integrity != "ok":
            os.unlink(tmp_path)
            return jsonify({"ok": False, "error": f"El archivo está corrupto: {integrity}"}), 400

        # 3. Crear backup de seguridad antes de restaurar
        create_backup(label="pre_restore_ext")

        # 4. Reemplazar la BD
        db_path = get_db_path()
        shutil.move(tmp_path, db_path)

        return jsonify({
            "ok": True,
            "message": "Copia externa restaurada con éxito. Reinicie la aplicación."
        })

    except Exception as e:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return jsonify({"ok": False, "error": f"Error crítico al procesar el archivo: {str(e)}"}), 500

@admin_bp.route('/api/admin/integrity', methods=['GET'])
def get_integrity():
    is_ok = check_integrity()
    return jsonify({"ok": is_ok, "status": "ok" if is_ok else "error"})

@admin_bp.route('/api/admin/version', methods=['GET'])
def get_version():
    from version import APP_VERSION
    try:
        local_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        local_sha = ""
    return jsonify({
        "ok": True,
        "version": APP_VERSION,
        "sha": local_sha[:7] if local_sha else "desconocido"
    })

@admin_bp.route('/api/admin/check_updates', methods=['GET'])
def check_updates():
    from version import APP_VERSION

    github_repo = "dtabuyodesigner/app_docente"
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Si es un .exe compilado sin git, devolver sin actualizaciones silenciosamente
    is_frozen = getattr(__import__('sys'), 'frozen', False)

    try:
        # Obtener SHA local
        local_sha = ""
        try:
            git_cmds = ["git"]
            if os.name == 'nt':
                git_cmds.extend([
                    r"C:\Program Files\Git\bin\git.exe",
                    r"C:\Program Files\Git\cmd\git.exe",
                    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Git\cmd\git.exe")
                ])
            for cmd in git_cmds:
                try:
                    local_sha = subprocess.check_output(
                        [cmd, "rev-parse", "HEAD"],
                        cwd=root_dir,
                        stderr=subprocess.PIPE,
                        timeout=3
                    ).decode().strip()
                    if local_sha:
                        break
                except Exception:
                    continue
        except Exception:
            local_sha = ""

        # Sin git local — comparar versiones directamente desde GitHub
        if not local_sha:
            latest_version = APP_VERSION
            try:
                branch_fallback = "master"
                version_url = f"https://raw.githubusercontent.com/{github_repo}/{branch_fallback}/version.py"
                rv = requests.get(version_url, timeout=4)
                if rv.status_code == 200:
                    import re as _re
                    m = _re.search(r'APP_VERSION\s*=\s*["\']([^"\']+)["\']', rv.text)
                    if m:
                        latest_version = m.group(1)
            except Exception:
                pass
            def _parse_ver2(v):
                try:
                    return tuple(int(x) for x in v.lstrip('v').split('.'))
                except Exception:
                    return (0, 0, 0)
            update_available = _parse_ver2(latest_version) > _parse_ver2(APP_VERSION)
            return jsonify({
                "ok": True,
                "update_available": update_available,
                "current_version": APP_VERSION,
                "latest_version": latest_version,
                "local_sha": "desconocido",
                "latest_sha": "desconocido",
                "cambios": [{"sha": "—", "mensaje": f"Nueva versión disponible: {latest_version}", "fecha": ""}] if update_available else [],
                "reason": "git_not_available"
            })

        # Siempre comparar versión desde la rama principal (master)
        dev_branch = "master"
        latest_version = APP_VERSION
        try:
            import re as _re
            version_url = f"https://raw.githubusercontent.com/{github_repo}/{dev_branch}/version.py"
            rv = requests.get(version_url, timeout=4)
            if rv.status_code == 200:
                m = _re.search(r'APP_VERSION\s*=\s*["\']([^"\']+)["\']', rv.text)
                if m:
                    latest_version = m.group(1)
        except Exception:
            pass

        # Si la versión remota es MAYOR que la local → hay actualización (comparación numérica)
        def _parse_ver(v):
            try:
                return tuple(int(x) for x in v.lstrip('v').split('.'))
            except Exception:
                return (0, 0, 0)
        update_available = _parse_ver(latest_version) > _parse_ver(APP_VERSION)

        # Consultar GitHub para lista de cambios
        commits_url = f"https://api.github.com/repos/{github_repo}/commits?sha={dev_branch}&per_page=5"
        r = requests.get(commits_url, timeout=5, headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AppEvaluar-TeacherNotebook"
        })

        commits = r.json() if r.status_code == 200 else []
        latest_sha = commits[0]["sha"] if commits else ""

        # Chequeo secundario por SHA (si git disponible y versiones coinciden)
        if not update_available and latest_sha and local_sha and latest_sha != local_sha:
            try:
                subprocess.check_call(
                    ["git", "merge-base", "--is-ancestor", latest_sha, local_sha],
                    cwd=root_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            except Exception:
                update_available = True

        cambios = []
        for c in commits:
            sha = c["sha"]
            msg = c["commit"]["message"].split("\n")[0]
            fecha = c["commit"]["committer"]["date"][:10]
            cambios.append({"sha": sha[:7], "mensaje": msg, "fecha": fecha})
            if sha == local_sha:
                break

        return jsonify({
            "ok": True,
            "update_available": update_available,
            "current_version": APP_VERSION,
            "latest_version": latest_version,
            "local_sha": local_sha[:7] if local_sha else "desconocido",
            "latest_sha": latest_sha[:7] if latest_sha else "desconocido",
            "cambios": cambios if update_available else []
        })

    except Exception:
        # Cualquier error (sin internet, timeout, etc.) — devolver sin error silenciosamente
        return jsonify({"ok": True, "update_available": False, "current_version": APP_VERSION})


@admin_bp.route('/api/admin/apply_update', methods=['POST'])
def apply_update():
    """Hace git pull y opcionalmente revierte carpetas no deseadas."""
    import subprocess
    import threading
    import sys

    data = request.json or {}
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    try:
        # 1. Obtener SHA actual antes de tirar
        try:
            sha_before = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], 
                cwd=root_dir, 
                stderr=subprocess.DEVNULL
            ).decode().strip()
        except:
            sha_before = None

        # 2. Crear backup antes de actualizar
        create_backup(label="pre_update")

        # 3. Ejecutar git pull
        # Intentar git pull de forma robusta
        try:
            git_cmds = ["git"]
            if os.name == 'nt':
                git_cmds.extend([
                    r"C:\Program Files\Git\bin\git.exe",
                    r"C:\Program Files\Git\cmd\git.exe",
                    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Git\cmd\git.exe")
                ])

            result = None
            for cmd in git_cmds:
                try:
                    result = subprocess.run(
                        [cmd, "pull"],
                        cwd=root_dir,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        shell=True if os.name == 'nt' else False
                    )
                    if result.returncode == 0: break
                    print(f"Sub-intento git pull falló con {cmd}: {result.stderr}")
                except Exception:
                    continue

            if not result or result.returncode != 0:
                error_msg = result.stderr if result else "No se pudo encontrar el ejecutable de Git"
                return jsonify({"ok": False, "error": f"Error al descargar (git pull): {error_msg}"}), 500
                
        except Exception as e:
            return jsonify({"ok": False, "error": f"Error crítico al intentar git pull: {str(e)}"}), 500

        output = result.stdout.strip()

        # 4. Reiniciar en un hilo separado para aplicar cambios
        def restart():
            import time
            import sys
            import subprocess
            time.sleep(1.5)
            
            # Detectar si estamos en un .exe de PyInstaller
            is_frozen = getattr(sys, 'frozen', False)
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            
            if os.name == 'nt':
                # DETACHED_PROCESS (0x00000008) para independencia total del proceso padre
                # Esto suele evitar que herede la consola o que se abra una innecesaria.
                creationflags = 0x00000008 
                
                if is_frozen:
                    # En el .exe, sys.executable ya es el programa completo
                    cmd = [sys.executable] + sys.argv[1:]
                else:
                    # Desde código fuente
                    cmd = [sys.executable] + sys.argv
                
                subprocess.Popen(cmd, creationflags=creationflags, close_fds=True)
            else:
                # Linux / Mac
                os.execl(sys.executable, sys.executable, *sys.argv)
            
            os._exit(0)

        threading.Thread(target=restart, daemon=True).start()

        return jsonify({
            "ok": True,
            "mensaje": "Actualización aplicada correctamente.",
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
