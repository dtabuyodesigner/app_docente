from flask import Blueprint, jsonify, request, session, send_file
from utils.db import get_db
from datetime import date
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Image as RLImage
import os

reuniones_bp = Blueprint('reuniones', __name__)

@reuniones_bp.route("/api/reuniones", methods=["GET", "POST"])
def api_reuniones():
    conn = get_db()
    cur = conn.cursor()
    
    if request.method == "POST":
        d = request.json
        alumno_id = d.get("alumno_id")
        fecha = d.get("fecha")
        asistentes = d.get("asistentes")
        temas = d.get("temas")
        dificultades = d.get("dificultades")
        propuestas_mejora = d.get("propuestas_mejora")
        acuerdos = d.get("acuerdos")
        tipo = d.get("tipo", "PADRES")
        ciclo_id = d.get("ciclo_id")
        grupo_id = d.get("grupo_id")
        plantilla_id = d.get("plantilla_id")
        lugar = d.get("lugar")

        try:
            cur.execute("""
                INSERT INTO reuniones
                    (alumno_id, fecha, asistentes, temas, dificultades, propuestas_mejora,
                     acuerdos, tipo, ciclo_id, grupo_id, plantilla_id, lugar)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (alumno_id, fecha, asistentes, temas, dificultades, propuestas_mejora,
                  acuerdos, tipo, ciclo_id, grupo_id, plantilla_id, lugar))
            conn.commit()
            return jsonify({"ok": True, "id": cur.lastrowid})
        except Exception as e:
            conn.rollback()
            print("Error en api_reuniones (POST):", str(e))
            return jsonify({"ok": False, "error": "Error interno al guardar la reunión."}), 500
            
    else:
        # GET
        rid = request.args.get("id")
        alumno_id = request.args.get("alumno_id")
        tipo = request.args.get("tipo")
        
        if rid:
            cur.execute("""
                SELECT r.*, a.nombre as alumno_nombre, c.nombre as ciclo_nombre
                FROM reuniones r
                LEFT JOIN alumnos a ON r.alumno_id = a.id
                LEFT JOIN config_ciclo c ON r.ciclo_id = c.id
                WHERE r.id = ?
            """, (rid,))
            r = cur.fetchone()
            if r:
                return jsonify(dict(r))
            return jsonify({"ok": False, "error": "Not found"}), 404
            
        elif alumno_id:
            cur.execute("""
                SELECT r.*, a.nombre as alumno_nombre
                FROM reuniones r
                LEFT JOIN alumnos a ON r.alumno_id = a.id
                WHERE r.alumno_id = ? 
                ORDER BY r.fecha DESC
            """, (alumno_id,))
            rows = cur.fetchall()
            return jsonify([dict(r) for r in rows])
        else:
            # List all (filtered by type if provided)
            grupo_id = session.get('active_group_id')
            ciclo_id = request.args.get("ciclo_id")
            
            sql = """
                SELECT r.*, a.nombre as alumno_nombre
                FROM reuniones r
                LEFT JOIN alumnos a ON r.alumno_id = a.id
                WHERE 1=1
            """
            params = []
            
            # Filtros obligatorios por tipo y grupo/ciclo
            print(f"[DEBUG] Fetching meetings: tipo={tipo}, grupo_id={grupo_id}, ciclo_id={ciclo_id}")
            if tipo == 'CICLO':
                sql += " AND r.tipo = 'CICLO'"
                if ciclo_id:
                    sql += " AND r.ciclo_id = ?"
                    params.append(ciclo_id)
            elif tipo == 'PADRES' or tipo == 'PADRES/TUTORES':
                sql += " AND r.tipo != 'CICLO'"
                if grupo_id:
                    # Incluimos reuniones del grupo Y reuniones generales (sin alumno_id)
                    sql += " AND (a.grupo_id = ? OR r.alumno_id IS NULL)"
                    params.append(grupo_id)
            else:
                # Si no hay tipo, filtramos por grupo_id si existe
                if grupo_id:
                    sql += " AND (r.tipo = 'CICLO' OR a.grupo_id = ? OR r.alumno_id IS NULL)"
                    params.append(grupo_id)

            sql += " ORDER BY r.fecha DESC"
            
            print(f"[DEBUG] SQL: {sql} | Params: {params}")
            cur.execute(sql, params)
            rows = cur.fetchall()
            print(f"[DEBUG] Found {len(rows)} meetings")
            return jsonify([dict(r) for r in rows])
@reuniones_bp.route("/api/reuniones/<int:rid>", methods=["PUT"])
def editar_reunion(rid):
    d = request.json
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE reuniones 
            SET fecha = ?, asistentes = ?, temas = ?, dificultades = ?, acuerdos = ?, alumno_id = ?, ciclo_id = ?
            WHERE id = ?
        """, (d.get("fecha"), d.get("asistentes"), d.get("temas"), d.get("dificultades"), d.get("acuerdos"), d.get("alumno_id"), d.get("ciclo_id"), rid))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        print("Error en editar_reunion:", str(e))
        return jsonify({"ok": False, "error": "Error interno al editar la reunión."}), 500
    finally:
        pass
        pass

@reuniones_bp.route("/api/reuniones/<int:rid>", methods=["DELETE"])
def borrar_reunion(rid):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM reuniones WHERE id = ?", (rid,))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        print("Error en borrar_reunion:", str(e))
        return jsonify({"ok": False, "error": "Error interno al borrar la reunión."}), 500
    
@reuniones_bp.route("/api/reuniones/<int:rid>", methods=["PATCH"])
def patch_reunion(rid):
    d = request.json
    conn = get_db()
    cur = conn.cursor()
    
    # Construir consulta dinámica basada en los campos proporcionados
    fields = []
    params = []
    for key in ["fecha", "asistentes", "temas", "dificultades", "acuerdos", "alumno_id", "ciclo_id"]:
        if key in d:
            fields.append(f"{key} = ?")
            params.append(d[key])
            
    if not fields:
        return jsonify({"ok": False, "error": "No hay campos para actualizar"}), 400
        
    params.append(rid)
    sql = f"UPDATE reuniones SET {', '.join(fields)} WHERE id = ?"
    
    try:
        cur.execute(sql, params)
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        print("Error en patch_reunion:", str(e))
        return jsonify({"ok": False, "error": str(e)}), 500


# --- CICLO CONFIGURATION ENDPOINTS ---

@reuniones_bp.route("/api/ciclos", methods=["GET", "POST"])
def api_ciclos():
    conn = get_db()
    cur = conn.cursor()
    
    if request.method == "POST":
        d = request.json
        nombre = d.get("nombre")
        asistentes_defecto = d.get("asistentes_defecto", "[]")  # JSON string
        
        if not nombre:
            return jsonify({"ok": False, "error": "Nombre requerido"}), 400
            
        try:
            cur.execute("INSERT INTO config_ciclo (nombre, asistentes_defecto) VALUES (?, ?)", 
                       (nombre, asistentes_defecto))
            conn.commit()
            return jsonify({"ok": True, "id": cur.lastrowid})
        except Exception as e:
            conn.rollback()
            print("Error en api_ciclos (POST):", str(e))
            return jsonify({"ok": False, "error": "Error interno al guardar ciclo."}), 500
        finally:
            pass
    else:
        # GET
        cur.execute("SELECT * FROM config_ciclo ORDER BY nombre")
        rows = cur.fetchall()
        return jsonify([dict(r) for r in rows])


@reuniones_bp.route("/api/ciclos/<int:cid>", methods=["PUT", "DELETE"])
def api_ciclo(cid):
    conn = get_db()
    cur = conn.cursor()
    
    if request.method == "PUT":
        d = request.json
        nombre = d.get("nombre")
        asistentes_defecto = d.get("asistentes_defecto", "[]")
        
        try:
            cur.execute("UPDATE config_ciclo SET nombre = ?, asistentes_defecto = ? WHERE id = ?",
                       (nombre, asistentes_defecto, cid))
            conn.commit()
            return jsonify({"ok": True})
        except Exception as e:
            conn.rollback()
            print("Error en api_ciclo (PUT):", str(e))
            return jsonify({"ok": False, "error": "Error interno al editar ciclo."}), 500
        finally:
            pass
    else:
        # DELETE
        try:
            cur.execute("DELETE FROM config_ciclo WHERE id = ?", (cid,))
            conn.commit()
            return jsonify({"ok": True})
        except Exception as e:
            conn.rollback()
            print("Error en api_ciclo (DELETE):", str(e))
            return jsonify({"ok": False, "error": "Error interno al borrar ciclo."}), 500
        finally:
            pass

# ==============================================================================
# INFORME PDF REUNIONES
# ==============================================================================

@reuniones_bp.route("/api/reuniones/<int:rid>/pdf")
def reunion_pdf(rid):
    """Genera informe PDF de una reunión con familia o ciclo. Formato unificado con logos."""
    from utils.db import get_app_data_dir
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT r.*, a.nombre as alumno_nombre, p.nombre as plantilla_nombre
        FROM reuniones r
        LEFT JOIN alumnos a ON r.alumno_id = a.id
        LEFT JOIN plantillas_reunion p ON r.plantilla_id = p.id
        WHERE r.id = ?
    """, (rid,))
    reunion = cur.fetchone()
    if not reunion:
        return jsonify({"ok": False, "error": "Reunión no encontrada"}), 404

    # Config: logos, firma, datos del centro
    cur.execute("""
        SELECT clave, valor FROM config
        WHERE clave LIKE 'logo_%' OR clave IN ('tutor_firma_filename', 'nombre_tutor', 'nombre_centro', 'curso_escolar')
    """)
    cfg = {r["clave"]: r["valor"] for r in cur.fetchall()}

    uploads_dir = os.path.join(get_app_data_dir(), "uploads")

    def logo_path(lado):
        fn = cfg.get(f"logo_{lado}_filename")
        if fn:
            p = os.path.join(uploads_dir, fn)
            if os.path.exists(p):
                return p
        return None

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=1.5*cm, bottomMargin=2*cm)
    elements = []
    styles = getSampleStyleSheet()

    style_label = ParagraphStyle('RLabel', parent=styles['Normal'],
                                 fontSize=10, fontName='Helvetica-Bold', spaceAfter=4)
    style_body = ParagraphStyle('RBody', parent=styles['Normal'],
                                fontSize=10, leading=16, spaceAfter=6)
    style_small = ParagraphStyle('RSmall', parent=styles['Normal'],
                                 fontSize=9, textColor=colors.grey)

    # --- CABECERA CON LOGOS ---
    nombre_centro = cfg.get("nombre_centro", "CEIP")
    curso_escolar = cfg.get("curso_escolar", "")
    tipo_raw = reunion["tipo"] or "PADRES"
    plantilla_nombre_pdf = (reunion["plantilla_nombre"] if "plantilla_nombre" in reunion.keys() else None) or ""
    _tipo_labels = {
        "CICLO": ("CICLO", "Reunión de Ciclo"),
        "NIVEL": ("NIVEL", "Reunión de Nivel"),
        "CCP": ("CCP", "Reunión de CCP"),
        "CLAUSTRO": ("CLAUSTRO", "Reunión de Claustro"),
        "COMISIONES": ("COMISIÓN", f"Comisión: {plantilla_nombre_pdf}" if plantilla_nombre_pdf else "Reunión de Comisión"),
        "FAMILIAS": ("FAMILIAS", "Reunión con Familias"),
        "PADRES": ("FAMILIAS", f"Entrevista: {reunion['alumno_nombre']}" if reunion['alumno_nombre'] else "Entrevista Individual"),
    }
    tipo_reunion, titulo_tipo = _tipo_labels.get(tipo_raw, (tipo_raw, f"Reunión — {tipo_raw}"))

    def make_logo(lado):
        p = logo_path(lado)
        if p:
            try:
                img = RLImage(p, width=3*cm, height=2*cm)
                img.hAlign = cfg.get(f"logo_{lado}_posicion", lado).upper()
                return img
            except Exception:
                pass
        return Paragraph(" ", styles['Normal'])

    col_centro_hdr = Paragraph(
        f"<b>{nombre_centro}</b><br/><b>ACTA DE REUNION - {tipo_reunion}</b>"
        + (f"<br/>Curso {curso_escolar}" if curso_escolar else ""),
        ParagraphStyle('hdr', parent=styles['Normal'], alignment=1,
                       fontSize=11, fontName='Helvetica-Bold', leading=16)
    )
    hdr_tbl = Table([[make_logo("izda"), col_centro_hdr, make_logo("dcha")]],
                    colWidths=[3.5*cm, 10*cm, 3.5*cm])
    hdr_tbl.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
    ]))
    elements.append(hdr_tbl)
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceAfter=10))

    # --- DATOS BÁSICOS ---
    alumno_nombre = reunion["alumno_nombre"] or ""
    fecha_raw = reunion["fecha"] or ""
    try:
        from datetime import datetime as dt
        fecha_fmt = dt.strptime(fecha_raw[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
        if len(fecha_raw) > 10:
            hora = fecha_raw[11:16]
            fecha_fmt += f" a las {hora} h"
    except Exception:
        fecha_fmt = fecha_raw

    asistentes_raw = (reunion["asistentes"] or "")
    
    # Parsear asistentes si viene en formato JSON
    import json
    if asistentes_raw.strip().startswith('['):
        try:
            asistentes_lista = json.loads(asistentes_raw)
            if isinstance(asistentes_lista, list):
                asistentes_raw = ', '.join([str(a).strip() for a in asistentes_lista if str(a).strip()])
        except json.JSONDecodeError:
            pass  # Si falla, usar original
    
    asistentes_raw = asistentes_raw.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    datos = [
        ["<b>Fecha:</b>", fecha_fmt],
        ["<b>Tipo:</b>", titulo_tipo],
    ]
    if alumno_nombre:
        datos.insert(0, ["<b>Alumno/a:</b>", alumno_nombre])
    if asistentes_raw:
        datos.append(["<b>Asistentes:</b>", asistentes_raw])

    t_datos = Table(
        [[Paragraph(k, style_label), Paragraph(v, style_body)] for k, v in datos],
        colWidths=[4.5*cm, 12*cm]
    )
    t_datos.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (-1, -2), 0.3, colors.lightgrey),
    ]))
    elements.append(t_datos)
    elements.append(Spacer(1, 12))

    # --- SECCIONES DE CONTENIDO ---
    def seccion(titulo, texto):
        if not texto:
            return
        elements.append(Paragraph(f"<b>{titulo}</b>", style_label))
        elements.append(Spacer(1, 4))
        texto_escaped = texto.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        for linea in texto_escaped.split('\n'):
            linea = linea.strip()
            if linea:
                elements.append(Paragraph(linea, style_body))
        elements.append(Spacer(1, 12))

    seccion("TEMAS TRATADOS", reunion["temas"])
    if reunion["tipo"] == "CICLO":
        seccion("DIFICULTADES", reunion["dificultades"])
    seccion("ACUERDOS / CONCLUSIONES", reunion["acuerdos"])

    # Fecha generación
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        f"Documento generado el {date.today().strftime('%d/%m/%Y')}",
        style_small
    ))
    elements.append(Spacer(1, 20))

    # --- FIRMAS ---
    # Obtener nombre del ciclo si es reunión de ciclo
    grupo_curso = ""
    coordinador_ciclo = ""
    try:
        ciclo_id_val = reunion["ciclo_id"] if "ciclo_id" in reunion.keys() else None
        if reunion["tipo"] == "CICLO" and ciclo_id_val:
            cur.execute("SELECT nombre FROM config_ciclo WHERE id = ?", (ciclo_id_val,))
            row_ciclo = cur.fetchone()
            if row_ciclo and row_ciclo["nombre"]:
                ciclo_nombre = row_ciclo["nombre"]
                import re
                match = re.match(r'(\d+[ºª])\s+', ciclo_nombre)
                if match:
                    grupo_curso = match.group(1)
                else:
                    grupo_curso = ciclo_nombre
        if not grupo_curso:
            grupo_id = session.get('active_group_id')
            if grupo_id:
                cur.execute("SELECT nombre, coordinador_ciclo FROM grupos WHERE id = ?", (grupo_id,))
                row_g = cur.fetchone()
                if row_g and row_g["nombre"]:
                    grupo_curso = row_g["nombre"]
                coordinador_ciclo = row_g["coordinador_ciclo"] if row_g and row_g["coordinador_ciclo"] else ""
        else:
            grupo_id = session.get('active_group_id')
            if grupo_id:
                cur.execute("SELECT coordinador_ciclo FROM grupos WHERE id = ?", (grupo_id,))
                row_g2 = cur.fetchone()
                coordinador_ciclo = row_g2["coordinador_ciclo"] if row_g2 and row_g2["coordinador_ciclo"] else ""
    except Exception as e:
        print(f"[WARNING] Error obteniendo curso del ciclo para firma del tutor: {e}")
        grupo_curso = ""
        coordinador_ciclo = ""

    # Etiqueta firma izquierda: "Tutor/a Xº Primaria" solo para FAMILIAS/PADRES; resto "El/La Maestro/a"
    if tipo_raw in ("FAMILIAS", "PADRES"):
        tutor_label = f"Tutor/a {grupo_curso}" if grupo_curso else "Tutor/a"
    else:
        tutor_label = "El/La Maestro/a"

    firma_fn = cfg.get("tutor_firma_filename")
    tutor_nombre = cfg.get("nombre_tutor", "El/La Tutor/a")
    firma_path_val = None
    if firma_fn:
        p = os.path.join(uploads_dir, firma_fn)
        if os.path.exists(p):
            firma_path_val = p

    elements.append(Paragraph("<b>FIRMAS</b>", style_label))
    elements.append(Spacer(1, 8))

    col_tutor = [Paragraph(f"<b>{tutor_label}:</b>", style_label), Spacer(1, 8)]
    if firma_path_val:
        try:
            img_f = RLImage(firma_path_val, width=4.5*cm, height=1.5*cm, kind='proportional')
            img_f.hAlign = 'CENTER'
            col_tutor.append(img_f)
        except Exception:
            col_tutor.append(Spacer(1, 20))
    else:
        col_tutor.append(Spacer(1, 28))
    col_tutor.append(Paragraph(f"<i>{tutor_nombre}</i>", style_small))

    firma_vacia = Paragraph("<i>Fdo: .............................................</i>", style_small)
    if tipo_raw in ("FAMILIAS", "PADRES"):
        col_otro = [Paragraph("<b>El/La Padre/Madre/Tutor Legal:</b>", style_label), Spacer(1, 36), firma_vacia]
    elif tipo_raw == "CICLO":
        col_otro = [Paragraph("<b>El/La Coordinador/a de Ciclo:</b>", style_label), Spacer(1, 36)]
        col_otro.append(Paragraph(f"<i>{coordinador_ciclo}</i>", style_small) if coordinador_ciclo else firma_vacia)
    elif tipo_raw == "CCP":
        col_otro = [Paragraph("<b>El/La Director/a:</b>", style_label), Spacer(1, 36), firma_vacia]
    elif tipo_raw == "CLAUSTRO":
        col_otro = [Paragraph("<b>El/La Director/a:</b>", style_label), Spacer(1, 36), firma_vacia]
    elif tipo_raw == "COMISIONES":
        col_otro = [Paragraph("<b>El/La Coordinador/a de Comisión:</b>", style_label), Spacer(1, 36), firma_vacia]
    else:
        col_otro = [Paragraph("<b>El/La Jefe/a de Estudios:</b>", style_label), Spacer(1, 36), firma_vacia]

    sig_tbl = Table([[col_tutor, col_otro]], colWidths=[8.5*cm, 8.5*cm])
    sig_tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(sig_tbl)

    doc.build(elements)
    buffer.seek(0)

    safe_fecha = fecha_raw[:10].replace('-', '')
    if alumno_nombre:
        filename = f"Acta_Reunion_{alumno_nombre.replace(' ', '_')}_{safe_fecha}.pdf"
    else:
        filename = f"Acta_Reunion_Ciclo_{safe_fecha}.pdf"

    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

@reuniones_bp.route("/api/reuniones/exportar/csv")
def exportar_reuniones_csv():
    conn = get_db()
    cur = conn.cursor()
    grupo_id = session.get('active_group_id')
    tipo = request.args.get("tipo")
    
    sql = """
        SELECT r.fecha, r.asistentes, r.temas, r.acuerdos, r.tipo, a.nombre as alumno_nombre
        FROM reuniones r
        LEFT JOIN alumnos a ON r.alumno_id = a.id
        WHERE (r.tipo = 'CICLO' OR a.grupo_id = ?)
    """
    params = [grupo_id]
    if tipo:
        sql += " AND r.tipo = ?"
        params.append(tipo)
        
    sql += " ORDER BY r.fecha DESC"
    
    cur.execute(sql, params)
    datos = cur.fetchall()
    
    import io
    import csv
    from flask import send_file
    
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["Fecha", "Tipo", "Alumno", "Asistentes", "Temas", "Acuerdos"])
    
    for row in datos:
        nom_alum = row["alumno_nombre"] or ""
        tipo_lbl = "Ciclo" if row["tipo"] == "CICLO" else "Padres/Tutores"
        cw.writerow([
            row["fecha"],
            tipo_lbl,
            nom_alum,
            row["asistentes"],
            row["temas"],
            row["acuerdos"]
        ])
        
    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    
    return send_file(
        output,
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"reuniones_export_{date.today()}.csv",
    )

@reuniones_bp.route("/api/reuniones/exportar/ical")
def exportar_reuniones_ical():
    conn = get_db()
    cur = conn.cursor()
    grupo_id = session.get('active_group_id')
    tipo = request.args.get("tipo")
    
    sql = """
        SELECT r.fecha, r.asistentes, r.temas, r.acuerdos, r.tipo, a.nombre as alumno_nombre
        FROM reuniones r
        LEFT JOIN alumnos a ON r.alumno_id = a.id
        WHERE (r.tipo = 'CICLO' OR a.grupo_id = ?)
    """
    params = [grupo_id]
    if tipo:
        sql += " AND r.tipo = ?"
        params.append(tipo)
        
    sql += " ORDER BY r.fecha DESC"
    
    cur.execute(sql, params)
    datos = cur.fetchall()
    
    import io
    from flask import send_file
    from datetime import datetime
    import uuid
    
    # Simple iCal builder
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//App Evaluacion//Reuniones//ES"
    ]
    
    for row in datos:
        try:
            # Parse date and default time to 16:00 if no time part available
            try:
                dt = datetime.strptime(row["fecha"], "%Y-%m-%dT%H:%M")
            except ValueError:
                dt = datetime.strptime(row["fecha"], "%Y-%m-%d")
                dt = dt.replace(hour=16, minute=0)
            
            # End time default to +1 hour
            dt_end = dt.replace(hour=dt.hour + 1)
            
            dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            dtstart = dt.strftime("%Y%m%dT%H%M%S")
            dtend = dt_end.strftime("%Y%m%dT%H%M%S")
            
            nom_alum = row["alumno_nombre"] or ""
            tipo_lbl = "Ciclo" if row["tipo"] == "CICLO" else "Padres"
            summary = f"Reunión {tipo_lbl}" + (f" - {nom_alum}" if nom_alum else "")
            
            desc = f"Asistentes: {row['asistentes']}\\n\\nTemas: {row['temas']}"
            if row['acuerdos']:
                desc += f"\\n\\nAcuerdos: {row['acuerdos']}"
                
            lines.extend([
                "BEGIN:VEVENT",
                f"UID:{uuid.uuid4()}@app_evaluacion",
                f"DTSTAMP:{dtstamp}",
                f"DTSTART;TZID=Europe/Madrid:{dtstart}",
                f"DTEND;TZID=Europe/Madrid:{dtend}",
                f"SUMMARY:{summary}",
                f"DESCRIPTION:{desc}",
                "END:VEVENT"
            ])
        except Exception as e:
            print(f"Error parsing date for iCal export: {e}")
            continue
            
    lines.append("END:VCALENDAR")
    lines.append("") # EOF trailing newline
    
    output = io.BytesIO()
    # \r\n is required by iCal spec
    output.write("\\r\\n".join(lines).encode('utf-8')) 
    output.seek(0)
    
    return send_file(
        output,
        mimetype="text/calendar",
        as_attachment=True,
        download_name=f"calendario_reuniones_{date.today()}.ics",
    )


# ==============================================================================
# PLANTILLAS DE REUNIÓN
# ==============================================================================

@reuniones_bp.route("/api/plantillas_reunion", methods=["GET", "POST"])
def api_plantillas_reunion():
    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        d = request.json
        nombre = d.get("nombre", "").strip()
        tipo = d.get("tipo", "").strip()
        descripcion = d.get("descripcion", "")
        orden_del_dia = d.get("orden_del_dia", "")
        miembros = d.get("miembros", [])  # lista de {nombre, rol}

        if not nombre or not tipo:
            return jsonify({"ok": False, "error": "Nombre y tipo son obligatorios"}), 400

        try:
            cur.execute(
                "INSERT INTO plantillas_reunion (nombre, tipo, descripcion, orden_del_dia) VALUES (?, ?, ?, ?)",
                (nombre, tipo, descripcion, orden_del_dia)
            )
            pid = cur.lastrowid
            for i, m in enumerate(miembros):
                cur.execute(
                    "INSERT INTO plantillas_reunion_miembros (plantilla_id, nombre, rol, orden) VALUES (?, ?, ?, ?)",
                    (pid, m.get("nombre", ""), m.get("rol", ""), i)
                )
            conn.commit()
            return jsonify({"ok": True, "id": pid})
        except Exception as e:
            conn.rollback()
            print("Error en api_plantillas_reunion (POST):", e)
            return jsonify({"ok": False, "error": "Error interno"}), 500
    else:
        tipo = request.args.get("tipo")
        sql = "SELECT * FROM plantillas_reunion"
        params = []
        if tipo:
            sql += " WHERE tipo = ?"
            params.append(tipo)
        sql += " ORDER BY tipo, nombre"
        cur.execute(sql, params)
        plantillas = [dict(r) for r in cur.fetchall()]
        # Añadir miembros a cada plantilla
        for p in plantillas:
            cur.execute(
                "SELECT * FROM plantillas_reunion_miembros WHERE plantilla_id = ? ORDER BY orden",
                (p["id"],)
            )
            p["miembros"] = [dict(m) for m in cur.fetchall()]
        return jsonify(plantillas)


@reuniones_bp.route("/api/plantillas_reunion/<int:pid>", methods=["GET", "PUT", "DELETE"])
def api_plantilla_reunion(pid):
    conn = get_db()
    cur = conn.cursor()

    if request.method == "GET":
        cur.execute("SELECT * FROM plantillas_reunion WHERE id = ?", (pid,))
        p = cur.fetchone()
        if not p:
            return jsonify({"ok": False, "error": "No encontrada"}), 404
        result = dict(p)
        cur.execute(
            "SELECT * FROM plantillas_reunion_miembros WHERE plantilla_id = ? ORDER BY orden",
            (pid,)
        )
        result["miembros"] = [dict(m) for m in cur.fetchall()]
        return jsonify(result)

    elif request.method == "PUT":
        d = request.json
        nombre = d.get("nombre", "").strip()
        tipo = d.get("tipo", "").strip()
        descripcion = d.get("descripcion", "")
        orden_del_dia = d.get("orden_del_dia", "")
        miembros = d.get("miembros", [])

        if not nombre or not tipo:
            return jsonify({"ok": False, "error": "Nombre y tipo son obligatorios"}), 400

        try:
            cur.execute(
                "UPDATE plantillas_reunion SET nombre=?, tipo=?, descripcion=?, orden_del_dia=? WHERE id=?",
                (nombre, tipo, descripcion, orden_del_dia, pid)
            )
            # Reemplazar miembros
            cur.execute("DELETE FROM plantillas_reunion_miembros WHERE plantilla_id = ?", (pid,))
            for i, m in enumerate(miembros):
                cur.execute(
                    "INSERT INTO plantillas_reunion_miembros (plantilla_id, nombre, rol, orden) VALUES (?, ?, ?, ?)",
                    (pid, m.get("nombre", ""), m.get("rol", ""), i)
                )
            conn.commit()
            return jsonify({"ok": True})
        except Exception as e:
            conn.rollback()
            print("Error en api_plantilla_reunion (PUT):", e)
            return jsonify({"ok": False, "error": "Error interno"}), 500

    else:  # DELETE
        try:
            cur.execute("DELETE FROM plantillas_reunion WHERE id = ?", (pid,))
            conn.commit()
            return jsonify({"ok": True})
        except Exception as e:
            conn.rollback()
            print("Error en api_plantilla_reunion (DELETE):", e)
            return jsonify({"ok": False, "error": "Error interno"}), 500


@reuniones_bp.route("/api/plantillas_reunion/<int:pid>/auto_miembros")
def auto_miembros_plantilla(pid):
    """Sugiere miembros automáticamente según el grupo activo y tipo de reunión."""
    import json
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM plantillas_reunion WHERE id = ?", (pid,))
    plantilla = cur.fetchone()
    if not plantilla:
        return jsonify({"ok": False, "error": "Plantilla no encontrada"}), 404

    grupo_id = session.get("active_group_id")
    miembros = []

    if grupo_id:
        cur.execute("SELECT nombre, equipo_docente, coordinador_ciclo FROM grupos WHERE id = ?", (grupo_id,))
        grupo = cur.fetchone()
        if grupo and grupo["equipo_docente"]:
            try:
                equipo = json.loads(grupo["equipo_docente"])
                for prof in equipo:
                    miembros.append({"nombre": prof, "rol": "Docente"})
            except Exception:
                pass
        if grupo and grupo["coordinador_ciclo"]:
            # Poner coordinador primero si es reunión de ciclo/CCP
            if plantilla["tipo"] in ("CICLO", "CCP"):
                miembros.insert(0, {"nombre": grupo["coordinador_ciclo"], "rol": "Coordinador/a"})

    return jsonify({"ok": True, "miembros": miembros})


# Ruta adicional para listar reuniones de todos los tipos (para el panel unificado)
@reuniones_bp.route("/api/reuniones/todas")
def api_reuniones_todas():
    """Lista todas las reuniones con información enriquecida para el panel unificado."""
    conn = get_db()
    cur = conn.cursor()

    sql = """
        SELECT DISTINCT r.id, r.fecha, r.tipo, r.asistentes, r.temas, r.acuerdos,
               r.dificultades, r.propuestas_mejora, r.lugar,
               r.alumno_id, r.ciclo_id, r.grupo_id, r.plantilla_id,
               a.nombre as alumno_nombre,
               p.nombre as plantilla_nombre
        FROM reuniones r
        LEFT JOIN alumnos a ON r.alumno_id = a.id
        LEFT JOIN plantillas_reunion p ON r.plantilla_id = p.id
        WHERE 1=1
    """
    params = []

    tipo_filter = request.args.get("tipo")
    if tipo_filter:
        if tipo_filter in ("PADRES", "FAMILIAS"):
            sql += " AND r.tipo IN ('PADRES', 'FAMILIAS')"
        else:
            sql += " AND r.tipo = ?"
            params.append(tipo_filter)

    sql += " ORDER BY r.fecha DESC"
    cur.execute(sql, params)
    rows = cur.fetchall()
    return jsonify([dict(r) for r in rows])


# ==============================================================================
# CLAUSTRO — almacén central de docentes del centro
# ==============================================================================

@reuniones_bp.route("/api/claustro", methods=["GET", "POST"])
def api_claustro():
    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        d = request.json
        nombre = (d.get("nombre") or "").strip()
        rol = d.get("rol", "Docente")
        if not nombre:
            return jsonify({"ok": False, "error": "Nombre obligatorio"}), 400
        cur.execute("SELECT MAX(orden) FROM claustro")
        row = cur.fetchone()
        orden = (row[0] or 0) + 1
        cur.execute("INSERT INTO claustro (nombre, rol, activo, orden) VALUES (?, ?, 1, ?)", (nombre, rol, orden))
        conn.commit()
        return jsonify({"ok": True, "id": cur.lastrowid})
    else:
        cur.execute("SELECT * FROM claustro ORDER BY orden, nombre")
        return jsonify([dict(r) for r in cur.fetchall()])


@reuniones_bp.route("/api/claustro/<int:cid>", methods=["PUT", "DELETE"])
def api_claustro_item(cid):
    conn = get_db()
    cur = conn.cursor()

    if request.method == "PUT":
        d = request.json
        nombre = (d.get("nombre") or "").strip()
        rol = d.get("rol", "Docente")
        activo = 1 if d.get("activo", True) else 0
        if not nombre:
            return jsonify({"ok": False, "error": "Nombre obligatorio"}), 400
        cur.execute("UPDATE claustro SET nombre=?, rol=?, activo=? WHERE id=?", (nombre, rol, activo, cid))
        conn.commit()
        return jsonify({"ok": True})
    else:
        cur.execute("DELETE FROM claustro WHERE id=?", (cid,))
        conn.commit()
        return jsonify({"ok": True})


# ==============================================================================
# ASISTENTES POR TIPO DE REUNIÓN
# ==============================================================================

@reuniones_bp.route("/api/reunion_asistentes/<tipo>", methods=["GET", "POST"])
def api_reunion_asistentes(tipo):
    """GET: lista claustro_ids asignados a este tipo. POST: guarda la selección completa."""
    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        d = request.json
        ids = d.get("ids", [])
        cur.execute("DELETE FROM reunion_tipo_asistentes WHERE tipo=?", (tipo,))
        for cid in ids:
            try:
                cur.execute("INSERT OR IGNORE INTO reunion_tipo_asistentes (tipo, claustro_id) VALUES (?, ?)", (tipo, cid))
            except Exception:
                pass
        conn.commit()
        return jsonify({"ok": True})
    else:
        cur.execute("""
            SELECT c.id, c.nombre, c.rol
            FROM claustro c
            JOIN reunion_tipo_asistentes rta ON rta.claustro_id = c.id
            WHERE rta.tipo = ?
            ORDER BY c.orden, c.nombre
        """, (tipo,))
        return jsonify([dict(r) for r in cur.fetchall()])


@reuniones_bp.route("/api/reunion_asistentes/<tipo>/sugeridos")
def api_asistentes_sugeridos(tipo):
    """Devuelve los asistentes configurados para este tipo, o fallback al claustro completo."""
    import json as json_mod
    conn = get_db()
    cur = conn.cursor()

    # Primero buscar configuración específica del tipo
    cur.execute("""
        SELECT c.nombre, c.rol FROM claustro c
        JOIN reunion_tipo_asistentes rta ON rta.claustro_id = c.id
        WHERE rta.tipo = ? AND c.activo = 1
        ORDER BY c.orden, c.nombre
    """, (tipo,))
    rows = cur.fetchall()
    if rows:
        return jsonify([{"nombre": r["nombre"], "rol": r["rol"]} for r in rows])

    # Fallback: todo el claustro activo
    cur.execute("SELECT nombre, rol FROM claustro WHERE activo=1 ORDER BY orden, nombre")
    rows = cur.fetchall()
    if rows:
        return jsonify([{"nombre": r["nombre"], "rol": r["rol"]} for r in rows])

    # Último fallback: equipo docente del grupo activo
    grupo_id = session.get("active_group_id")
    if grupo_id:
        cur.execute("SELECT equipo_docente, coordinador_ciclo FROM grupos WHERE id=?", (grupo_id,))
        g = cur.fetchone()
        if g and g["equipo_docente"]:
            try:
                equipo = json_mod.loads(g["equipo_docente"])
                miembros = [{"nombre": p, "rol": "Docente"} for p in equipo]
                if g["coordinador_ciclo"] and tipo in ("CICLO", "CCP"):
                    miembros.insert(0, {"nombre": g["coordinador_ciclo"], "rol": "Coordinador/a"})
                return jsonify(miembros)
            except Exception:
                pass

    return jsonify([])
