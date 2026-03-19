from flask import Flask, request, redirect, url_for, session, send_file
try:
    from flasgger import Swagger
    HAS_SWAGGER = True
except ImportError:
    HAS_SWAGGER = False

import os
import shutil
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

from utils.db import init_db_if_not_exists, get_db_path
init_db_if_not_exists()

from utils.db import run_migrations
run_migrations()

# Tareas de blindaje técnico (Integridad y Backup)
from utils.backup import run_startup_tasks
run_startup_tasks()

# Register Blueprints
from routes.main import main_bp
from routes.alumnos import alumnos_bp
from routes.asistencia import asistencia_bp
# from routes.evaluacion import evaluacion_bp (Moved to sda/directa)
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
from routes.eventos import eventos_bp
from routes.observaciones import observaciones_bp
from routes.evaluacion import evaluacion_bp
from routes.rubricas import rubricas_bp
from flask_wtf.csrf import CSRFProtect, generate_csrf

app.register_blueprint(main_bp)
app.register_blueprint(alumnos_bp)
app.register_blueprint(asistencia_bp)
# app.register_blueprint(evaluacion_bp)
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
app.register_blueprint(evaluacion_bp, url_prefix='/api/evaluacion')
app.register_blueprint(eventos_bp)
app.register_blueprint(observaciones_bp)
app.register_blueprint(rubricas_bp)

# Database Initialization and CLI commands
from utils.db import close_db, get_db
import click

app.teardown_appcontext(close_db)

csrf = CSRFProtect()
csrf.init_app(app)
csrf.exempt(curricular_bp)
csrf.exempt(alumnos_bp)

@app.route('/api/csrf-token', methods=['GET'])
def get_csrf_token():
    return {"ok": True, "csrf_token": generate_csrf()}

# Nota: El endpoint /api/admin/backup se ha movido a routes/admin.py

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


@app.before_request
def require_auth():
    # Allow static files and the login/logout routes
    if (request.path.startswith('/static/') or 
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
            return {"ok": False, "error": "No autorizado"}, 401
        return redirect(url_for('main.login_page'))

@app.cli.command('init-db')
def init_db_command():
    path = get_db_path()
    if not os.path.exists(path):
        print("Initializing database...")
        conn = get_db()
        with open("schema.sql") as f:
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

if __name__ == "__main__":
    app.run(debug=True, port=5000)
