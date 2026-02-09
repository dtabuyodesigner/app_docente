from flask import Blueprint, jsonify, request, redirect, url_for, session
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os
import json
from datetime import datetime, timedelta
from utils.db import get_db

google_cal_bp = Blueprint('google_cal', __name__)

# Config (Should ideally come from .env or app config)
SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

# Allow insecure transport for local development (OAuth2 requires HTTPS otherwise)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

@google_cal_bp.route("/google/authorize")
def google_authorize():
    if not os.path.exists(CREDENTIALS_FILE):
        return "Falta credentials.json", 500

    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE, scopes=SCOPES)
    flow.redirect_uri = url_for('google_cal.oauth2callback', _external=True)
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent',
        include_granted_scopes='true')
    
    session['state'] = state
    return redirect(authorization_url)

@google_cal_bp.route("/oauth2callback")
def oauth2callback():
    state = session['state']
    
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = url_for('google_cal.oauth2callback', _external=True)
    
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    creds = flow.credentials
    
    with open(TOKEN_FILE, 'w') as token:
        token.write(creds.to_json())

    return redirect("/programacion")

@google_cal_bp.route("/api/calendar/status")
def calendar_status():
    authorized = os.path.exists(TOKEN_FILE)
    return jsonify({"connected": authorized, "authorized": authorized})

@google_cal_bp.route("/api/calendar/import", methods=['POST'])
def import_calendar():
    try:
        if not os.path.exists(TOKEN_FILE):
            return jsonify({"ok": False, "error": "No autorizado"}), 401
            
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
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
                # Check if exists
                cur.execute("SELECT id FROM programacion_diaria WHERE fecha = ? AND actividad = ?", (fecha, titulo))
                if not cur.fetchone():
                    cur.execute("""
                        INSERT INTO programacion_diaria (fecha, actividad, observaciones, tipo, color)
                        VALUES (?, ?, ?, ?, ?)
                    """, (fecha, titulo, descripcion, 'general', '#3788d8'))
                    imported += 1
            except Exception as e:
                print(f"Error importing event {titulo}: {e}")
                continue
                
        conn.commit()
        conn.close()
        
        return jsonify({"ok": True, "imported": imported, "count": imported})
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        print(f"Global error in import_calendar: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@google_cal_bp.route("/api/calendar/sync", methods=['POST'])
def sync_calendar():
    if not os.path.exists(TOKEN_FILE):
        return jsonify({"ok": False, "error": "No autorizado"}), 401
        
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    service = build('calendar', 'v3', credentials=creds)
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT fecha, actividad, observaciones FROM programacion_diaria")
    local_events = cur.fetchall()
    conn.close()
    
    pushed = 0
    try:
        for le in local_events:
            if not le['fecha'] or not le['actividad']:
                continue
                
            # Check if already in GC (basic title check to avoid duplicates)
            time_min = le['fecha'] + "T00:00:00Z"
            time_max = le['fecha'] + "T23:59:59Z"
            
            try:
                existing = service.events().list(calendarId='primary', timeMin=time_min, timeMax=time_max, q=le['actividad']).execute()
                if not existing.get('items'):
                    event_body = {
                        'summary': le['actividad'],
                        'description': le['observaciones'] or "",
                        'start': {'date': le['fecha']},
                        'end': {'date': le['fecha']}
                    }
                    service.events().insert(calendarId='primary', body=event_body).execute()
                    pushed += 1
            except Exception as e:
                print(f"Error syncing event {le['actividad']}: {e}")
                continue
                
        return jsonify({"ok": True, "synced": pushed, "pushed": pushed})
    except Exception as e:
        print(f"Global error in sync_calendar: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
