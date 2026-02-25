from flask import Blueprint, send_from_directory, request, jsonify, session, redirect, url_for
from werkzeug.security import check_password_hash
from utils.db import get_db
import os

main_bp = Blueprint('main', __name__)

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

@main_bp.route("/tareas")
def tareas_page():
    return send_from_directory("static", "tareas.html")

@main_bp.route("/login", methods=["GET"])
def login_page():
    return send_from_directory("static", "login.html")

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
        
        # Load default active group
        cur.execute("SELECT id FROM profesores WHERE usuario_id = ?", (user["id"],))
        prof = cur.fetchone()
        if prof:
            cur.execute("SELECT id FROM grupos WHERE profesor_id = ? ORDER BY id LIMIT 1", (prof["id"],))
            grupo = cur.fetchone()
            if grupo:
                session['active_group_id'] = grupo["id"]

        return jsonify({"ok": True})
        
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
        SELECT g.id, g.nombre, g.curso, COUNT(a.id) as num_alumnos
        FROM grupos g
        LEFT JOIN alumnos a ON g.id = a.grupo_id AND a.deleted_at IS NULL
        WHERE g.profesor_id = ?
        GROUP BY g.id, g.nombre, g.curso
        ORDER BY g.curso ASC, g.nombre ASC
    """, (prof["id"],))
    grupos = [dict(g) for g in cur.fetchall()]
    return jsonify(grupos)

@main_bp.route("/api/grupos", methods=["POST"])
def new_grupo():
    if not session.get('logged_in'):
        return jsonify({"ok": False, "error": "No autorizado"}), 401
        
    data = request.json
    etapa_curso = data.get("etapa_curso", "")
    linea = data.get("linea", "")
    
    if not etapa_curso:
        return jsonify({"ok": False, "error": "Faltan datos de etapa/curso"}), 400
        
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
        
    try:
        cur.execute("INSERT INTO grupos (nombre, curso, profesor_id) VALUES (?, ?, ?)", (nombre_final, etapa_curso, prof_id))
        new_group_id = cur.lastrowid
        
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
    nuevo_nombre = data.get("nombre", "").strip()
    nuevo_curso = data.get("curso", "").strip()
    if not nuevo_nombre:
        return jsonify({"ok": False, "error": "Faltan datos requeridos (nombre)"}), 400

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
        
    try:
        cur.execute("UPDATE grupos SET nombre = ?, curso = ? WHERE id = ?", (nuevo_nombre, nuevo_curso, grupo_id))
        conn.commit()
        return jsonify({"ok": True})
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
        if not grupo_id:
            return jsonify({"ok": False, "error": "Falta grupo_id"}), 400
            
        session['active_group_id'] = grupo_id
        return jsonify({"ok": True, "active_group_id": grupo_id})
    else:
        # GET
        active_id = session.get('active_group_id')
        if active_id:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT nombre, curso FROM grupos WHERE id = ?", (active_id,))
            g = cur.fetchone()
            if g:
                return jsonify({"id": active_id, "nombre": g["nombre"], "curso": g["curso"]})
                
        return jsonify({"id": None, "nombre": "Seleccionar Grupo", "curso": ""})

@main_bp.route("/logout")
def do_logout():
    session.clear()
    return redirect(url_for('main.login_page'))
