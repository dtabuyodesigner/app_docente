from flask import Blueprint, send_from_directory, request, jsonify, session, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from utils.db import get_db
import os
from utils.security import get_security_logger

main_bp = Blueprint('main', __name__)
security_logger = get_security_logger()

# ─── PRIMER ARRANQUE ─────────────────────────────────────────────────────────

@main_bp.route("/api/setup", methods=["GET"])
def setup_status():
    """Devuelve si la app ya tiene usuarios configurados."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM usuarios")
    count = cur.fetchone()[0]
    return jsonify({"ok": True, "needs_setup": count == 0})

@main_bp.route("/api/setup", methods=["POST"])
def do_setup():
    """Crea el primer usuario administrador. Solo funciona si no hay usuarios."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM usuarios")
    if cur.fetchone()[0] > 0:
        return jsonify({"ok": False, "error": "Ya hay usuarios configurados. Accede con tu cuenta."}), 403

    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    confirm  = data.get("confirm", "")

    if not username or not password:
        return jsonify({"ok": False, "error": "El usuario y la contraseña son obligatorios."}), 400
    if len(username) < 3:
        return jsonify({"ok": False, "error": "El usuario debe tener al menos 3 caracteres."}), 400
    if len(password) < 6:
        return jsonify({"ok": False, "error": "La contraseña debe tener al menos 6 caracteres."}), 400
    if password != confirm:
        return jsonify({"ok": False, "error": "Las contraseñas no coinciden."}), 400

    try:
        pwd_hash = generate_password_hash(password)
        cur.execute(
            "INSERT INTO usuarios (username, password_hash, role) VALUES (?, ?, ?)",
            (username, pwd_hash, "admin")
        )
        conn.commit()
        security_logger.info(f"Primer usuario administrador '{username}' creado durante el setup inicial.")

        # Iniciar sesión automáticamente
        session['logged_in'] = True
        session['user_id']   = cur.lastrowid
        session['username']  = username
        session['role']      = 'admin'
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": "Error interno al crear el usuario."}), 500

@main_bp.route("/")
def inicio():
    return send_from_directory("static", "index.html")

@main_bp.route("/alumnos")
def alumnos_page():
    return send_from_directory("static", "alumnos.html")

@main_bp.route("/asistencia")
def asistencia_page():
    return send_from_directory("static", "asistencia.html")

@main_bp.route("/evaluacion")
def evaluacion_page():
    return send_from_directory("static", "evaluacion.html")

@main_bp.route("/informes")
def informes_page():
    return send_from_directory("static", "informes.html")

@main_bp.route("/programacion")
def programacion_page():
    return send_from_directory("static", "programacion.html")

@main_bp.route("/rubricas")
def rubricas_page():
    return send_from_directory("static", "rubricas.html")

@main_bp.route("/diario")
def diario_page():
    return send_from_directory("static", "diario.html")

@main_bp.route("/reuniones")
def reuniones_page():
    return send_from_directory('static', 'reuniones.html')

@main_bp.route("/horario")
def horario_page():
    return send_from_directory("static", "horario.html")

@main_bp.route("/comedor")
def comedor_page():
    return send_from_directory("static", "comedor.html")

@main_bp.route("/perfil/<int:id>")
def perfil_page(id):
    return send_from_directory("static", "perfil.html")

@main_bp.route("/criterios")
def criterios_page():
    return send_from_directory("static", "evaluacion.html")

@main_bp.route("/areas")
def areas_page():
    return send_from_directory("static", "areas.html")

@main_bp.route("/gestion_areas")
def gestion_areas_page():
    return send_from_directory("static", "areas.html")

@main_bp.route("/tareas")
def tareas_page():
    return send_from_directory("static", "tareas.html")

@main_bp.route("/login", methods=["GET"])
def login_page():
    return send_from_directory("static", "login.html")

@main_bp.route("/biblioteca")
def biblioteca_page():
    return send_from_directory("static", "biblioteca.html")

@main_bp.route("/material")
def material_page():
    return send_from_directory("static", "material.html")

@main_bp.route("/configuracion")
def configuracion_page():
    return send_from_directory("static", "configuracion.html")

@main_bp.route("/prestamos")
def prestamos_page():
    return redirect("/biblioteca#prestamos")

# We exempt login so that users whose session expired don't get 400 Bad Request
# However, for a fully secure app we should supply a CSRF token to the login page as well.
# For simplicity in this Phase 1, we will exempt it.
@main_bp.route("/login", methods=["POST"])
def do_login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"ok": False, "error": "Faltan credenciales"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password_hash, role FROM usuarios WHERE username = ?", (username,))
    user = cur.fetchone()

    # Si por algún casual la DB no tiene usuarios y existe APP_PASSWORD, se deja como fallback de emergencia temporal
    legacy_pwd = os.getenv("APP_PASSWORD")
    if not user and legacy_pwd and password == legacy_pwd and username == "admin":
        session['logged_in'] = True
        session['user_id'] = 0
        session['username'] = 'admin'
        session['role'] = 'admin'
        return jsonify({"ok": True})

    if user and check_password_hash(user["password_hash"], password):
        session['logged_in'] = True
        session['user_id'] = user["id"]
        session['username'] = user["username"]
        session['role'] = user["role"]
        
        security_logger.info(f"Successful login for user '{username}'. IP: {request.remote_addr}")
        
        # Load default active group
        cur.execute("SELECT id FROM profesores WHERE usuario_id = ?", (user["id"],))
        prof = cur.fetchone()
        if prof:
            cur.execute("SELECT id FROM grupos WHERE profesor_id = ? ORDER BY id LIMIT 1", (prof["id"],))
            grupo = cur.fetchone()
            if grupo:
                session['active_group_id'] = grupo["id"]

        return jsonify({"ok": True})
        
    security_logger.warning(f"Failed login attempt for username '{username}'. IP: {request.remote_addr}")
    return jsonify({"ok": False, "error": "Credenciales incorrectas"}), 401

@main_bp.route("/api/grupos", methods=["GET"])
def get_mis_grupos():
    if not session.get('logged_in'):
        return jsonify({"ok": False, "error": "No autorizado"}), 401
        
    conn = get_db()
    cur = conn.cursor()
    # Find profesor linked to this user
    cur.execute("SELECT id FROM profesores WHERE usuario_id = ?", (session.get("user_id"),))
    prof = cur.fetchone()
    
    if not prof:
        # If no profesor record exists yet, maybe they are admin. Return empty or handle gracefully.
        return jsonify([])
        
    cur.execute("""
        SELECT g.id, g.nombre, g.curso, COUNT(a.id) as num_alumnos, g.equipo_docente
        FROM grupos g
        LEFT JOIN alumnos a ON g.id = a.grupo_id AND a.deleted_at IS NULL
        WHERE g.profesor_id = ?
        GROUP BY g.id, g.nombre, g.curso, g.equipo_docente
        ORDER BY g.curso ASC, g.nombre ASC
    """, (prof["id"],))
    grupos = [dict(g) for g in cur.fetchall()]
    return jsonify(grupos)


@main_bp.route("/api/grupos", methods=["POST"])
def new_grupo():
    if not session.get('logged_in'):
        return jsonify({"ok": False, "error": "No autorizado"}), 401
        
    data = request.json
    print(f"[DEBUG] Creando nuevo grupo. Datos recibidos: {data}")
    etapa_curso = data.get("etapa_curso", "")
    linea = data.get("linea", "")
    eq_doc = data.get("equipo_docente", "")
    
    if not etapa_curso:
        print(f"[DEBUG] Error: etapa_curso está vacío. Session user_id: {session.get('user_id')}")
        return jsonify({"ok": False, "error": "Faltan datos de etapa/curso. Verifica que hayas seleccionado una opción."}), 400
        
    nombres_map = {
        "infantil_3": "Infantil 3 años",
        "infantil_4": "Infantil 4 años",
        "infantil_5": "Infantil 5 años",
        "primaria_1": "1º Primaria",
        "primaria_2": "2º Primaria",
        "primaria_3": "3º Primaria",
        "primaria_4": "4º Primaria",
        "primaria_5": "5º Primaria",
        "primaria_6": "6º Primaria",
        "unitario_infantil": "Unitario Infantil",
        "unitario_primaria": "Unitario Primaria",
        "unitario_mixto": "Unitario Mixto (Inf. y Prim.)"
    }
    
    base_name = nombres_map.get(etapa_curso, "Grupo Personalizado")
    nombre_final = f"{base_name} {linea}".strip()
    
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT id FROM profesores WHERE usuario_id = ?", (session.get("user_id"),))
    prof = cur.fetchone()
    
    if not prof:
        cur.execute("INSERT INTO profesores (usuario_id, nombre) VALUES (?, ?)", (session.get("user_id"), session.get("username")))
        prof_id = cur.lastrowid
    else:
        prof_id = prof["id"]
        
    # Determinar etapa_id: infantil → 1, primaria/secundaria → 2 (o 3)
    etapa_id_map = {
        "infantil_3": 1, "infantil_4": 1, "infantil_5": 1, "unitario_infantil": 1,
        "primaria_1": 2, "primaria_2": 2, "primaria_3": 2, "primaria_4": 2,
        "primaria_5": 2, "primaria_6": 2, "unitario_primaria": 2, "unitario_mixto": 2,
    }
    # Buscar id real de etapas en BD
    cur.execute("SELECT id, nombre FROM etapas")
    etapas_db = {r["nombre"].lower(): r["id"] for r in cur.fetchall()}
    
    etapa_id_num = etapa_id_map.get(etapa_curso, 2)
    
    # Intento de recuperación robusta por nombre si el ID no cuadra
    if etapa_id_num == 1:
        etapa_id_real = etapas_db.get("infantil", 1)
        tipo_eval = "infantil"
    else:
        etapa_id_real = etapas_db.get("primaria", 2)
        tipo_eval = "primaria"
    
    print(f"[DEBUG] Etapa detectada: {tipo_eval} (ID real: {etapa_id_real})")
    
    try:
        cur.execute(
            "INSERT INTO grupos (nombre, curso, profesor_id, etapa_id, tipo_evaluacion, equipo_docente) VALUES (?, ?, ?, ?, ?, ?)",
            (nombre_final, etapa_curso, prof_id, etapa_id_real, tipo_eval, eq_doc)
        )
        new_group_id = cur.lastrowid
        print(f"[DEBUG] Grupo creado con ID: {new_group_id}")
        
        # If it's the first group created and they have none active
        if not session.get('active_group_id'):
            session['active_group_id'] = new_group_id
            
        conn.commit()
        return jsonify({"ok": True, "id": new_group_id, "nombre": nombre_final})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@main_bp.route("/api/grupos/<int:grupo_id>", methods=["PUT"])
def rename_grupo(grupo_id):
    if not session.get('logged_in'):
        return jsonify({"ok": False, "error": "No autorizado"}), 401
        
    data = request.json
    nuevo_curso = data.get("curso", "").strip()
    nueva_linea = data.get("linea", "").strip()
    eq_doc = data.get("equipo_docente", "")
    
    if not nuevo_curso:
        return jsonify({"ok": False, "error": "Falta la etapa/curso"}), 400

    nombres_map = {
        "infantil_3": "Infantil 3 años",
        "infantil_4": "Infantil 4 años",
        "infantil_5": "Infantil 5 años",
        "primaria_1": "1º Primaria",
        "primaria_2": "2º Primaria",
        "primaria_3": "3º Primaria",
        "primaria_4": "4º Primaria",
        "primaria_5": "5º Primaria",
        "primaria_6": "6º Primaria",
        "unitario_infantil": "Unitario Infantil",
        "unitario_primaria": "Unitario Primaria",
        "unitario_mixto": "Unitario Mixto (Inf. y Prim.)"
    }
    
    base_name = nombres_map.get(nuevo_curso, "Grupo Personalizado")
    nombre_final = f"{base_name} {nueva_linea}".strip()

    conn = get_db()
    cur = conn.cursor()
    
    # Verify the group belongs to the current user's profesor record
    cur.execute("SELECT p.id FROM profesores p WHERE p.usuario_id = ?", (session.get("user_id"),))
    prof = cur.fetchone()
    if not prof:
        return jsonify({"ok": False, "error": "Profesor no encontrado"}), 404
        
    cur.execute("SELECT id FROM grupos WHERE id = ? AND profesor_id = ?", (grupo_id, prof["id"]))
    if not cur.fetchone():
        return jsonify({"ok": False, "error": "Grupo no encontrado o no autorizado"}), 404
    
    # Recalcular etapa_id y tipo_evaluacion
    etapa_id_map = {
        "infantil_3": 1, "infantil_4": 1, "infantil_5": 1, "unitario_infantil": 1,
        "primaria_1": 2, "primaria_2": 2, "primaria_3": 2, "primaria_4": 2,
        "primaria_5": 2, "primaria_6": 2, "unitario_primaria": 2, "unitario_mixto": 2,
    }
    cur.execute("SELECT id, nombre FROM etapas")
    etapas_db = {r["nombre"].lower(): r["id"] for r in cur.fetchall()}
    
    etapa_id_num = etapa_id_map.get(nuevo_curso, 2)
    if etapa_id_num == 1:
        etapa_id_real = etapas_db.get("infantil", 1)
        tipo_eval = "infantil"
    else:
        etapa_id_real = etapas_db.get("primaria", 2)
        tipo_eval = "primaria"

        
    try:
        cur.execute("""
            UPDATE grupos 
            SET nombre = ?, curso = ?, etapa_id = ?, tipo_evaluacion = ?, equipo_docente = ? 
            WHERE id = ?
        """, (nombre_final, nuevo_curso, etapa_id_real, tipo_eval, eq_doc, grupo_id))
        conn.commit()
        return jsonify({"ok": True, "nombre": nombre_final})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@main_bp.route("/api/grupos/<int:grupo_id>", methods=["DELETE"])
def delete_grupo(grupo_id):
    if not session.get('logged_in'):
        return jsonify({"ok": False, "error": "No autorizado"}), 401
        
    conn = get_db()
    cur = conn.cursor()
    
    # Verify the group belongs to the current user's profesor record
    cur.execute("SELECT p.id FROM profesores p WHERE p.usuario_id = ?", (session.get("user_id"),))
    prof = cur.fetchone()
    if not prof:
        return jsonify({"ok": False, "error": "Profesor no encontrado"}), 404
        
    cur.execute("SELECT id FROM grupos WHERE id = ? AND profesor_id = ?", (grupo_id, prof["id"]))
    if not cur.fetchone():
        return jsonify({"ok": False, "error": "Grupo no encontrado o no autorizado"}), 404
        
    # Check if there are active students in this group
    cur.execute("SELECT COUNT(*) FROM alumnos WHERE grupo_id = ? AND deleted_at IS NULL", (grupo_id,))
    alumnos_count = cur.fetchone()[0]
    
    if alumnos_count > 0:
        return jsonify({"ok": False, "error": f"No se puede eliminar porque hay {alumnos_count} alumno(s) activo(s) en este grupo. Transfiérelos o elimínalos primero."}), 400
        
    try:
        cur.execute("BEGIN")
        # Hard delete any remaining soft-deleted students to prevent orphans
        cur.execute("DELETE FROM alumnos WHERE grupo_id = ?", (grupo_id,))
        cur.execute("DELETE FROM grupos WHERE id = ?", (grupo_id,))
        
        # If the deleted group was the active one, clear it
        if session.get('active_group_id') == str(grupo_id) or session.get('active_group_id') == grupo_id:
            session.pop('active_group_id', None)
            
        conn.commit()
        security_logger.info(f"User '{session.get('username')}' deleted group ID {grupo_id}. IP: {request.remote_addr}")
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@main_bp.route("/api/grupo_activo", methods=["GET", "POST"])
def manage_grupo_activo():
    if not session.get('logged_in'):
        return jsonify({"ok": False, "error": "No autorizado"}), 401
        
    if request.method == "POST":
        data = request.json
        grupo_id = data.get("grupo_id")
        
        if grupo_id:
            session['active_group_id'] = grupo_id
        else:
            session.pop('active_group_id', None)
            
        security_logger.info(f"User '{session.get('username')}' changed active group to {grupo_id or 'None (All)'}. IP: {request.remote_addr}")
        return jsonify({"ok": True, "active_group_id": grupo_id})
    else:
        # GET
        active_id = session.get('active_group_id')
        if active_id:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT nombre, curso, etapa_id FROM grupos WHERE id = ?", (active_id,))
            g = cur.fetchone()
            if g:
                return jsonify({"id": active_id, "nombre": g["nombre"], "curso": g["curso"], "etapa_id": g["etapa_id"]})

        return jsonify({"id": None, "nombre": "Seleccionar Grupo", "curso": "", "etapa_id": None})

@main_bp.route("/logout")
def do_logout():
    session.clear()
    return redirect(url_for('main.login_page'))

@main_bp.route("/api/perfil/seguridad", methods=["GET"])
def get_seguridad():
    if not session.get('logged_in'):
        return jsonify({"ok": False, "error": "No autorizado"}), 401
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT pregunta_seguridad FROM usuarios WHERE id = ?", (session.get("user_id"),))
    usr = cur.fetchone()
    if not usr:
        return jsonify({"ok": False, "error": "Usuario no encontrado"}), 404
        
    return jsonify({"ok": True, "pregunta_seguridad": usr["pregunta_seguridad"]})

@main_bp.route("/api/perfil/seguridad", methods=["POST"])
def update_seguridad():
    if not session.get('logged_in'):
        return jsonify({"ok": False, "error": "No autorizado"}), 401
        
    data = request.json
    pwd = data.get("password", "").strip()
    pregunta = data.get("pregunta", "").strip()
    respuesta = data.get("respuesta", "").strip()
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        from werkzeug.security import generate_password_hash
        
        updates = []
        params = []
        
        if pwd:
            updates.append("password_hash = ?")
            params.append(generate_password_hash(pwd))
            
        if pregunta:
            updates.append("pregunta_seguridad = ?")
            params.append(pregunta)
            
        if respuesta:
            updates.append("respuesta_seguridad_hash = ?")
            params.append(generate_password_hash(respuesta))
            
        if not updates:
            return jsonify({"ok": True, "message": "No hay cambios"})
            
        params.append(session.get("user_id"))
        
        query = f"UPDATE usuarios SET {', '.join(updates)} WHERE id = ?"
        cur.execute(query, tuple(params))
        conn.commit()
        
        security_logger.info(f"User '{session.get('username')}' updated their security settings. IP: {request.remote_addr}")
        return jsonify({"ok": True})
        
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@main_bp.route("/api/recover_password", methods=["GET"])
def get_recovery_question():
    username = request.args.get("username", "").strip()
    if not username:
        return jsonify({"ok": False, "error": "Falta el usuario"}), 400
        
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT pregunta_seguridad FROM usuarios WHERE username = ?", (username,))
    usr = cur.fetchone()
    
    if not usr:
        # Prevent username enumeration theoretically, but here it's fine to tell them it's wrong
        return jsonify({"ok": False, "error": "Usuario no encontrado"}), 404
        
    if not usr["pregunta_seguridad"]:
        return jsonify({"ok": False, "error": "Este usuario no tiene configurada una pregunta de seguridad. Contacta con el administrador."}), 400
        
    return jsonify({"ok": True, "pregunta": usr["pregunta_seguridad"]})

@main_bp.route("/api/recover_password", methods=["POST"])
def do_recover_password():
    data = request.json
    username = data.get("username", "").strip()
    respuesta = data.get("respuesta", "").strip()
    new_password = data.get("new_password", "").strip()
    
    if not username or not respuesta or not new_password:
        return jsonify({"ok": False, "error": "Faltan datos"}), 400
        
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, respuesta_seguridad_hash FROM usuarios WHERE username = ?", (username,))
    usr = cur.fetchone()
    
    if not usr or not usr["respuesta_seguridad_hash"]:
        security_logger.warning(f"Failed password recovery attempt for '{username}' (no user or no security question). IP: {request.remote_addr}")
        return jsonify({"ok": False, "error": "No se puede recuperar la contraseña para este usuario"}), 400
        
    from werkzeug.security import check_password_hash, generate_password_hash
    
    if not check_password_hash(usr["respuesta_seguridad_hash"], respuesta):
        security_logger.warning(f"Failed password recovery attempt for '{username}' (wrong answer). IP: {request.remote_addr}")
        return jsonify({"ok": False, "error": "La respuesta de seguridad es incorrecta"}), 400
        
    try:
        new_hash = generate_password_hash(new_password)
        cur.execute("UPDATE usuarios SET password_hash = ? WHERE id = ?", (new_hash, usr["id"]))
        conn.commit()
        security_logger.info(f"Password successfully recovered for '{username}'. IP: {request.remote_addr}")
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": "Error interno"}), 500

@main_bp.route("/api/emergency_reset", methods=["POST"])
def emergency_reset():
    # Only allow from localhost
    if request.remote_addr not in ["127.0.0.1", "::1"]:
        security_logger.warning(f"Unauthorized emergency reset attempt from {request.remote_addr}")
        return jsonify({"ok": False, "error": "No autorizado - Solo desde este equipo"}), 403
        
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Look for admins
        cur.execute("SELECT id, username FROM usuarios WHERE role = 'admin' OR username IN ('admin', 'daniel')")
        admins = cur.fetchall()
        
        if not admins:
            return jsonify({"ok": False, "error": "No hay administradores en el sistema"}), 400
            
        from werkzeug.security import generate_password_hash
        hashed = generate_password_hash("1234")
        
        for admin in admins:
            cur.execute("UPDATE usuarios SET password_hash = ? WHERE id = ?", (hashed, admin["id"]))
            
        conn.commit()
        security_logger.warning(f"EMERGENCY RESET TRIGGERED from {request.remote_addr}")
        
        return jsonify({"ok": True, "mensaje": "Contraseñas reseteadas a '1234'. Podrás entrar ahora mismo."})
    except Exception as e:
        security_logger.error(f"Error during emergency reset: {e}")
        return jsonify({"ok": False, "error": "Error interno del servidor"}), 500
@main_bp.route("/api/check_updates", methods=["GET"])
def check_updates():
    """Comprueba si hay actualizaciones disponibles en el repositorio remoto."""
    import subprocess
    try:
        # Hash local actual
        local = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        # Rama actual
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        # Hash remoto (sin hacer fetch, solo consulta)
        remote = subprocess.run(
            ["git", "ls-remote", "origin", branch.stdout.strip()],
            capture_output=True, text=True, timeout=8,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

        local_hash = local.stdout.strip()
        remote_line = remote.stdout.strip()
        remote_hash = remote_line.split()[0] if remote_line else None

        if not local_hash or not remote_hash:
            return jsonify({"ok": True, "updates_available": False, "reason": "no_info"})

        updates_available = local_hash != remote_hash
        return jsonify({
            "ok": True,
            "updates_available": updates_available,
            "local_hash": local_hash[:7],
            "remote_hash": remote_hash[:7],
            "branch": branch.stdout.strip()
        })
    except FileNotFoundError:
        # git no está instalado / no accesible
        return jsonify({"ok": True, "updates_available": False, "reason": "git_not_found"})
    except Exception as e:
        return jsonify({"ok": True, "updates_available": False, "reason": str(e)})

@main_bp.route("/api/exit", methods=["POST"])

def exit_app():
    """Cierra el proceso del servidor (útil para modo escritorio)."""
    # Solo permitir desde localhost para seguridad
    if request.remote_addr not in ["127.0.0.1", "::1"]:
        return jsonify({"ok": False, "error": "No autorizado"}), 403
        
    security_logger.warning("Solicitud de cierre de aplicación recibida.")
    
    def shutdown():
        import time
        import os
        import signal
        time.sleep(1)  # Dar tiempo a que la respuesta llegue al cliente
        os.kill(os.getpid(), signal.SIGINT)
        
    import threading
    threading.Thread(target=shutdown).start()
    
    return jsonify({"ok": True, "message": "Cerrando aplicación..."})
