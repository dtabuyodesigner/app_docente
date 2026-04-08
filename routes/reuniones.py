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
        alumno_id = d.get("alumno_id") # Puede ser None si tipo=CICLO (pero en db es INTEGER)
        fecha = d.get("fecha")
        asistentes = d.get("asistentes")
        temas = d.get("temas")
        dificultades = d.get("dificultades")
        acuerdos = d.get("acuerdos")
        tipo = d.get("tipo", "PADRES")
        ciclo_id = d.get("ciclo_id")  # Solo para tipo=CICLO
        
        try:
            cur.execute("""
                INSERT INTO reuniones (alumno_id, fecha, asistentes, temas, dificultades, acuerdos, tipo, ciclo_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (alumno_id, fecha, asistentes, temas, dificultades, acuerdos, tipo, ciclo_id))
            conn.commit()
            return jsonify({"ok": True, "id": cur.lastrowid})
        except Exception as e:
            conn.rollback()
            print("Error en api_reuniones (POST):", str(e))
            return jsonify({"ok": False, "error": "Error interno al guardar la reunión."}), 500
        finally:
            pass
            pass
            
    else:
        # GET
        rid = request.args.get("id")
        alumno_id = request.args.get("alumno_id")
        tipo = request.args.get("tipo")
        
        if rid:
            cur.execute("""
                SELECT r.*, a.nombre as alumno_nombre
                FROM reuniones r
                LEFT JOIN alumnos a ON r.alumno_id = a.id
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
        SELECT r.*, a.nombre as alumno_nombre
        FROM reuniones r
        LEFT JOIN alumnos a ON r.alumno_id = a.id
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

    # --- CABECERA CON LOGOS (igual que actas evaluación) ---
    nombre_centro = cfg.get("nombre_centro", "CEIP")
    curso_escolar = cfg.get("curso_escolar", "")
    tipo_reunion = "CICLO" if reunion["tipo"] == "CICLO" else "FAMILIAS"
    titulo_tipo = "Reunión de Ciclo" if reunion["tipo"] == "CICLO" else "Reunión con Familias"

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
    firma_fn = cfg.get("tutor_firma_filename")
    tutor_nombre = cfg.get("nombre_tutor", "El/La Tutor/a")
    firma_path_val = None
    if firma_fn:
        p = os.path.join(uploads_dir, firma_fn)
        if os.path.exists(p):
            firma_path_val = p

    # Obtener curso del grupo si es reunión de ciclo
    grupo_curso = ""
    try:
        if reunion["tipo"] == "CICLO" and reunion.get("ciclo_id"):
            cur.execute("SELECT g.curso FROM grupos g WHERE g.id = ?", (reunion["ciclo_id"],))
            row_curso = cur.fetchone()
            if row_curso and row_curso["curso"]:
                grupo_curso = row_curso["curso"]
    except Exception as e:
        print(f"[WARNING] Error obteniendo curso del grupo para firma del tutor: {e}")
        grupo_curso = ""

    # Construir etiqueta del tutor con curso si está disponible
    tutor_label = f"Tutor/a {grupo_curso}" if grupo_curso else "Tutor/a"

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

    if reunion["tipo"] == "CICLO":
        col_otro = [
            Paragraph("<b>El/La Coordinador/a:</b>", style_label),
            Spacer(1, 36),
            Paragraph("<i>Fdo: .............................................</i>", style_small)
        ]
    else:
        col_otro = [
            Paragraph("<b>El/La Padre/Madre/Tutor Legal:</b>", style_label),
            Spacer(1, 36),
            Paragraph("<i>Fdo: .............................................</i>", style_small)
        ]

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
