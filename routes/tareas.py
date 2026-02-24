from flask import Blueprint, request, jsonify
from utils.db import get_db

tareas_bp = Blueprint('tareas', __name__)

@tareas_bp.route("/api/gestor_tareas", methods=["GET"])
def get_tareas():
    # Obtener listado, opcionalmente filtrar por estado ('pendiente' o 'completada')
    estado = request.args.get("estado")
    
    conn = get_db()
    cur = conn.cursor()
    
    if estado:
        cur.execute("SELECT * FROM gestor_tareas WHERE estado = ? ORDER BY fecha_limite ASC NULLS LAST, prioridad DESC, id DESC", (estado,))
    else:
        cur.execute("SELECT * FROM gestor_tareas ORDER BY estado DESC, fecha_limite ASC NULLS LAST, prioridad DESC, id DESC")
        
    rows = cur.fetchall()
    
    tareas = []
    for r in rows:
        tareas.append({
            "id": r["id"],
            "titulo": r["titulo"],
            "descripcion": r["descripcion"] or "",
            "estado": r["estado"],
            "prioridad": r["prioridad"],
            "fecha_limite": r["fecha_limite"]
        })
        
    return jsonify(tareas)

@tareas_bp.route("/api/gestor_tareas", methods=["POST"])
def new_tarea():
    d = request.get_json(silent=True) or {}
    titulo = d.get("titulo", "").strip()
    if not titulo:
        return jsonify({"ok": False, "error": "El título de la tarea es obligatorio."}), 400
        
    descripcion = d.get("descripcion", "")
    prioridad = d.get("prioridad", "media")
    fecha_limite = d.get("fecha_limite") or None
    
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        cur.execute("""
            INSERT INTO gestor_tareas (titulo, descripcion, prioridad, fecha_limite)
            VALUES (?, ?, ?, ?)
        """, (titulo, descripcion, prioridad, fecha_limite))
        conn.commit()
        return jsonify({"ok": True, "id": cur.lastrowid})
    except Exception as e:
        conn.rollback()
        print("Error en new_tarea:", str(e))
        return jsonify({"ok": False, "error": "Error interno al crear tarea."}), 500

@tareas_bp.route("/api/gestor_tareas/<int:id>", methods=["PUT"])
def update_tarea(id):
    d = request.get_json(silent=True) or {}
    
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        # Support full update or just status toggle
        if "estado" in d and len(d) == 1:
            cur.execute("UPDATE gestor_tareas SET estado = ? WHERE id = ?", (d["estado"], id))
        else:
            titulo = d.get("titulo", "").strip()
            if not titulo:
                return jsonify({"ok": False, "error": "El título no puede estar vacío."}), 400
                
            cur.execute("""
                UPDATE gestor_tareas 
                SET titulo = ?, descripcion = ?, prioridad = ?, fecha_limite = ?, estado = ?
                WHERE id = ?
            """, (titulo, d.get("descripcion", ""), d.get("prioridad", "media"), d.get("fecha_limite") or None, d.get("estado", "pendiente"), id))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        print("Error en update_tarea:", str(e))
        return jsonify({"ok": False, "error": "Error interno al actualizar la tarea."}), 500

@tareas_bp.route("/api/gestor_tareas/<int:id>", methods=["DELETE"])
def delete_tarea(id):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        cur.execute("DELETE FROM gestor_tareas WHERE id = ?", (id,))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        print("Error en delete_tarea:", str(e))
        return jsonify({"ok": False, "error": "Error interno al eliminar la tarea."}), 500
