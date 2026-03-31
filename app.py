# ==============================================================================
# IMPORTACIONES
# ==============================================================================
# Cuaderno del Tutor - Versión Final Sincronizada
from flask import Flask, request, redirect, url_for, session, send_file, send_from_directory, jsonify
try:
    from flasgger import Swagger
    HAS_SWAGGER = True
except ImportError:
    HAS_SWAGGER = False

import os
import shutil
from datetime import datetime
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect, generate_csrf
import click

# ==============================================================================
# CONFIGURACIÓN INICIAL
# ==============================================================================

# Load environment variables
load_dotenv()

# Sentry — monitorización de errores en producción
try:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        integrations=[FlaskIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=True,
    )
except ImportError:
    pass

# Build app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-key-change-in-prod")

# Initialize Swagger if available
swagger = None
if HAS_SWAGGER:
    swagger = Swagger(app, template={
        "info": {
            "title": "APP_EVALUAR API",
            "description": "API Backend para la plataforma APP_EVALUAR",
            "version": "1.0.0"
        }
    })

# ==============================================================================
# INICIALIZACIÓN DE BASE DE DATOS Y TAREAS DE STARTUP
# ==============================================================================
from utils.db import init_db_if_not_exists, get_db_path
init_db_if_not_exists()

from utils.db import run_migrations
run_migrations()

# Tareas de blindaje técnico (Integridad y Backup)
from utils.backup import run_startup_tasks
run_startup_tasks()

# ==============================================================================
# REGISTRO DE BLUEPRINTS (CORREGIDO: SIN DUPLICADOS)
# ==============================================================================
from routes.main import main_bp
from routes.alumnos import alumnos_bp
from routes.asistencia import asistencia_bp
from routes.evaluacion import evaluacion_bp
from routes.dashboard import dashboard_bp
from routes.horario import horario_bp
from routes.comedor import comedor_bp
from routes.reuniones import reuniones_bp
from routes.informes import informes_bp
from routes.google_cal import google_cal_bp
from routes.tareas import tareas_bp
from routes.usuarios import usuarios_bp
from routes.programacion_docs import programacion_docs_bp
from routes.lectura import lectura_bp
from routes.admin import admin_bp
from routes.material import material_bp
from routes.configuracion import configuracion_bp
from routes.criterios_api import criterios_bp
from routes.ayuda import ayuda_bp
from routes.curricular import curricular_bp
from routes.evaluacion_sda import evaluacion_sda_bp
from routes.evaluacion_directa import evaluacion_directa_bp
from routes.evaluacion_actividades import evaluacion_actividades_bp
from routes.evaluacion_cuaderno import evaluacion_cuaderno_bp
from routes.eventos import eventos_bp
from routes.observaciones import observaciones_bp
from routes.rubricas import rubricas_bp

app.register_blueprint(main_bp)
app.register_blueprint(alumnos_bp)
app.register_blueprint(asistencia_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(horario_bp)
app.register_blueprint(comedor_bp)
app.register_blueprint(reuniones_bp)
app.register_blueprint(informes_bp)
app.register_blueprint(google_cal_bp)
app.register_blueprint(tareas_bp)
app.register_blueprint(usuarios_bp)
app.register_blueprint(programacion_docs_bp)
app.register_blueprint(lectura_bp, url_prefix='/api')
app.register_blueprint(admin_bp)
app.register_blueprint(material_bp)
app.register_blueprint(configuracion_bp)
app.register_blueprint(ayuda_bp)
app.register_blueprint(criterios_bp)
app.register_blueprint(curricular_bp, url_prefix='/api/curricular')
app.register_blueprint(evaluacion_sda_bp, url_prefix='/api/evaluacion/sda')
app.register_blueprint(evaluacion_directa_bp, url_prefix='/api/evaluacion/directa')
app.register_blueprint(evaluacion_actividades_bp, url_prefix='/api/evaluacion/actividades')
app.register_blueprint(evaluacion_cuaderno_bp, url_prefix='/api/evaluacion')
app.register_blueprint(evaluacion_bp, url_prefix='/api/evaluacion', name='evaluacion_curricular_final')
app.register_blueprint(eventos_bp)
app.register_blueprint(observaciones_bp)
app.register_blueprint(rubricas_bp)

# ==============================================================================
# CONFIGURACIÓN DE SEGURIDAD Y CONTEXTO
# ==============================================================================
from utils.db import close_db, get_db

app.teardown_appcontext(close_db)

csrf = CSRFProtect()
csrf.init_app(app)
csrf.exempt(curricular_bp)
csrf.exempt(alumnos_bp)
csrf.exempt(evaluacion_actividades_bp)
csrf.exempt(evaluacion_cuaderno_bp)
csrf.exempt("routes.main.exit_app")

# ==============================================================================
# RUTAS Y ENDPOINTS
# ==============================================================================

@app.route('/api/csrf-token', methods=['GET'])
def get_csrf_token():
    return {"ok": True, "csrf_token": generate_csrf()}

@app.route('/service-worker.js')
def serve_sw():
    """Sirve el Service Worker desde la raíz para que su scope sea '/'."""
    response = send_file(
        os.path.join(app.root_path, 'static', 'service-worker.js'),
        mimetype='application/javascript'
    )
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Cache-Control'] = 'no-cache'
    return response

@app.route('/manifest.json')
def serve_manifest():
    """Sirve el manifest PWA desde la raíz."""
    return send_file(
        os.path.join(app.root_path, 'static', 'manifest.json'),
        mimetype='application/manifest+json'
    )

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'icon-192.png',
        mimetype='image/vnd.microsoft.icon'
    )

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    from utils.db import get_app_data_dir
    # 1. Try persistent AppData uploads folder first
    app_data_uploads = os.path.join(get_app_data_dir(), 'uploads')
    if os.path.exists(os.path.join(app_data_uploads, filename)):
        return send_from_directory(app_data_uploads, filename)
    # 2. Fallback to legacy static uploads folder
    static_uploads = os.path.join(app.root_path, 'static', 'uploads')
    return send_from_directory(static_uploads, filename)

@app.before_request
def require_auth():
    # Allow static files and certain routes without authentication
    if (request.path.startswith('/static/') or
        request.path.startswith('/uploads/') or
        request.path == '/favicon.ico' or
        (HAS_SWAGGER and (
            request.path.startswith('/apidocs/') or
            request.path.startswith('/flasgger_static/') or
            request.path == '/apispec_1.json'
        )) or
        request.path in ['/login', '/logout', '/api/csrf-token', '/api/recover_password', '/api/setup', '/service-worker.js', '/manifest.json', '/static/plantilla_sda.csv'] or
        request.path.endswith('.js') or
        request.path.endswith('.css') or
        request.path.endswith('.csv') or
        request.endpoint == 'static'):
        return
    
    if not session.get('logged_in') or 'username' not in session:
        if request.path.startswith('/api/'):
            return jsonify({"ok": False, "error": "No autorizado"}), 401
        return redirect(url_for('main.login_page'))

@app.errorhandler(404)
def page_not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({"ok": False, "error": "Endpoint no encontrado"}), 404
    return redirect(url_for('main.login_page'))

@app.errorhandler(500)
def server_error(e):
    return jsonify({"ok": False, "error": "Error interno del servidor"}), 500

# ==============================================================================
# COMANDOS CLI
# ==============================================================================

@app.cli.command('init-db')
def init_db_command():
    path = get_db_path()
    if not os.path.exists(path):
        print("Initializing database...")
        conn = get_db()
        # Corrección crítica para Windows: especificar encoding utf-8
        with open("schema.sql", "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        print("Database initialized.")
    else:
        print("Database already exists. Run migrations manually if schema changed.")

@app.cli.command('create-user')
@click.argument('username')
@click.argument('password')
@click.option('--role', default='profesor', help='Role del usuario (admin, profesor, etc)')
def create_user_command(username, password, role):
    from werkzeug.security import generate_password_hash
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
    if cur.fetchone():
        print(f"Error: El usuario '{username}' ya existe.")
        return
    
    pwd_hash = generate_password_hash(password)
    cur.execute("INSERT INTO usuarios (username, password_hash, role) VALUES (?, ?, ?)", (username, pwd_hash, role))
    conn.commit()
    print(f"Usuario '{username}' creado exitosamente con rol '{role}'.")

# ==============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# ==============================================================================

if __name__ == "__main__":
    app.run(debug=True, port=5000)