from flask import Blueprint, jsonify, request, send_file
from utils.db import get_db
import os
import io
import csv
import json
import re
from datetime import datetime, date

# Validation helpers
def _validar_email(email):
    if not email: return True
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email.strip()))

def _validar_telefono(tel):
    if not tel: return True
    tel_clean = re.sub(r"[\s\-\.]", "", str(tel))
    return bool(re.match(r"^\+?\d{9,15}$", tel_clean))

def _validar_fecha(fecha):
    if not fecha: return True
    try:
        datetime.strptime(fecha.strip(), "%Y-%m-%d")
        return True
    except ValueError:
        return False
        
def _check_validaciones(f_nac, m_tel, m_email, p_tel, p_email):
    if not _validar_fecha(f_nac): return "El formato de la fecha de nacimiento no es válido (YYYY-MM-DD)."
    if not _validar_telefono(m_tel): return "El teléfono de la madre no tiene un formato válido."
    if not _validar_email(m_email): return "El email de la madre no tiene un formato válido."
    if not _validar_telefono(p_tel): return "El teléfono del padre no tiene un formato válido."
    if not _validar_email(p_email): return "El email del padre no tiene un formato válido."
    return None

alumnos_bp = Blueprint('alumnos', __name__)

@alumnos_bp.route("/api/alumnos")
def obtener_alumnos():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, nombre, no_comedor, comedor_dias, foto
        FROM alumnos
        ORDER BY nombre
    """)

    alumnos = [
        {
            "id": r["id"],
            "nombre": r["nombre"],
            "no_comedor": r["no_comedor"],
            "comedor_dias": r["comedor_dias"],
            "foto": r["foto"]
        }
        for r in cur.fetchall()
    ]

    return jsonify(alumnos)

@alumnos_bp.route("/api/alumnos/nuevo", methods=["POST"])
def nuevo_alumno():
    d = request.json
    nombre = d.get("nombre")
    no_comedor = int(d.get("no_comedor", 0))
    comedor_dias = d.get("comedor_dias")

    # Campos de la ficha
    f_nac = d.get("fecha_nacimiento")
    direccion = d.get("direccion")
    m_nom = d.get("madre_nombre")
    m_tel = d.get("madre_telefono")
    m_email = d.get("madre_email")
    p_nom = d.get("padre_nombre")
    p_tel = d.get("padre_telefono")
    p_email = d.get("padre_email")
    obs = d.get("observaciones_generales")
    autorizados = d.get("personas_autorizadas")

    if not nombre:
        return jsonify({"ok": False, "error": "El nombre es obligatorio"}), 400

    err = _check_validaciones(f_nac, m_tel, m_email, p_tel, p_email)
    if err:
        return jsonify({"ok": False, "error": err}), 400

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        cur.execute("INSERT INTO alumnos (nombre, no_comedor, comedor_dias) VALUES (?, ?, ?)", 
                    (nombre, no_comedor, comedor_dias))
        alumno_id = cur.lastrowid
        
        cur.execute("""
            INSERT INTO ficha_alumno (
                alumno_id, fecha_nacimiento, direccion, madre_nombre, 
                madre_telefono, madre_email, padre_nombre, padre_telefono, padre_email,
                observaciones_generales, personas_autorizadas
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (alumno_id, f_nac, direccion, m_nom, m_tel, m_email, p_nom, p_tel, p_email, obs, autorizados))
        
        conn.commit()
        return jsonify({"ok": True, "id": alumno_id})
    except Exception as e:
        conn.rollback()
        print("Error en nuevo_alumno:", str(e))
        return jsonify({"ok": False, "error": "Error interno al guardar el alumno."}), 500

@alumnos_bp.route("/api/alumnos/<int:alumno_id>", methods=["PUT"])
def editar_alumno_info(alumno_id):
    d = request.json
    nombre = d.get("nombre")
    no_comedor = int(d.get("no_comedor", 0))
    comedor_dias = d.get("comedor_dias")

    if not nombre:
        return jsonify({"ok": False, "error": "El nombre es obligatorio"}), 400

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        cur.execute("""
            UPDATE alumnos
            SET nombre = ?, no_comedor = ?, comedor_dias = ?
            WHERE id = ?
        """, (nombre, no_comedor, comedor_dias, alumno_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Error en editar_alumno_info:", str(e))
        return jsonify({"ok": False, "error": "Error interno al editar el alumno."}), 500

    return jsonify({"ok": True})

@alumnos_bp.route("/api/alumnos/<int:alumno_id>", methods=["DELETE"])
def borrar_alumno(alumno_id):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        # La base de datos se encarga de borrar de asistencia, evaluaciones, ficha_alumno, etc. gracias a ON DELETE CASCADE
        cur.execute("DELETE FROM alumnos WHERE id = ?", (alumno_id,))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Error en borrar_alumno:", str(e))
        return jsonify({"ok": False, "error": "Error interno al borrar el alumno."}), 500

    return jsonify({"ok": True})

@alumnos_bp.route("/api/alumnos/foto/<int:alumno_id>", methods=["POST"])
def subir_foto_alumno(alumno_id):
    if 'foto' not in request.files:
        return jsonify({"ok": False, "error": "No file part"}), 400
    
    file = request.files['foto']
    if file.filename == '':
        return jsonify({"ok": False, "error": "No selected file"}), 400

    if file:
        filename = f"alumno_{alumno_id}_{int(datetime.now().timestamp())}.jpg"
        filepath = os.path.join("static", "uploads", filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        file.save(filepath)

        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE alumnos SET foto = ? WHERE id = ?", (filename, alumno_id))
        conn.commit()

        return jsonify({"ok": True, "foto": filename})
    
    return jsonify({"ok": False, "error": "Error desconocido"}), 500

@alumnos_bp.route("/api/alumnos/ficha/<int:alumno_id>")
def obtener_ficha_alumno(alumno_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            fecha_nacimiento, direccion, 
            madre_nombre, madre_telefono, madre_email,
            padre_nombre, padre_telefono, padre_email,
            observaciones_generales, personas_autorizadas
        FROM ficha_alumno
        WHERE alumno_id = ?
    """, (alumno_id,))

    f = cur.fetchone()

    if f:
        return jsonify({
            "fecha_nacimiento": f["fecha_nacimiento"] or "",
            "direccion": f["direccion"] or "",
            "madre_nombre": f["madre_nombre"] or "",
            "madre_telefono": f["madre_telefono"] or "",
            "madre_email": f["madre_email"] or "",
            "padre_nombre": f["padre_nombre"] or "",
            "padre_telefono": f["padre_telefono"] or "",
            "padre_email": f["padre_email"] or "",
            "observaciones_generales": f["observaciones_generales"] or "",
            "personas_autorizadas": f["personas_autorizadas"] or ""
        })
    return jsonify({})

@alumnos_bp.route("/api/alumnos/ficha", methods=["POST"])
def guardar_ficha_alumno():
    d = request.json
    
    err = _check_validaciones(d.get("fecha_nacimiento"), d.get("madre_telefono"), d.get("madre_email"), d.get("padre_telefono"), d.get("padre_email"))
    if err:
        return jsonify({"ok": False, "error": err}), 400

    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("BEGIN")
        cur.execute("""
            INSERT OR REPLACE INTO ficha_alumno (
                alumno_id, fecha_nacimiento, direccion, madre_nombre, 
                madre_telefono, madre_email, padre_nombre, padre_telefono, padre_email,
                observaciones_generales, personas_autorizadas
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            d["alumno_id"],
            d.get("fecha_nacimiento", ""),
            d.get("direccion", ""),
            d.get("madre_nombre", ""),
            d.get("madre_telefono", ""),
            d.get("madre_email", ""),
            d.get("padre_nombre", ""),
            d.get("padre_telefono", ""),
            d.get("padre_email", ""),
            d.get("observaciones_generales", ""),
            d.get("personas_autorizadas", "")
        ))

        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        print("Error en guardar_ficha_alumno:", str(e))
        return jsonify({"ok": False, "error": "Error interno al guardar la ficha del alumno."}), 500

@alumnos_bp.route("/api/alumnos/progreso/<int:alumno_id>")
def progreso_alumno(alumno_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT e.trimestre, ar.nombre, AVG(e.nota) as media
        FROM evaluaciones e
        JOIN areas ar ON ar.id = e.area_id
        WHERE e.alumno_id = ?
        GROUP BY e.trimestre, ar.nombre
        ORDER BY e.trimestre ASC, ar.nombre ASC
    """, (alumno_id,))
    rows = cur.fetchall()
    
    result = {1: [], 2: [], 3: []}
    for row in rows:
        result[row["trimestre"]].append({
            "area": row["nombre"],
            "media": round(row["media"], 2)
        })
    
    return jsonify(result)

@alumnos_bp.route("/api/alumnos/exportar/json")
def exportar_alumnos_json():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.id, a.nombre, a.no_comedor, a.comedor_dias, 
               f.fecha_nacimiento, f.direccion, f.madre_nombre, f.madre_telefono, f.madre_email,
               f.padre_nombre, f.padre_telefono, f.padre_email, f.observaciones_generales
        FROM alumnos a
        LEFT JOIN ficha_alumno f ON a.id = f.alumno_id
    """)
    rows = cur.fetchall()
    
    data = [dict(r) for r in rows]
    
    output = io.BytesIO()
    output.write(json.dumps(data, indent=4).encode('utf-8'))
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name=f"alumnos_export_{date.today()}.json",
        mimetype='application/json'
    )

@alumnos_bp.route("/api/alumnos/exportar/csv")
def exportar_alumnos_csv():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.id, a.nombre, a.no_comedor, a.comedor_dias, 
               f.fecha_nacimiento, f.direccion, f.madre_nombre, f.madre_telefono, f.madre_email,
               f.padre_nombre, f.padre_telefono, f.padre_email, f.observaciones_generales
        FROM alumnos a
        LEFT JOIN ficha_alumno f ON a.id = f.alumno_id
    """)
    rows = cur.fetchall()
    
    # Generate CSV
    si = io.StringIO()
    cw = csv.writer(si, delimiter=';')
    cw.writerow(["ID", "Nombre", "No Comedor", "Días Comedor", "Fecha Nacimiento", "Dirección", 
                 "Madre", "Tel Madre", "Email Madre", "Padre", "Tel Padre", "Email Padre", "Observaciones"])
    
    for r in rows:
        cw.writerow([
            r["id"], r["nombre"], r["no_comedor"], r["comedor_dias"],
            r["fecha_nacimiento"], r["direccion"], r["madre_nombre"], r["madre_telefono"], r["madre_email"],
            r["padre_nombre"], r["padre_telefono"], r["padre_email"], r["observaciones_generales"]
        ])
        
    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8-sig'))
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name=f"alumnos_export_{date.today()}.csv",
        mimetype='text/csv'
    )

@alumnos_bp.route("/api/alumnos/plantilla")
def descargar_plantilla_alumnos():
    si = io.StringIO()
    cw = csv.writer(si, delimiter=';')
    cw.writerow(["Nombre", "No Comedor (0/1)", "Días Comedor (0,1,2,3,4)", "Fecha Nacimiento (YYYY-MM-DD)", "Dirección", "Madre", "Tel Madre", "Email Madre", "Padre", "Tel Padre", "Email Padre", "Observaciones"])
    cw.writerow(["Juan Pérez", "0", "0,2,4", "2015-05-20", "Calle Falsa 123", "Maria", "600111222", "m@example.com", "Pepe", "600333444", "p@example.com", "Alérgico al polen"])
    
    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8-sig'))
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name="plantilla_alumnos.csv",
        mimetype='text/csv'
    )
