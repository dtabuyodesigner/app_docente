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
        return jsonify({"ok": True})
        
    return jsonify({"ok": False, "error": "Credenciales incorrectas"}), 401

@main_bp.route("/logout")
def do_logout():
    session.clear()
    return redirect(url_for('main.login_page'))
