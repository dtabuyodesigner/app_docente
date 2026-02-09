from flask import Blueprint, jsonify, request, send_file
from utils.db import get_db, nivel_a_nota
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
import json
from datetime import date

import pandas as pd
from datetime import date

informes_bp = Blueprint('informes', __name__)

def generar_pie_circular(valores, etiquetas, titulo):
    # valores: lista de numeros, etiquetas: lista de strings
    if not valores or sum(valores) == 0:
        return None
        
    plt.figure(figsize=(4, 3))
    plt.pie(valores, labels=etiquetas, autopct='%1.1f%%', startangle=140)
    plt.title(titulo)
    plt.axis('equal') 
    
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', bbox_inches='tight')
    plt.close()
    img_buffer.seek(0)
    return img_buffer

@informes_bp.route("/api/informe/pdf_individual")
def informe_pdf_individual():
    alumno_id = request.args.get("alumno_id")
    trimestre = request.args.get("trimestre")
    
    if not alumno_id or not trimestre:
        return "Faltan parámetros", 400
        
    conn = get_db()
    cur = conn.cursor()
    
    # 1. Datos Alumno
    cur.execute("SELECT nombre FROM alumnos WHERE id = ?", (alumno_id,))
    alumno = cur.fetchone()["nombre"]
    
    # 2. Asistencia
    # (Simplified for brevity, assuming standard logic)
    cur.execute("""
        SELECT estado, COUNT(*) 
        FROM asistencia 
        WHERE alumno_id = ?
        GROUP BY estado
    """, (alumno_id,))
    asist_data = dict(cur.fetchall())
    
    # 3. Notas
    cur.execute("""
        SELECT a.nombre, ROUND(AVG(e.nota), 2)
        FROM evaluaciones e
        JOIN areas a ON e.area_id = a.id
        WHERE e.alumno_id = ? AND e.trimestre = ?
        GROUP BY a.id, a.nombre
    """, (alumno_id, trimestre))
    notas = cur.fetchall()
    
    conn.close()
    
    # Generate PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph(f"Informe Trimestral - Trimestre {trimestre}", styles['Title']))
    elements.append(Paragraph(f"Alumno: {alumno}", styles['Heading2']))
    elements.append(Spacer(1, 12))
    
    # Asistencia
    elements.append(Paragraph("Resumen de Asistencia", styles['Heading3']))
    data_asist = [
        ["Estado", "Días"],
        ["Presente", asist_data.get('presente', 0)],
        ["Retraso", asist_data.get('retraso', 0)],
        ["Falta Justificada", asist_data.get('falta_justificada', 0)],
        ["Falta No Justificada", asist_data.get('falta_no_justificada', 0)],
    ]
    t_asist = Table(data_asist)
    t_asist.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black)]))
    elements.append(t_asist)
    elements.append(Spacer(1, 12))
    
    # Notas
    elements.append(Paragraph("Rendimiento Académico", styles['Heading3']))
    data_notas = [["Área", "Nota Media"]]
    for area, nota in notas:
        data_notas.append([area, str(nota)])
        
    t_notas = Table(data_notas)
    t_notas.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black)]))
    elements.append(t_notas)

    doc.build(elements)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"Informe_{alumno}_T{trimestre}.pdf",
        mimetype='application/pdf'
    )

@informes_bp.route("/api/informe/pdf_diario/<int:alumno_id>")
def informe_pdf_diario(alumno_id):
    conn = get_db()
    cur = conn.cursor()
    
    # Alumno
    cur.execute("SELECT nombre FROM alumnos WHERE id = ?", (alumno_id,))
    alumno = cur.fetchone()["nombre"]
    
    # Observaciones
    cur.execute("""
        SELECT o.fecha, ar.nombre, o.texto
        FROM observaciones o
        LEFT JOIN areas ar ON o.area_id = ar.id
        WHERE o.alumno_id = ?
        ORDER BY o.fecha DESC
    """, (alumno_id,))
    obs = cur.fetchall()
    
    conn.close()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph(f"Diario de Clase: {alumno}", styles['Title']))
    elements.append(Spacer(1, 12))
    
    for fecha, area, texto in obs:
        area_str = f" ({area})" if area else ""
        elements.append(Paragraph(f"<b>{fecha}{area_str}:</b> {texto}", styles['BodyText']))
        elements.append(Spacer(1, 6))
        
    doc.build(elements)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"Diario_{alumno}.pdf",
        mimetype='application/pdf'
    )

@informes_bp.route("/api/reuniones/<int:rid>/pdf")
def informe_reunion_pdf(rid):
    tutor_nombre = request.args.get("tutor", "El Tutor/a")
    
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT r.*, a.nombre as alumno_nombre
        FROM reuniones r
        LEFT JOIN alumnos a ON r.alumno_id = a.id
        WHERE r.id = ?
    """, (rid,))
    r = cur.fetchone()
    conn.close()
    
    if not r:
        return "Reunión no encontrada", 404
        
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    style_label = ParagraphStyle('LabelStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10)
    style_content = ParagraphStyle('ContentStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leftIndent=10)
    
    title = f"Acta de Reunión - {r['tipo']}"
    elements.append(Paragraph(title, styles['Title']))
    elements.append(Spacer(1, 15))
    
    # Info Table
    info_data = [
        [Paragraph("<b>Fecha:</b>", style_label), Paragraph(r['fecha'], style_content)],
        [Paragraph("<b>Tutor/a:</b>", style_label), Paragraph(tutor_nombre, style_content)]
    ]
    
    if r['alumno_nombre']:
        info_data.insert(0, [Paragraph("<b>Alumno/a:</b>", style_label), Paragraph(r['alumno_nombre'], style_content)])
        
    info_data.append([Paragraph("<b>Asistentes:</b>", style_label), Paragraph(r['asistentes'] or "", style_content)])
    
    t_info = Table(info_data, colWidths=[3*cm, 14*cm])
    t_info.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 20))
    
    # Body
    elements.append(Paragraph("<b>Temas Tratados:</b>", styles['Heading3']))
    elements.append(Paragraph(r['temas'] or "Sin contenido", styles['Normal']))
    elements.append(Spacer(1, 15))
    
    elements.append(Paragraph("<b>Acuerdos / Conclusiones:</b>", styles['Heading3']))
    elements.append(Paragraph(r['acuerdos'] or "Sin acuerdos registrados", styles['Normal']))
    elements.append(Spacer(1, 40))
    
    # Signatures
    elements.append(Paragraph("<b>Firmas:</b>", styles['Heading4']))
    elements.append(Spacer(1, 20))
    
    sig_data = []
    if r['tipo'] == 'PADRES':
        sig_data = [
            [f"Fdo: {tutor_nombre}", "Fdo: La Familia"],
            ["(Tutor/a)", ""]
        ]
        t_sig = Table(sig_data, colWidths=[8*cm, 8*cm])
    else:
        # CICLO: Signature for each attendee
        # Assuming asistentes are separated by newline or comma
        ast_list = []
        if r['asistentes']:
            # Try newline first, then comma
            if '\n' in r['asistentes']:
                ast_list = [a.strip() for a in r['asistentes'].split('\n') if a.strip()]
            else:
                ast_list = [a.strip() for a in r['asistentes'].split(',') if a.strip()]
        
        # Add tutor to list if not there? 
        # Usually tutor is one of the attendees in cycle meetings too
        
        sig_table_rows = []
        # Create pairs for signature grid
        for i in range(0, len(ast_list), 2):
            row = [f"Fdo: {ast_list[i]}", f"Fdo: {ast_list[i+1]}" if i+1 < len(ast_list) else ""]
            sig_table_rows.append(row)
            sig_table_rows.append(["", ""]) # Space for signature
            sig_table_rows.append(["", ""]) # Extra space
            
        if not sig_table_rows:
             sig_table_rows = [[f"Fdo: {tutor_nombre}", ""]]
             
        t_sig = Table(sig_table_rows, colWidths=[8*cm, 8*cm])

    t_sig.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    elements.append(t_sig)
    
    doc.build(elements)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"Acta_Reunion_{r['fecha']}.pdf",
        mimetype='application/pdf'
    )

@informes_bp.route("/api/informe/grupo_obs", methods=["GET", "POST"])
def grupo_obs():
    trimestre = request.args.get("trimestre") if request.method == "GET" else request.json.get("trimestre")
    if not trimestre:
        return jsonify({"ok": False, "error": "Falta trimestre"}), 400
        
    conn = get_db()
    cur = conn.cursor()
    
    if request.method == "POST":
        d = request.json
        obs = d.get("observaciones", "")
        prop = d.get("propuestas_mejora", "")
        conc = d.get("conclusion", "")
        
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
    else:
        cur.execute("SELECT * FROM informe_grupo WHERE trimestre = ?", (trimestre,))
        row = cur.fetchone()
        conn.close()
        if row:
            return jsonify({
                "observaciones": row["observaciones"],
                "propuestas_mejora": row["propuestas_mejora"],
                "conclusion": row["conclusion"]
            })
        return jsonify({})

@informes_bp.route("/api/informe/grupo_data")
def grupo_data():
    trimestre = request.args.get("trimestre", "1")
    conn = get_db()
    cur = conn.cursor()
    
    # 1. GENERALES
    cur.execute("SELECT COUNT(*) FROM alumnos")
    total_alumnos = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*), AVG(nota) FROM evaluaciones WHERE trimestre = ?", (trimestre,))
    row_evals = cur.fetchone()
    total_evals = row_evals[0]
    media_general = round(row_evals[1] or 0, 2)
    
    # 2. ASISTENCIA (Estimación trimestral - Usando mes actual como proxy o query compleja)
    # Para simplificar, cogemos TODA la asistencia (Ajustar si se requiere filtro por fechas trimestre)
    # Asumimos fechas trimestre: 1T (Sept-Dic), 2T (Ene-Mar), 3T (Abr-Jun)
    # Implementación simple: Filtro por fechas
    
    start_date, end_date = "", ""
    year = date.today().year
    if trimestre == "1":
        start_date = f"{year-1}-09-01"
        end_date = f"{year-1}-12-31"
    elif trimestre == "2":
        start_date = f"{year}-01-01"
        end_date = f"{year}-03-31"
    else:
        start_date = f"{year}-04-01"
        end_date = f"{year}-06-30"
        
    cur.execute("""
        SELECT estado, COUNT(*)
        FROM asistencia
        WHERE fecha BETWEEN ? AND ?
        GROUP BY estado
    """, (start_date, end_date))
    
    asist_stats = dict(cur.fetchall())
    
    # 3. PROMOCION (Alumnos con 0, 1, 2, +2 suspensos)
    cur.execute("""
        SELECT alumno_id, COUNT(*)
        FROM evaluaciones
        WHERE trimestre = ? AND nota < 5
        GROUP BY alumno_id
    """, (trimestre,))
    suspensos_map = dict(cur.fetchall()) # {alumno_id: num_suspensos}
    
    # Rellenar con 0 los que no tienen suspensos
    cur.execute("SELECT id FROM alumnos")
    all_ids = [r[0] for r in cur.fetchall()]
    
    distribucion = {0: 0, 1: 0, 2: 0, 3: 0} # 3 representa >2
    
    for aid in all_ids:
        num = suspensos_map.get(aid, 0)
        if num > 2:
            distribucion[3] += 1
        else:
            distribucion[num] += 1
            
    conn.close()
    
    def pct(n):
        return round(n * 100.0 / total_alumnos, 1) if total_alumnos > 0 else 0
    
    return jsonify({
        "generales": {
            "total_alumnos": total_alumnos,
            "media_general": media_general,
            "total_evals": total_evals
        },
        "asistencia": {
            "total_faltas": asist_stats.get('falta_justificada', 0) + asist_stats.get('falta_no_justificada', 0),
            "f_justificada": asist_stats.get('falta_justificada', 0),
            "f_no_justificada": asist_stats.get('falta_no_justificada', 0),
            "total_retrasos": asist_stats.get('retraso', 0)
        },
        "promocion": {
            "todo": {"num": distribucion[0], "pct": pct(distribucion[0])},
            "una": {"num": distribucion[1], "pct": pct(distribucion[1])},
            "dos": {"num": distribucion[2], "pct": pct(distribucion[2])},
            "mas_de_dos": {"num": distribucion[3], "pct": pct(distribucion[3])}
        }
    })

@informes_bp.route("/api/informe/asistencia_detalle")
def asistencia_detalle():
    trimestre = request.args.get("trimestre", "1")
    estado = request.args.get("estado")
    
    # Filter by trimester dates
    start_date, end_date = "", ""
    year = date.today().year
    if trimestre == "1":
        start_date = f"{year-1}-09-01"
        end_date = f"{year-1}-12-31"
    elif trimestre == "2":
        start_date = f"{year}-01-01"
        end_date = f"{year}-03-31"
    else:
        start_date = f"{year}-04-01"
        end_date = f"{year}-06-30"

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.nombre, asi.fecha
        FROM asistencia asi
        JOIN alumnos a ON asi.alumno_id = a.id
        WHERE asi.estado = ? AND asi.fecha BETWEEN ? AND ?
        ORDER BY asi.fecha DESC
    """, (estado, start_date, end_date))
    rows = cur.fetchall()
    conn.close()
    
    return jsonify([{"nombre": r["nombre"], "fecha": r["fecha"]} for r in rows])

@informes_bp.route("/api/informe/observacion", methods=["GET", "POST"])
def observacion_individual():
    if request.method == "POST":
        d = request.json
        alumno_id = d.get("alumno_id")
        trimestre = d.get("trimestre")
        texto = d.get("texto")
        
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO informe_individual (alumno_id, trimestre, texto)
            VALUES (?, ?, ?)
            ON CONFLICT(alumno_id, trimestre) DO UPDATE SET
                texto = excluded.texto,
                fecha_actualizacion = CURRENT_TIMESTAMP
        """, (alumno_id, trimestre, texto))
        
        conn.commit()
        conn.close()
        return jsonify({"ok": True})
    else:
        alumno_id = request.args.get("alumno_id")
        trimestre = request.args.get("trimestre")
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT texto FROM informe_individual WHERE alumno_id = ? AND trimestre = ?", (alumno_id, trimestre))
        row = cur.fetchone()
        conn.close()
        
        return jsonify({"texto": row["texto"] if row else ""})

@informes_bp.route("/api/informe/asistencia_alumno")
def asistencia_alumno_stats():
    alumno_id = request.args.get("alumno_id")
    trimestre = request.args.get("trimestre")
    
    start_date, end_date = "", ""
    year = date.today().year
    if trimestre == "1":
        start_date = f"{year-1}-09-01"
        end_date = f"{year-1}-12-31"
    elif trimestre == "2":
        start_date = f"{year}-01-01"
        end_date = f"{year}-03-31"
    else:
        start_date = f"{year}-04-01"
        end_date = f"{year}-06-30"

    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT estado, COUNT(*)
        FROM asistencia
        WHERE alumno_id = ? AND fecha BETWEEN ? AND ?
        GROUP BY estado
    """, (alumno_id, start_date, end_date))
    
    stats = dict(cur.fetchall())
    conn.close()
    
    return jsonify({
        "retrasos": stats.get("retraso", 0),
        "f_justificada": stats.get("falta_justificada", 0),
        "f_no_justificada": stats.get("falta_no_justificada", 0),
        "total_faltas": stats.get("falta_justificada", 0) + stats.get("falta_no_justificada", 0)
    })

@informes_bp.route("/api/informe/pdf_general")
def informe_pdf_todos():
    trimestre = request.args.get("trimestre")
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre FROM alumnos ORDER BY nombre")
    alumnos = cur.fetchall()
    conn.close()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    for al in alumnos:
        elements.append(Paragraph(f"Informe Trimestral - Trimestre {trimestre}", styles['Title']))
        elements.append(Paragraph(f"Alumno: {al['nombre']}", styles['Heading2']))
        elements.append(Spacer(1, 12))
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT a.nombre, ROUND(AVG(e.nota), 2)
            FROM evaluaciones e
            JOIN areas a ON e.area_id = a.id
            WHERE e.alumno_id = ? AND e.trimestre = ?
            GROUP BY a.id, a.nombre
        """, (al['id'], trimestre))
        notas = cur.fetchall()
        cur.execute("SELECT texto FROM informe_individual WHERE alumno_id = ? AND trimestre = ?", (al['id'], trimestre))
        obs_row = cur.fetchone()
        obs_text = obs_row["texto"] if obs_row else ""
        conn.close()
        
        data_notas = [["Área", "Nota Media"]]
        for area, nota in notas:
            data_notas.append([area, str(nota)])
        t = Table(data_notas)
        t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black)]))
        elements.append(t)
        
        if obs_text:
             elements.append(Spacer(1, 12))
             elements.append(Paragraph("<b>Observaciones:</b>", styles['Heading3']))
             elements.append(Paragraph(obs_text, styles['Normal']))

        elements.append(PageBreak())
        
    doc.build(elements)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"Informes_Trimestre_{trimestre}.pdf",
        mimetype='application/pdf'
    )

@informes_bp.route("/api/informe/excel_grupo")
def excel_grupo():
    trimestre = request.args.get("trimestre")
    conn = get_db()
    
    query = """
    SELECT al.nombre as Alumno, ar.nombre as Area, ROUND(AVG(e.nota), 2) as Nota
    FROM evaluaciones e
    JOIN alumnos al ON e.alumno_id = al.id
    JOIN areas ar ON e.area_id = ar.id
    WHERE e.trimestre = ?
    GROUP BY al.nombre, ar.nombre
    """
    df = pd.read_sql_query(query, conn, params=(trimestre,))
    conn.close()
    
    if df.empty:
         return "No hay datos", 404
         
    pivot = df.pivot(index='Alumno', columns='Area', values='Nota')
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pivot.to_excel(writer, sheet_name=f'Trimestre_{trimestre}')
        
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name=f"Notas_Grupo_T{trimestre}.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@informes_bp.route("/api/informe/pdf_grupo")
def pdf_grupo():
    trimestre = request.args.get("trimestre")
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM informe_grupo WHERE trimestre = ?", (trimestre,))
    row = cur.fetchone()
    conn.close()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph(f"Informe Global de Grupo - Trimestre {trimestre}", styles['Title']))
    elements.append(Spacer(1, 12))
    
    if row:
        if row["observaciones"]:
            elements.append(Paragraph("Valoración General del Tutor", styles['Heading3']))
            elements.append(Paragraph(row["observaciones"], styles['BodyText']))
            elements.append(Spacer(1, 12))
            
        if row["propuestas_mejora"]:
            elements.append(Paragraph("Propuestas de Mejora", styles['Heading3']))
            elements.append(Paragraph(row["propuestas_mejora"], styles['BodyText']))
            elements.append(Spacer(1, 12))
            
        if row["conclusion"]:
            elements.append(Paragraph("Conclusión Final", styles['Heading3']))
            elements.append(Paragraph(row["conclusion"], styles['BodyText']))
    else:
        elements.append(Paragraph("No hay datos guardados para este trimestre.", styles['Normal']))
        
    doc.build(elements)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"Informe_Grupo_T{trimestre}.pdf",
        mimetype='application/pdf'
    )

@informes_bp.route("/api/rubricas/pdf/<int:sda_id>")
def rubrica_pdf_sda(sda_id):
    conn = get_db()
    cur = conn.cursor()
    
    # SDA
    cur.execute("SELECT nombre FROM sda WHERE id = ?", (sda_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return "SDA no encontrada", 404
    sda_name = row["nombre"]
    
    # Criterios y Rúbricas
    cur.execute("""
        SELECT c.id, c.codigo, c.descripcion
        FROM criterios c
        JOIN sda_criterios sc ON sc.criterio_id = c.id
        WHERE sc.sda_id = ?
        ORDER BY c.id
    """, (sda_id,))
    criterios = cur.fetchall()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph(f"Rúbricas: {sda_name}", styles['Title']))
    elements.append(Spacer(1, 12))
    
    for c in criterios:
        elements.append(Paragraph(f"<b>Criterio {c['codigo']}:</b>", styles['Heading3']))
        elements.append(Paragraph(c['descripcion'], styles['Normal']))
        elements.append(Spacer(1, 8))
        
        cur.execute("SELECT nivel, descriptor FROM rubricas WHERE criterio_id = ? ORDER BY nivel", (c['id'],))
        rubs = cur.fetchall()
        
        if rubs:
            data = [["Nivel", "Descriptor"]]
            for r in rubs:
                data.append([str(r['nivel']), Paragraph(r['descriptor'], styles['Normal'])])
            
            t = Table(data, colWidths=[2*cm, 14*cm])
            t.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)
            ]))
            elements.append(t)
        else:
            elements.append(Paragraph("<i>No hay rúbricas definidas para este criterio.</i>", styles['Normal']))
            
        elements.append(Spacer(1, 15))
        
    conn.close()
    doc.build(elements)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"Rubricas_{sda_name}.pdf",
        mimetype='application/pdf'
    )
