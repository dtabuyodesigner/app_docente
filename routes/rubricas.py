from flask import Blueprint, jsonify, request, session
from utils.db import get_db

rubricas_bp = Blueprint('rubricas', __name__)

@rubricas_bp.route("/api/rubricas/<int:crit_id>", methods=["GET"])
def get_rubrica(crit_id):
    if not session.get('logged_in'):
        return jsonify({"ok": False, "error": "No autorizado"}), 401
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT nivel, descriptor FROM rubricas WHERE criterio_id = ? ORDER BY nivel", (crit_id,))
    rows = cur.fetchall()
    
    data = {row["nivel"]: row["descriptor"] for row in rows}
    return jsonify(data)

@rubricas_bp.route("/api/rubricas", methods=["POST"])
def save_rubrica():
    if not session.get('logged_in'):
        return jsonify({"ok": False, "error": "No autorizado"}), 401
    
    d = request.json
    crit_id = d.get("criterio_id")
    descriptores = d.get("descriptores") # Expecting { "1": "...", "2": "...", ... }
    
    if not crit_id or not descriptores:
        return jsonify({"ok": False, "error": "Faltan datos"}), 400
        
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("BEGIN")
        # Optional: delete existing before re-inserting or use UPSERT logic
        # Standard schema has UNIQUE(criterio_id, nivel)
        for nivel, texto in descriptores.items():
            if not texto.strip():
                cur.execute("DELETE FROM rubricas WHERE criterio_id = ? AND nivel = ?", (crit_id, int(nivel)))
                continue
                
            cur.execute("""
                INSERT INTO rubricas (criterio_id, nivel, descriptor)
                VALUES (?, ?, ?)
                ON CONFLICT(criterio_id, nivel) DO UPDATE SET descriptor = excluded.descriptor
            """, (crit_id, int(nivel), texto))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@rubricas_bp.route("/api/rubricas/<int:crit_id>", methods=["DELETE"])
def delete_rubrica(crit_id):
    if not session.get('logged_in'):
        return jsonify({"ok": False, "error": "No autorizado"}), 401
        
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM rubricas WHERE criterio_id = ?", (crit_id,))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
