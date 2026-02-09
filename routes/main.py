from flask import Blueprint, send_from_directory

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
