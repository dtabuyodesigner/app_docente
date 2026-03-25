from flask import Blueprint, jsonify, request, send_file, session
from utils.db import get_db
import os
import io
import csv
import json
import re
from datetime import datetime, date
from utils.security import sanitize_input

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

    grupo_id = session.get('active_group_id')
    if not grupo_id:
        return jsonify([])

    cur.execute("""
        SELECT a.id, a.nombre AS student_name, a.no_comedor, a.comedor_dias, a.foto, a.tiene_ayuda_material,
               f.madre_telefono, f.padre_telefono
        FROM alumnos a
        LEFT JOIN ficha_alumno f ON a.id = f.alumno_id
        WHERE a.grupo_id = ? AND a.deleted_at IS NULL
        ORDER BY a.nombre
    """, (grupo_id,))

    rows = cur.fetchall()
    alumnos = []
    for r in rows:
        # Debug print to app.log
        # print(f"DEBUG: Enviando alumno ID {r['id']} con nombre: |{r['student_name']}|", flush=True)
        alumnos.append({
            "id": r["id"],
            "nombre": r["student_name"] or "",
            "no_comedor": r["no_comedor"],
            "comedor_dias": r["comedor_dias"],
            "foto": r["foto"],
            "tiene_ayuda_material": r["tiene_ayuda_material"],
            "madre_telefono": str(r["madre_telefono"]) if r["madre_telefono"] else "",
            "padre_telefono": str(r["padre_telefono"]) if r["padre_telefono"] else ""
        })

    return jsonify(alumnos)

@alumnos_bp.route("/api/alumnos/por-grupo/<int:grupo_id_param>")
def alumnos_por_grupo(grupo_id_param):
    """Get students for a specific group (used by Quick Loan modal)."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, nombre
        FROM alumnos
        WHERE grupo_id = ? AND deleted_at IS NULL
        ORDER BY nombre
    """, (grupo_id_param,))
    alumnos = [{"id": r["id"], "nombre": r["nombre"]} for r in cur.fetchall()]
    return jsonify(alumnos)

@alumnos_bp.route("/api/alumnos/nuevo", methods=["POST"])
def nuevo_alumno():
    d = request.json
    nombre = sanitize_input(d.get("nombre"))
    no_comedor = int(d.get("no_comedor", 0))
    comedor_dias = d.get("comedor_dias")

    # Campos de la ficha
    f_nac = d.get("fecha_nacimiento")
    direccion = sanitize_input(d.get("direccion"))
    m_nom = sanitize_input(d.get("madre_nombre"))
    m_tel = sanitize_input(d.get("madre_telefono"))
    m_email = sanitize_input(d.get("madre_email"))
    p_nom = sanitize_input(d.get("padre_nombre"))
    p_tel = sanitize_input(d.get("padre_telefono"))
    p_email = sanitize_input(d.get("padre_email"))
    obs = sanitize_input(d.get("observaciones_generales"))
    autorizados = sanitize_input(d.get("personas_autorizadas"))

    if not nombre:
        return jsonify({"ok": False, "error": "El nombre es obligatorio"}), 400

    err = _check_validaciones(f_nac, m_tel, m_email, p_tel, p_email)
    if err:
        return jsonify({"ok": False, "error": err}), 400

    grupo_id = session.get('active_group_id')
    if not grupo_id:
        return jsonify({"ok": False, "error": "No hay grupo seleccionado"}), 400

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        cur.execute("INSERT INTO alumnos (nombre, no_comedor, comedor_dias, grupo_id) VALUES (?, ?, ?, ?)", 
                    (nombre, no_comedor, comedor_dias, grupo_id))
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
    nombre = sanitize_input(d.get("nombre"))
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

        # Actualizar o insertar ficha_alumno
        cur.execute("SELECT alumno_id FROM ficha_alumno WHERE alumno_id = ?", (alumno_id,))
        if cur.fetchone():
            cur.execute("""
                UPDATE ficha_alumno SET
                    fecha_nacimiento = ?, direccion = ?,
                    madre_nombre = ?, madre_telefono = ?, madre_email = ?,
                    padre_nombre = ?, padre_telefono = ?, padre_email = ?,
                    personas_autorizadas = ?
                WHERE alumno_id = ?
            """, (
                d.get("fecha_nacimiento", ""),
                sanitize_input(d.get("direccion", "")),
                sanitize_input(d.get("madre_nombre", "")),
                d.get("madre_telefono", ""),
                d.get("madre_email", ""),
                sanitize_input(d.get("padre_nombre", "")),
                d.get("padre_telefono", ""),
                d.get("padre_email", ""),
                d.get("personas_autorizadas", ""),
                alumno_id
            ))
        else:
            cur.execute("""
                INSERT INTO ficha_alumno
                    (alumno_id, fecha_nacimiento, direccion,
                     madre_nombre, madre_telefono, madre_email,
                     padre_nombre, padre_telefono, padre_email,
                     personas_autorizadas)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alumno_id,
                d.get("fecha_nacimiento", ""),
                sanitize_input(d.get("direccion", "")),
                sanitize_input(d.get("madre_nombre", "")),
                d.get("madre_telefono", ""),
                d.get("madre_email", ""),
                sanitize_input(d.get("padre_nombre", "")),
                d.get("padre_telefono", ""),
                d.get("padre_email", ""),
                d.get("personas_autorizadas", "")
            ))

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
        # Soft delete: sólo marcamos como borrado
        cur.execute("UPDATE alumnos SET deleted_at = CURRENT_TIMESTAMP WHERE id = ?", (alumno_id,))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Error en borrar_alumno:", str(e))
        return jsonify({"ok": False, "error": "Error interno al borrar el alumno."}), 500

    return jsonify({"ok": True, "mensaje": "Alumno archivado correctamente."})

@alumnos_bp.route("/api/alumnos/<int:alumno_id>/foto", methods=["POST"])
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
            sanitize_input(d.get("direccion", "")),
            sanitize_input(d.get("madre_nombre", "")),
            sanitize_input(d.get("madre_telefono", "")),
            sanitize_input(d.get("madre_email", "")),
            sanitize_input(d.get("padre_nombre", "")),
            sanitize_input(d.get("padre_telefono", "")),
            sanitize_input(d.get("padre_email", "")),
            sanitize_input(d.get("observaciones_generales", "")),
            sanitize_input(d.get("personas_autorizadas", ""))
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

@alumnos_bp.route("/api/alumnos/<int:alumno_id>/transferir", methods=["PUT"])
def transferir_alumno(alumno_id):
    data = request.json
    nuevo_grupo_id = data.get("nuevo_grupo_id")
    if not nuevo_grupo_id:
        return jsonify({"ok": False, "error": "Falta el nuevo grupo ID"}), 400

    conn = get_db()
    cur = conn.cursor()
    try:
        # Prevent transferring to a group not owned by the active professor
        if 'profesor_id' in session:
            cur.execute("SELECT id FROM grupos WHERE id = ? AND profesor_id = ?", (nuevo_grupo_id, session['profesor_id']))
            if not cur.fetchone():
                return jsonify({"ok": False, "error": "El nuevo grupo no te pertenece o no existe."}), 403

        cur.execute("UPDATE alumnos SET grupo_id = ? WHERE id = ?", (nuevo_grupo_id, alumno_id))
        conn.commit()
        return jsonify({"ok": True, "mensaje": "Alumno transferido con éxito."})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@alumnos_bp.route("/api/alumnos/exportar/json")
def exportar_alumnos_json():
    conn = get_db()
    cur = conn.cursor()
    grupo_id = session.get('active_group_id')
    
    cur.execute("""
        SELECT a.id, a.nombre, a.no_comedor, a.comedor_dias, 
               f.fecha_nacimiento, f.direccion, f.madre_nombre, f.madre_telefono, f.madre_email,
               f.padre_nombre, f.padre_telefono, f.padre_email, f.observaciones_generales
        FROM alumnos a
        LEFT JOIN ficha_alumno f ON a.id = f.alumno_id
        WHERE a.grupo_id = ?
    """, (grupo_id,))
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
    grupo_id = session.get('active_group_id')
    cur.execute("""
        SELECT a.id, a.nombre, a.no_comedor, a.comedor_dias, 
               f.fecha_nacimiento, f.direccion, f.madre_nombre, f.madre_telefono, f.madre_email,
               f.padre_nombre, f.padre_telefono, f.padre_email, f.observaciones_generales
        FROM alumnos a
        LEFT JOIN ficha_alumno f ON a.id = f.alumno_id
        WHERE a.grupo_id = ?
    """, (grupo_id,))
    rows = cur.fetchall()
    
    # Generate CSV
    si = io.StringIO()
    cw = csv.writer(si, delimiter=';')
    cw.writerow(["Nombre", "No Comedor", "Días Comedor", "Fecha Nacimiento", "Dirección", 
                 "Madre", "Tel Madre", "Email Madre", "Padre", "Tel Padre", "Email Padre", "Observaciones"])
    
    for r in rows:
        cw.writerow([
            r["nombre"], r["no_comedor"], r["comedor_dias"],
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

@alumnos_bp.route("/api/alumnos/importar", methods=["POST"])
def importar_alumnos_csv():
    grupo_id = session.get('active_group_id')
    if not grupo_id:
        return jsonify({"ok": False, "error": "No hay grupo activo seleccionado"}), 400

    if 'file' not in request.files:
        return jsonify({"ok": False, "error": "No se recibió ningún archivo"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"ok": False, "error": "Archivo vacío"}), 400

    try:
        raw = file.read()
        content = None
        for enc in ('utf-8-sig', 'utf-8', 'latin-1'):
            try:
                content = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            return jsonify({"ok": False, "error": "No se pudo decodificar el archivo"}), 400

        reader = csv.reader(io.StringIO(content), delimiter=';')
        rows = list(reader)

        if not rows:
            return jsonify({"ok": False, "error": "El archivo está vacío"}), 400

        data_rows = rows[1:]  # Skip header

        conn = get_db()
        importados = 0
        omitidos = 0
        errores = []

        for i, row in enumerate(data_rows, start=2):
            if not row or all(c.strip() == '' for c in row):
                continue

            try:
                def col(idx, default=''):
                    return row[idx].strip() if idx < len(row) else default

                nombre = sanitize_input(col(0))
                if not nombre:
                    omitidos += 1
                    errores.append(f"Fila {i}: nombre vacío, omitida.")
                    continue

                no_comedor = int(col(1, '0') or '0')
                comedor_dias = col(2) or None
                f_nac = col(3) or None
                direccion = sanitize_input(col(4))
                m_nom = sanitize_input(col(5))
                m_tel = sanitize_input(col(6))
                m_email = sanitize_input(col(7))
                p_nom = sanitize_input(col(8))
                p_tel = sanitize_input(col(9))
                p_email = sanitize_input(col(10))
                obs = sanitize_input(col(11))

                err_val = _check_validaciones(f_nac, m_tel, m_email, p_tel, p_email)
                if err_val:
                    omitidos += 1
                    errores.append(f"Fila {i} ({nombre}): {err_val}")
                    continue

                cur = conn.cursor()
                cur.execute("BEGIN")
                cur.execute(
                    "INSERT INTO alumnos (nombre, no_comedor, comedor_dias, grupo_id) VALUES (?, ?, ?, ?)",
                    (nombre, no_comedor, comedor_dias, grupo_id)
                )
                alumno_id = cur.lastrowid
                cur.execute("""
                    INSERT INTO ficha_alumno (
                        alumno_id, fecha_nacimiento, direccion, madre_nombre,
                        madre_telefono, madre_email, padre_nombre, padre_telefono, padre_email,
                        observaciones_generales, personas_autorizadas
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (alumno_id, f_nac, direccion, m_nom, m_tel, m_email, p_nom, p_tel, p_email, obs, ''))
                conn.commit()
                importados += 1

            except Exception as e:
                conn.rollback()
                omitidos += 1
                errores.append(f"Fila {i}: error interno — {str(e)}")

        return jsonify({
            "ok": True,
            "importados": importados,
            "omitidos": omitidos,
            "errores": errores
        })

    except Exception as e:
        return jsonify({"ok": False, "error": f"Error procesando el archivo: {str(e)}"}), 500
