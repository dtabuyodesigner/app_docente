from flask import Blueprint, request, jsonify, session, send_from_directory
from utils.db import get_db
from werkzeug.security import generate_password_hash

usuarios_bp = Blueprint('usuarios', __name__)

@usuarios_bp.route("/usuarios")
def view_usuarios():
    # Solo permite a admin entrar a este panel HTML
    if session.get('role') != 'admin':
        return "Acceso denegado. Se requiere rol de Administrador.", 403
    return send_from_directory("static", "usuarios.html")

@usuarios_bp.route("/api/usuarios", methods=["GET"])
def get_usuarios():
    if session.get('role') != 'admin':
        return jsonify({"ok": False, "error": "No autorizado"}), 403
        
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, username, role, fecha_creacion FROM usuarios ORDER BY id ASC")
    users = [dict(r) for r in cur.fetchall()]
    return jsonify(users)

@usuarios_bp.route("/api/usuarios", methods=["POST"])
def post_usuario():
    if session.get('role') != 'admin':
        return jsonify({"ok": False, "error": "No autorizado"}), 403
        
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    role = data.get("role", "profesor")
    
    if not username or not password:
        return jsonify({"ok": False, "error": "Faltan datos requeridos"}), 400
        
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
    if cur.fetchone():
        return jsonify({"ok": False, "error": "El usuario ya existe."}), 400
        
    try:
        pwd_hash = generate_password_hash(password)
        cur.execute("INSERT INTO usuarios (username, password_hash, role) VALUES (?, ?, ?)", (username, pwd_hash, role))
        conn.commit()
        return jsonify({"ok": True, "id": cur.lastrowid})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": "Error interno"}), 500

@usuarios_bp.route("/api/usuarios/<int:id>", methods=["DELETE"])
def delete_usuario(id):
    if session.get('role') != 'admin':
        return jsonify({"ok": False, "error": "No autorizado"}), 403
        
    if str(id) == str(session.get('user_id')):
         return jsonify({"ok": False, "error": "No puedes eliminar tu propia cuenta"}), 400
         
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM usuarios WHERE id = ?", (id,))
    conn.commit()
    return jsonify({"ok": True})
