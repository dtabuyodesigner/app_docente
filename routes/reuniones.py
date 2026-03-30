from flask import Blueprint, jsonify, request, session, send_file
from utils.db import get_db
from datetime import date
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

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
    """Genera informe PDF de una reunión con familia o ciclo."""
    conn = get_db()
    cur = conn.cursor()
    
    # Obtener datos de la reunión
    cur.execute("""
        SELECT r.*, a.nombre as alumno_nombre
        FROM reuniones r
        LEFT JOIN alumnos a ON r.alumno_id = a.id
        WHERE r.id = ?
    """, (rid,))
    reunion = cur.fetchone()
    
    if not reunion:
        return "Reunión no encontrada", 404
    
    # Crear buffer PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=2*cm, leftMargin=2*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilo título
    styles.add(ParagraphStyle(
        name='Title',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=12,
        alignment=1  # Center
    ))
    
    # Estilo normal mejorado
    styles.add(ParagraphStyle(
        name='Normal',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        spaceAfter=6
    ))
    
    # Estilo para subtítulos
    styles.add(ParagraphStyle(
        name='Heading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=8,
        spaceBefore=12
    ))
    
    # Cabecera
    tipo_reunion = "Ciclo" if reunion["tipo"] == "CICLO" else "Familias"
    alumno_nombre = reunion["alumno_nombre"] or ""
    
    header_data = [
        [Paragraph(f"Acta de Reunión - {tipo_reunion}", styles['Title'])]
    ]
    if alumno_nombre:
        header_data.append([Paragraph(f"Alumno/a: {alumno_nombre}", styles['Normal'])])
    
    header_table = Table(header_data, colWidths=[16*cm])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 10))
    
    # Información básica
    info_data = [
        [Paragraph("<b>Fecha:</b>", styles['Normal']), Paragraph(reunion["fecha"] or "—", styles['Normal'])],
        [Paragraph("<b>Asistentes:</b>", styles['Normal']), Paragraph(reunion["asistentes"] or "—", styles['Normal'])],
    ]
    
    if reunion["tipo"] == "CICLO":
        info_data.append([Paragraph("<b>Tipo:</b>", styles['Normal']), Paragraph("Reunión de Ciclo", styles['Normal'])])
    else:
        info_data.append([Paragraph("<b>Tipo:</b>", styles['Normal']), Paragraph("Reunión con Familias", styles['Normal'])])
    
    table_info = Table(info_data, colWidths=[4*cm, 12*cm])
    table_info.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(table_info)
    elements.append(Spacer(1, 15))
    
    # Temas tratados
    elements.append(Paragraph("📝 TEMAS TRATADOS", styles['Heading2']))
    temas_text = reunion["temas"] or "Sin contenido"
    # Escapar caracteres especiales para ReportLab
    temas_text = temas_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    elements.append(Paragraph(temas_text, styles['Normal']))
    elements.append(Spacer(1, 15))
    
    # Acuerdos / Conclusiones
    if reunion["acuerdos"]:
        elements.append(Paragraph("🤝 ACUERDOS / CONCLUSIONES", styles['Heading2']))
        acuerdos_text = reunion["acuerdos"] or ""
        acuerdos_text = acuerdos_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        elements.append(Paragraph(acuerdos_text, styles['Normal']))
        elements.append(Spacer(1, 15))
    
    # Dificultades (solo para tipo CICLO)
    if reunion["tipo"] == "CICLO" and reunion.get("dificultades"):
        elements.append(Paragraph("⚠️ DIFICULTADES", styles['Heading2']))
        dificultades_text = reunion["dificultades"]
        dificultades_text = dificultades_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        elements.append(Paragraph(dificultades_text, styles['Normal']))
        elements.append(Spacer(1, 15))
    
    # Pie de página con fecha de generación
    elements.append(Spacer(1, 30))
    footer_text = f"Documento generado el {date.today().strftime('%d/%m/%Y')}"
    elements.append(Paragraph(footer_text, styles['Normal']))
    
    # Construir PDF
    doc.build(elements)
    buffer.seek(0)
    
    # Nombre del archivo
    if alumno_nombre:
        filename = f"Reunion_{alumno_nombre.replace(' ', '_')}_{reunion['fecha']}.pdf"
    else:
        filename = f"Reunion_Ciclo_{reunion['fecha']}.pdf"
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

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
