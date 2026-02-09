from flask import Blueprint, jsonify, request
from utils.db import get_db
from datetime import date

reuniones_bp = Blueprint('reuniones', __name__)

@reuniones_bp.route("/api/reuniones", methods=["GET", "POST"])
def api_reuniones():
    conn = get_db()
    cur = conn.cursor()
    
    if request.method == "POST":
        d = request.json
        alumno_id = d.get("alumno_id") # Puede ser None si tipo=CICLO (pero en db es INTEGER)
        fecha = d.get("fecha")
        asistentes = d.get("asistentes")
        temas = d.get("temas")
        acuerdos = d.get("acuerdos")
        tipo = d.get("tipo", "PADRES")
        
        try:
            cur.execute("""
                INSERT INTO reuniones (alumno_id, fecha, asistentes, temas, acuerdos, tipo)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (alumno_id, fecha, asistentes, temas, acuerdos, tipo))
            conn.commit()
            return jsonify({"ok": True, "id": cur.lastrowid})
        except Exception as e:
            conn.rollback()
            return jsonify({"ok": False, "error": str(e)}), 500
        finally:
            conn.close()
            
    else:
        # GET
        rid = request.args.get("id")
        alumno_id = request.args.get("alumno_id")
        tipo = request.args.get("tipo")
        
        if rid:
            cur.execute("SELECT * FROM reuniones WHERE id = ?", (rid,))
            r = cur.fetchone()
            conn.close()
            if r:
                return jsonify(dict(r))
            return jsonify({"ok": False, "error": "Not found"}), 404
            
        elif alumno_id:
            cur.execute("SELECT * FROM reuniones WHERE alumno_id = ? ORDER BY fecha DESC", (alumno_id,))
            rows = cur.fetchall()
            conn.close()
            return jsonify([dict(r) for r in rows])
        else:
            # List all (filtered by type if provided)
            sql = """
                SELECT r.*, a.nombre as alumno_nombre
                FROM reuniones r
                LEFT JOIN alumnos a ON r.alumno_id = a.id
                WHERE 1=1
            """
            params = []
            if tipo:
                sql += " AND r.tipo = ?"
                params.append(tipo)
                
            sql += " ORDER BY r.fecha DESC"
            
            cur.execute(sql, params)
            rows = cur.fetchall()
            conn.close()
            return jsonify([dict(r) for r in rows])

@reuniones_bp.route("/api/reuniones/<int:rid>", methods=["DELETE"])
def borrar_reunion(rid):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM reuniones WHERE id = ?", (rid,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()
    return jsonify({"ok": True})
