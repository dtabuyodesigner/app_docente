from flask import Blueprint, jsonify, request, session
from utils.db import get_db

observaciones_bp = Blueprint('observaciones', __name__)

@observaciones_bp.route("/api/observaciones", methods=["POST"])
def guardar_observacion():
    d = request.json
    alumno_id = d["alumno_id"]
    fecha = d.get("fecha")
    texto = d["texto"]
    area_id = d.get("area_id")
    if area_id == "" or area_id is None:
        area_id = None
    else:
        try:
            area_id = int(area_id)
        except:
            area_id = None

    conn = get_db()
    cur = conn.cursor()

    if not texto.strip():
        try:
            cur.execute("BEGIN")
            if area_id:
                cur.execute("DELETE FROM observaciones WHERE alumno_id = ? AND fecha = ? AND area_id = ?", (alumno_id, fecha, area_id))
            else:
                cur.execute("DELETE FROM observaciones WHERE alumno_id = ? AND fecha = ? AND area_id IS NULL", (alumno_id, fecha))
            conn.commit()
            return jsonify({"ok": True, "deleted": True})
        except Exception as e:
            conn.rollback()
            return jsonify({"ok": False, "error": str(e)}), 500

    try:
        cur.execute("BEGIN")
        if area_id:
            cur.execute("SELECT id FROM observaciones WHERE alumno_id = ? AND fecha = ? AND area_id = ?", (alumno_id, fecha, area_id))
        else:
            cur.execute("SELECT id FROM observaciones WHERE alumno_id = ? AND fecha = ? AND area_id IS NULL", (alumno_id, fecha))
        
        row = cur.fetchone()

        if row:
            cur.execute("UPDATE observaciones SET texto = ? WHERE id = ?", (texto, row["id"]))
        else:
            cur.execute("""
                INSERT INTO observaciones (alumno_id, fecha, texto, area_id)
                VALUES (?, ?, ?, ?)
            """, (alumno_id, fecha, texto, area_id))

        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@observaciones_bp.route("/api/observaciones/dia")
def obtener_observaciones_dia():
    fecha = request.args.get("fecha")
    area_id = request.args.get("area_id")

    conn = get_db()
    cur = conn.cursor()
    
    grupo_id = session.get('active_group_id')
    
    if area_id:
        cur.execute("""
            SELECT a.id, a.nombre, a.foto, o.texto, asi.estado, 
                   f.madre_telefono, f.padre_telefono, f.madre_email, f.padre_email
            FROM alumnos a
            LEFT JOIN observaciones o ON o.alumno_id = a.id AND o.fecha = ? AND o.area_id = ?
            LEFT JOIN asistencia asi ON asi.alumno_id = a.id AND asi.fecha = ?
            LEFT JOIN ficha_alumno f ON f.alumno_id = a.id
            WHERE a.grupo_id = ?
            ORDER BY a.nombre
        """, (fecha, area_id, fecha, grupo_id))
    else:
        cur.execute("""
            SELECT a.id, a.nombre, a.foto, o.texto, asi.estado, 
                   f.madre_telefono, f.padre_telefono, f.madre_email, f.padre_email
            FROM alumnos a
            LEFT JOIN observaciones o ON o.alumno_id = a.id AND o.fecha = ? AND o.area_id IS NULL
            LEFT JOIN asistencia asi ON asi.alumno_id = a.id AND asi.fecha = ?
            LEFT JOIN ficha_alumno f ON f.alumno_id = a.id
            WHERE a.grupo_id = ?
            ORDER BY a.nombre
        """, (fecha, fecha, grupo_id))
    
    data = []
    for row in cur.fetchall():
        data.append({
            "id": row["id"],
            "nombre": row["nombre"],
            "foto": row["foto"] or "",
            "observacion": row["texto"] or "",
            "asistencia": row["estado"] or "presente",
            "madre_tel": row["madre_telefono"] or "",
            "padre_tel": row["padre_telefono"] or "",
            "madre_email": row["madre_email"] or "",
            "padre_email": row["padre_email"] or ""
        })
    return jsonify(data)

@observaciones_bp.route("/api/observaciones/<int:alumno_id>")
def ver_observaciones(alumno_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, fecha, texto
        FROM observaciones
        WHERE alumno_id = ?
        ORDER BY fecha DESC
    """, (alumno_id,))
    datos = cur.fetchall()
    return jsonify([
        {"id": r["id"], "fecha": r["fecha"], "texto": r["texto"]}
        for r in datos
    ])

@observaciones_bp.route("/api/observaciones/<int:obs_id>", methods=["PUT"])
def editar_observacion(obs_id):
    d = request.json
    texto = d.get("texto", "")
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        if not texto.strip():
            cur.execute("DELETE FROM observaciones WHERE id = ?", (obs_id,))
            conn.commit()
            return jsonify({"ok": True, "deleted": True})
        cur.execute("UPDATE observaciones SET texto = ? WHERE id = ?", (texto, obs_id))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@observaciones_bp.route("/api/observaciones/<int:obs_id>", methods=["DELETE"])
def borrar_observacion(obs_id):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        cur.execute("DELETE FROM observaciones WHERE id = ?", (obs_id,))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@observaciones_bp.route("/api/observaciones/historial")
def historial_observaciones():
    """Historial de observaciones con filtros opcionales."""
    alumno_id = request.args.get("alumno_id")
    fecha_desde = request.args.get("fecha_desde")
    fecha_hasta = request.args.get("fecha_hasta")
    area_id = request.args.get("area_id")
    
    conn = get_db()
    cur = conn.cursor()
    
    query = """
        SELECT o.id, o.alumno_id, o.area_id, o.fecha, o.texto,
               a.nombre as alumno_nombre, ar.nombre as area_nombre
        FROM observaciones o
        INNER JOIN alumnos a ON o.alumno_id = a.id
        LEFT JOIN areas ar ON o.area_id = ar.id
        WHERE 1=1
    """
    params = []
    
    if alumno_id:
        query += " AND o.alumno_id = ?"
        params.append(alumno_id)
    if fecha_desde:
        query += " AND o.fecha >= ?"
        params.append(fecha_desde)
    if fecha_hasta:
        query += " AND o.fecha <= ?"
        params.append(fecha_hasta)
    if area_id:
        query += " AND o.area_id = ?"
        params.append(area_id)
        
    query += " ORDER BY o.fecha DESC, o.id DESC LIMIT 200"
    
    cur.execute(query, params)
    data = cur.fetchall()
    return jsonify([dict(r) for r in data])
