from flask import Blueprint, jsonify, request, session
from utils.db import get_db
import json
import os
import re
from datetime import datetime

horario_bp = Blueprint('horario', __name__)

def get_config_value(key):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT valor FROM config WHERE clave = ?", (key,))
    row = cur.fetchone()
    return row["valor"] if row else None

def set_config_value(key, value):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO config (clave, valor) VALUES (?, ?) ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor", (key, value))
    conn.commit()

@horario_bp.route("/api/horario")
def get_horario():
    conn = get_db()
    cur = conn.cursor()
    
    tipo = request.args.get("tipo", "clase")
    
    cur.execute("SELECT id, dia, hora_inicio, hora_fin, asignatura, detalles FROM horario WHERE tipo = ? ORDER BY dia, hora_inicio", (tipo,))
    rows = cur.fetchall()
    
    manual = []
    for r in rows:
        manual.append({
            "id": r["id"],
            "dia": r["dia"],
            "hora_inicio": r["hora_inicio"],
            "hora_fin": r["hora_fin"],
            "asignatura": r["asignatura"],
            "detalles": r["detalles"]
        })
    
    img_clase = get_config_value("horario_img_path_clase")
    img_profesor = get_config_value("horario_img_path_profesor")
    
    # Check legacy
    if not img_clase:
        img_clase = get_config_value("horario_img_path")

    rows_config_json = get_config_value("horario_rows")
    if rows_config_json:
        rows_config = json.loads(rows_config_json)
    else:
        rows_config = [
            {"start": "09:00", "end": "10:00"},
            {"start": "10:00", "end": "11:00"},
            {"start": "11:00", "end": "12:00"},
            {"start": "12:00", "end": "13:00"},
            {"start": "13:00", "end": "14:00"},
        ]

    return jsonify({
        "manual": manual, 
        "imagen_clase": img_clase, 
        "imagen_profesor": img_profesor,
        "config": rows_config
    })

@horario_bp.route("/api/horario/config", methods=["POST"])
def set_horario_config():
    data = request.json
    if not data or 'rows' not in data:
        return jsonify({"ok": False, "error": "Invalid data"}), 400
    
    try:
        rows_json = json.dumps(data['rows'])
        set_config_value("horario_rows", rows_json)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@horario_bp.route("/api/horario/manual", methods=["POST"])
def save_horario_manual():
    d = request.json
    dia = d.get("dia")
    
    try:
        if dia is not None:
            dia = int(dia)
    except ValueError:
        pass 
        
    hora_inicio = d.get("hora_inicio")
    hora_fin = d.get("hora_fin")
    asignatura = d.get("asignatura")
    detalles = d.get("detalles", "")
    tipo = d.get("tipo", "clase")
    
    if dia is None or not hora_inicio or not hora_fin or not asignatura:
        return jsonify({"ok": False, "error": "Faltan datos obligatorios"}), 400
        
    if not re.match(r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$", hora_inicio):
        return jsonify({"ok": False, "error": "El formato de la hora de inicio no es válido (HH:MM)."}), 400
        
    if not re.match(r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$", hora_fin):
        return jsonify({"ok": False, "error": "El formato de la hora de fin no es válido (HH:MM)."}), 400
        
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO horario (dia, hora_inicio, hora_fin, asignatura, detalles, tipo)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (dia, hora_inicio, hora_fin, asignatura, detalles, tipo))
        new_id = cur.lastrowid
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Error en save_horario_manual:", str(e))
        return jsonify({"ok": False, "error": "Error interno al guardar el horario."}), 500
        
    return jsonify({"ok": True, "id": new_id})

@horario_bp.route("/api/horario/manual/<int:id>", methods=["DELETE"])
def delete_horario_manual(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM horario WHERE id = ?", (id,))
    conn.commit()
    return jsonify({"ok": True})

@horario_bp.route("/api/horario/upload", methods=["POST"])
def upload_horario_img():
    if 'foto' not in request.files:
        return jsonify({"ok": False, "error": "No file part"}), 400
    
    tipo = request.form.get("tipo", "clase")
    file = request.files['foto']
    if file.filename == '':
        return jsonify({"ok": False, "error": "No selected file"}), 400

    if file:
        from werkzeug.utils import secure_filename
        secure_filename(file.filename)  # validar
        filename = f"horario_{tipo}_{int(datetime.now().timestamp())}.jpg"
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = os.path.join(base_dir, "static", "uploads", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        file.save(filepath)
        
        config_key = f"horario_img_path_{tipo}"
        set_config_value(config_key, filename)
        return jsonify({"ok": True, "imagen": filename})
        
    return jsonify({"ok": False}), 500

@horario_bp.route("/api/horario/imagen", methods=["DELETE"])
def delete_horario_img():
    tipo = request.args.get("tipo", "clase")
    config_key = f"horario_img_path_{tipo}"
    set_config_value(config_key, "")
    return jsonify({"ok": True})
