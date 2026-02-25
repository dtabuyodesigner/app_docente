from flask import Blueprint, jsonify, request, session
from utils.db import get_db
import os
from datetime import date, datetime

comedor_bp = Blueprint('comedor', __name__)

def calculate_comedor_total(conn, fecha_iso, grupo_id=None):
    cur = conn.cursor()
    # Get day of week (0=Mon, 6=Sun)
    dt = datetime.fromisoformat(fecha_iso)
    weekday = str(dt.weekday())

    # Get students and their attendance/dining settings
    cur.execute("""
        SELECT 
            a.id, 
            a.no_comedor, 
            a.comedor_dias,
            asist.estado,
            asist.comedor,
            asist.tipo_ausencia,
            asist.horas_ausencia
        FROM alumnos a
        LEFT JOIN asistencia asist ON asist.alumno_id = a.id AND asist.fecha = ?
        WHERE (? IS NULL OR a.grupo_id = ?)
    """, (fecha_iso, grupo_id, grupo_id))
    
    rows = cur.fetchall()
    total = 0
    
    for r in rows:
        no_comedor = r["no_comedor"]
        comedor_dias = r["comedor_dias"]
        estado = r["estado"]
        as_comedor = r["comedor"]
        tipo_ausencia = r["tipo_ausencia"]
        
        # If absent (full day), they don't eat (unless explicitly overridden)
        current_state = estado if estado else 'presente'
        current_tipo = tipo_ausencia if tipo_ausencia else 'dia'
        
        if current_state in ('falta_justificada', 'falta_no_justificada') and current_tipo == 'dia':
            if as_comedor != 1:
                continue
            
        eats = False
        
        if as_comedor is not None:
            eats = (as_comedor == 1)
        else:
            if no_comedor == 1:
                eats = False
            elif comedor_dias:
                if weekday in comedor_dias.split(','):
                    eats = True
                else:
                    eats = False
            else:
                eats = True
        
        if eats:
            total += 1
            
    return total

@comedor_bp.route("/api/comedor/hoy")
def comedor_hoy():
    fecha = request.args.get("fecha", date.today().isoformat())
    conn = get_db()
    grupo_id = session.get('active_group_id')
    total = calculate_comedor_total(conn, fecha, grupo_id)
    return jsonify({"total": total})

@comedor_bp.route("/api/comedor/menu")
def get_comedor_menu():
    mes = request.args.get("mes")
    if not mes:
        mes = datetime.now().strftime("%Y-%m")
        
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT imagen FROM menus_comedor WHERE mes = ?", (mes,))
    row = cur.fetchone()
    
    return jsonify({"imagen": row["imagen"] if row else None, "mes": mes})

@comedor_bp.route("/api/comedor/menu/upload", methods=["POST"])
def upload_comedor_menu():
    if 'foto' not in request.files:
        return jsonify({"ok": False, "error": "No file part"}), 400
    
    file = request.files['foto']
    mes = request.form.get('mes')
    
    if file.filename == '' or not mes:
        return jsonify({"ok": False, "error": "No selected file or month"}), 400

    if file:
        filename = f"menu_comedor_{mes}_{int(datetime.now().timestamp())}.jpg"
        filepath = os.path.join("static", "uploads", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        file.save(filepath)
        
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("INSERT OR REPLACE INTO menus_comedor (mes, imagen) VALUES (?, ?)", (mes, filename))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print("Error en upload_comedor_menu:", str(e))
            return jsonify({"ok": False, "error": "Error interno al guardar menú de comedor."}), 500
            
        return jsonify({"ok": True, "imagen": filename})
        
    return jsonify({"ok": False}), 500
