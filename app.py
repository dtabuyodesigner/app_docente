from flask import Flask
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

# Database Initialization (Optional: keep if needed for first run)
from utils.db import get_db

def init_db():
    if not os.path.exists("app_evaluar.db"):
        print("Initializing database...")
        conn = get_db()
        with open("schema.sql") as f:
            conn.executescript(f.read())
        conn.close()

if __name__ == "__main__":
    # init_db() # Uncomment to init db on start if needed
    app.run(debug=True, port=5000)
