from flask import Blueprint, jsonify, request, session, send_file
from utils.db import get_db
from utils.security import sanitize_input
import csv
import io
import os

material_bp = Blueprint('material', __name__)

@material_bp.route("/api/material")
def get_material():
    grupo_id = session.get('active_group_id')
    if not grupo_id:
        return jsonify({"info": {}, "material": []})

    conn = get_db()
    cur = conn.cursor()

    # Get general info
    cur.execute("SELECT * FROM material_info WHERE grupo_id = ?", (grupo_id,))
    info_row = cur.fetchone()
    info = dict(info_row) if info_row else {
        "centro": "",
        "curso_escolar": "",
        "nivel_curso": "",
        "observaciones": ""
    }

    # Get material items
    cur.execute("SELECT * FROM material_alumnado WHERE grupo_id = ? ORDER BY categoria, id", (grupo_id,))
    material = [dict(r) for r in cur.fetchall()]

    return jsonify({"info": info, "material": material})

@material_bp.route("/api/material/info", methods=["POST"])
def save_material_info():
    grupo_id = session.get('active_group_id')
    if not grupo_id:
        return jsonify({"ok": False, "error": "No hay grupo seleccionado"}), 400

    d = request.json
    centro = sanitize_input(d.get("centro", ""))
    curso_escolar = sanitize_input(d.get("curso_escolar", ""))
    nivel_curso = sanitize_input(d.get("nivel_curso", ""))
    observaciones = sanitize_input(d.get("observaciones", ""))

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT OR REPLACE INTO material_info (grupo_id, centro, curso_escolar, nivel_curso, observaciones)
            VALUES (?, ?, ?, ?, ?)
        """, (grupo_id, centro, curso_escolar, nivel_curso, observaciones))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@material_bp.route("/api/material", methods=["POST"])
def add_material_item():
    grupo_id = session.get('active_group_id')
    if not grupo_id:
        return jsonify({"ok": False, "error": "No hay grupo seleccionado"}), 400

    d = request.json
    categoria = d.get("categoria") # 'AYUDA' or 'TODO'
    unidades = d.get("unidades", 1)
    material = sanitize_input(d.get("material", ""))

    if not categoria or not material:
        return jsonify({"ok": False, "error": "Categoría y material son obligatorios"}), 400

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO material_alumnado (grupo_id, categoria, unidades, material)
            VALUES (?, ?, ?, ?)
        """, (grupo_id, categoria, unidades, material))
        conn.commit()
        return jsonify({"ok": True, "id": cur.lastrowid})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@material_bp.route("/api/material/<int:item_id>", methods=["PUT"])
def update_material_item(item_id):
    d = request.json
    unidades = d.get("unidades", 1)
    material = sanitize_input(d.get("material", ""))

    if not material:
        return jsonify({"ok": False, "error": "El material es obligatorio"}), 400

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE material_alumnado
            SET unidades = ?, material = ?
            WHERE id = ?
        """, (unidades, material, item_id))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@material_bp.route("/api/material/<int:item_id>", methods=["DELETE"])
def delete_material_item(item_id):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM material_alumnado WHERE id = ?", (item_id,))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@material_bp.route("/api/material/importar", methods=["POST"])
def importar_material():
    grupo_id = session.get('active_group_id')
    if not grupo_id:
        return jsonify({"ok": False, "error": "No hay grupo seleccionado"}), 400

    if 'archivo' not in request.files:
        return jsonify({"ok": False, "error": "No se ha subido ningún archivo"}), 400
    
    file = request.files['archivo']
    if file.filename == '':
        return jsonify({"ok": False, "error": "Archivo no seleccionado"}), 400

    try:
        stream = io.StringIO(file.stream.read().decode("utf-8-sig"), newline=None)
        reader = csv.DictReader(stream, delimiter=';')
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute("BEGIN")
        
        count = 0
        for row in reader:
            categoria = row.get("Categoría", "TODO").upper()
            if categoria not in ['AYUDA', 'TODO']: categoria = 'TODO'
            
            unidades = row.get("Unidades", "1")
            material = sanitize_input(row.get("Material", ""))
            
            if material:
                cur.execute("""
                    INSERT INTO material_alumnado (grupo_id, categoria, unidades, material)
                    VALUES (?, ?, ?, ?)
                """, (grupo_id, categoria, unidades, material))
                count += 1
        
        conn.commit()
        return jsonify({"ok": True, "count": count})
    except Exception as e:
        if 'conn' in locals(): conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@material_bp.route("/api/material/plantilla")
def descargar_plantilla_material():
    si = io.StringIO()
    cw = csv.writer(si, delimiter=';')
    cw.writerow(["Categoría", "Unidades", "Material"])
    cw.writerow(["AYUDA", "2", "Lápices HB"])
    cw.writerow(["TODO", "1", "Caja de colores (12 unidades)"])
    cw.writerow(["TODO", "1", "Pegamento de barra"])
    
    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8-sig'))
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name="plantilla_material.csv",
        mimetype='text/csv'
    )

@material_bp.route("/api/material/estado/<int:alumno_id>")
def get_material_alumno(alumno_id):
    conn = get_db()
    cur = conn.cursor()
    
    # Get group of the student
    cur.execute("SELECT grupo_id FROM alumnos WHERE id = ?", (alumno_id,))
    row = cur.fetchone()
    if not row:
        return jsonify({"ok": False, "error": "Alumno no encontrado"}), 404
    grupo_id = row["grupo_id"]

    # Get all material for that group
    cur.execute("SELECT * FROM material_alumnado WHERE grupo_id = ? ORDER BY categoria, id", (grupo_id,))
    material = [dict(r) for r in cur.fetchall()]

    # Get delivered status
    cur.execute("SELECT material_id, entregado FROM material_entregado WHERE alumno_id = ?", (alumno_id,))
    status = {r["material_id"]: r["entregado"] for r in cur.fetchall()}

    # Merge
    for m in material:
        m["entregado"] = status.get(m["id"], 0)

    return jsonify(material)

@material_bp.route("/api/material/estado", methods=["POST"])
def toggle_material_status():
    d = request.json
    alumno_id = d.get("alumno_id")
    material_id = d.get("material_id")
    entregado = int(d.get("entregado", 0))

    if not alumno_id or not material_id:
        return jsonify({"ok": False, "error": "Datos incompletos"}), 400

    conn = get_db()
    cur = conn.cursor()
    try:
        from datetime import datetime
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if entregado else None
        
        cur.execute("""
            INSERT INTO material_entregado (alumno_id, material_id, entregado, fecha_entrega)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(alumno_id, material_id) DO UPDATE SET
                entregado = excluded.entregado,
                fecha_entrega = excluded.fecha_entrega
        """, (alumno_id, material_id, entregado, fecha))
        
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
