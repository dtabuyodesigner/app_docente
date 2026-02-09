from flask import Blueprint, jsonify, request
from utils.db import get_db
import json
import os
from datetime import datetime

horario_bp = Blueprint('horario', __name__)

def get_config_value(key):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT valor FROM config WHERE clave = ?", (key,))
    row = cur.fetchone()
    conn.close()
    return row["valor"] if row else None

def set_config_value(key, value):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO config (clave, valor) VALUES (?, ?) ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor", (key, value))
    conn.commit()
    conn.close()

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

    conn.close()
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
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()
        
    return jsonify({"ok": True, "id": new_id})

@horario_bp.route("/api/horario/manual/<int:id>", methods=["DELETE"])
def delete_horario_manual(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM horario WHERE id = ?", (id,))
    conn.commit()
    conn.close()
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
        filename = f"horario_{tipo}_{int(datetime.now().timestamp())}.jpg"
        filepath = os.path.join("static", "uploads", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        file.save(filepath)
        
        config_key = f"horario_img_path_{tipo}"
        set_config_value(config_key, filename)
        return jsonify({"ok": True, "imagen": filename})
        
    return jsonify({"ok": False}), 500

@horario_bp.route("/api/programacion")
def obtener_programacion():
    start = request.args.get("start")
    end = request.args.get("end")

    conn = get_db()
    cur = conn.cursor()

    sql = """
        SELECT id, fecha, actividad, tipo, observaciones, color 
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
    conn.close()
    
    events = []
    for r in rows:
        events.append({
            "id": r["id"],
            "title": r["actividad"],
            "start": r["fecha"],
            "activity_type": r["tipo"],
            "description": r["observaciones"],
            "color": r["color"] or "#3788d8"
        })
    return jsonify(events)

@horario_bp.route("/api/programacion", methods=["POST"])
def guardar_evento():
    d = request.json
    print("Guardando evento:", d) # Debug
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO programacion_diaria (fecha, actividad, tipo, observaciones, color)
            VALUES (?, ?, ?, ?, ?)
        """, (d["fecha"], d["actividad"], d.get("tipo", "general"), d.get("observaciones", ""), d.get("color", "#3788d8")))
        new_id = cur.lastrowid
        conn.commit()
        return jsonify({"ok": True, "id": new_id})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()

@horario_bp.route("/api/programacion/<int:event_id>", methods=["PUT"])
def actualizar_evento(event_id):
    d = request.json
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE programacion_diaria
            SET fecha = ?, actividad = ?, tipo = ?, observaciones = ?, color = ?
            WHERE id = ?
        """, (d["fecha"], d["actividad"], d.get("tipo", "general"), d.get("observaciones", ""), d.get("color", "#3788d8"), event_id))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()

@horario_bp.route("/api/programacion/<int:event_id>", methods=["DELETE"])
def borrar_evento(event_id):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM programacion_diaria WHERE id = ?", (event_id,))
        conn.commit()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()
    return jsonify({"ok": True})

@horario_bp.route("/api/tareas")
def obtener_tareas():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, texto, completada FROM tareas ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return jsonify([{"id":r["id"], "texto":r["texto"], "completada":bool(r["completada"])} for r in rows])

@horario_bp.route("/api/tareas", methods=["POST"])
def crear_tarea():
    d = request.json
    if not d or not d.get("texto"): 
        return jsonify({"ok":False}), 400
        
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO tareas (texto, completada) VALUES (?, 0)", (d["texto"],))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "id": new_id})

@horario_bp.route("/api/tareas/<int:id>", methods=["PUT"])
def actualizar_tarea(id):
    d = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE tareas SET completada = ? WHERE id = ?", (1 if d.get("completada") else 0, id))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@horario_bp.route("/api/tareas/<int:id>", methods=["DELETE"])
def borrar_tarea(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@horario_bp.route("/api/observaciones", methods=["POST"])
def guardar_observacion():
    d = request.json
    alumno_id = d["alumno_id"]
    fecha = d.get("fecha")
    texto = d["texto"]
    area_id = d.get("area_id") or None

    conn = get_db()
    cur = conn.cursor()

    if not texto.strip():
        if area_id:
            cur.execute("DELETE FROM observaciones WHERE alumno_id = ? AND fecha = ? AND area_id = ?", (alumno_id, fecha, area_id))
        else:
            cur.execute("DELETE FROM observaciones WHERE alumno_id = ? AND fecha = ? AND area_id IS NULL", (alumno_id, fecha))
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "deleted": True})

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
    conn.close()

    return jsonify({"ok": True})

@horario_bp.route("/api/observaciones/dia")
def obtener_observaciones_dia():
    fecha = request.args.get("fecha")
    area_id = request.args.get("area_id")

    conn = get_db()
    cur = conn.cursor()
    
    if area_id:
        cur.execute("""
            SELECT a.id, a.nombre, a.foto, o.texto, asi.estado, 
                   f.madre_telefono, f.padre_telefono, f.madre_email, f.padre_email
            FROM alumnos a
            LEFT JOIN observaciones o ON o.alumno_id = a.id AND o.fecha = ? AND o.area_id = ?
            LEFT JOIN asistencia asi ON asi.alumno_id = a.id AND asi.fecha = ?
            LEFT JOIN ficha_alumno f ON f.alumno_id = a.id
            ORDER BY a.nombre
        """, (fecha, area_id, fecha))
    else:
        cur.execute("""
            SELECT a.id, a.nombre, a.foto, o.texto, asi.estado, 
                   f.madre_telefono, f.padre_telefono, f.madre_email, f.padre_email
            FROM alumnos a
            LEFT JOIN observaciones o ON o.alumno_id = a.id AND o.fecha = ? AND o.area_id IS NULL
            LEFT JOIN asistencia asi ON asi.alumno_id = a.id AND asi.fecha = ?
            LEFT JOIN ficha_alumno f ON f.alumno_id = a.id
            ORDER BY a.nombre
        """, (fecha, fecha))
    
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
    
    conn.close()
    return jsonify(data)

@horario_bp.route("/api/observaciones/<int:alumno_id>")
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
    conn.close()

    return jsonify([
        {"id": r["id"], "fecha": r["fecha"], "texto": r["texto"]}
        for r in datos
    ])

@horario_bp.route("/api/observaciones/<int:obs_id>", methods=["PUT"])
def editar_observacion(obs_id):
    d = request.json
    texto = d.get("texto", "")
    
    conn = get_db()
    cur = conn.cursor()
    
    if not texto.strip():
        cur.execute("DELETE FROM observaciones WHERE id = ?", (obs_id,))
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "deleted": True})
        
    cur.execute("UPDATE observaciones SET texto = ? WHERE id = ?", (texto, obs_id))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@horario_bp.route("/api/observaciones/<int:obs_id>", methods=["DELETE"])
def borrar_observacion(obs_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM observaciones WHERE id = ?", (obs_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})
