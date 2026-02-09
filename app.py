from flask import Flask, jsonify, request, send_from_directory, Response, redirect, url_for, session
import sqlite3
from datetime import datetime, date
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
import pandas as pd
import os
import json
import csv
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

app = Flask(__name__)
app.secret_key = 'tu-clave-secreta-super-segura-cambiala'  # Cambiar en producción

# -------------------------------------------------
# CONFIG
# -------------------------------------------------

DB_PATH = "app_evaluar.db"

# Google Calendar API Configuration
SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

def get_db():
    return sqlite3.connect(DB_PATH)

def nivel_a_nota(nivel):
    """Convierte un nivel (1-4) en una nota numérica (0-10)"""
    # Mapeo simple de ejemplo. Ajustar según criterio real.
    mapping = {1: 2.5, 2: 5.0, 3: 7.5, 4: 10.0}
    return mapping.get(nivel, 0.0)



# -------------------------------------------------
# INICIO
# -------------------------------------------------

@app.route("/")
def inicio():
    return send_from_directory("static", "index.html")

@app.route("/alumnos")
def alumnos_page():
    return send_from_directory("static", "alumnos.html")

@app.route("/asistencia")
def asistencia_page():
    return send_from_directory("static", "asistencia.html")

@app.route("/evaluacion")
def evaluacion_page():
    return send_from_directory("static", "evaluacion.html")

@app.route("/informes")
def informes_page():
    return send_from_directory("static", "informes.html")

@app.route("/programacion")
def programacion_page():
    return send_from_directory("static", "programacion.html")

@app.route("/rubricas")
def rubricas_page():
    return send_from_directory("static", "rubricas.html")

@app.route("/diario")
def diario_page():
    return send_from_directory("static", "diario.html")

@app.route("/reuniones")
def reuniones_page():
    return send_from_directory('static', 'reuniones.html')


# -------------------------------------------------
# ALUMNOS
# -------------------------------------------------

@app.route("/api/alumnos")
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
            "id": r[0],
            "nombre": r[1],
            "no_comedor": r[2],
            "comedor_dias": r[3],
            "foto": r[4]
        }
        for r in cur.fetchall()
    ]

    conn.close()
    return jsonify(alumnos)


@app.route("/api/alumnos/nuevo", methods=["POST"])
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
        return jsonify({"ok": False, "error": "Nombre es obligatorio"}), 400

    conn = get_db()
    cur = conn.cursor()
    try:
        # 1. Insertar en alumnos
        cur.execute("INSERT INTO alumnos (nombre, no_comedor, comedor_dias) VALUES (?, ?, ?)", 
                    (nombre, no_comedor, comedor_dias))
        alumno_id = cur.lastrowid
        
        # 2. Insertar en ficha_alumno
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
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()


# -------------------------------------------------
# IMPORTAR ALUMNOS POR CSV
# -------------------------------------------------

@app.route("/api/alumnos/plantilla")
def descargar_plantilla_alumnos():
    output = io.StringIO()
    writer = csv.writer(output)
    # Cabeceras
    writer.writerow([
        "Nombre", 
        "Fecha Nacimiento", 
        "Dirección", 
        "Madre Nombre", 
        "Madre Teléfono", 
        "Padre Nombre", 
        "Padre Teléfono", 
        "Observaciones Generales", 
        "Personas Autorizadas",
        "Días Comedor (0-4 separados por comas)"
    ])
    # Ejemplo
    writer.writerow([
        "Ejemplo Alumno", 
        "2018-05-15", 
        "Calle Mayor 1", 
        "Carmen", 
        "611223344", 
        "Alberto", 
        "655443322", 
        "Sin alergias", 
        "Abuela Maria",
        "0,1,2,3,4"
    ])
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=plantilla_alumnos.csv"}
    )

@app.route("/api/alumnos/importar", methods=["POST"])
def importar_alumnos_csv():
    if 'file' not in request.files:
        return jsonify({"ok": False, "error": "No hay archivo"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"ok": False, "error": "Nombre de archivo vacío"}), 400

    try:
        # Use StringIO handle decode
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        reader = csv.DictReader(stream)
        
        conn = get_db()
        cur = conn.cursor()
        count = 0
        
        for row in reader:
            nombre = row.get("Nombre")
            if not nombre: continue # Saltar filas vacías
            
            f_nac = row.get("Fecha Nacimiento")
            direccion = row.get("Dirección")
            m_nom = row.get("Madre Nombre")
            m_tel = row.get("Madre Teléfono")
            p_nom = row.get("Padre Nombre")
            p_tel = row.get("Padre Teléfono")
            obs = row.get("Observaciones Generales")
            autorizados = row.get("Personas Autorizadas")
            dias = row.get("Días Comedor (0-4 separados por comas)") or ""
            
            no_comedor = 0 if dias else 1
            
            # Insertar alumno
            cur.execute("INSERT INTO alumnos (nombre, no_comedor, comedor_dias) VALUES (?, ?, ?)",
                        (nombre, no_comedor, dias))
            alumno_id = cur.lastrowid
            
            # Insertar ficha
            cur.execute("""
                INSERT INTO ficha_alumno (
                    alumno_id, fecha_nacimiento, direccion, madre_nombre, 
                    madre_telefono, padre_nombre, padre_telefono, 
                    observaciones_generales, personas_autorizadas
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (alumno_id, f_nac, direccion, m_nom, m_tel, p_nom, p_tel, obs, autorizados))
            
            count += 1
            
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "count": count})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


def subir_foto_alumno(alumno_id):
    if 'foto' not in request.files:
        return jsonify({"ok": False, "error": "No file part"}), 400
    
    file = request.files['foto']
    if file.filename == '':
        return jsonify({"ok": False, "error": "No selected file"}), 400

    if file:
        filename = f"alumno_{alumno_id}_{int(datetime.now().timestamp())}.jpg"
        filepath = os.path.join("static", "uploads", filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        file.save(filepath)

        # Update DB
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE alumnos SET foto = ? WHERE id = ?", (filename, alumno_id))
        conn.commit()
        conn.close()

        return jsonify({"ok": True, "foto": filename})
    
    return jsonify({"ok": False, "error": "Error desconocido"}), 500


@app.route("/api/alumnos/<int:alumno_id>", methods=["PUT"])
def editar_alumno_info(alumno_id):
    d = request.json
    nombre = d.get("nombre")
    no_comedor = int(d.get("no_comedor", 0))
    comedor_dias = d.get("comedor_dias")

    if not nombre:
        return jsonify({"ok": False, "error": "Nombre es obligatorio"}), 400

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE alumnos
            SET nombre = ?, no_comedor = ?, comedor_dias = ?
            WHERE id = ?
        """, (nombre, no_comedor, comedor_dias, alumno_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()

    return jsonify({"ok": True})


@app.route("/api/alumnos/<int:alumno_id>", methods=["DELETE"])
def borrar_alumno(alumno_id):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        # 1. Recopilar datos para backup
        backup_data = {}
        
        # Datos básicos
        cur.execute("SELECT * FROM alumnos WHERE id = ?", (alumno_id,))
        alumno = cur.fetchone()
        if not alumno:
            return jsonify({"ok": False, "error": "Alumno no encontrado"}), 404
        backup_data["alumno"] = dict(alumno)
        
        # Ficha
        cur.execute("SELECT * FROM ficha_alumno WHERE alumno_id = ?", (alumno_id,))
        ficha = cur.fetchone()
        backup_data["ficha"] = dict(ficha) if ficha else None
        
        # Asistencia
        cur.execute("SELECT * FROM asistencia WHERE alumno_id = ?", (alumno_id,))
        backup_data["asistencia"] = [dict(r) for r in cur.fetchall()]
        
        # Evaluaciones
        cur.execute("SELECT * FROM evaluaciones WHERE alumno_id = ?", (alumno_id,))
        backup_data["evaluaciones"] = [dict(r) for r in cur.fetchall()]
        
        # Observaciones
        cur.execute("SELECT * FROM observaciones WHERE alumno_id = ?", (alumno_id,))
        backup_data["observaciones"] = [dict(r) for r in cur.fetchall()]

        # 2. Guardar backup en archivo
        os.makedirs("backups/borrados", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_safe = "".join(c for c in alumno["nombre"] if c.isalnum() or c in (" ", "_")).strip().replace(" ", "_")
        filename = f"backups/borrados/{timestamp}_{nombre_safe}_id{alumno_id}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=4)

        # 3. Borrado manual en cascada
        cur.execute("DELETE FROM asistencia WHERE alumno_id = ?", (alumno_id,))
        cur.execute("DELETE FROM evaluaciones WHERE alumno_id = ?", (alumno_id,))
        cur.execute("DELETE FROM ficha_alumno WHERE alumno_id = ?", (alumno_id,))
        cur.execute("DELETE FROM observaciones WHERE alumno_id = ?", (alumno_id,))
        cur.execute("DELETE FROM informe_observaciones WHERE alumno_id = ?", (alumno_id,))
        
        # Borrar alumno
        cur.execute("DELETE FROM alumnos WHERE id = ?", (alumno_id,))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()

    return jsonify({"ok": True})


# -------------------------------------------------
# ASISTENCIA POR FECHA
# -------------------------------------------------

@app.route("/api/asistencia/hoy")
def asistencia_hoy():
    fecha = request.args.get("fecha", date.today().isoformat())

    conn = get_db()
    cur = conn.cursor()

    # Determine weekday (0=Mon, 6=Sun)
    day_of_week = str(date.fromisoformat(fecha).weekday())

    cur.execute("""
        SELECT 
            a.id,
            a.nombre,
            a.no_comedor,
            a.comedor_dias,
            COALESCE(asist.estado, 'presente') AS estado,
            asist.id AS asistencia_id,
            asist.comedor AS asist_comedor,
            asist.tipo_ausencia,
            asist.horas_ausencia
        FROM alumnos a
        LEFT JOIN asistencia asist
            ON asist.alumno_id = a.id
           AND asist.fecha = ?
        ORDER BY a.nombre
    """, (fecha,))

    datos = cur.fetchall()
    conn.close()

    resultado = []
    for (aid, nombre, no_comedor, comedor_dias, estado, asist_id, asist_comedor, tipo_ausencia, horas_ausencia) in datos:
        # Calculate default dining status checking specific days
        if asist_id is not None:
             final_comedor = asist_comedor
        else:
             tipo_ausencia = "dia"
             horas_ausencia = None
             # Logic for default
             if comedor_dias:
                 # Check if today is in the allowed list
                 if day_of_week in comedor_dias.split(','):
                     final_comedor = 1
                 else:
                     final_comedor = 0
             else:
                 # Standard logic
                 final_comedor = 0 if no_comedor == 1 else 1

        resultado.append({
            "id": aid,
            "nombre": nombre,
            "estado": estado,
            "comedor": final_comedor,
            "no_comedor": no_comedor,
            "tipo_ausencia": tipo_ausencia,
            "horas_ausencia": horas_ausencia
        })
    

    return jsonify(resultado)


@app.route("/api/asistencia/mes")
def asistencia_mes():
    mes = request.args.get("mes", date.today().strftime("%Y-%m"))
    # mes format "YYYY-MM"

    conn = get_db()
    cur = conn.cursor()

    # Get all attendance records for that month
    cur.execute("""
        SELECT 
            a.nombre,
            asist.estado,
            asist.fecha
        FROM alumnos a
        JOIN asistencia asist ON asist.alumno_id = a.id
        WHERE strftime('%Y-%m', asist.fecha) = ?
          AND asist.estado IN ('retraso', 'falta_justificada', 'falta_no_justificada')
        ORDER BY a.nombre, asist.fecha
    """, (mes,))

    datos = cur.fetchall()
    conn.close()

    # Process data
    resumen = {}
    for nombre, estado, fecha in datos:
        if nombre not in resumen:
            resumen[nombre] = {
                "nombre": nombre,
                "retrasos": 0,
                "justificadas": 0,
                "injustificadas": 0,
                "detalles": []
            }
        
        entry = resumen[nombre]
        if estado == 'retraso':
            entry['retrasos'] += 1
        elif estado == 'falta_justificada':
            entry['justificadas'] += 1
        elif estado == 'falta_no_justificada':
            entry['injustificadas'] += 1
        
        entry['detalles'].append({
            "fecha": fecha,
            "estado": estado
        })

    # Convert to list and sort by total incidents descending
    lista = list(resumen.values())
    lista.sort(key=lambda x: (x['injustificadas'] + x['justificadas'] + x['retrasos']), reverse=True)

    return jsonify(lista)


# -------------------------------------------------
# GUARDAR ASISTENCIA
# -------------------------------------------------

@app.route("/api/asistencia", methods=["POST"])
def guardar_asistencia():
    d = request.json

    alumno_id = d["alumno_id"]
    fecha = d.get("fecha", date.today().isoformat())
    estado = d.get("estado", "presente")

    conn = get_db()
    cur = conn.cursor()

    # saber si normalmente va a comedor
    cur.execute("SELECT no_comedor FROM alumnos WHERE id = ?", (alumno_id,))
    no_comedor = cur.fetchone()[0]

    # If updating status, get current comedor or default
    # If updating comedor, get current status or default
    cur.execute("SELECT estado, comedor FROM asistencia WHERE alumno_id = ? AND fecha = ?", (alumno_id, fecha))
    row = cur.fetchone()
    
    current_estado = row[0] if row else "presente"
    current_comedor = row[1] if row else (0 if no_comedor == 1 else 1)

    new_estado = d.get("estado", current_estado)
    new_comedor = d.get("comedor", current_comedor)
    tipo_ausencia = d.get("tipo_ausencia", "dia")
    horas_ausencia = d.get("horas_ausencia")

    # Business rule: if they are absent, they can't eat
    if new_estado in ("falta_justificada", "falta_no_justificada"):
        if tipo_ausencia == "dia":
            new_comedor = 0

    cur.execute("""
        INSERT INTO asistencia (alumno_id, fecha, estado, comedor, tipo_ausencia, horas_ausencia)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(alumno_id, fecha)
        DO UPDATE SET
            estado = excluded.estado,
            comedor = excluded.comedor,
            tipo_ausencia = excluded.tipo_ausencia,
            horas_ausencia = excluded.horas_ausencia
    """, (alumno_id, fecha, new_estado, new_comedor, tipo_ausencia, horas_ausencia))

    conn.commit()
    conn.close()

    return jsonify({"ok": True})


# -------------------------------------------------
# RESUMEN ASISTENCIA
# -------------------------------------------------

@app.route("/api/asistencia/resumen")
def resumen_asistencia():
    fecha = request.args.get("fecha", date.today().isoformat())

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            a.nombre,
            COALESCE(asist.estado, 'presente'),
            asist.tipo_ausencia,
            asist.horas_ausencia
        FROM alumnos a
        LEFT JOIN asistencia asist
            ON asist.alumno_id = a.id
           AND asist.fecha = ?
    """, (fecha,))

    filas = cur.fetchall()
    conn.close()

    presentes = 0
    retrasos = 0
    faltas = 0  # Total
    faltas_justificadas = 0
    faltas_injustificadas = 0
    lista_faltan = []

    for nombre, estado, tipo_ausencia, horas_ausencia in filas:
        if estado == "presente":
            presentes += 1
        elif estado == "retraso":
            presentes += 1
            retrasos += 1
        elif estado == "falta_justificada":
            faltas += 1
            faltas_justificadas += 1
            label = nombre
            if tipo_ausencia == "horas" and horas_ausencia:
                h_list = json.loads(horas_ausencia)
                label += f" ({len(h_list)}h J)"
            else:
                label += " (J)"
            lista_faltan.append(label)
        elif estado == "falta_no_justificada":
            faltas += 1
            faltas_injustificadas += 1
            label = nombre
            if tipo_ausencia == "horas" and horas_ausencia:
                h_list = json.loads(horas_ausencia)
                label += f" ({len(h_list)}h NJ)"
            else:
                label += " (NJ)"
            lista_faltan.append(label)
        else:
            faltas += 1
            faltas_injustificadas += 1
            lista_faltan.append(nombre)

    return jsonify({
        "presentes": presentes,
        "retrasos": retrasos,
        "faltan": faltas,
        "faltas_justificadas": faltas_justificadas,
        "faltas_injustificadas": faltas_injustificadas,
        "lista_faltan": lista_faltan
    })


# -------------------------------------------------
# COMEDOR
# -------------------------------------------------

def calculate_comedor_total(conn, fecha_iso):
    cur = conn.cursor()
    # Get day of week (0=Mon, 6=Sun)
    dt = datetime.fromisoformat(fecha_iso)
    weekday = str(dt.weekday())

    # Get students and their attendance/dining settings
    cur.execute("""
        SELECT 
            a.id, 
            a.no_comedor, 
            a.comedor_dias,
            asist.estado,
            asist.comedor,
            asist.tipo_ausencia,
            asist.horas_ausencia
        FROM alumnos a
        LEFT JOIN asistencia asist ON asist.alumno_id = a.id AND asist.fecha = ?
    """, (fecha_iso,))
    
    rows = cur.fetchall()
    total = 0
    
    for r in rows:
        a_id, no_comedor, comedor_dias, estado, as_comedor, tipo_ausencia, horas_ausencia = r  # Note: I need to check if I updated the SELECT in calculate_comedor_total
        
        # If absent (full day), they don't eat (unless explicitly overridden)
        current_state = estado if estado else 'presente'
        current_tipo = tipo_ausencia if tipo_ausencia else 'dia'
        
        # Business rule check:
        # Full day absent (tipo='dia') -> skip (unless overridden by as_comedor)
        # Partial absent (tipo='horas') -> allow (follow dining settings)
        if current_state in ('falta_justificada', 'falta_no_justificada') and current_tipo == 'dia':
            # Only count if explicitly marked as comedor=1 today
            if as_comedor != 1:
                continue
            
        # Determine if they eat
        eats = False
        
        if as_comedor is not None:
            # Explicit daily override
            eats = (as_comedor == 1)
        else:
            # Default logic
            if no_comedor == 1:
                eats = False
            elif comedor_dias:
                # Check specific days. comedor_dias="1,3"
                if weekday in comedor_dias.split(','):
                    eats = True
                else:
                    eats = False
            else:
                # Legacy: if no_comedor=0 and comedor_dias empty -> eats everyday
                eats = True
        
        if eats:
            total += 1
            
    return total

@app.route("/api/comedor/hoy")
def comedor_hoy():
    fecha = request.args.get("fecha", date.today().isoformat())
    conn = get_db()
    total = calculate_comedor_total(conn, fecha)
    conn.close()
    return jsonify({"total": total})


# -------------------------------------------------
# OBSERVACIONES DIARIAS
# -------------------------------------------------

@app.route("/api/observaciones", methods=["POST"])
def guardar_observacion():
    d = request.json
    alumno_id = d["alumno_id"]
    fecha = d.get("fecha", date.today().isoformat())
    texto = d["texto"]
    area_id = d.get("area_id") or None

    conn = get_db()
    cur = conn.cursor()

    # If text is empty, delete if exists
    if not texto.strip():
        if area_id:
            cur.execute("DELETE FROM observaciones WHERE alumno_id = ? AND fecha = ? AND area_id = ?", (alumno_id, fecha, area_id))
        else:
            cur.execute("DELETE FROM observaciones WHERE alumno_id = ? AND fecha = ? AND area_id IS NULL", (alumno_id, fecha))
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "deleted": True})

    # Check if exists
    if area_id:
        cur.execute("SELECT id FROM observaciones WHERE alumno_id = ? AND fecha = ? AND area_id = ?", (alumno_id, fecha, area_id))
    else:
        cur.execute("SELECT id FROM observaciones WHERE alumno_id = ? AND fecha = ? AND area_id IS NULL", (alumno_id, fecha))
    
    row = cur.fetchone()

    if row:
        cur.execute("UPDATE observaciones SET texto = ? WHERE id = ?", (texto, row[0]))
    else:
        cur.execute("""
            INSERT INTO observaciones (alumno_id, fecha, texto, area_id)
            VALUES (?, ?, ?, ?)
        """, (alumno_id, fecha, texto, area_id))

    conn.commit()
    conn.close()

    return jsonify({"ok": True})


@app.route("/api/observaciones/dia")
def obtener_observaciones_dia():
    fecha = request.args.get("fecha", date.today().isoformat())
    area_id = request.args.get("area_id") # Optional

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
        # Default to NULL area (general observations)
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
    for uid, nombre, foto, texto, estado_asi, m_tel, p_tel, m_email, p_email in cur.fetchall():
        data.append({
            "id": uid,
            "nombre": nombre,
            "foto": foto or "",
            "observacion": texto or "",
            "asistencia": estado_asi or "presente",
            "madre_tel": m_tel or "",
            "padre_tel": p_tel or "",
            "madre_email": m_email or "",
            "padre_email": p_email or ""
        })
    
    conn.close()
    return jsonify(data)


@app.route("/api/observaciones/<int:alumno_id>")
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
        {"id": r[0], "fecha": r[1], "texto": r[2]}
        for r in datos
    ])

@app.route("/api/observaciones/<int:obs_id>", methods=["PUT"])
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

@app.route("/api/observaciones/<int:obs_id>", methods=["DELETE"])
def borrar_observacion(obs_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM observaciones WHERE id = ?", (obs_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})
    
    

    
    
# -------------------------------------------------
# DASHBOARD
# -------------------------------------------------

@app.route("/api/dashboard/resumen")
def dashboard_resumen():
    fecha_hoy = date.today().isoformat()
    # MM-DD match for birthdays
    hoy_mm_dd = date.today().strftime("%m-%d")

    conn = get_db()
    cur = conn.cursor()

    # 1. Asistencia
    cur.execute("""
        SELECT 
            SUM(CASE WHEN COALESCE(asist.estado, 'presente') IN ('presente', 'retraso') THEN 1 ELSE 0 END) as presentes,
            SUM(CASE WHEN asist.estado IN ('falta_justificada', 'falta_no_justificada') THEN 1 ELSE 0 END) as faltas
        FROM alumnos a
        LEFT JOIN asistencia asist ON asist.alumno_id = a.id AND asist.fecha = ?
    """, (fecha_hoy,))
    asist_stats = cur.fetchone()

    # 2. Comedor
    comedor_total = calculate_comedor_total(conn, fecha_hoy)

    # 3. Cumpleaños
    cur.execute("""
        SELECT a.nombre 
        FROM ficha_alumno f
        JOIN alumnos a ON a.id = f.alumno_id
        WHERE strftime('%m-%d', f.fecha_nacimiento) = ?
    """, (hoy_mm_dd,))
    cumples = [r[0] for r in cur.fetchall()]

    # 4. Media Clase (último trimestre con datos)
    # 4. Media Clase (último trimestre con datos)
    cur.execute("SELECT MAX(trimestre) FROM evaluaciones")
    ultimo_tri = cur.fetchone()[0] or 1
    
    cur.execute("SELECT AVG(nota) FROM evaluaciones WHERE trimestre = ?", (ultimo_tri,))
    media_clase = cur.fetchone()[0] or 0

    # 5. Asistencia Semanal (Últimos 7 días)
    cur.execute("""
        SELECT fecha, 
               SUM(CASE WHEN estado IN ('presente', 'retraso') THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
        FROM asistencia
        WHERE fecha >= date('now', '-6 days')
        GROUP BY fecha
        ORDER BY fecha ASC
    """)
    asist_semanal = [{"fecha": r[0], "porcentaje": round(r[1], 1)} for r in cur.fetchall()]

    # 6. Distribución de notas (Global del trimestre actual)
    cur.execute("""
        SELECT 
            CASE 
                WHEN nota < 5 THEN 'Insuficiente'
                WHEN nota < 7 THEN 'Suficiente/Bien'
                WHEN nota < 9 THEN 'Notable'
                ELSE 'Sobresaliente'
            END as rango,
            COUNT(*)
        FROM (
            SELECT alumno_id, AVG(nota) as nota
            FROM evaluaciones 
            WHERE trimestre = ?
            GROUP BY alumno_id
        )
        GROUP BY 
            CASE 
                WHEN nota < 5 THEN 'Insuficiente'
                WHEN nota < 7 THEN 'Suficiente/Bien'
                WHEN nota < 9 THEN 'Notable'
                ELSE 'Sobresaliente'
            END
    """, (ultimo_tri,))
    distribucion = {r[0]: r[1] for r in cur.fetchall()}

    # 7. Alertas (Alumnos con >3 faltas este mes o media < 5)
    mes_actual = date.today().strftime("%Y-%m")
    alertas = []

    # Alertas Faltas
    cur.execute("""
        SELECT a.nombre, COUNT(*)
        FROM asistencia ast
        JOIN alumnos a ON a.id = ast.alumno_id
        WHERE strftime('%Y-%m', ast.fecha) = ? 
          AND ast.estado IN ('falta_justificada', 'falta_no_justificada')
        GROUP BY a.id, a.nombre
        HAVING COUNT(*) >= 3
    """, (mes_actual,))
    for nombre, count in cur.fetchall():
        alertas.append(f"⚠️ {nombre} tiene {count} faltas este mes.")

    # Alertas Notas
    cur.execute("""
        SELECT a.nombre, AVG(e.nota)
        FROM evaluaciones e
        JOIN alumnos a ON a.id = e.alumno_id
        WHERE e.trimestre = ?
        GROUP BY a.id, a.nombre
        HAVING AVG(e.nota) < 5
    """, (ultimo_tri,))
    for nombre, media in cur.fetchall():
        alertas.append(f"📉 {nombre} tiene media suspensa ({round(media, 1)}).")

    # 8. Próximas Actividades
    cur.execute("""
        SELECT fecha, actividad
        FROM programacion_diaria
        WHERE fecha >= ?
        ORDER BY fecha ASC
        LIMIT 3
    """, (fecha_hoy,))
    proximas = [{"fecha": r[0], "actividad": r[1]} for r in cur.fetchall()]

    conn.close()

    return jsonify({
        "asistencia": {
            "presentes": asist_stats[0] if asist_stats[0] else 0,
            "faltas": asist_stats[1] if asist_stats[1] else 0
        },
        "comedor": comedor_total,
        "cumples": cumples,
        "media_clase": round(media_clase, 2),
        "trimestre_actual": ultimo_tri,
        "asistencia_semanal": asist_semanal,
        "distribucion_notas": distribucion,
        "alertas": alertas,
        "proximas_actividades": proximas
    })


# -------------------------------------------------
# FICHA DEL ALUMNO (ESTABLE)
# -------------------------------------------------



@app.route("/api/alumnos/progreso/<int:alumno_id>")
def progreso_alumno(alumno_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT e.trimestre, ar.nombre, AVG(e.nota)
        FROM evaluaciones e
        JOIN areas ar ON ar.id = e.area_id
        WHERE e.alumno_id = ?
        GROUP BY e.trimestre, ar.nombre
        ORDER BY e.trimestre ASC, ar.nombre ASC
    """, (alumno_id,))
    rows = cur.fetchall()
    conn.close()
    
    result = {1: [], 2: [], 3: []}
    for tri, area_nombre, media in rows:
        result[tri].append({
            "area": area_nombre,
            "media": round(media, 2)
        })
    
    return jsonify(result)

# -------------------------------------------------
# HORARIO Y COMEDOR (NUEVO)
# -------------------------------------------------

def get_config_value(key):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT valor FROM config WHERE clave = ?", (key,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def set_config_value(key, value):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO config (clave, valor) VALUES (?, ?) ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor", (key, value))
    conn.commit()
    conn.close()

# --- HORARIO ---

@app.route("/horario")
def horario_page():
    return send_from_directory("static", "horario.html")

@app.route("/api/horario")
def get_horario():
    conn = get_db()
    cur = conn.cursor()
    
    # Get manual entries
    tipo = request.args.get("tipo", "clase")
    
    # Get manual entries
    cur.execute("SELECT id, dia, hora_inicio, hora_fin, asignatura, detalles FROM horario WHERE tipo = ? ORDER BY dia, hora_inicio", (tipo,))
    rows = cur.fetchall()
    
    manual = []
    for r in rows:
        manual.append({
            "id": r[0],
            "dia": r[1],
            "hora_inicio": r[2],
            "hora_fin": r[3],
            "asignatura": r[4],
            "detalles": r[5]
        })
    
    # Get image path
    img_path = get_config_value("horario_img_path")
    
    # Get rows config
    rows_config_json = get_config_value("horario_rows")
    if rows_config_json:
        rows_config = json.loads(rows_config_json)
    else:
        # Default configuration if none exists
        rows_config = [
            {"start": "09:00", "end": "10:00"},
            {"start": "10:00", "end": "11:00"},
            {"start": "11:00", "end": "12:00"},
            {"start": "12:00", "end": "13:00"},
            {"start": "13:00", "end": "14:00"},
        ]

    conn.close()
    return jsonify({"manual": manual, "imagen": img_path, "config": rows_config})

@app.route("/api/horario/config", methods=["POST"])
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

@app.route("/api/horario/manual", methods=["POST"])
def save_horario_manual():
    d = request.json
    dia = d.get("dia")
    
    # Enforce integer for dia
    try:
        if dia is not None:
            dia = int(dia)
    except ValueError:
        pass # Let validation fail below if needed
        
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

@app.route("/api/horario/manual/<int:id>", methods=["DELETE"])
def delete_horario_manual(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM horario WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/horario/upload", methods=["POST"])
def upload_horario_img():
    if 'foto' not in request.files:
        return jsonify({"ok": False, "error": "No file part"}), 400
    
    file = request.files['foto']
    if file.filename == '':
        return jsonify({"ok": False, "error": "No selected file"}), 400

    if file:
        filename = f"horario_{int(datetime.now().timestamp())}.jpg"
        filepath = os.path.join("static", "uploads", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        file.save(filepath)
        
        set_config_value("horario_img_path", filename)
        return jsonify({"ok": True, "imagen": filename})
        
    return jsonify({"ok": False}), 500

# --- COMEDOR MENU ---

@app.route("/comedor")
def comedor_page():
    return send_from_directory("static", "comedor.html")

@app.route("/api/comedor/menu")
def get_comedor_menu():
    mes = request.args.get("mes")
    if not mes:
        mes = datetime.now().strftime("%Y-%m")
        
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT imagen FROM menus_comedor WHERE mes = ?", (mes,))
    row = cur.fetchone()
    conn.close()
    
    return jsonify({"imagen": row[0] if row else None, "mes": mes})

@app.route("/api/comedor/menu/upload", methods=["POST"])
def upload_comedor_menu():
    if 'foto' not in request.files:
        return jsonify({"ok": False, "error": "No file part"}), 400
    
    file = request.files['foto']
    mes = request.form.get('mes')
    
    if file.filename == '' or not mes:
        return jsonify({"ok": False, "error": "No selected file or month"}), 400

    if file:
        filename = f"menu_comedor_{mes}_{int(datetime.now().timestamp())}.jpg"
        filepath = os.path.join("static", "uploads", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        file.save(filepath)
        
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("INSERT OR REPLACE INTO menus_comedor (mes, imagen) VALUES (?, ?)", (mes, filename))
            conn.commit()
        except Exception as e:
            conn.rollback()
            return jsonify({"ok": False, "error": str(e)}), 500
        finally:
            conn.close()
            
        return jsonify({"ok": True, "imagen": filename})
        
    return jsonify({"ok": False}), 500



@app.route("/api/alumnos/ficha/<int:alumno_id>")
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
    conn.close()

    if f:
        return jsonify({
            "fecha_nacimiento": f[0] or "",
            "direccion": f[1] or "",
            "madre_nombre": f[2] or "",
            "madre_telefono": f[3] or "",
            "madre_email": f[4] or "",
            "padre_nombre": f[5] or "",
            "padre_telefono": f[6] or "",
            "padre_email": f[7] or "",
            "observaciones_generales": f[8] or "",
            "personas_autorizadas": f[9] or ""
        })
    return jsonify({})

    return jsonify({
        "fecha_nacimiento": "",
        "direccion": "",
        "madre_nombre": "",
        "madre_telefono": "",
        "padre_nombre": "",
        "padre_telefono": "",
        "observaciones_generales": "",
        "personas_autorizadas": ""
    })
# -------------------------------------------------
# GUARDAR FICHA DEL ALUMNO 
# -------------------------------------------------

@app.route("/api/alumnos/ficha", methods=["POST"])
def guardar_ficha_alumno():
    d = request.json
    conn = get_db()
    cur = conn.cursor()

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
    conn.close()
    return jsonify({"ok": True})
# -------------------------------------------------
# BORRAR FICHA DEL ALUMNO 
# -------------------------------------------------
@app.route("/api/alumnos/ficha/<int:alumno_id>", methods=["DELETE"])
def borrar_ficha_alumno(alumno_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM ficha_alumno
        WHERE alumno_id = ?
    """, (alumno_id,))

    conn.commit()
    conn.close()

    return jsonify({"ok": True})
#------------------------
# GUARDAR EVALUACIÓN-----
#------------------------
@app.route("/api/evaluacion", methods=["DELETE"])
def borrar_evaluacion():
    alumno_id = request.args.get("alumno_id")
    sda_id = request.args.get("sda_id")
    trimestre = request.args.get("trimestre")
    if not (alumno_id and sda_id and trimestre):
        return jsonify({"ok": False, "error": "Faltan parametros"}), 400
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM evaluaciones WHERE alumno_id = ? AND sda_id = ? AND trimestre = ?", (alumno_id, sda_id, trimestre))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/evaluacion", methods=["POST"])
def guardar_evaluacion():
    d = request.json

    nivel = int(d["nivel"])
    nota = nivel_a_nota(nivel)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO evaluaciones (
            alumno_id, area_id, trimestre, sda_id, criterio_id,
            nivel, nota
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(alumno_id, criterio_id, sda_id, trimestre)
        DO UPDATE SET
            nivel = excluded.nivel,
            nota = excluded.nota
    """, (
        d["alumno_id"],
        d["area_id"],
        d["trimestre"],
        d["sda_id"],
        d["criterio_id"],
        nivel,
        nota
    ))

    conn.commit()
    conn.close()

    return jsonify({"ok": True})



#---------------------------
# OBTENER EVALUACIÓN SDA----
#---------------------------

@app.route("/api/evaluacion")
def obtener_evaluacion():
    area_id = request.args["area_id"]
    sda_id = request.args["sda_id"]
    trimestre = request.args["trimestre"]

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT alumno_id, criterio_id, nivel
        FROM evaluaciones
        WHERE area_id = ?
          AND sda_id = ?
          AND trimestre = ?
    """, (area_id, sda_id, trimestre))

    datos = cur.fetchall()
    conn.close()

    return jsonify([
        {
            "alumno_id": a,
            "criterio_id": c,
            "nivel": n
        }
        for a, c, n in datos
    ])
#---------------------------
# EVALUACIÓN ÁREAS----------
#---------------------------
@app.route("/api/evaluacion/areas")
def evaluacion_areas():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id, nombre FROM areas ORDER BY nombre")
    datos = cur.fetchall()
    conn.close()

    return jsonify([
        {"id": a[0], "nombre": a[1]}
        for a in datos
    ])
#---------------------------
# EVALUACIÓN SDA----------
#---------------------------
@app.route("/api/evaluacion/sda/<int:area_id>")
def evaluacion_sda(area_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, nombre
        FROM sda
        WHERE area_id = ?
        ORDER BY id
    """, (area_id,))

    datos = cur.fetchall()
    conn.close()

    return jsonify([
        {"id": s[0], "nombre": s[1]}
        for s in datos
    ])
#---------------------------
# EVALUACIÓN CRITERIOS------
#---------------------------
@app.route("/api/evaluacion/criterios/<int:sda_id>")
def evaluacion_criterios(sda_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT c.id, c.codigo, c.descripcion
        FROM criterios c
        JOIN sda_criterios sc ON sc.criterio_id = c.id
        WHERE sc.sda_id = ?
        ORDER BY c.id
    """, (sda_id,))

    datos = cur.fetchall()
    conn.close()

    return jsonify([
        {"id": c[0], "codigo": c[1], "descripcion": c[2]}
        for c in datos
    ])
#---------------------------
# EVALUACIÓN ALUMNO---------
#---------------------------
@app.route("/api/evaluacion/alumno")
def evaluacion_alumno():
    alumno_id = request.args.get("alumno_id")
    sda_id = request.args.get("sda_id")
    trimestre = request.args.get("trimestre")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT criterio_id, nivel
        FROM evaluaciones
        WHERE alumno_id = ?
          AND sda_id = ?
          AND trimestre = ?
    """, (alumno_id, sda_id, trimestre))


    datos = cur.fetchall()
    conn.close()

    return jsonify({
        str(c[0]): c[1]
        for c in datos
    })
#---------------------------
# GUARDAR EVALUACIÓN--------
#---------------------------

#---------------------------
# MEDIA EVALUACIÓN----------
#---------------------------
@app.route("/api/evaluacion/media")
def media_sda():
    alumno_id = request.args.get("alumno_id")
    sda_id = request.args.get("sda_id")
    trimestre = request.args.get("trimestre")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT ROUND(AVG(nota), 2)
        FROM evaluaciones
        WHERE alumno_id = ?
          AND sda_id = ?
          AND trimestre = ?
    """, (alumno_id, sda_id, trimestre))

    media = cur.fetchone()[0]
    conn.close()

    return jsonify({
        "media": media if media is not None else 0
    })


# -------------------------------------------------
# MEDIA DEL ÁREA
# -------------------------------------------------
@app.route("/api/evaluacion/media_area")
def media_area():
    alumno_id = request.args.get("alumno_id")
    area_id = request.args.get("area_id")
    trimestre = request.args.get("trimestre")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT ROUND(AVG(nota), 2)
        FROM evaluaciones
        WHERE alumno_id = ?
          AND area_id = ?
          AND trimestre = ?
    """, (alumno_id, area_id, trimestre))

    media = cur.fetchone()[0]
    conn.close()

    return jsonify({
        "media": media if media is not None else 0
    })



# -------------------------------------------------
# RESUMEN POR ÁREA (ALUMNO)
# -------------------------------------------------
@app.route("/api/evaluacion/resumen_areas")
def resumen_areas_alumno():
    alumno_id = request.args.get("alumno_id")
    trimestre = request.args.get("trimestre")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT a.nombre, ROUND(AVG(e.nota), 2)
        FROM evaluaciones e
        JOIN areas a ON e.area_id = a.id
        WHERE e.alumno_id = ?
          AND e.trimestre = ?
        GROUP BY a.id, a.nombre
        ORDER BY a.nombre
    """, (alumno_id, trimestre))

    datos = cur.fetchall()
    conn.close()

    return jsonify([
        {"area": d[0], "media": d[1]}
        for d in datos
    ])


# -------------------------------------------------
# RESUMEN DE TODAS LAS SDA (ALUMNO)
# -------------------------------------------------
@app.route("/api/evaluacion/resumen_sda_todos")
def resumen_sda_todos():
    alumno_id = request.args.get("alumno_id")
    trimestre = request.args.get("trimestre")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT a.nombre, s.nombre, ROUND(AVG(e.nota), 2)
        FROM evaluaciones e
        JOIN sda s ON e.sda_id = s.id
        JOIN areas a ON e.area_id = a.id
        WHERE e.alumno_id = ?
          AND e.trimestre = ?
        GROUP BY s.id, a.nombre, s.nombre
        ORDER BY a.nombre, s.nombre
    """, (alumno_id, trimestre))

    datos = cur.fetchall()
    conn.close()

    return jsonify([
        {"area": d[0], "sda": d[1], "media": d[2]}
        for d in datos
    ])

# -------------------------------------------------
# OBSERVACIONES DE INFORME
# -------------------------------------------------
@app.route("/api/informe/observacion", methods=["GET"])
def obtener_observacion_informe():
    alumno_id = request.args.get("alumno_id")
    trimestre = request.args.get("trimestre")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT texto
        FROM informe_observaciones
        WHERE alumno_id = ? AND trimestre = ?
    """, (alumno_id, trimestre))

    fila = cur.fetchone()
    conn.close()

    return jsonify({
        "texto": fila[0] if fila else ""
    })

@app.route("/api/informe/observacion", methods=["POST"])
def guardar_observacion_informe():
    d = request.json

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO informe_observaciones (alumno_id, trimestre, texto)
        VALUES (?, ?, ?)
        ON CONFLICT(alumno_id, trimestre)
        DO UPDATE SET texto = excluded.texto
    """, (d["alumno_id"], d["trimestre"], d["texto"]))

    conn.commit()
    conn.close()

    return jsonify({"ok": True})

# -------------------------------------------------
# GENERACIÓN DE INFORME PDF
# -------------------------------------------------
def get_color_nota(nota):
    """Retorna color RGB basado en la nota"""
    if nota < 5:
        return colors.Color(220/255, 53/255, 69/255)  # Rojo
    elif nota < 7:
        return colors.Color(255/255, 193/255, 7/255)  # Amarillo
    else:
        return colors.Color(40/255, 167/255, 69/255)  # Verde

# CUSTOM CANVAS FOR PAGE NUMBERING "X of Y"
class PageNumCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.pages = []

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            self.draw_canvas(page_count)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_canvas(self, page_count):
        # Footer: Page X of Y
        page = f"Página {self._pageNumber} de {page_count}"
        self.saveState()
        self.setFont('Helvetica', 9)
        self.drawRightString(A4[0] - 2*cm, 1*cm, page)
        self.restoreState()

def draw_school_header(canvas, doc):
    canvas.saveState()
    # Header: Name, Location, Date
    canvas.setFont('Helvetica-Bold', 14)
    canvas.drawString(2*cm, A4[1] - 1.5*cm, "CEIP Ayatimas")
    
    canvas.setFont('Helvetica', 10)
    canvas.drawString(2*cm, A4[1] - 2*cm, "Localidad: Valle de Guerra")
    
    curr_date = datetime.now().strftime("%d/%m/%Y")
    canvas.drawRightString(A4[0] - 2*cm, A4[1] - 1.5*cm, f"Fecha: {curr_date}")
    
    # Line
    canvas.setLineWidth(0.5)
    canvas.line(2*cm, A4[1] - 2.2*cm, A4[0] - 2*cm, A4[1] - 2.2*cm)
    canvas.restoreState()

def generar_pdf_alumno(alumno_id, trimestre, buffer):
    """Genera PDF de informe para un alumno"""
    conn = get_db()
    cur = conn.cursor()
    
    # Obtener nombre del alumno
    cur.execute("SELECT nombre FROM alumnos WHERE id = ?", (alumno_id,))
    alumno_nombre = cur.fetchone()[0]
    
    # Crear PDF
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                            rightMargin=2*cm, leftMargin=2*cm, 
                            topMargin=3.5*cm, bottomMargin=2*cm)
    elements = []
    styles = getSampleStyleSheet()
    
    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#333333'),
        spaceAfter=30
    )
    title = Paragraph(f"Informe - {alumno_nombre} - Trimestre {trimestre}", title_style)
    elements.append(title)
    
    # Medias por Área
    cur.execute("""
        SELECT a.nombre, ROUND(AVG(e.nota), 2)
        FROM evaluaciones e
        JOIN areas a ON e.area_id = a.id
        WHERE e.alumno_id = ? AND e.trimestre = ?
        GROUP BY a.id, a.nombre
        ORDER BY a.nombre
    """, (alumno_id, trimestre))
    areas = cur.fetchall()
    
    if areas:
        elements.append(Paragraph("📈 Medias por Área", styles['Heading2']))
        elements.append(Spacer(1, 0.3*cm))
        
        data = [['Área', 'Media']]
        for area, media in areas:
            data.append([area, f"{media:.2f}"])
        
        table = Table(data, colWidths=[12*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        # Aplicar colores a las notas
        for i, (area, media) in enumerate(areas, start=1):
            color = get_color_nota(media)
            table.setStyle(TableStyle([
                ('TEXTCOLOR', (1, i), (1, i), color),
                ('FONTNAME', (1, i), (1, i), 'Helvetica-Bold')
            ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.5*cm))
        
        # Generar gráfica de áreas
        fig, ax = plt.subplots(figsize=(8, 4))
        area_names = [a[0] for a in areas]
        area_medias = [a[1] for a in areas]
        
        # Asignar colores a las barras
        bar_colors = []
        for media in area_medias:
            if media < 5:
                bar_colors.append('#dc3545')  # Rojo
            elif media < 7:
                bar_colors.append('#ffc107')  # Amarillo
            else:
                bar_colors.append('#28a745')  # Verde
        
        bars = ax.barh(area_names, area_medias, color=bar_colors)
        ax.set_xlabel('Media', fontweight='bold')
        ax.set_title('Gráfica de Medias por Área', fontweight='bold', pad=15)
        ax.set_xlim(0, 10)
        ax.grid(axis='x', alpha=0.3)
        
        # Añadir valores en las barras
        for i, (bar, media) in enumerate(zip(bars, area_medias)):
            ax.text(media + 0.2, bar.get_y() + bar.get_height()/2, 
                   f'{media:.2f}', va='center', fontweight='bold')
        
        plt.tight_layout()
        
        # Guardar gráfica en buffer
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150)
        img_buffer.seek(0)
        plt.close(fig)
        
        # Añadir imagen al PDF
        img = Image(img_buffer, width=15*cm, height=7*cm)
        elements.append(img)
        elements.append(Spacer(1, 1*cm))
    
    # Medias por SDA
    cur.execute("""
        SELECT a.nombre, s.nombre, ROUND(AVG(e.nota), 2)
        FROM evaluaciones e
        JOIN sda s ON e.sda_id = s.id
        JOIN areas a ON e.area_id = a.id
        WHERE e.alumno_id = ? AND e.trimestre = ?
        GROUP BY s.id, a.nombre, s.nombre
        ORDER BY a.nombre, s.nombre
    """, (alumno_id, trimestre))
    sdas = cur.fetchall()
    
    if sdas:
        elements.append(Paragraph("📋 Medias por SDA", styles['Heading2']))
        elements.append(Spacer(1, 0.3*cm))
        
        data = [['Área', 'SDA', 'Media']]
        for area, sda, media in sdas:
            data.append([area, sda, f"{media:.2f}"])
        
        table = Table(data, colWidths=[5*cm, 8*cm, 2*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        # Aplicar colores a las notas
        for i, (area, sda, media) in enumerate(sdas, start=1):
            color = get_color_nota(media)
            table.setStyle(TableStyle([
                ('TEXTCOLOR', (2, i), (2, i), color),
                ('FONTNAME', (2, i), (2, i), 'Helvetica-Bold')
            ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.5*cm))
        
        # Generar gráfica de SDAs
        fig, ax = plt.subplots(figsize=(10, max(6, len(sdas) * 0.4)))
        sda_labels = [f"{s[0][:15]}... - {s[1][:30]}..." if len(s[1]) > 30 else f"{s[0][:15]}... - {s[1]}" 
                      for s in sdas]
        sda_medias = [s[2] for s in sdas]
        
        # Asignar colores a las barras
        bar_colors = []
        for media in sda_medias:
            if media < 5:
                bar_colors.append('#dc3545')  # Rojo
            elif media < 7:
                bar_colors.append('#ffc107')  # Amarillo
            else:
                bar_colors.append('#28a745')  # Verde
        
        bars = ax.barh(sda_labels, sda_medias, color=bar_colors)
        ax.set_xlabel('Media', fontweight='bold')
        ax.set_title('Gráfica de Medias por SDA', fontweight='bold', pad=15)
        ax.set_xlim(0, 10)
        ax.grid(axis='x', alpha=0.3)
        
        # Añadir valores en las barras
        for i, (bar, media) in enumerate(zip(bars, sda_medias)):
            ax.text(media + 0.2, bar.get_y() + bar.get_height()/2, 
                   f'{media:.2f}', va='center', fontweight='bold')
        
        plt.tight_layout()
        
        # Guardar gráfica en buffer
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150)
        img_buffer.seek(0)
        plt.close(fig)
        
        # Añadir imagen al PDF
        img = Image(img_buffer, width=15*cm, height=max(9*cm, len(sdas) * 0.6*cm))
        elements.append(img)
        elements.append(Spacer(1, 1*cm))
    
    # --- REGISTRO DE ASISTENCIA ---
    # Mapeo de fechas por trimestre
    fechas_trimestre = {
        "1": ("2025-09-01", "2025-12-31"),
        "2": ("2026-01-01", "2026-03-31"),
        "3": ("2026-04-01", "2026-06-30")
    }
    f_ini, f_fin = fechas_trimestre.get(str(trimestre), ("2000-01-01", "2100-12-31"))

    cur.execute("""
        SELECT estado, COUNT(*)
        FROM asistencia
        WHERE alumno_id = ? AND fecha BETWEEN ? AND ?
        AND estado IN ('retraso', 'falta_justificada', 'falta_no_justificada')
        GROUP BY estado
    """, (alumno_id, f_ini, f_fin))
    
    asist_filas = cur.fetchall()
    asist_dict = {row[0]: row[1] for row in asist_filas}
    
    elements.append(Paragraph("📅 Registro de Asistencia", styles['Heading2']))
    elements.append(Spacer(1, 0.3*cm))
    
    data_asist = [
        ['Tipo de incidencia', 'Total'],
        ['Retrasos', str(asist_dict.get('retraso', 0))],
        ['Faltas Justificadas', str(asist_dict.get('falta_justificada', 0))],
        ['Faltas No Justificadas', str(asist_dict.get('falta_no_justificada', 0))]
    ]
    
    table_asist = Table(data_asist, colWidths=[10*cm, 5*cm])
    table_asist.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table_asist)
    elements.append(Spacer(1, 1*cm))
    
    # Observaciones
    cur.execute("""
        SELECT texto
        FROM informe_observaciones
        WHERE alumno_id = ? AND trimestre = ?
    """, (alumno_id, trimestre))
    obs = cur.fetchone()
    
    if obs and obs[0]:
        elements.append(Paragraph("📝 Observaciones del tutor", styles['Heading2']))
        elements.append(Spacer(1, 0.3*cm))
        elements.append(Paragraph(obs[0], styles['BodyText']))
    
    # --- FIRMA ---
    elements.append(Spacer(1, 2*cm))
    firma_style = ParagraphStyle('FirmaStyle', parent=styles['BodyText'], alignment=2) # Derecha
    elements.append(Paragraph("<b>Fdo: El Tutor / La Tutora</b>", firma_style))
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph("____________________________", firma_style))

    conn.close()
    doc.build(elements, onFirstPage=draw_school_header, onLaterPages=draw_school_header, canvasmaker=PageNumCanvas)

@app.route("/api/informe/pdf_individual")
def pdf_individual():
    alumno_id = request.args.get("alumno_id")
    trimestre = request.args.get("trimestre")
    
    buffer = BytesIO()
    generar_pdf_alumno(alumno_id, trimestre, buffer)
    buffer.seek(0)
    
    return Response(
        buffer.getvalue(),
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename=informe_alumno_{alumno_id}_T{trimestre}.pdf'
        }
    )

@app.route("/api/informe/pdf_general")
def pdf_general():
    trimestre = request.args.get("trimestre")
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM alumnos ORDER BY nombre")
    alumnos = cur.fetchall()
    conn.close()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    for i, (alumno_id,) in enumerate(alumnos):
        if i > 0:
            elements.append(PageBreak())
        
        # Generar contenido para cada alumno
        temp_buffer = BytesIO()
        generar_pdf_alumno(alumno_id, trimestre, temp_buffer)
        
        # Re-generar elementos para este alumno
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("SELECT nombre FROM alumnos WHERE id = ?", (alumno_id,))
        alumno_nombre = cur.fetchone()[0]
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#333333'),
            spaceAfter=30
        )
        title = Paragraph(f"Informe - {alumno_nombre} - Trimestre {trimestre}", title_style)
        elements.append(title)
        
        # Medias por Área
        cur.execute("""
            SELECT a.nombre, ROUND(AVG(e.nota), 2)
            FROM evaluaciones e
            JOIN areas a ON e.area_id = a.id
            WHERE e.alumno_id = ? AND e.trimestre = ?
            GROUP BY a.id, a.nombre
            ORDER BY a.nombre
        """, (alumno_id, trimestre))
        areas = cur.fetchall()
        
        if areas:
            elements.append(Paragraph("📈 Medias por Área", styles['Heading2']))
            elements.append(Spacer(1, 0.3*cm))
            
            data = [['Área', 'Media']]
            for area, media in areas:
                data.append([area, f"{media:.2f}"])
            
            table = Table(data, colWidths=[12*cm, 3*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            for i, (area, media) in enumerate(areas, start=1):
                color = get_color_nota(media)
                table.setStyle(TableStyle([
                    ('TEXTCOLOR', (1, i), (1, i), color),
                    ('FONTNAME', (1, i), (1, i), 'Helvetica-Bold')
                ]))
            
            elements.append(table)
            elements.append(Spacer(1, 1*cm))
        
        # Medias por SDA
        cur.execute("""
            SELECT a.nombre, s.nombre, ROUND(AVG(e.nota), 2)
            FROM evaluaciones e
            JOIN sda s ON e.sda_id = s.id
            JOIN areas a ON e.area_id = a.id
            WHERE e.alumno_id = ? AND e.trimestre = ?
            GROUP BY s.id, a.nombre, s.nombre
            ORDER BY a.nombre, s.nombre
        """, (alumno_id, trimestre))
        sdas = cur.fetchall()
        
        if sdas:
            elements.append(Paragraph("📋 Medias por SDA", styles['Heading2']))
            elements.append(Spacer(1, 0.3*cm))
            
            data = [['Área', 'SDA', 'Media']]
            for area, sda, media in sdas:
                data.append([area, sda, f"{media:.2f}"])
            
            table = Table(data, colWidths=[5*cm, 8*cm, 2*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            for i, (area, sda, media) in enumerate(sdas, start=1):
                color = get_color_nota(media)
                table.setStyle(TableStyle([
                    ('TEXTCOLOR', (2, i), (2, i), color),
                    ('FONTNAME', (2, i), (2, i), 'Helvetica-Bold')
                ]))
            
            elements.append(table)
            elements.append(Spacer(1, 1*cm))
        
        # Observaciones
        cur.execute("""
            SELECT texto
            FROM informe_observaciones
            WHERE alumno_id = ? AND trimestre = ?
        """, (alumno_id, trimestre))
        obs = cur.fetchone()
        
        if obs and obs[0]:
            elements.append(Paragraph("📝 Observaciones del tutor", styles['Heading2']))
            elements.append(Spacer(1, 0.3*cm))
            elements.append(Paragraph(obs[0], styles['BodyText']))
        
        conn.close()
    
    doc.build(elements)
    buffer.seek(0)
    
    return Response(
        buffer.getvalue(),
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename=informe_general_T{trimestre}.pdf'
        }
    )

# -------------------------------------------------
# INFORME DE GRUPO - DATOS Y OBSERVACIONES
# -------------------------------------------------

@app.route("/api/informe/grupo_obs")
def obtener_grupo_obs():
    trimestre = request.args.get("trimestre")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT observaciones, propuestas_mejora, conclusion FROM informe_grupo WHERE trimestre = ?", (trimestre,))
    row = cur.fetchone()
    conn.close()
    if row:
        return jsonify({"observaciones": row[0], "propuestas_mejora": row[1], "conclusion": row[2] or ""})
    return jsonify({"observaciones": "", "propuestas_mejora": "", "conclusion": ""})

@app.route("/api/informe/grupo_obs", methods=["POST"])
def guardar_grupo_obs():
    d = request.json
    trimestre = d.get("trimestre")
    obs = d.get("observaciones", "")
    prop = d.get("propuestas_mejora", "")
    conc = d.get("conclusion", "")
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO informe_grupo (trimestre, observaciones, propuestas_mejora, conclusion)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(trimestre) DO UPDATE SET
            observaciones = excluded.observaciones,
            propuestas_mejora = excluded.propuestas_mejora,
            conclusion = excluded.conclusion
    """, (trimestre, obs, prop, conc))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/informe/grupo_data")
def grupo_data():
    trimestre = int(request.args.get("trimestre", 2))
    conn = get_db()
    cur = conn.cursor()

    # 1. Datos generales
    cur.execute("SELECT COUNT(*) FROM alumnos")
    total_alumnos = cur.fetchone()[0]

    cur.execute("SELECT ROUND(AVG(nota), 2) FROM evaluaciones WHERE trimestre = ?", (trimestre,))
    media_general = cur.fetchone()[0] or 0

    # Evolución (media del trimestre anterior)
    media_anterior = 0
    if trimestre > 1:
        cur.execute("SELECT ROUND(AVG(nota), 2) FROM evaluaciones WHERE trimestre = ?", (trimestre - 1,))
        media_anterior = cur.fetchone()[0] or 0
    
    evolucion = round(media_general - media_anterior, 2) if media_anterior else 0

    # Counts extra
    cur.execute("SELECT COUNT(DISTINCT area_id) FROM evaluaciones WHERE trimestre = ?", (trimestre,))
    num_areas = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT sda_id) FROM evaluaciones WHERE trimestre = ?", (trimestre,))
    num_sdas = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM evaluaciones WHERE trimestre = ?", (trimestre,))
    total_evals = cur.fetchone()[0]

    # 2. Medias por áreas (grupo)
    cur.execute("""
        SELECT a.nombre, ROUND(AVG(e.nota), 2)
        FROM evaluaciones e
        JOIN areas a ON e.area_id = a.id
        WHERE e.trimestre = ?
        GROUP BY a.id
        ORDER BY a.nombre
    """, (trimestre,))
    medias_areas = [{"area": r[0], "media": r[1]} for r in cur.fetchall()]

    # 3. Distribución de niveles Global
    cur.execute("""
        SELECT nivel, COUNT(*)
        FROM evaluaciones
        WHERE trimestre = ?
        GROUP BY nivel
    """, (trimestre,))
    dist_raw = cur.fetchall()
    distribucion_global = {1: 0, 2: 0, 3: 0, 4: 0}
    for nivel, count in dist_raw:
        distribucion_global[nivel] = count

    # 4. SDA Performance
    cur.execute("""
        SELECT a.nombre, s.nombre, ROUND(AVG(e.nota), 2)
        FROM evaluaciones e
        JOIN sda s ON e.sda_id = s.id
        JOIN areas a ON e.area_id = a.id
        WHERE e.trimestre = ?
        GROUP BY s.id
    """, (trimestre,))
    sda_stats = [{"area": r[0], "sda": r[1], "media": r[2]} for r in cur.fetchall()]
    
    mejor_sda = max(sda_stats, key=lambda x: x['media']) if sda_stats else None
    peor_sda = min(sda_stats, key=lambda x: x['media']) if sda_stats else None

    # 6. Distribución de suspensos
    cur.execute("""
        SELECT alumno_id, COUNT(*) as suspensas
        FROM (
            SELECT alumno_id, area_id, AVG(nota) as media_area
            FROM evaluaciones
            WHERE trimestre = ?
            GROUP BY alumno_id, area_id
            HAVING media_area < 5
        )
        GROUP BY alumno_id
    """, (trimestre,))
    suspensos_count = {r[0]: r[1] for r in cur.fetchall()}
    
    cur.execute("SELECT id FROM alumnos")
    todos_id = [r[0] for r in cur.fetchall()]
    
    promocion = {"todo": 0, "una": 0, "dos": 0, "mas_de_dos": 0}
    for aid in todos_id:
        s = suspensos_count.get(aid, 0)
        if s == 0: promocion["todo"] += 1
        elif s == 1: promocion["una"] += 1
        elif s == 2: promocion["dos"] += 1
        else: promocion["mas_de_dos"] += 1
    
    if total_alumnos > 0:
        for k in promocion:
            promocion[k] = {"num": promocion[k], "pct": round(promocion[k] * 100 / total_alumnos, 1)}

    # 7. Asistencia
    fechas = {"1": ("2025-09-01", "2025-12-31"), "2": ("2026-01-01", "2026-03-31"), "3": ("2026-04-01", "2026-06-30")}
    f_ini, f_fin = fechas.get(str(trimestre), ("2000-01-01", "2100-12-31"))
    
    cur.execute("""
        SELECT estado, COUNT(*)
        FROM asistencia
        WHERE fecha BETWEEN ? AND ?
        GROUP BY estado
    """, (f_ini, f_fin))
    asist_raw = {r[0]: r[1] for r in cur.fetchall()}
    f_just = asist_raw.get('falta_justificada', 0)
    f_no_just = asist_raw.get('falta_no_justificada', 0)
    total_faltas = f_just + f_no_just
    total_retrasos = asist_raw.get('retraso', 0)
    media_faltas = round(total_faltas / total_alumnos, 2) if total_alumnos > 0 else 0

    # Alumno con más faltas
    cur.execute("""
        SELECT a.nombre, COUNT(*) as c
        FROM asistencia ast
        JOIN alumnos a ON ast.alumno_id = a.id
        WHERE ast.fecha BETWEEN ? AND ? AND ast.estado LIKE 'falta%'
        GROUP BY ast.alumno_id ORDER BY c DESC LIMIT 1
    """, (f_ini, f_fin))
    top_faltas = cur.fetchone()
    
    # Alumno con más retrasos
    cur.execute("""
        SELECT a.nombre, COUNT(*) as c
        FROM asistencia ast
        JOIN alumnos a ON ast.alumno_id = a.id
        WHERE ast.fecha BETWEEN ? AND ? AND ast.estado = 'retraso'
        GROUP BY ast.alumno_id ORDER BY c DESC LIMIT 1
    """, (f_ini, f_fin))
    top_retrasos = cur.fetchone()

    conn.close()

    res = {
        "generales": {
            "total_alumnos": total_alumnos,
            "media_general": media_general,
            "evolucion": evolucion,
            "num_areas": num_areas,
            "num_sdas": num_sdas,
            "total_evals": total_evals
        },
        "medias_areas": medias_areas,
        "sda_stats": {
            "lista": sda_stats,
            "mejor": mejor_sda,
            "peor": peor_sda
        },
        "promocion": promocion,
        "asistencia": {
            "total_faltas": total_faltas,
            "f_justificada": f_just,
            "f_no_justificada": f_no_just,
            "total_retrasos": total_retrasos,
            "media_faltas": media_faltas,
            "top_faltas": {"nombre": top_faltas[0], "num": top_faltas[1]} if top_faltas else None,
            "top_retrasos": {"nombre": top_retrasos[0], "num": top_retrasos[1]} if top_retrasos else None
        }
    }
    return jsonify(res)

@app.route("/api/informe/asistencia_alumno")
def asistencia_alumno():
    alumno_id = request.args.get("alumno_id")
    trimestre = request.args.get("trimestre")
    
    fechas = {"1": ("2025-09-01", "2025-12-31"), "2": ("2026-01-01", "2026-03-31"), "3": ("2026-04-01", "2026-06-30")}
    f_ini, f_fin = fechas.get(str(trimestre), ("2000-01-01", "2100-12-31"))
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT estado, COUNT(*)
        FROM asistencia
        WHERE alumno_id = ? AND fecha BETWEEN ? AND ?
        GROUP BY estado
    """, (alumno_id, f_ini, f_fin))
    
    datos = {r[0]: r[1] for r in cur.fetchall()}
    conn.close()
    
    return jsonify({
        "f_justificada": datos.get("falta_justificada", 0),
        "f_no_justificada": datos.get("falta_no_justificada", 0),
        "retrasos": datos.get("retraso", 0),
        "total_faltas": datos.get("falta_justificada", 0) + datos.get("falta_no_justificada", 0)
    })

@app.route("/api/informe/asistencia_detalle")
def asistencia_detalle():
    trimestre = request.args.get("trimestre")
    estado = request.args.get("estado")
    
    fechas = {"1": ("2025-09-01", "2025-12-31"), "2": ("2026-01-01", "2026-03-31"), "3": ("2026-04-01", "2026-06-30")}
    f_ini, f_fin = fechas.get(str(trimestre), ("2000-01-01", "2100-12-31"))
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.nombre, ast.fecha
        FROM asistencia ast
        JOIN alumnos a ON a.id = ast.alumno_id
        WHERE ast.fecha BETWEEN ? AND ? AND ast.estado = ?
        ORDER BY ast.fecha DESC, a.nombre ASC
    """, (f_ini, f_fin, estado))
    
    datos = [{"nombre": r[0], "fecha": r[1]} for r in cur.fetchall()]
    conn.close()
    
    return jsonify(datos)

# -------------------------------------------------
# GENERACIÓN DE INFORME PDF GRUPO
# -------------------------------------------------

def generar_conclusion_ia(stats, obs, prop):
    """Generador de conclusión 'IA' basado en reglas"""
    # Esta es una implementación simplificada que simula un análisis inteligente
    media = stats['generales']['media_general']
    evol = stats['generales']['evolucion']
    todo_aprobado = stats['promocion']['todo']['pct']
    faltas = stats['asistencia']['media_faltas']
    
    concl = f"Análisis del Trimestre:\n\n"
    
    if media >= 7:
        concl += "El grupo muestra un rendimiento académico sólido y superior a la media. "
    elif media >= 5:
        concl += "El grupo mantiene un rendimiento estable dentro de la normalidad. "
    else:
        concl += "Se observa un trimestre con dificultades generalizadas en el rendimiento. "
        
    if evol > 0.5:
        concl += "Es destacable la evolución positiva respecto al periodo anterior. "
    elif evol < -0.5:
        concl += "Se detecta un retroceso significativo que requiere atención inmediata. "
        
    concl += f"Un {todo_aprobado}% del alumnado ha superado todas las áreas con éxito. "
    
    if faltas > 5:
        concl += "El absentismo está por encima de lo deseado, lo que impacta directamente en los resultados."
    
    return concl

@app.route("/api/informe/pdf_grupo")
def pdf_grupo():
    trimestre = int(request.args.get("trimestre", 2))
    
    # Obtener datos
    conn = get_db()
    cur = conn.cursor()
    
    # 1. Datos generales
    cur.execute("SELECT COUNT(*) FROM alumnos")
    total_alumnos = cur.fetchone()[0]
    cur.execute("SELECT ROUND(AVG(nota), 2) FROM evaluaciones WHERE trimestre = ?", (trimestre,))
    media_general = cur.fetchone()[0] or 0
    cur.execute("SELECT COUNT(DISTINCT area_id) FROM evaluaciones WHERE trimestre = ?", (trimestre,))
    num_areas = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT sda_id) FROM evaluaciones WHERE trimestre = ?", (trimestre,))
    num_sdas = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM evaluaciones WHERE trimestre = ?", (trimestre,))
    total_evals = cur.fetchone()[0]
    
    # 2. Medias por área
    cur.execute("""
        SELECT a.nombre, ROUND(AVG(e.nota), 2)
        FROM evaluaciones e JOIN areas a ON e.area_id = a.id
        WHERE e.trimestre = ? GROUP BY a.id ORDER BY a.nombre
    """, (trimestre,))
    medias_areas = cur.fetchall()
    
    # 3. Medias por SDA
    cur.execute("""
        SELECT a.nombre, s.nombre, ROUND(AVG(e.nota), 2)
        FROM evaluaciones e
        JOIN sda s ON e.sda_id = s.id
        JOIN areas a ON e.area_id = a.id
        WHERE e.trimestre = ?
        GROUP BY s.id ORDER BY a.nombre, s.nombre
    """, (trimestre,))
    sda_stats = cur.fetchall()
    
    # 4. Análisis de Promoción (Suspensos)
    cur.execute("""
        SELECT alumno_id, COUNT(*) as suspensas
        FROM (
            SELECT alumno_id, area_id, AVG(nota) as media_area
            FROM evaluaciones
            WHERE trimestre = ?
            GROUP BY alumno_id, area_id
            HAVING media_area < 5
        )
        GROUP BY alumno_id
    """, (trimestre,))
    susp_raw = {r[0]: r[1] for r in cur.fetchall()}
    cur.execute("SELECT id FROM alumnos")
    todos_id = [r[0] for r in cur.fetchall()]
    prom = {"todo": 0, "una": 0, "dos": 0, "mas_de_dos": 0}
    for aid in todos_id:
        s = susp_raw.get(aid, 0)
        if s == 0: prom["todo"] += 1
        elif s == 1: prom["una"] += 1
        elif s == 2: prom["dos"] += 1
        else: prom["mas_de_dos"] += 1

    # 5. Asistencia
    fechas = {"1": ("2025-09-01", "2025-12-31"), "2": ("2026-01-01", "2026-03-31"), "3": ("2026-04-01", "2026-06-30")}
    f_ini, f_fin = fechas.get(str(trimestre), ("2000-01-01", "2100-12-31"))
    cur.execute("SELECT estado, COUNT(*) FROM asistencia WHERE fecha BETWEEN ? AND ? GROUP BY estado", (f_ini, f_fin))
    asist_raw = {r[0]: r[1] for r in cur.fetchall()}
    f_just = asist_raw.get('falta_justificada', 0)
    f_no_just = asist_raw.get('falta_no_justificada', 0)
    total_faltas = f_just + f_no_just
    total_retrasos = asist_raw.get('retraso', 0)
    
    cur.execute("""
        SELECT a.nombre, COUNT(*) as c FROM asistencia ast JOIN alumnos a ON ast.alumno_id = a.id
        WHERE ast.fecha BETWEEN ? AND ? AND ast.estado LIKE 'falta%' GROUP BY ast.alumno_id ORDER BY c DESC LIMIT 1
    """, (f_ini, f_fin))
    top_faltas = cur.fetchone()
    cur.execute("""
        SELECT a.nombre, COUNT(*) as c FROM asistencia ast JOIN alumnos a ON ast.alumno_id = a.id
        WHERE ast.fecha BETWEEN ? AND ? AND ast.estado = 'retraso' GROUP BY ast.alumno_id ORDER BY c DESC LIMIT 1
    """, (f_ini, f_fin))
    top_retrasos = cur.fetchone()
    
    # Cualitativos
    cur.execute("SELECT observaciones, propuestas_mejora, conclusion FROM informe_grupo WHERE trimestre = ?", (trimestre,))
    row_qual = cur.fetchone()
    obs_text = row_qual[0] if row_qual else ""
    prop_text = row_qual[1] if row_qual else ""
    conc_text = row_qual[2] if row_qual else ""
    
    # Distribución Personal por Notas (GPA)
    cur.execute("""
        SELECT AVG(nota) as media_alumno 
        FROM evaluaciones WHERE trimestre = ? GROUP BY alumno_id
    """, (trimestre,))
    medias_personales = [r[0] for r in cur.fetchall()]

    conn.close()
    
    # Documento PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=3.5*cm, bottomMargin=2*cm)
    elements = []
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(name='MainTitle', fontSize=18, alignment=1, spaceAfter=20, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='SectionHeader', fontSize=14, spaceBefore=15, spaceAfter=10, textColor=colors.HexColor('#003366'), fontName='Helvetica-Bold'))
    
    # 1. Datos generales
    elements.append(Paragraph("INFORME GENERAL DE LA CLASE", styles['MainTitle']))
    elements.append(Paragraph("🏫 1. Datos generales", styles['SectionHeader']))
    curr_date = datetime.now().strftime("%d/%m/%Y")
    data_gen = [
        ["Curso:", "1.º de Primaria"], ["Grupo:", "A"], ["Tutor/a:", "Dani Tabuyo"],
        ["Trimestre:", f"{trimestre}.º"], ["Fecha del informe:", curr_date], ["Número de alumnos:", str(total_alumnos)]
    ]
    t_gen = Table(data_gen, colWidths=[5*cm, 10*cm])
    elements.append(t_gen)
    
    # 2. Resumen global del grupo
    elements.append(Paragraph("📊 2. Resumen global del grupo", styles['SectionHeader']))
    data_res = [
        ["Indicador", "Valor"], ["Media general del grupo", str(media_general)],
        ["Áreas evaluadas", str(num_areas)], ["Situaciones de aprendizaje", str(num_sdas)],
        ["Evaluaciones registradas", str(total_evals)]
    ]
    t_res = Table(data_res, colWidths=[8*cm, 4*cm])
    t_res.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')]))
    elements.append(t_res)
    
    # 3. Medias por área + Gráfica
    elements.append(Paragraph("📘 3. Medias por área", styles['SectionHeader']))
    data_area = [["Área", "Media"]] + [[r[0], str(r[1])] for r in medias_areas]
    t_area = Table(data_area, colWidths=[10*cm, 3*cm])
    t_area.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')]))
    elements.append(t_area)
    
    if medias_areas:
        fig, ax = plt.subplots(figsize=(8, 3.5))
        a_names = [r[0][:20] for r in medias_areas]
        a_vals = [r[1] for r in medias_areas]
        colors_list = ['#dc3545' if v < 5 else '#ffc107' if v < 7 else '#28a745' for v in a_vals]
        ax.barh(a_names, a_vals, color=colors_list)
        ax.set_xlim(0, 10)
        ax.set_title("Medias por Área")
        plt.tight_layout()
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=100)
        img_buffer.seek(0)
        plt.close(fig)
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Image(img_buffer, width=15*cm, height=6.5*cm))

    # 4. Medias por SDA
    elements.append(PageBreak())
    elements.append(Paragraph("📚 4. Medias por Situación de Aprendizaje (SDA)", styles['SectionHeader']))
    data_sda = [["Área", "Situación de Aprendizaje", "Media"]] + [[r[0][:25], r[1][:35], str(r[2])] for r in sda_stats]
    t_sda = Table(data_sda, colWidths=[4*cm, 8.5*cm, 2*cm])
    t_sda.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('FONTSIZE', (0,1), (-1,-1), 9)]))
    elements.append(t_sda)
    
    if sda_stats:
        mejor = max(sda_stats, key=lambda x: x[2])
        peor = min(sda_stats, key=lambda x: x[2])
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(f"<b>⭐ SDA con mejor valoración:</b> {mejor[1]} ({mejor[2]})", styles['BodyText']))
        elements.append(Paragraph(f"<b>⚠️ SDA con mayor dificultad:</b> {peor[1]} ({peor[2]})", styles['BodyText']))

    # 5. Distribución del Alumnado por Notas (GPA Personal)
    elements.append(Paragraph("📈 5. Distribución del Alumnado por Notas", styles['SectionHeader']))
    dist_notas = {"Excl (9-10)": 0, "Not (7-8.9)": 0, "Bien (6-6.9)": 0, "Suff (5-5.9)": 0, "Insuff (<5)": 0}
    for m in medias_personales:
        if m >= 9: dist_notas["Excl (9-10)"] += 1
        elif m >= 7: dist_notas["Not (7-8.9)"] += 1
        elif m >= 6: dist_notas["Bien (6-6.9)"] += 1
        elif m >= 5: dist_notas["Suff (5-5.9)"] += 1
        else: dist_notas["Insuff (<5)"] += 1
    
    data_dist = [["Rango", "Nº Alumnos"]] + [[k, str(v)] for k, v in dist_notas.items()]
    t_dist = Table(data_dist, colWidths=[8*cm, 4*cm])
    t_dist.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')]))
    elements.append(t_dist)

    # 6. Análisis de Promoción + Gráfica
    elements.append(Paragraph("📋 6. Análisis de Promoción", styles['SectionHeader']))
    pct = lambda n: f"{round(n*100/total_alumnos, 1) if total_alumnos else 0}%"
    data_prom = [
        ["Estado", "Nº Alumnos", "%"],
        ["Pasando todo", str(prom["todo"]), pct(prom["todo"])],
        ["Suspendiendo 1", str(prom["una"]), pct(prom["una"])],
        ["Suspendiendo 2", str(prom["dos"]), pct(prom["dos"])],
        ["Suspendiendo +2", str(prom["mas_de_dos"]), pct(prom["mas_de_dos"])]
    ]
    t_prom = Table(data_prom, colWidths=[6*cm, 4*cm, 3*cm])
    t_prom.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')]))
    elements.append(t_prom)
    
    fig, ax = plt.subplots(figsize=(6, 3))
    p_labels = ['Todo OK', '1 Susp', '2 Susp', '>2 Susp']
    p_vals = [prom['todo'], prom['una'], prom['dos'], prom['mas_de_dos']]
    ax.pie(p_vals, labels=p_labels, autopct='%1.1f%%', colors=['#28a745', '#ffc107', '#fd7e14', '#dc3545'])
    ax.set_title("Distribución de Promoción")
    plt.tight_layout()
    img_prom = BytesIO()
    plt.savefig(img_prom, format='png', dpi=100)
    img_prom.seek(0)
    plt.close(fig)
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Image(img_prom, width=10*cm, height=6.5*cm))
    
    # 7. Resumen de asistencia del grupo
    elements.append(PageBreak())
    elements.append(Paragraph("🧍‍♂️ 7. Resumen de asistencia del grupo", styles['SectionHeader']))
    data_asist = [
        ["Indicador", "Total"], ["Total de faltas", str(total_faltas)],
        ["Faltas justificadas", str(f_just)], ["Faltas no justificadas", str(f_no_just)],
        ["Retrasos", str(total_retrasos)], ["Media de faltas por alumno", str(round(total_faltas/total_alumnos, 2) if total_alumnos else 0)],
        ["Máx faltas", f"{top_faltas[0]} ({top_faltas[1]})" if top_faltas else "-"],
        ["Máx retrasos", f"{top_retrasos[0]} ({top_retrasos[1]})" if top_retrasos else "-"]
    ]
    t_asist = Table(data_asist, colWidths=[8*cm, 4*cm])
    t_asist.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')]))
    elements.append(t_asist)
    
    # 8. Valoración general del tutor
    elements.append(Paragraph("📝 8. Valoración general del tutor", styles['SectionHeader']))
    elements.append(Paragraph(obs_text if obs_text else "Sin registrar.", styles['BodyText']))
    
    # 9. Propuestas de mejora
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph("🛠 9. Propuestas de mejora", styles['SectionHeader']))
    elements.append(Paragraph(prop_text if prop_text else "Sin registrar.", styles['BodyText']))
    
    # 10. Conclusión final
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph("✅ 10. Conclusión final", styles['SectionHeader']))
    elements.append(Paragraph(conc_text if conc_text else "Sin registrar.", styles['BodyText']))
    
    doc.build(elements, onFirstPage=draw_school_header, onLaterPages=draw_school_header, canvasmaker=PageNumCanvas)
    buffer.seek(0)
    return Response(buffer.getvalue(), mimetype='application/pdf', headers={'Content-Disposition': f'attachment; filename=informe_grupo_T{trimestre}.pdf'})

# -------------------------------------------------
# GENERACIÓN DE INFORME EXCEL GRUPO
# -------------------------------------------------

@app.route("/api/informe/excel_grupo")
def excel_grupo():
    trimestre = request.args.get("trimestre", "2")
    conn = get_db()
    cur = conn.cursor()

    # Get all areas
    cur.execute("SELECT id, nombre FROM areas ORDER BY nombre")
    areas = cur.fetchall()
    area_ids = [a[0] for a in areas]
    area_nombres = [a[1] for a in areas]

    # Date ranges for attendance
    fechas = {"1": ("2025-09-01", "2025-12-31"), "2": ("2026-01-01", "2026-03-31"), "3": ("2026-04-01", "2026-06-30")}
    f_ini, f_fin = fechas.get(str(trimestre), ("2000-01-01", "2100-12-31"))

    # Get all pupils
    cur.execute("SELECT id, nombre FROM alumnos ORDER BY nombre")
    alumnos = cur.fetchall()

    rows = []
    for aid, nombre in alumnos:
        row = {"Alumno": nombre}
        
        # Area averages
        for area_id, area_nombre in zip(area_ids, area_nombres):
            cur.execute("""
                SELECT ROUND(AVG(nota), 2)
                FROM evaluaciones
                WHERE alumno_id = ? AND area_id = ? AND trimestre = ?
            """, (aid, area_id, trimestre))
            res = cur.fetchone()
            row[area_nombre] = res[0] if res[0] is not None else ""

        # Attendance (Justified and Unjustified)
        cur.execute("""
            SELECT 
                SUM(CASE WHEN estado = 'falta_justificada' THEN 1 ELSE 0 END) as just,
                SUM(CASE WHEN estado = 'falta_no_justificada' THEN 1 ELSE 0 END) as unjust
            FROM asistencia
            WHERE alumno_id = ? AND fecha BETWEEN ? AND ?
        """, (aid, f_ini, f_fin))
        asist = cur.fetchone()
        row["Faltas Justificadas"] = asist[0] if asist[0] else 0
        row["Faltas Injustificadas"] = asist[1] if asist[1] else 0
        
        rows.append(row)

    conn.close()

    df = pd.DataFrame(rows)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=f'Trimestre {trimestre}')
    
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-disposition": f"attachment; filename=Informe_Grupo_T{trimestre}.xlsx"}
    )


# -------------------------------------------------
# CURRÍCULO Y PROGRAMACIÓN (REFRESCADO)
# -------------------------------------------------

@app.route("/api/curricular/full")
def api_curriculo_full():
    """Retorna todo el currículo (Áreas > SDA > Actividades > Criterios)"""
    conn = get_db()
    cur = conn.cursor()
    
    # 1. Áreas
    cur.execute("SELECT id, nombre FROM areas")
    areas = [{"id": r[0], "nombre": r[1], "sdas": []} for r in cur.fetchall()]
    
    for area in areas:
        # 2. SDAs de cada área
        cur.execute("SELECT id, nombre, trimestre FROM sda WHERE area_id = ?", (area["id"],))
        sdas = [{"id": r[0], "nombre": r[1], "trimestre": r[2], "actividades": [], "criterios": []} for r in cur.fetchall()]
        area["sdas"] = sdas
        
        for sda in sdas:
            # 3. Actividades de cada SDA
            cur.execute("SELECT id, nombre, sesiones, descripcion FROM actividades_sda WHERE sda_id = ?", (sda["id"],))
            sda["actividades"] = [
                {"id": r[0], "nombre": r[1], "sesiones": r[2], "descripcion": r[3]} 
                for r in cur.fetchall()
            ]
            
            # 4. Criterios de cada SDA
            cur.execute("""
                SELECT c.id, c.codigo, c.descripcion 
                FROM criterios c
                JOIN sda_criterios sc ON sc.criterio_id = c.id
                WHERE sc.sda_id = ?
            """, (sda["id"],))
            sda["criterios"] = [{"id": r[0], "codigo": r[1], "descripcion": r[2]} for r in cur.fetchall()]
            
    conn.close()
    return jsonify(areas)

@app.route("/api/importar_sda", methods=["POST"])
def api_importar_sda_new():
    import re
    data = request.json
    csv_text = data.get("csv", "")
    lines = csv_text.strip().split("\n")
    
    count = 0
    conn = get_db()
    cur = conn.cursor()
    
    try:
        for line in lines:
            line = line.strip()
            if not line: continue
            # Try splitting by semicolon first, then by tabs or 2+ spaces
            if ";" in line:
                parts = line.split(";")
            else:
                parts = re.split(r'\t|\s{2,}', line)
            
            if len(parts) >= 5:
                area_nom = parts[0].strip()
                sda_nom = parts[1].strip()
                trim_str = parts[2].strip()
                try:
                    trim = int(trim_str)
                except:
                    trim = 1 # fallback
                crit_cod = parts[3].strip()
                crit_desc = parts[4].strip()
                
                # Buscar Área
                cur.execute("SELECT id FROM areas WHERE nombre = ?", (area_nom,))
                area_row = cur.fetchone()
                area_id = None
                if area_row:
                    area_id = area_row[0]
                else:
                    cur.execute("INSERT INTO areas (nombre) VALUES (?)", (area_nom,))
                    area_id = cur.lastrowid
                
                # Buscar o insertar SDA
                cur.execute("SELECT id FROM sda WHERE nombre = ? AND area_id = ?", (sda_nom, area_id))
                sda_row = cur.fetchone()
                sda_id = None
                if sda_row:
                    sda_id = sda_row[0]
                else:
                    cur.execute("INSERT INTO sda (nombre, area_id, trimestre) VALUES (?, ?, ?)", (sda_nom, area_id, trim))
                    sda_id = cur.lastrowid
                
                # Buscar o insertar Criterio
                cur.execute("SELECT id FROM criterios WHERE codigo = ?", (crit_cod,))
                crit_row = cur.fetchone()
                crit_id = None
                if crit_row:
                    crit_id = crit_row[0]
                else:
                    cur.execute("INSERT INTO criterios (codigo, descripcion) VALUES (?, ?)", (crit_cod, crit_desc))
                    crit_id = cur.lastrowid
                
                # Relacionar SDA y Criterio
                cur.execute("SELECT 1 FROM sda_criterios WHERE sda_id = ? AND criterio_id = ?", (sda_id, crit_id))
                if not cur.fetchone():
                    cur.execute("INSERT INTO sda_criterios (sda_id, criterio_id) VALUES (?, ?)", (sda_id, crit_id))
                    count += 1
        
        conn.commit()
        return jsonify({"ok": True, "count": count})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)})
    finally:
        conn.close()

@app.route("/api/importar_actividades", methods=["POST"])
def api_importar_actividades():
    import re
    data = request.json
    csv_text = data.get("csv", "")
    lines = csv_text.strip().split("\n")
    
    count = 0
    conn = get_db()
    cur = conn.cursor()
    
    try:
        for line in lines:
            line = line.strip()
            if not line: continue
            # Try splitting by semicolon first, then by tabs or 2+ spaces
            if ";" in line:
                parts = line.split(";")
            else:
                parts = re.split(r'\t|\s{2,}', line)
                
            if len(parts) >= 3:
                sda_nom = parts[0].strip()
                act_nom = parts[1].strip()
                sesiones_str = parts[2].strip()
                try:
                    sesiones = int(sesiones_str)
                except:
                    sesiones = 1 # fallback
                desc = parts[3].strip() if len(parts) > 3 else ""
                
                # Buscar SDA
                cur.execute("SELECT id FROM sda WHERE nombre = ?", (sda_nom,))
                sda_row = cur.fetchone()
                if sda_row:
                    sda_id = sda_row[0]
                    cur.execute("""
                        INSERT INTO actividades_sda (sda_id, nombre, sesiones, descripcion)
                        VALUES (?, ?, ?, ?)
                    """, (sda_id, act_nom, sesiones, desc))
                    count += 1
        
        conn.commit()
        return jsonify({"ok": True, "count": count})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)})
    finally:
        conn.close()

@app.route("/api/programacion", methods=["GET"])
def api_get_programacion():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.id, p.fecha, p.sda_id, p.actividad, p.observaciones, s.nombre as sda_nombre,
               p.tipo, p.color
        FROM programacion_diaria p
        LEFT JOIN sda s ON p.sda_id = s.id
        ORDER BY p.fecha DESC
    """)
    res = [
        {
            "id": r[0],
            "start": r[1],          # FullCalendar expects 'start'
            "title": r[3] or "Sin título", # FullCalendar expects 'title'
            "sda_id": r[2],
            "actividad": r[3],
            "observaciones": r[4],
            "sda_nombre": r[5],
            "tipo": r[6] or "clase",
            "color": r[7] or "#3788d8",    # Event color
            "allDay": True
        }
        for r in cur.fetchall()
    ]
    conn.close()
    return jsonify(res)

@app.route("/api/programacion", methods=["POST"])
def api_save_programacion():
    d = request.json
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO programacion_diaria (fecha, sda_id, actividad, observaciones, tipo, color)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            d["fecha"], 
            d.get("sda_id") or None, 
            d["actividad"], 
            d.get("observaciones", ""),
            d.get("tipo", "clase"),
            d.get("color", "#3788d8")
        ))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)})
    finally:
        conn.close()
    return jsonify({"ok": True})

@app.route("/api/programacion/<int:id>", methods=["PUT"])
def api_update_programacion(id):
    d = request.json
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE programacion_diaria
            SET fecha = ?, sda_id = ?, actividad = ?, observaciones = ?, tipo = ?, color = ?
            WHERE id = ?
        """, (
            d["fecha"], 
            d.get("sda_id") or None, 
            d["actividad"], 
            d.get("observaciones", ""),
            d.get("tipo", "clase"),
            d.get("color", "#3788d8"),
            id
        ))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)})
    finally:
        conn.close()
    return jsonify({"ok": True})

@app.route("/api/programacion/<int:id>", methods=["DELETE"])
def api_delete_programacion(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM programacion_diaria WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})
# ARRANQUE
# -------------------------------------------------

# -------------------------------------------------
# TAREAS (TO-DO)
# -------------------------------------------------
@app.route("/api/tareas", methods=["GET"])
def get_tareas():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, texto, hecha, fecha FROM tareas ORDER BY hecha ASC, id DESC")
    rows = cur.fetchall()
    conn.close()
    return jsonify([{"id":r[0], "texto":r[1], "hecha":bool(r[2]), "fecha":r[3]} for r in rows])

@app.route("/api/tareas", methods=["POST"])
def add_tarea():
    d = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO tareas (texto, fecha, hecha) VALUES (?, ?, 0)", (d["texto"], d.get("fecha","")))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/tareas/<int:id>", methods=["PUT"])
def toggle_tarea(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE tareas SET hecha = NOT hecha WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/tareas/<int:id>", methods=["DELETE"])
def delete_tarea(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

# -------------------------------------------------
# GESTIÓN DE RÚBRICAS
# -------------------------------------------------

@app.route("/api/rubricas/<int:criterio_id>", methods=["GET"])
def get_rubrica(criterio_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT nivel, descriptor FROM rubricas WHERE criterio_id = ?", (criterio_id,))
    data = {r[0]: r[1] for r in cur.fetchall()}
    conn.close()
    return jsonify(data)

@app.route("/api/rubricas", methods=["POST"])
def save_rubrica():
    data = request.json
    criterio_id = data.get("criterio_id")
    descriptores = data.get("descriptores") # Expects {1: "desc", 2: "desc", ...}
    
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM rubricas WHERE criterio_id = ?", (criterio_id,))
        for nivel, desc in descriptores.items():
            if desc.strip():
                cur.execute("INSERT INTO rubricas (criterio_id, nivel, descriptor) VALUES (?, ?, ?)", 
                           (criterio_id, nivel, desc))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)})
    finally:
        conn.close()

@app.route("/api/rubricas/<int:criterio_id>", methods=["DELETE"])
def delete_rubrica(criterio_id):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM rubricas WHERE criterio_id = ?", (criterio_id,))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)})
    finally:
        conn.close()

@app.route("/api/rubricas/pdf/<int:sda_id>")
def pdf_rubrica(sda_id):
    conn = get_db()
    cur = conn.cursor()
    
    # 1. Get SDA Info
    cur.execute("SELECT nombre, area_id FROM sda WHERE id = ?", (sda_id,))
    sda = cur.fetchone()
    if not sda: return "SDA not found", 404
    sda_nombre = sda[0]
    
    # 2. Get Criteria & Rubrics
    cur.execute("""
        SELECT c.id, c.codigo, c.descripcion
        FROM criterios c
        JOIN sda_criterios sc ON sc.criterio_id = c.id
        WHERE sc.sda_id = ?
    """, (sda_id,))
    criterios = cur.fetchall()
    
    data_criterios = []
    for c in criterios:
        cid, cod, desc = c
        cur.execute("SELECT nivel, descriptor FROM rubricas WHERE criterio_id = ?", (cid,))
        rubs = {r[0]: r[1] for r in cur.fetchall()}
        data_criterios.append({
            "codigo": cod,
            "descripcion": desc,
            "rubricas": rubs
        })
    conn.close()

    # GENERATE PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=1*cm, leftMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph(f"Rúbrica de Evaluación: {sda_nombre}", styles['title']))
    elements.append(Spacer(1, 0.5*cm))
    
    table_data = [["Criterio", "Insuficiente (1)", "Suficiente/Bien (2)", "Notable (3)", "Sobresaliente (4)"]]
    
    style_body = ParagraphStyle('body', fontSize=8, leading=10)
    
    for c in data_criterios:
        row = [
            Paragraph(f"<b>{c['codigo']}</b><br/>{c['descripcion']}", style_body),
            Paragraph(c['rubricas'].get(1, ""), style_body),
            Paragraph(c['rubricas'].get(2, ""), style_body),
            Paragraph(c['rubricas'].get(3, ""), style_body),
            Paragraph(c['rubricas'].get(4, ""), style_body)
        ]
        table_data.append(row)
        
    t = Table(table_data, colWidths=[4*cm, 5.5*cm, 5.5*cm, 5.5*cm, 5.5*cm])
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t)
    
    doc.build(elements)
    buffer.seek(0)
    
    return Response(buffer.getvalue(), mimetype='application/pdf', 
                   headers={'Content-Disposition': f'attachment; filename=Rubrica_{sda_id}.pdf'})


@app.route("/api/dashboard/ultimas_observaciones")
def ultimas_observaciones():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT o.texto, o.fecha, al.nombre as alumno, ar.nombre as area, o.id
        FROM observaciones o
        JOIN alumnos al ON o.alumno_id = al.id
        LEFT JOIN areas ar ON o.area_id = ar.id
        ORDER BY o.fecha DESC, o.id DESC
        LIMIT 5
    """)
    rows = cur.fetchall()
    conn.close()
    
    obs = []
    for row in rows:
        obs.append({
            "texto": row[0],
            "fecha": row[1],
            "alumno": row[2],
            "area": row[3] or "General",
            "id": row[4]
        })
    return jsonify(obs)


@app.route("/api/informe/preview_diario/<int:alumno_id>")
def preview_diario(alumno_id):
    conn = get_db()
    cur = conn.cursor()
    
    # Get Student Info
    cur.execute("SELECT nombre FROM alumnos WHERE id = ?", (alumno_id,))
    alumno = cur.fetchone()
    if not alumno:
        return jsonify({"ok": False, "error": "Alumno no encontrado"}), 404
    nombre_alumno = alumno[0]

    # Get Observations
    cur.execute("""
        SELECT o.fecha, o.texto, a.nombre, o.id
        FROM observaciones o
        LEFT JOIN areas a ON o.area_id = a.id
        WHERE o.alumno_id = ?
        ORDER BY o.fecha DESC, a.nombre ASC
    """, (alumno_id,))
    rows = cur.fetchall()
    conn.close()

    # Group by Date
    data_by_date = {}
    for fecha, texto, area, obs_id in rows:
        if fecha not in data_by_date:
            data_by_date[fecha] = []
        data_by_date[fecha].append({
            "texto": texto,
            "area": area or "Observación General",
            "id": obs_id
        })

    # Format for JSON
    preview_data = []
    for fecha, obs_list in data_by_date.items():
        try:
            d = datetime.strptime(fecha, "%Y-%m-%d")
            fecha_fmt = d.strftime("%d/%m/%Y")
        except:
            fecha_fmt = fecha
        
        preview_data.append({
            "fecha": fecha_fmt,
            "raw_fecha": fecha,
            "observaciones": obs_list
        })

    return jsonify({
        "ok": True,
        "nombre_alumno": nombre_alumno,
        "data": preview_data
    })


@app.route("/api/informe/pdf_diario/<int:alumno_id>")
def generar_pdf_diario(alumno_id):
    conn = get_db()
    cur = conn.cursor()
    
    # Get Student Info
    cur.execute("SELECT nombre FROM alumnos WHERE id = ?", (alumno_id,))
    alumno = cur.fetchone()
    if not alumno:
        return "Alumno no encontrado", 404
    nombre_alumno = alumno[0]

    # Get Observations
    # Grouped by Date descending
    cur.execute("""
        SELECT o.fecha, o.texto, a.nombre
        FROM observaciones o
        LEFT JOIN areas a ON o.area_id = a.id
        WHERE o.alumno_id = ?
        ORDER BY o.fecha DESC, a.nombre ASC
    """, (alumno_id,))
    rows = cur.fetchall()
    conn.close()

    # Group by Date
    data_by_date = {}
    for fecha, texto, area in rows:
        if fecha not in data_by_date:
            data_by_date[fecha] = []
        data_by_date[fecha].append({
            "texto": texto,
            "area": area or "Observación General"
        })

    # PDF Generation
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    elements.append(Paragraph(f"Diario de Clase: {nombre_alumno}", styles['Title']))
    elements.append(Paragraph(f"Fecha Informe: {date.today().strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))

    # Content
    for fecha, obs_list in data_by_date.items():
        # Date Header
        # Format date nicely if possible, else use raw ISO
        try:
            d = datetime.strptime(fecha, "%Y-%m-%d")
            fecha_fmt = d.strftime("%d/%m/%Y")
        except:
            fecha_fmt = fecha
            
        elements.append(Paragraph(f"<b><u>{fecha_fmt}</u></b>", styles['Heading3']))
        
        for obs in obs_list:
            area_text = f"<b>[{obs['area']}]</b>: "
            full_text = area_text + obs['texto']
            elements.append(Paragraph(full_text, styles['Normal']))
            elements.append(Spacer(1, 0.2*cm))
            
        elements.append(Spacer(1, 0.5*cm))
        # Add a line separator
        elements.append(Paragraph("_" * 60, styles['Normal']))
        elements.append(Spacer(1, 0.5*cm))

    if not rows:
        elements.append(Paragraph("No hay observaciones registradas.", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)

    return Response(buffer.getvalue(), mimetype='application/pdf', 
                   headers={'Content-Disposition': f'attachment; filename="Diario_{nombre_alumno}.pdf"'})

# Init Tables
def init_db_tables():
    with app.app_context():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS asistencia (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alumno_id INTEGER NOT NULL,
                fecha TEXT NOT NULL,
                estado TEXT CHECK (estado IN ('presente', 'retraso', 'falta_justificada', 'falta_no_justificada')) NOT NULL,
                comedor INTEGER DEFAULT 1,
                observacion TEXT,
                tipo_ausencia TEXT DEFAULT 'dia',
                horas_ausencia TEXT,
                UNIQUE (alumno_id, fecha),
                FOREIGN KEY (alumno_id) REFERENCES alumnos(id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tareas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                texto TEXT NOT NULL,
                fecha TEXT,
                hecha INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()

try:
    init_db_tables()
except:
    pass



# -------------------------------------------------
# GOOGLE CALENDAR INTEGRATION
# -------------------------------------------------

def get_google_credentials():
    """Get or refresh Google Calendar credentials"""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            return None
    
    return creds

@app.route("/google/authorize")
def google_authorize():
    """Initiate OAuth flow"""
    # Allow insecure transport for local development
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    
    session['state'] = state
    return redirect(authorization_url)

@app.route("/oauth2callback")
def oauth2callback():
    """Handle OAuth callback"""
    # Allow insecure transport for local development
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    
    state = session['state']
    
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        state=state,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    
    flow.fetch_token(authorization_response=request.url)
    
    credentials = flow.credentials
    with open(TOKEN_FILE, 'w') as token:
        token.write(credentials.to_json())
    
    return redirect('/programacion')

@app.route("/api/calendar/status")
def calendar_status():
    """Check if Google Calendar is connected"""
    creds = get_google_credentials()
    return jsonify({
        "connected": creds is not None,
        "token_exists": os.path.exists(TOKEN_FILE)
    })

@app.route("/api/calendar/sync", methods=['POST'])
def calendar_sync():
    """Sync events to Google Calendar"""
    creds = get_google_credentials()
    if not creds:
        return jsonify({"ok": False, "error": "No autorizado. Conecta Google Calendar primero."}), 401
    
    try:
        service = build('calendar', 'v3', credentials=creds)
        
        # Get events from local database
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, fecha, actividad, observaciones, tipo, color
            FROM programacion_diaria
            ORDER BY fecha
        """)
        events = cur.fetchall()
        conn.close()
        
        synced_count = 0
        for event in events:
            event_id, fecha, actividad, observaciones, tipo, color = event
            
            # Create Google Calendar event
            google_event = {
                'summary': actividad,
                'description': observaciones or '',
                'start': {
                    'date': fecha,
                    'timeZone': 'Europe/Madrid',
                },
                'end': {
                    'date': fecha,
                    'timeZone': 'Europe/Madrid',
                },
                'colorId': '1' if tipo == 'examen' else '9' if tipo == 'excursion' else '7',
            }
            
            try:
                service.events().insert(calendarId='primary', body=google_event).execute()
                synced_count += 1
            except Exception as e:
                print(f"Error syncing event {event_id}: {e}")
        
        return jsonify({"ok": True, "synced": synced_count})
    
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/calendar/import", methods=['POST'])
def calendar_import():
    """Import events from Google Calendar"""
    creds = get_google_credentials()
    if not creds:
        return jsonify({"ok": False, "error": "No autorizado"}), 401
    
    try:
        service = build('calendar', 'v3', credentials=creds)
        
        # Get events from Google Calendar (last 60 days + next 90 days)
        from datetime import timedelta
        import datetime as dt_module
        
        # Use simple date format YYYY-MM-DD for consistency
        now = datetime.utcnow()
        start_date = (now - timedelta(days=60)).isoformat() + 'Z'
        end_date = (now + timedelta(days=90)).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_date,
            timeMax=end_date,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        conn = get_db()
        cur = conn.cursor()
        imported_count = 0
        
        for event in events:
            summary = event.get('summary', 'Sin título')
            original_desc = event.get('description', '')
            
            start_data = event['start']
            end_data = event['end']
            
            # Check if it's all-day or timed
            if 'date' in start_data:
                # All-day event
                event_date = start_data['date'] # YYYY-MM-DD
                final_desc = original_desc
            elif 'dateTime' in start_data:
                # Timed event
                raw_start = start_data['dateTime'] # ISO string
                event_date = raw_start.split('T')[0]
                
                # Extract time for description (e.g., "14:30")
                try:
                    # Handle basic ISO format with timezone
                    # Example: 2026-02-04T10:00:00+01:00
                    time_part = raw_start.split('T')[1][:5]
                    time_info = f"[Hora: {time_part}]"
                    final_desc = f"{time_info} {original_desc}".strip()
                except:
                    final_desc = original_desc
            else:
                continue # Unknown format
            
            # Check if event already exists
            cur.execute("SELECT id FROM programacion_diaria WHERE fecha = ? AND actividad = ?", (event_date, summary))
            if cur.fetchone():
                continue
            
            # Insert into database
            cur.execute("""
                INSERT INTO programacion_diaria (fecha, actividad, observaciones, tipo, color)
                VALUES (?, ?, ?, ?, ?)
            """, (event_date, summary, final_desc, 'clase', '#3788d8'))
            imported_count += 1
        
        conn.commit()
        conn.close()
        
        return jsonify({"ok": True, "imported": imported_count})
    
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/alumnos/exportar/json")
def exportar_alumnos_json():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT a.nombre, a.comedor_dias, f.* 
        FROM alumnos a
        LEFT JOIN ficha_alumno f ON a.id = f.alumno_id
    """)
    rows = cur.fetchall()
    conn.close()
    
    data = [dict(row) for row in rows]
    return jsonify(data)

@app.route("/api/alumnos/exportar/csv")
def exportar_alumnos_csv():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT a.nombre, a.comedor_dias, f.fecha_nacimiento, f.direccion, 
               f.madre_nombre, f.madre_telefono, f.madre_email,
               f.padre_nombre, f.padre_telefono, f.padre_email,
               f.observaciones_generales, f.personas_autorizadas
        FROM alumnos a
        LEFT JOIN ficha_alumno f ON a.id = f.alumno_id
    """)
    rows = cur.fetchall()
    conn.close()

    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=alumnos_export.csv"}
    )

@app.route("/api/reuniones", methods=["GET", "POST"])
def api_reuniones():
    conn = get_db()
    cur = conn.cursor()

    if request.method == "GET":
        alumno_id = request.args.get("alumno_id")
        if not alumno_id:
            return jsonify([])
        
        cur.execute("SELECT id, fecha, asistentes, temas, acuerdos FROM reuniones WHERE alumno_id = ? ORDER BY fecha DESC", (alumno_id,))
        rows = cur.fetchall()
        conn.close()

        data = []
        for r in rows:
            data.append({
                "id": r[0],
                "fecha": r[1],
                "asistentes": r[2],
                "temas": r[3],
                "acuerdos": r[4]
            })
        return jsonify(data)

    elif request.method == "POST":
        d = request.json
        cur.execute("""
            INSERT INTO reuniones (alumno_id, fecha, asistentes, temas, acuerdos)
            VALUES (?, ?, ?, ?, ?)
        """, (d["alumno_id"], d["fecha"], d["asistentes"], d["temas"], d["acuerdos"]))
        conn.commit()
        lid = cur.lastrowid
        conn.close()
        return jsonify({"ok": True, "id": lid})


@app.route("/api/reuniones/<int:rid>", methods=["PUT", "DELETE"])
def api_reuniones_item(rid):
    conn = get_db()
    cur = conn.cursor()

    if request.method == "DELETE":
        cur.execute("DELETE FROM reuniones WHERE id = ?", (rid,))
        conn.commit()
        conn.close()
        return jsonify({"ok": True})

    elif request.method == "PUT":
        d = request.json
        cur.execute("""
            UPDATE reuniones 
            SET fecha = ?, asistentes = ?, temas = ?, acuerdos = ?
            WHERE id = ?
        """, (d["fecha"], d["asistentes"], d["temas"], d["acuerdos"], rid))
        conn.commit()
        conn.close()
        return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True)

