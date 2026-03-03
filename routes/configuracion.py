from flask import Blueprint, jsonify, request, session
from utils.db import get_db

configuracion_bp = Blueprint('configuracion', __name__)

@configuracion_bp.route("/api/configuracion", methods=["GET"])
def get_all_config():
    conn = get_db()
    cur = conn.cursor()
    
    # Get from 'config' table
    cur.execute("SELECT clave, valor FROM config")
    config_rows = cur.fetchall()
    config_data = {r["clave"]: r["valor"] for r in config_rows}
    
    # Get from 'configuracion' table (specifically for library)
    cur.execute("SELECT clave, valor FROM configuracion")
    config_old_rows = cur.fetchall()
    for r in config_old_rows:
        if r["clave"] not in config_data:
            config_data[r["clave"]] = r["valor"]
            
    return jsonify(config_data)

@configuracion_bp.route("/api/configuracion", methods=["POST"])
def save_config():
    data = request.json
    if not data:
        return jsonify({"ok": False, "error": "No hay datos"}), 400
        
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("BEGIN")
        for clave, valor in data.items():
            # Save to 'config' table as the primary store
            cur.execute("""
                INSERT INTO config (clave, valor) VALUES (?, ?)
                ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor
            """, (clave, str(valor)))
            
            # Special case: Sync to 'configuracion' table to maintain compatibility with lectura.py
            if clave == 'max_dias_prestamo':
                cur.execute("""
                    INSERT INTO configuracion (clave, valor) VALUES (?, ?)
                    ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor
                """, (clave, str(valor)))
                
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
