from flask import Blueprint, jsonify, request, redirect, url_for, session
# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import Flow
# from googleapiclient.discovery import build
import os
import json
from datetime import datetime, timedelta
from utils.db import get_db

# Helper for lazy imports to prevent crashes if libraries are missing
def get_google_libs():
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import Flow
        from googleapiclient.discovery import build
        Credentials, Flow, build, Request = get_google_libs()
        if not Credentials:
            return jsonify({"ok": False, "error": "Librerías de Google no instaladas"}), 500
        return Credentials, Flow, build, Request
    except ImportError:
        return None, None, None, None

google_cal_bp = Blueprint('google_cal', __name__)

# Config
SCOPES = ['https://www.googleapis.com/auth/calendar']
# Rutas absolutas para evitar problemas con el directorio de trabajo
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Priorizar credenciales en la carpeta de usuario
USER_DATA_DIR = os.path.expanduser("~/.cuadernodeltutor")
if not os.path.exists(USER_DATA_DIR):
    os.makedirs(USER_DATA_DIR, exist_ok=True)

USER_CREDENTIALS = os.path.join(USER_DATA_DIR, 'credentials.json')
CREDENTIALS_FILE = USER_CREDENTIALS if os.path.exists(USER_CREDENTIALS) else os.path.join(BASE_DIR, 'credentials.json')
TOKEN_FILE = os.path.join(USER_DATA_DIR, 'token.json')

# Allow insecure transport for local development (OAuth2 requires HTTPS otherwise)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

@google_cal_bp.route("/google/authorize")
def google_authorize():
    try:
        Credentials, Flow, build, Request = get_google_libs()
        if not Credentials:
            return jsonify({"ok": False, "error": "Librerías de Google no instaladas"}), 500
        if not Flow:
            return redirect(url_for('programacion') + "?error=missing_libraries")

        if not os.path.exists(CREDENTIALS_FILE):
            return redirect(url_for('programacion') + "?error=missing_credentials")

        flow = Flow.from_client_secrets_file(
            CREDENTIALS_FILE, scopes=SCOPES)
        # Forzar la URL de redirección basada en la petición actual para evitar discrepancias
        parts = request.url_root.rstrip('/')
        flow.redirect_uri = f"{parts}/oauth2callback"
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            prompt='consent',
            include_granted_scopes='true')
        
        session['state'] = state
        return redirect(authorization_url)
    except Exception as e:
        print(f"Error in google_authorize: {e}")
        return redirect(url_for('programacion') + f"?error=auth_failed&msg={str(e)}")

@google_cal_bp.route("/oauth2callback")
def oauth2callback():
    try:
        Credentials, Flow, build, Request = get_google_libs()
        if not Credentials:
            return jsonify({"ok": False, "error": "Librerías de Google no instaladas"}), 500
        if not Flow:
            return redirect(url_for('programacion') + "?error=missing_libraries")

        state = session.get('state')
        if not state:
            return redirect(url_for('programacion') + "?error=missing_state")
            
        flow = Flow.from_client_secrets_file(
            CREDENTIALS_FILE, scopes=SCOPES, state=state)
        parts = request.url_root.rstrip('/')
        flow.redirect_uri = f"{parts}/oauth2callback"
        
        authorization_response = request.url
        flow.fetch_token(authorization_response=authorization_response)

        creds = flow.credentials
        
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

        return redirect("/programacion")
    except Exception as e:
        print(f"Error in oauth2callback: {e}")
        return redirect(url_for('programacion') + f"?error=callback_failed&msg={str(e)}")

@google_cal_bp.route("/api/calendar/status")
def calendar_status():
    authorized = os.path.exists(TOKEN_FILE)
    return jsonify({"connected": authorized, "authorized": authorized})

@google_cal_bp.route("/api/calendar/import", methods=['POST'])
def import_calendar():
    try:
        if not os.path.exists(TOKEN_FILE):
            return jsonify({"ok": False, "error": "No autorizado"}), 401
            
        Credentials, Flow, build, Request = get_google_libs()
        if not Credentials:
            return jsonify({"ok": False, "error": "Librerías de Google no instaladas"}), 500
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                print(f"Error refreshing token: {e}")
                if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE)
                return jsonify({"ok": False, "error": "La sesión de Google ha expirado de forma permanente. Por favor, vuelve a Conectar con Google Calendar."}), 401

        if not creds or not creds.valid:
            if os.path.exists(TOKEN_FILE):
                os.remove(TOKEN_FILE)
            return jsonify({"ok": False, "error": "Credenciales inválidas, vuelve a conectar Google Calendar"}), 401

        service = build('calendar', 'v3', credentials=creds)
        
        now = datetime.utcnow()
        time_min = (now - timedelta(days=30)).isoformat() + 'Z'
        time_max = (now + timedelta(days=90)).isoformat() + 'Z'
        
        events_result = service.events().list(calendarId='primary', timeMin=time_min,
                                            timeMax=time_max, singleEvents=True,
                                            orderBy='startTime').execute()
        events = events_result.get('items', [])
        
        conn = get_db()
        cur = conn.cursor()
        imported = 0
        
        for event in events:
            start_obj = event.get('start', {})
            start = start_obj.get('dateTime', start_obj.get('date'))
            if not start:
                continue
                
            # Date is YYYY-MM-DD
            fecha = start[:10]
            titulo = event.get('summary', '(Sin título)')
            descripcion = event.get('description', '')
            
            try:
                # Check if exists (Using descripcion as title)
                cur.execute("SELECT id FROM programacion_diaria WHERE fecha = ? AND descripcion = ?", (fecha, titulo))
                if not cur.fetchone():
                    cur.execute("""
                        INSERT INTO programacion_diaria (fecha, descripcion, tipo, color)
                        VALUES (?, ?, ?, ?)
                    """, (fecha, titulo, 'general', '#3788d8'))
                    imported += 1
            except Exception as e:
                print(f"Error importing event {titulo}: {e}")
                continue
                
        conn.commit()
        
        return jsonify({"ok": True, "imported": imported, "count": imported})
    except Exception as e:
        print(f"Global error in import_calendar: {e}")
        error_msg = str(e)
        if "invalid_grant" in error_msg:
            return jsonify({"ok": False, "error": "La sesión de Google ha expirado. Por favor, vuelve a Conectar con Google Calendar."}), 401
        return jsonify({"ok": False, "error": f"Error al importar calendario: {error_msg}"}), 500

@google_cal_bp.route("/api/calendar/sync", methods=['POST'])
def sync_calendar():
    try:
        if not os.path.exists(TOKEN_FILE):
            return jsonify({"ok": False, "error": "No autorizado"}), 401
            
        Credentials, Flow, build, Request = get_google_libs()
        if not Credentials:
            return jsonify({"ok": False, "error": "Librerías de Google no instaladas"}), 500
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                print(f"Error refreshing token in sync: {e}")
                if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE)
                return jsonify({"ok": False, "error": "La sesión de Google ha expirado de forma permanente. Por favor, vuelve a Conectar con Google Calendar."}), 401

        if not creds or not creds.valid:
            if os.path.exists(TOKEN_FILE):
                os.remove(TOKEN_FILE)
            return jsonify({"ok": False, "error": "Credenciales inválidas, vuelve a conectar Google Calendar"}), 401
            
        service = build('calendar', 'v3', credentials=creds)
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT fecha, descripcion FROM programacion_diaria")
        local_events = cur.fetchall()
        
        pushed = 0
        for le in local_events:
            if not le['fecha'] or not le['descripcion']:
                continue
                
            # Check if already in GC (basic title check to avoid duplicates)
            time_min = le['fecha'] + "T00:00:00Z"
            time_max = le['fecha'] + "T23:59:59Z"
            
            try:
                existing = service.events().list(calendarId='primary', timeMin=time_min, timeMax=time_max, q=le['descripcion']).execute()
                if not existing.get('items'):
                    event_body = {
                        'summary': le['descripcion'],
                        'description': "",
                        'start': {'date': le['fecha']},
                        'end': {'date': le['fecha']}
                    }
                    service.events().insert(calendarId='primary', body=event_body).execute()
                    pushed += 1
            except Exception as e:
                print(f"Error syncing event {le['descripcion']}: {e}")
                continue
                
        return jsonify({"ok": True, "synced": pushed, "pushed": pushed})
    except Exception as e:
        print(f"Global error in sync_calendar: {e}")
        error_msg = str(e)
        if "invalid_grant" in error_msg:
             return jsonify({"ok": False, "error": "La sesión de Google ha expirado. Por favor, vuelve a Conectar con Google Calendar."}), 401
        return jsonify({"ok": False, "error": f"Error al sincronizar con Google Calendar: {error_msg}"}), 500
