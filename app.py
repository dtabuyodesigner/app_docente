from flask import Flask, request, redirect, url_for, session
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Build app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-key-change-in-prod")

# Register Blueprints
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

app.register_blueprint(main_bp)
app.register_blueprint(alumnos_bp)
app.register_blueprint(asistencia_bp)
app.register_blueprint(evaluacion_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(horario_bp)
app.register_blueprint(comedor_bp)
app.register_blueprint(reuniones_bp)
app.register_blueprint(informes_bp)
app.register_blueprint(google_cal_bp)
app.register_blueprint(tareas_bp)
app.register_blueprint(usuarios_bp)

# Database Initialization and CLI commands
from utils.db import close_db, get_db
import click

app.teardown_appcontext(close_db)

@app.before_request
def require_auth():
    # Allow static files and the login/logout routes
    if request.path.startswith('/static/') or request.path in ['/login', '/logout'] or request.path.endswith('.js') or request.path.endswith('.css') or request.endpoint == 'static':
        return
        
    if not session.get('logged_in') or 'username' not in session:
        if request.path.startswith('/api/'):
            return {"ok": False, "error": "No autorizado"}, 401
        return redirect(url_for('main.login_page'))

@app.cli.command('init-db')
def init_db_command():
    if not os.path.exists("app_evaluar.db"):
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
