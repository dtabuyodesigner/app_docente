from flask import Blueprint, send_from_directory, request, jsonify, session, redirect, url_for
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
    pwd = os.getenv("APP_PASSWORD")
    data = request.get_json(silent=True) or {}
    
    if not pwd:
        session['logged_in'] = True
        return jsonify({"ok": True})
        
    if data.get("password") == pwd:
        session['logged_in'] = True
        return jsonify({"ok": True})
        
    return jsonify({"ok": False, "error": "Contraseña incorrecta"}), 401

@main_bp.route("/logout")
def do_logout():
    session.pop('logged_in', None)
    return redirect(url_for('main.login_page'))
