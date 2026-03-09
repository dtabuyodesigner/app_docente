from flask import Blueprint, jsonify, request
from utils.db import get_db

eventos_bp = Blueprint('eventos', __name__)

@eventos_bp.route("/api/programacion")
def obtener_programacion():
    start = request.args.get("start")
    end = request.args.get("end")

    conn = get_db()
    cur = conn.cursor()

    # 1. Fetch from programacion_diaria
    sql = """
        SELECT id, fecha, actividad, tipo, observaciones, color, sda_id, evaluable, criterio_id
        FROM programacion_diaria
        WHERE 1=1
    """
    params = []

    if start:
        sql += " AND fecha >= ?"
        params.append(start)
    if end:
        sql += " AND fecha <= ?"
        params.append(end)

    cur.execute(sql, params)
    rows = cur.fetchall()
    
    events = []
    for r in rows:
        events.append({
            "id": r["id"],
            "title": r["actividad"],
            "start": r["fecha"],
            "color": r["color"] or "#3788d8",
            "extendedProps": {
                "tipo": r["tipo"],
                "observaciones": r["observaciones"] or "",
                "sda_id": r["sda_id"],
                "evaluable": r["evaluable"],
                "criterio_id": r["criterio_id"]
            }
        })
        
    # 2. Fetch from sesiones_actividad (Actualizado a programacion_diaria segun el nuevo esquema)
    # Sin embargo, para mantener compatibilidad con el frontend que espera sesiones de actividades_sda:
    sql_sesiones = """
        SELECT sa.id, sa.fecha, sa.descripcion, sa.numero_sesion, sa.actividad_id, act.nombre as act_nombre, sda.nombre as sda_nombre, sda.id as sda_id, sa.evaluable, sa.criterio_id
        FROM programacion_diaria sa
        JOIN actividades_sda act ON sa.actividad_id = act.id
        JOIN sda ON act.sda_id = sda.id
        WHERE sa.actividad_id IS NOT NULL
    """
    params_ses = []

    if start:
        sql_sesiones += " AND sa.fecha >= ?"
        params_ses.append(start)
    if end:
        sql_sesiones += " AND sa.fecha <= ?"
        params_ses.append(end)

    cur.execute(sql_sesiones, params_ses)
    rows_sesiones = cur.fetchall()
    
    for r in rows_sesiones:
        title = f"[{r['sda_nombre']}] {r['act_nombre']} - Sesión {r['numero_sesion']}"
        if r['descripcion']:
            title += f": {r['descripcion']}"
            
        events.append({
            "id": f"ses_{r['id']}", 
            "title": title,
            "start": r["fecha"],
            "color": "#17a2b8", 
            "extendedProps": {
                "tipo": "sesion_actividad",
                "observaciones": r["descripcion"] or "",
                "sda_id": r["sda_id"],
                "actividad_id": r["actividad_id"],
                "sesion_id": r["id"],
                "numero_sesion": r["numero_sesion"],
                "evaluable": r["evaluable"],
                "criterio_id": r["criterio_id"]
            }
        })
        
    return jsonify(events)

@eventos_bp.route("/api/programacion", methods=["POST"])
def guardar_evento():
    d = request.json
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO programacion_diaria (fecha, actividad, tipo, observaciones, color, sda_id, evaluable, criterio_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (d["fecha"], d["actividad"], d.get("tipo", "general"), d.get("observaciones", ""), d.get("color", "#3788d8"), d.get("sda_id") or None, d.get("evaluable", 0), d.get("criterio_id") or None))
        new_id = cur.lastrowid
        conn.commit()
        return jsonify({"ok": True, "id": new_id})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@eventos_bp.route("/api/programacion/<int:event_id>", methods=["PUT"])
def actualizar_evento(event_id):
    d = request.json
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE programacion_diaria
            SET fecha = ?, actividad = ?, tipo = ?, observaciones = ?, color = ?, sda_id = ?, evaluable = ?, criterio_id = ?
            WHERE id = ?
        """, (d["fecha"], d["actividad"], d.get("tipo", "general"), d.get("observaciones", ""), d.get("color", "#3788d8"), d.get("sda_id") or None, d.get("evaluable", 0), d.get("criterio_id") or None, event_id))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@eventos_bp.route("/api/programacion/<int:event_id>", methods=["DELETE"])
def borrar_evento(event_id):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM programacion_diaria WHERE id = ?", (event_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
    return jsonify({"ok": True})
