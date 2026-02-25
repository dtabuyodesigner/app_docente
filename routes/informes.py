from flask import Blueprint, jsonify, request, send_file, session
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
from datetime import date, datetime

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
    tutor_nombre = request.args.get("tutor", "")
    
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
    # 3. Notas por Área
    cur.execute("""
        SELECT a.id, a.nombre, ROUND(AVG(e.nota), 2)
        FROM evaluaciones e
        JOIN areas a ON e.area_id = a.id
        WHERE e.alumno_id = ? AND e.trimestre = ?
        GROUP BY a.id, a.nombre
    """, (alumno_id, trimestre))
    notas_area = cur.fetchall()

    # 4. Notas por SDA con Criterios
    cur.execute("""
        SELECT a.nombre as area, s.nombre as sda, c.codigo as criterio_codigo, 
               c.descripcion as criterio_desc, e.nota
        FROM evaluaciones e
        JOIN sda s ON e.sda_id = s.id
        JOIN areas a ON e.area_id = a.id
        JOIN criterios c ON e.criterio_id = c.id
        WHERE e.alumno_id = ? AND e.trimestre = ?
        ORDER BY a.nombre, s.nombre, c.codigo
    """, (alumno_id, trimestre))
    notas_criterios = cur.fetchall()

    # 5. Detalle de Faltas (Nuevo)
    # Filter by trimester dates
    start_date, end_date = "", ""
    year = date.today().year
    if trimestre == "1":
        start_date = f"{year-1}-09-01"; end_date = f"{year-1}-12-31"
    elif trimestre == "2":
        start_date = f"{year}-01-01"; end_date = f"{year}-03-31"
    else:
        start_date = f"{year}-04-01"; end_date = f"{year}-06-30"

    cur.execute("""
        SELECT fecha, estado
        FROM asistencia
        WHERE alumno_id = ? AND estado IN ('retraso', 'falta_justificada', 'falta_no_justificada')
        AND fecha BETWEEN ? AND ?
        ORDER BY fecha
    """, (alumno_id, start_date, end_date))
    faltas_detalle = cur.fetchall()
    
    
    # Generate PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph(f"Informe Trimestral - Trimestre {trimestre}", styles['Title']))
    elements.append(Paragraph(f"Alumno: {alumno}", styles['Heading2']))
    if tutor_nombre:
        elements.append(Paragraph(f"Tutor/a: {tutor_nombre}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Asistencia
    elements.append(Paragraph("Resumen de Asistencia", styles['Heading3']))
    data_asist = [
        ["Estado", "Días"],
        [Paragraph('<font color="#ffc107">●</font> Retraso', styles['Normal']), asist_data.get('retraso', 0)],
        [Paragraph('<font color="#17a2b8">●</font> Falta Justificada', styles['Normal']), asist_data.get('falta_justificada', 0)],
        [Paragraph('<font color="#dc3545">●</font> Falta No Justificada', styles['Normal']), asist_data.get('falta_no_justificada', 0)],
    ]
    t_asist = Table(data_asist, colWidths=[6*cm, 2*cm])
    t_asist.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]))
    elements.append(t_asist)
    
    # Detalle de Faltas
    if faltas_detalle:
        elements.append(Spacer(1, 8))
        fechas_str = []
        for f, e in faltas_detalle:
            # Format date DD/MM
            d_obj = datetime.strptime(f, '%Y-%m-%d')
            d_str = d_obj.strftime('%d/%m')
            
            if e == 'retraso':
                color = "#ffc107"
                tipo = "R"
            elif e == 'falta_justificada':
                color = "#17a2b8"
                tipo = "F"
            else: # falta_no_justificada
                color = "#dc3545"
                tipo = "F"
                
            fechas_str.append(f'<font color="{color}">{d_str}({tipo})</font>')
        
        elements.append(Paragraph("<b>Detalle (Día/Tipo):</b> " + ", ".join(fechas_str), styles['Normal']))

    elements.append(Spacer(1, 12))
    
    # Notas
    elements.append(Paragraph("Rendimiento Académico", styles['Heading3']))
    
    # Group Criterios by Area and SDA
    # Structure: Area (avg) → SDA 1 → Criterio 1, Criterio 2... → SDA 2 → ...
    
    area_sda_map = {}  # {area_name: {sda_name: [(criterio, nota), ...]}}
    for area, sda, crit_cod, crit_desc, nota in notas_criterios:
        if area not in area_sda_map:
            area_sda_map[area] = {}
        if sda not in area_sda_map[area]:
            area_sda_map[area][sda] = []
        area_sda_map[area][sda].append((f"{crit_cod}", nota))
        
    data_notas = [["Área", "Nota Media", "Detalle SDA y Criterios"]]
    for aid, area_nombre, nota_media in notas_area:
        # Build hierarchical string for this area
        sda_dict = area_sda_map.get(area_nombre, {})
        detail_lines = []
        for sda_name, criterios in sda_dict.items():
            # Calculate SDA average
            sda_avg = round(sum(c[1] for c in criterios) / len(criterios), 2) if criterios else 0
            detail_lines.append(f"<b>{sda_name}</b>: {sda_avg}")
            for crit_cod, nota in criterios:
                detail_lines.append(f"  • {crit_cod}: {nota}")
        
        detail_str = "<br/>".join(detail_lines) if detail_lines else "Sin datos"
        data_notas.append([
            Paragraph(area_nombre, styles['Normal']), 
            str(nota_media), 
            Paragraph(detail_str, styles['Normal'])
        ])
        
    t_notas = Table(data_notas, colWidths=[4*cm, 2.5*cm, 10*cm])
    t_notas.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
    ]))
    elements.append(t_notas)
    elements.append(Spacer(1, 15))
    
    # Generar gráfica de notas por área
    if notas_area:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from reportlab.platypus import Image as RLImage
        
        areas = [row[1] for row in notas_area]
        notas = [row[2] for row in notas_area]
        
        fig, ax = plt.subplots(figsize=(8, max(3, len(areas) * 0.5)))
        colors_bars = ['#28a745' if n >= 5 else '#dc3545' for n in notas]
        bars = ax.barh(areas, notas, color=colors_bars)
        ax.set_xlabel('Nota Media')
        ax.set_title(f'Rendimiento por Área - {alumno}')
        ax.set_xlim(0, 10)
        ax.grid(axis='x', alpha=0.3)
        
        # Añadir valores en las barras
        for i, (bar, nota) in enumerate(zip(bars, notas)):
            ax.text(nota + 0.2, i, f'{nota:.2f}', va='center', fontweight='bold')
        
        chart_buf = BytesIO()
        plt.savefig(chart_buf, format='png', bbox_inches='tight', dpi=150)
        chart_buf.seek(0)
        plt.close()
        
        chart_img = RLImage(chart_buf, width=15*cm, height=max(6*cm, len(areas) * 1*cm))
        elements.append(chart_img)
        elements.append(Spacer(1, 15))
    
    # Signature
    elements.append(Spacer(1, 40))
    if tutor_nombre:
        elements.append(Paragraph(f"Fdo: {tutor_nombre}", styles['Normal']))
        elements.append(Paragraph("(Tutor/a)", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"Informe_{alumno}_T{trimestre}.pdf",
        mimetype='application/pdf'
    )

@informes_bp.route("/api/informe/preview_diario/<int:alumno_id>")
def informe_preview_diario(alumno_id):
    conn = get_db()
    cur = conn.cursor()
    
    # 1. Alumno
    cur.execute("SELECT nombre FROM alumnos WHERE id = ?", (alumno_id,))
    row_alumno = cur.fetchone()
    if not row_alumno:
        return jsonify({"ok": False, "error": "Alumno no encontrado"}), 404
        
    nombre_alumno = row_alumno["nombre"]
    
    # 2. Observaciones
    cur.execute("""
        SELECT o.id, o.fecha, o.texto, ar.nombre as area_nombre
        FROM observaciones o
        LEFT JOIN areas ar ON o.area_id = ar.id
        WHERE o.alumno_id = ?
        ORDER BY o.fecha DESC, o.id DESC
    """, (alumno_id,))
    rows = cur.fetchall()
    
    # 3. Group by date
    grouped = {}
    for r in rows:
        fecha = r["fecha"] # YYYY-MM-DD string from standard SQL DATE
        if fecha not in grouped:
            grouped[fecha] = []
            
        grouped[fecha].append({
            "id": r["id"],
            "texto": r["texto"],
            "area": r["area_nombre"] or "General"
        })
        
    # Convert to list
    data = []
    # Sort keys (dates) descending
    for fecha in sorted(grouped.keys(), reverse=True):
        # Format date for display? Let's keep YYYY-MM-DD for sorting/raw, 
        # and maybe add a display version if needed. Frontend uses 'fecha' for display.
        # Let's try to format it nicely if possible, or just send YYYY-MM-DD.
        # The frontend uses 'raw_fecha' for updates.
        
        # Simple format DD/MM/YYYY
        y, m, d = fecha.split('-')
        fecha_fmt = f"{d}/{m}/{y}"
        
        data.append({
            "fecha": fecha_fmt,       # Display
            "raw_fecha": fecha,       # For logic/updates
            "observaciones": grouped[fecha]
        })
        
    return jsonify({
        "ok": True,
        "nombre_alumno": nombre_alumno,
        "data": data
    })

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
        SELECT r.*, a.nombre as alumno_nombre, c.nombre as ciclo_nombre
        FROM reuniones r
        LEFT JOIN alumnos a ON r.alumno_id = a.id
        LEFT JOIN config_ciclo c ON r.ciclo_id = c.id
        WHERE r.id = ?
    """, (rid, ))
    r = cur.fetchone()
    
    if not r:
        return "Reunión no encontrada", 404
        
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    style_label = ParagraphStyle('LabelStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10)
    style_content = ParagraphStyle('ContentStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leftIndent=10)
    
    is_ciclo = (r['tipo'] == 'CICLO')
    if is_ciclo:
        title = f"Acta de reunión de {r['ciclo_nombre'] or 'Ciclo'}"
    else:
        title = f"Acta de reunión con familias"
        
    elements.append(Paragraph(title, styles['Title']))
    elements.append(Spacer(1, 15))
    
    # Info Table
    info_data = []
    
    if not is_ciclo:
        if r['alumno_nombre']:
            info_data.append([Paragraph("<b>Alumno/a:</b>", style_label), Paragraph(r['alumno_nombre'], style_content)])
        info_data.append([Paragraph("<b>Tutor/a:</b>", style_label), Paragraph(tutor_nombre, style_content)])
    
    info_data.append([Paragraph("<b>Fecha:</b>", style_label), Paragraph(r['fecha'], style_content)])
        
    # Asistentes parsing
    asistentes_str = r['asistentes'] or ""
    asistentes_list = []
    if asistentes_str:
        # Normalize separators
        if '[' in asistentes_str and ']' in asistentes_str:
            # Handle JSON list if we start saving it as such, but for now it's TEXT
            try:
                asistentes_list = json.loads(asistentes_str)
            except:
                normalized = asistentes_str.replace('\n', ',')
                asistentes_list = [a.strip() for a in normalized.split(',') if a.strip()]
        else:
            normalized = asistentes_str.replace('\n', ',')
            asistentes_list = [a.strip() for a in normalized.split(',') if a.strip()]
    
    asistentes_display = ", ".join(asistentes_list) if isinstance(asistentes_list, list) else asistentes_str
    info_data.append([Paragraph("<b>Asistentes:</b>", style_label), Paragraph(asistentes_display, style_content)])
    
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
    elements.append(Spacer(1, 10))
    
    sig_table_rows = []
    firmantes = []
    
    if not is_ciclo:
        firmantes.append(f"Tutor/a: {tutor_nombre}")
        for p in asistentes_list:
             if p.strip() and p.lower() not in tutor_nombre.lower(): 
                  firmantes.append(p.strip())
    else:
        if isinstance(asistentes_list, list):
            firmantes = asistentes_list
        else:
            firmantes = [a.strip() for a in asistentes_str.replace('\n', ',').split(',') if a.strip()]
             
    # Create grid of 2 columns
    for i in range(0, len(firmantes), 2):
        sig1_name = firmantes[i]
        sig2_name = firmantes[i+1] if i+1 < len(firmantes) else ""
        
        # Row 1: Signature gap
        sig_table_rows.append(["", ""])
        
        # Row 2: "Fdo: Name" underlined
        row_names = [
            Paragraph(f"Fdo: <u>{sig1_name}</u>", styles['Normal']),
            Paragraph(f"Fdo: <u>{sig2_name}</u>", styles['Normal']) if sig2_name else ""
        ]
        sig_table_rows.append(row_names)
        
    row_heights = []
    for _ in range(0, len(firmantes), 2):
        row_heights.extend([2.5*cm, 1.0*cm]) # Gap, "Fdo: Name" 
    
    t_sig = Table(sig_table_rows, colWidths=[8.5*cm, 8.5*cm], rowHeights=row_heights)
    t_sig.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
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
        return jsonify({"ok": True})
    else:
        cur.execute("SELECT * FROM informe_grupo WHERE trimestre = ?", (trimestre,))
        row = cur.fetchone()
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
    
    grupo_id = session.get('active_group_id')
    
    # 1. GENERALES
    cur.execute("SELECT COUNT(*) FROM alumnos WHERE grupo_id = ?", (grupo_id,))
    total_alumnos = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*), AVG(e.nota) FROM evaluaciones e JOIN alumnos a ON e.alumno_id = a.id WHERE e.trimestre = ? AND a.grupo_id = ?", (trimestre, grupo_id))
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
        SELECT asi.estado, COUNT(*)
        FROM asistencia asi
        JOIN alumnos a ON a.id = asi.alumno_id
        WHERE asi.fecha BETWEEN ? AND ? AND a.grupo_id = ?
        GROUP BY asi.estado
    """, (start_date, end_date, grupo_id))
    
    asist_stats = dict(cur.fetchall())
    
    # 3. PROMOCION (Alumnos con 0, 1, 2, +2 suspensos)
    cur.execute("""
        SELECT e.alumno_id, COUNT(*)
        FROM evaluaciones e
        JOIN alumnos a ON a.id = e.alumno_id
        WHERE e.trimestre = ? AND e.nota < 5 AND a.grupo_id = ?
        GROUP BY e.alumno_id
    """, (trimestre, grupo_id))
    suspensos_map = dict(cur.fetchall()) # {alumno_id: num_suspensos}
    
    # Rellenar con 0 los que no tienen suspensos
    cur.execute("SELECT id FROM alumnos WHERE grupo_id = ?", (grupo_id,))
    all_ids = [r[0] for r in cur.fetchall()]
    
    distribucion = {0: 0, 1: 0, 2: 0, 3: 0} # 3 representa >2
    
    for aid in all_ids:
        num = suspensos_map.get(aid, 0)
        if num > 2:
            distribucion[3] += 1
        else:
            distribucion[num] += 1
            
    
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

    grupo_id = session.get('active_group_id')
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.nombre, asi.fecha
        FROM asistencia asi
        JOIN alumnos a ON asi.alumno_id = a.id
        WHERE asi.estado = ? AND asi.fecha BETWEEN ? AND ? AND a.grupo_id = ?
        ORDER BY asi.fecha DESC
    """, (estado, start_date, end_date, grupo_id))
    rows = cur.fetchall()
    
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
        return jsonify({"ok": True})
    else:
        alumno_id = request.args.get("alumno_id")
        trimestre = request.args.get("trimestre")
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT texto FROM informe_individual WHERE alumno_id = ? AND trimestre = ?", (alumno_id, trimestre))
        row = cur.fetchone()
        
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
    
    return jsonify({
        "retrasos": stats.get("retraso", 0),
        "f_justificada": stats.get("falta_justificada", 0),
        "f_no_justificada": stats.get("falta_no_justificada", 0),
        "total_faltas": stats.get("falta_justificada", 0) + stats.get("falta_no_justificada", 0)
    })

@informes_bp.route("/api/informe/pdf_general")
def informe_pdf_todos():
    trimestre = request.args.get("trimestre")
    tutor_nombre = request.args.get("tutor", "")
    
    conn = get_db()
    cur = conn.cursor()
    
    # --- 1. DATOS GRUPALES ---
    # Valoración
    cur.execute("SELECT * FROM informe_grupo WHERE trimestre = ?", (trimestre,))
    row_grupo = cur.fetchone()
    
    grupo_id = session.get('active_group_id')
    
    # Promoción (Suspensos)
    cur.execute("""
        SELECT a.nombre, COUNT(*) as num_suspensos
        FROM evaluaciones e
        JOIN alumnos a ON a.id = e.alumno_id
        WHERE e.trimestre = ? AND e.nota < 5 AND a.grupo_id = ?
        GROUP BY a.id, a.nombre
    """, (trimestre, grupo_id))
    suspensos_data = cur.fetchall()
    
    susp_map = {0: 0, 1: 0, 2: 0, 3: 0} # 0, 1, 2, +2
    for r in suspensos_data:
        n = r["num_suspensos"]
        if n > 2:
            susp_map[3] += 1
        else:
            susp_map[n] += 1
            
    # Total alumnos (para los que tienen 0 suspensos)
    cur.execute("SELECT count(*) FROM alumnos WHERE grupo_id = ?", (grupo_id,))
    total_alumnos = cur.fetchone()[0]
    alumnos_con_suspensos = sum(susp_map.values()) - susp_map[0] # remove 0 if it was counted
    susp_map[0] = total_alumnos - len(suspensos_data)

    # Asistencia Max
    # Start/End dates logic (Copy from grupo_data or simplify)
    # Using simple approach: ALL time or filter by trimester if needed. 
    # Let's filter by trimester to be accurate.
    start_date, end_date = "", ""
    year = date.today().year
    if trimestre == "1":
        start_date = f"{year-1}-09-01"; end_date = f"{year-1}-12-31"
    elif trimestre == "2":
        start_date = f"{year}-01-01"; end_date = f"{year}-03-31"
    else:
        start_date = f"{year}-04-01"; end_date = f"{year}-06-30"

    cur.execute("""
        SELECT a.nombre, asi.estado, COUNT(*) as c
        FROM asistencia asi
        JOIN alumnos a ON a.id = asi.alumno_id
        WHERE asi.fecha BETWEEN ? AND ? AND a.grupo_id = ?
        GROUP BY a.id, a.nombre, asi.estado
        ORDER BY c DESC
    """, (start_date, end_date, grupo_id))
    asist_rows = cur.fetchall()
    
    max_faltas = {"nombre": "Nadie", "num": 0}
    max_retrasos = {"nombre": "Nadie", "num": 0}
    
    # Process max
    temp_faltas = {}
    temp_retrasos = {}
    
    for r in asist_rows:
        if r["estado"] in ["falta_justificada", "falta_no_justificada"]:
            temp_faltas[r["nombre"]] = temp_faltas.get(r["nombre"], 0) + r["c"]
        elif r["estado"] == "retraso":
            temp_retrasos[r["nombre"]] = temp_retrasos.get(r["nombre"], 0) + r["c"]
            
    if temp_faltas:
        u_max = max(temp_faltas, key=temp_faltas.get)
        max_faltas = {"nombre": u_max, "num": temp_faltas[u_max]}
        
    if temp_retrasos:
        u_max = max(temp_retrasos, key=temp_retrasos.get)
        max_retrasos = {"nombre": u_max, "num": temp_retrasos[u_max]}

    # Alumnos list
    cur.execute("SELECT id, nombre FROM alumnos WHERE grupo_id = ? ORDER BY nombre", (grupo_id,))
    alumnos = cur.fetchall()
    
    
    # --- GENERAR PDF ---
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # PORTADA / RESUMEN GRUPAL
    elements.append(Paragraph(f"Informe Global del Grupo - Trimestre {trimestre}", styles['Title']))
    if tutor_nombre:
        elements.append(Paragraph(f"Tutor/a: {tutor_nombre}", styles['Heading2']))
    elements.append(Spacer(1, 20))
    
    # 1. Valoración
    if row_grupo:
        if row_grupo["observaciones"]:
            elements.append(Paragraph("Valoración General:", styles['Heading3']))
            elements.append(Paragraph(row_grupo["observaciones"], styles['BodyText']))
        if row_grupo["propuestas_mejora"]:
            elements.append(Paragraph("Propuestas de Mejora:", styles['Heading3']))
            elements.append(Paragraph(row_grupo["propuestas_mejora"], styles['BodyText']))
        if row_grupo["conclusion"]:
            elements.append(Paragraph("Conclusión:", styles['Heading3']))
            elements.append(Paragraph(row_grupo["conclusion"], styles['BodyText']))
    else:
        elements.append(Paragraph("No hay valoración grupal registrada.", styles['Normal']))
    elements.append(Spacer(1, 15))
    
    # 2. Promoción
    elements.append(Paragraph("Análisis de Promoción (Resultados):", styles['Heading3']))
    
    def calc_pct(n):
        return f"{round(n * 100 / total_alumnos, 1)}%" if total_alumnos > 0 else "0%"

    data_prom = [
        ["Todo Aprobado", f"{susp_map[0]} ({calc_pct(susp_map[0])})"],
        ["1 Suspenso", f"{susp_map[1]} ({calc_pct(susp_map[1])})"],
        ["2 Suspensos", f"{susp_map[2]} ({calc_pct(susp_map[2])})"],
        ["+2 Suspensos", f"{susp_map[3]} ({calc_pct(susp_map[3])})"]
    ]
    t_prom = Table(data_prom, colWidths=[4*cm, 4*cm])
    t_prom.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.grey),
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey)
    ]))
    elements.append(t_prom)
    elements.append(Spacer(1, 15))
    
    # 3. Asistencia Highlights
    elements.append(Paragraph("Datos de Asistencia Destacados:", styles['Heading3']))
    elements.append(Paragraph(f"• Alumno/a con más faltas: <b>{max_faltas['nombre']}</b> ({max_faltas['num']} faltas)", styles['Normal']))
    elements.append(Paragraph(f"• Alumno/a con más retrasos: <b>{max_retrasos['nombre']}</b> ({max_retrasos['num']} retrasos)", styles['Normal']))
    
    elements.append(PageBreak())
    
    # --- INFORMES INDIVIDUALES ---
    for al in alumnos:
        conn = get_db() # Helper inside loop to be safe or reuse logic
        cur = conn.cursor()
        
        elements.append(Paragraph(f"Informe Trimestral - Trimestre {trimestre}", styles['Title']))
        elements.append(Paragraph(f"Alumno: {al['nombre']}", styles['Heading2']))
        if tutor_nombre:
            elements.append(Paragraph(f"Tutor/a: {tutor_nombre}", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Asistencia
        cur.execute("""
            SELECT estado, COUNT(*) 
            FROM asistencia 
            WHERE alumno_id = ?
            GROUP BY estado
        """, (al['id'],))
        asist_data = dict(cur.fetchall())

        cur.execute("""
            SELECT a.id, a.nombre, ROUND(AVG(e.nota), 2)
            FROM evaluaciones e
            JOIN areas a ON e.area_id = a.id
            WHERE e.alumno_id = ? AND e.trimestre = ?
            GROUP BY a.id, a.nombre
        """, (al['id'], trimestre))
        notas_area = cur.fetchall()

        # Notas SDA con Criterios
        cur.execute("""
            SELECT a.nombre as area, s.nombre as sda, c.codigo as criterio_codigo,
                   c.descripcion as criterio_desc, e.nota
            FROM evaluaciones e
            JOIN sda s ON e.sda_id = s.id
            JOIN areas a ON e.area_id = a.id
            JOIN criterios c ON e.criterio_id = c.id
            WHERE e.alumno_id = ? AND e.trimestre = ?
            ORDER BY a.nombre, s.nombre, c.codigo
        """, (al['id'], trimestre))
        notas_criterios = cur.fetchall()

        # Detalle Faltas
        cur.execute("""
            SELECT fecha, estado
            FROM asistencia
            WHERE alumno_id = ? AND estado IN ('retraso', 'falta_justificada', 'falta_no_justificada')
            AND fecha BETWEEN ? AND ?
            ORDER BY fecha
        """, (al['id'], start_date, end_date))
        faltas_detalle = cur.fetchall()
        
        cur.execute("SELECT texto FROM informe_individual WHERE alumno_id = ? AND trimestre = ?", (al['id'], trimestre))
        obs_row = cur.fetchone()
        obs_text = obs_row["texto"] if obs_row else ""
        
        # Tabla Asistencia
        elements.append(Paragraph("Resumen de Asistencia", styles['Heading3']))
        data_asist = [
            ["Estado", "Días"],
            [Paragraph('<font color="#ffc107">●</font> Retraso', styles['Normal']), asist_data.get('retraso', 0)],
            [Paragraph('<font color="#17a2b8">●</font> Falta Justificada', styles['Normal']), asist_data.get('falta_justificada', 0)],
            [Paragraph('<font color="#dc3545">●</font> Falta No Justificada', styles['Normal']), asist_data.get('falta_no_justificada', 0)],
        ]
        t_asist = Table(data_asist, colWidths=[6*cm, 2*cm])
        t_asist.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
        ]))
        elements.append(t_asist)
        elements.append(Spacer(1, 12))

        elements.append(Spacer(1, 12))
        
        # Detalle Faltas
        if faltas_detalle:
            fechas_str = []
            for f, e in faltas_detalle:
                d_obj = datetime.strptime(f, '%Y-%m-%d')
                d_str = d_obj.strftime('%d/%m')
                
                if e == 'retraso':
                    color = "#ffc107"
                    tipo = "R"
                elif e == 'falta_justificada':
                    color = "#17a2b8"
                    tipo = "F"
                else: # falta_no_justificada
                    color = "#dc3545"
                    tipo = "F"
                    
                fechas_str.append(f'<font color="{color}">{d_str}({tipo})</font>')
            elements.append(Paragraph("<b>Detalle (Día/Tipo):</b> " + ", ".join(fechas_str), styles['Normal']))
            elements.append(Spacer(1, 12))

        # Tabla Notas
        elements.append(Paragraph("Rendimiento Académico", styles['Heading3']))
        
        area_sda_map = {}  # {area_name: {sda_name: [(criterio, nota), ...]}}
        for area, sda, crit_cod, crit_desc, nota in notas_criterios:
            if area not in area_sda_map:
                area_sda_map[area] = {}
            if sda not in area_sda_map[area]:
                area_sda_map[area][sda] = []
            area_sda_map[area][sda].append((f"{crit_cod}", nota))
            
        data_notas = [["Área", "Nota Media", "Detalle SDA y Criterios"]]
        for aid, area_nombre, nota_media in notas_area:
            sda_dict = area_sda_map.get(area_nombre, {})
            detail_lines = []
            for sda_name, criterios in sda_dict.items():
                sda_avg = round(sum(c[1] for c in criterios) / len(criterios), 2) if criterios else 0
                detail_lines.append(f"<b>{sda_name}</b>: {sda_avg}")
                detail_lines.append(f"  • {crit_cod}: {nota}")
            detail_str = "<br/>".join(detail_lines) if detail_lines else "Sin datos"
            data_notas.append([
                Paragraph(area_nombre, styles['Normal']), 
                str(nota_media), 
                Paragraph(detail_str, styles['Normal'])
            ])
            
        t = Table(data_notas, colWidths=[4*cm, 2.5*cm, 10*cm])
        t.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)
        ]))
        elements.append(t)
        
        if obs_text:
             elements.append(Spacer(1, 12))
             elements.append(Paragraph("<b>Observaciones:</b>", styles['Heading3']))
             elements.append(Paragraph(obs_text, styles['Normal']))

        # Signature
        elements.append(Spacer(1, 40))
        if tutor_nombre:
            elements.append(Paragraph(f"Fdo: {tutor_nombre}", styles['Normal']))
            elements.append(Paragraph("(Tutor/a)", styles['Normal']))

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
    import matplotlib
    matplotlib.use('Agg')  # Non-GUI backend
    import matplotlib.pyplot as plt
    from openpyxl.drawing.image import Image as XLImage
    
    trimestre = request.args.get("trimestre")
    conn = get_db()
    cur = conn.cursor()
    
    grupo_id = session.get('active_group_id')
    
    # 1. Notas por Alumno y Área
    query = """
    SELECT al.nombre as Alumno, ar.nombre as Area, ROUND(AVG(e.nota), 2) as Nota
    FROM evaluaciones e
    JOIN alumnos al ON e.alumno_id = al.id
    JOIN areas ar ON e.area_id = ar.id
    WHERE e.trimestre = ? AND al.grupo_id = ?
    GROUP BY al.nombre, ar.nombre
    """
    df_notas = pd.read_sql_query(query, conn, params=(trimestre, grupo_id))
    
    # 2. Valoración del Grupo
    cur.execute("SELECT * FROM informe_grupo WHERE trimestre = ?", (trimestre,))
    row_grupo = cur.fetchone()
    
    grupo_data = {
        "Concepto": ["Valoración", "Propuestas", "Conclusión"],
        "Texto": [
            row_grupo["observaciones"] if row_grupo else "",
            row_grupo["propuestas_mejora"] if row_grupo else "",
            row_grupo["conclusion"] if row_grupo else ""
        ]
    }
    df_grupo = pd.DataFrame(grupo_data)

    # 3. Promoción (Suspensos)
    cur.execute("""
        SELECT a.nombre, COUNT(*) as Num_Suspensos
        FROM evaluaciones e
        JOIN alumnos a ON a.id = e.alumno_id
        WHERE e.trimestre = ? AND e.nota < 5 AND a.grupo_id = ?
        GROUP BY a.id, a.nombre
    """, (trimestre, grupo_id))
    susp_data = cur.fetchall()
    
    # Calcular estadísticas de promoción
    susp_map = {0: 0, 1: 0, 2: 0, 3: 0}
    for r in susp_data:
        n = r["Num_Suspensos"]
        if n > 2:
            susp_map[3] += 1
        else:
            susp_map[n] += 1
    
    cur.execute("SELECT count(*) FROM alumnos WHERE grupo_id = ?", (grupo_id,))
    total_alumnos = cur.fetchone()[0]
    susp_map[0] = total_alumnos - len(susp_data)
    
    # DataFrame de estadísticas de promoción
    promo_stats = {
        "Categoría": ["Todo Aprobado", "1 Suspenso", "2 Suspensos", "+2 Suspensos"],
        "Cantidad": [susp_map[0], susp_map[1], susp_map[2], susp_map[3]],
        "Porcentaje": [
            f"{round(susp_map[0] * 100 / total_alumnos, 1)}%" if total_alumnos > 0 else "0%",
            f"{round(susp_map[1] * 100 / total_alumnos, 1)}%" if total_alumnos > 0 else "0%",
            f"{round(susp_map[2] * 100 / total_alumnos, 1)}%" if total_alumnos > 0 else "0%",
            f"{round(susp_map[3] * 100 / total_alumnos, 1)}%" if total_alumnos > 0 else "0%"
        ]
    }
    df_promo = pd.DataFrame(promo_stats)
    
    # DataFrame de alumnos con suspensos
    df_susp = pd.DataFrame(susp_data, columns=["Alumno", "Num_Suspensos"]) if susp_data else pd.DataFrame(columns=["Alumno", "Num_Suspensos"])

    # 4. Asistencia Destacada
    start_date, end_date = "", ""
    year = date.today().year
    if trimestre == "1":
        start_date = f"{year-1}-09-01"; end_date = f"{year-1}-12-31"
    elif trimestre == "2":
        start_date = f"{year}-01-01"; end_date = f"{year}-03-31"
    else:
        start_date = f"{year}-04-01"; end_date = f"{year}-06-30"

    cur.execute("""
        SELECT a.nombre, estado, COUNT(*) as c
        FROM asistencia asi
        JOIN alumnos a ON a.id = asi.alumno_id
        WHERE asi.fecha BETWEEN ? AND ? AND a.grupo_id = ?
        GROUP BY a.id, a.nombre, estado
        ORDER BY c DESC
    """, (start_date, end_date, grupo_id))
    asist_rows = cur.fetchall()
    
    max_faltas = {"nombre": "Nadie", "num": 0}
    max_retrasos = {"nombre": "Nadie", "num": 0}
    
    temp_faltas = {}
    temp_retrasos = {}
    
    for r in asist_rows:
        if r["estado"] in ["falta_justificada", "falta_no_justificada"]:
            temp_faltas[r["nombre"]] = temp_faltas.get(r["nombre"], 0) + r["c"]
        elif r["estado"] == "retraso":
            temp_retrasos[r["nombre"]] = temp_retrasos.get(r["nombre"], 0) + r["c"]
            
    if temp_faltas:
        u_max = max(temp_faltas, key=temp_faltas.get)
        max_faltas = {"nombre": u_max, "num": temp_faltas[u_max]}
        
    if temp_retrasos:
        u_max = max(temp_retrasos, key=temp_retrasos.get)
        max_retrasos = {"nombre": u_max, "num": temp_retrasos[u_max]}
    
    # DataFrame asistencia destacada
    asist_highlights = {
        "Tipo": ["Alumno con más faltas", "Alumno con más retrasos"],
        "Nombre": [max_faltas["nombre"], max_retrasos["nombre"]],
        "Cantidad": [max_faltas["num"], max_retrasos["num"]]
    }
    df_asist = pd.DataFrame(asist_highlights)
    
    
    # --- GENERAR GRÁFICAS ---
    
    # Gráfica 1: Pie Chart de Promoción
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    colors_promo = ['#28a745', '#ffc107', '#fd7e14', '#dc3545']
    ax1.pie([susp_map[0], susp_map[1], susp_map[2], susp_map[3]], 
            labels=promo_stats["Categoría"],
            autopct='%1.1f%%',
            colors=colors_promo,
            startangle=90)
    ax1.set_title('Análisis de Promoción')
    promo_chart = BytesIO()
    plt.savefig(promo_chart, format='png', bbox_inches='tight')
    promo_chart.seek(0)
    plt.close()
    
    # Gráfica 2: Bar Chart de Asistencia
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    categories = ['Faltas', 'Retrasos']
    values = [max_faltas["num"], max_retrasos["num"]]
    colors_asist = ['#dc3545', '#fd7e14']
    ax2.bar(categories, values, color=colors_asist)
    ax2.set_ylabel('Cantidad')
    ax2.set_title('Asistencia Destacada (Máximos)')
    ax2.grid(axis='y', alpha=0.3)
    asist_chart = BytesIO()
    plt.savefig(asist_chart, format='png', bbox_inches='tight')
    asist_chart.seek(0)
    plt.close()
    
    # Gráfica 3: Bar Chart de Rendimiento por Área
    if not df_notas.empty:
        area_avg = df_notas.groupby('Area')['Nota'].mean().sort_values(ascending=False)
        fig3, ax3 = plt.subplots(figsize=(8, 5))
        ax3.barh(area_avg.index, area_avg.values, color='#17a2b8')
        ax3.set_xlabel('Nota Media')
        ax3.set_title('Rendimiento por Área')
        ax3.grid(axis='x', alpha=0.3)
        area_chart = BytesIO()
        plt.savefig(area_chart, format='png', bbox_inches='tight')
        area_chart.seek(0)
        plt.close()
    else:
        area_chart = None
    
    # --- GENERAR EXCEL ---
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet 1: Notas Pivot
        if not df_notas.empty:
            pivot = df_notas.pivot(index='Alumno', columns='Area', values='Nota')
            pivot.to_excel(writer, sheet_name=f'Notas_T{trimestre}')
            
        # Sheet 2: Valoración
        df_grupo.to_excel(writer, sheet_name="Valoracion_Grupo", index=False)
        
        # Sheet 3: Promoción
        df_promo.to_excel(writer, sheet_name="Promocion", index=False, startrow=0)
        ws_promo = writer.sheets["Promocion"]
        
        # Insertar gráfica de promoción
        img_promo = XLImage(promo_chart)
        ws_promo.add_image(img_promo, 'E2')
        
        # Sheet 4: Alumnos con Suspensos
        if not df_susp.empty:
            df_susp.to_excel(writer, sheet_name="Alumnos_Suspensos", index=False)
        
        # Sheet 5: Asistencia
        df_asist.to_excel(writer, sheet_name="Asistencia", index=False, startrow=0)
        ws_asist = writer.sheets["Asistencia"]
        
        # Insertar gráfica de asistencia
        img_asist = XLImage(asist_chart)
        ws_asist.add_image(img_asist, 'E2')
        
        # Sheet 6: Rendimiento por Área (con gráfica)
        if area_chart:
            area_avg_df = area_avg.reset_index()
            area_avg_df.columns = ['Área', 'Nota Media']
            area_avg_df.to_excel(writer, sheet_name="Rendimiento_Areas", index=False)
            ws_areas = writer.sheets["Rendimiento_Areas"]
            img_areas = XLImage(area_chart)
            ws_areas.add_image(img_areas, 'D2')
        
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name=f"Resumen_Grupo_T{trimestre}.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@informes_bp.route("/api/informe/pdf_grupo")
def pdf_grupo():
    trimestre = request.args.get("trimestre")
    
    conn = get_db()
    cur = conn.cursor()
    
    # --- 1. DATOS GRUPALES ---
    # Valoración
    cur.execute("SELECT * FROM informe_grupo WHERE trimestre = ?", (trimestre,))
    row_grupo = cur.fetchone()
    
    grupo_id = session.get('active_group_id')
    
    # Promoción (Suspensos)
    cur.execute("""
        SELECT a.nombre, COUNT(*) as num_suspensos
        FROM evaluaciones e
        JOIN alumnos a ON a.id = e.alumno_id
        WHERE e.trimestre = ? AND e.nota < 5 AND a.grupo_id = ?
        GROUP BY a.id, a.nombre
    """, (trimestre, grupo_id))
    suspensos_data = cur.fetchall()
    
    susp_map = {0: 0, 1: 0, 2: 0, 3: 0} # 0, 1, 2, +2
    for r in suspensos_data:
        n = r["num_suspensos"]
        if n > 2:
            susp_map[3] += 1
        else:
            susp_map[n] += 1
            
    # Total alumnos (para los que tienen 0 suspensos)
    cur.execute("SELECT count(*) FROM alumnos WHERE grupo_id = ?", (grupo_id,))
    total_alumnos = cur.fetchone()[0]
    susp_map[0] = total_alumnos - len(suspensos_data)

    # Asistencia Max
    start_date, end_date = "", ""
    year = date.today().year
    if trimestre == "1":
        start_date = f"{year-1}-09-01"; end_date = f"{year-1}-12-31"
    elif trimestre == "2":
        start_date = f"{year}-01-01"; end_date = f"{year}-03-31"
    else:
        start_date = f"{year}-04-01"; end_date = f"{year}-06-30"

    cur.execute("""
        SELECT a.nombre, estado, COUNT(*) as c
        FROM asistencia asi
        JOIN alumnos a ON a.id = asi.alumno_id
        WHERE asi.fecha BETWEEN ? AND ? AND a.grupo_id = ?
        GROUP BY a.id, a.nombre, estado
        ORDER BY c DESC
    """, (start_date, end_date, grupo_id))
    asist_rows = cur.fetchall()
    
    max_faltas = {"nombre": "Nadie", "num": 0}
    max_retrasos = {"nombre": "Nadie", "num": 0}
    
    # Process max
    temp_faltas = {}
    temp_retrasos = {}
    
    for r in asist_rows:
        if r["estado"] in ["falta_justificada", "falta_no_justificada"]:
            temp_faltas[r["nombre"]] = temp_faltas.get(r["nombre"], 0) + r["c"]
        elif r["estado"] == "retraso":
            temp_retrasos[r["nombre"]] = temp_retrasos.get(r["nombre"], 0) + r["c"]
            
    if temp_faltas:
        u_max = max(temp_faltas, key=temp_faltas.get)
        max_faltas = {"nombre": u_max, "num": temp_faltas[u_max]}
        
    if temp_retrasos:
        u_max = max(temp_retrasos, key=temp_retrasos.get)
        max_retrasos = {"nombre": u_max, "num": temp_retrasos[u_max]}
    
    
    # --- GENERAR GRÁFICAS ---
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from reportlab.platypus import Image as RLImage
    
    # Gráfica 1: Pie Chart de Promoción
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    colors_promo = ['#28a745', '#ffc107', '#fd7e14', '#dc3545']
    ax1.pie([susp_map[0], susp_map[1], susp_map[2], susp_map[3]], 
            labels=["Todo Aprobado", "1 Suspenso", "2 Suspensos", "+2 Suspensos"],
            autopct='%1.1f%%',
            colors=colors_promo,
            startangle=90)
    ax1.set_title('Análisis de Promoción')
    promo_chart_buf = BytesIO()
    plt.savefig(promo_chart_buf, format='png', bbox_inches='tight', dpi=150)
    promo_chart_buf.seek(0)
    plt.close()
    
    # Gráfica 2: Bar Chart de Asistencia
    fig2, ax2 = plt.subplots(figsize=(6, 3.5))
    categories = ['Faltas\n' + max_faltas["nombre"], 'Retrasos\n' + max_retrasos["nombre"]]
    values = [max_faltas["num"], max_retrasos["num"]]
    colors_asist = ['#dc3545', '#fd7e14']
    ax2.bar(categories, values, color=colors_asist, width=0.6)
    ax2.set_ylabel('Cantidad')
    ax2.set_title('Asistencia Destacada')
    ax2.grid(axis='y', alpha=0.3)
    for i, v in enumerate(values):
        ax2.text(i, v + 0.5, str(v), ha='center', fontweight='bold')
    asist_chart_buf = BytesIO()
    plt.savefig(asist_chart_buf, format='png', bbox_inches='tight', dpi=150)
    asist_chart_buf.seek(0)
    plt.close()
    
    # --- GENERAR PDF ---
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph(f"Informe Global de Grupo - Trimestre {trimestre}", styles['Title']))
    elements.append(Spacer(1, 20))
    
    # 1. Valoración
    if row_grupo:
        if row_grupo["observaciones"]:
            elements.append(Paragraph("Valoración General:", styles['Heading3']))
            elements.append(Paragraph(row_grupo["observaciones"], styles['BodyText']))
        if row_grupo["propuestas_mejora"]:
            elements.append(Paragraph("Propuestas de Mejora:", styles['Heading3']))
            elements.append(Paragraph(row_grupo["propuestas_mejora"], styles['BodyText']))
        if row_grupo["conclusion"]:
            elements.append(Paragraph("Conclusión:", styles['Heading3']))
            elements.append(Paragraph(row_grupo["conclusion"], styles['BodyText']))
    else:
        elements.append(Paragraph("No hay valoración grupal registrada.", styles['Normal']))
    elements.append(Spacer(1, 15))
    
    # 2. Promoción con Gráfica
    elements.append(Paragraph("Análisis de Promoción (Resultados):", styles['Heading3']))
    
    def calc_pct(n):
        return f"{round(n * 100 / total_alumnos, 1)}%" if total_alumnos > 0 else "0%"

    data_prom = [
        ["Todo Aprobado", f"{susp_map[0]} ({calc_pct(susp_map[0])})"],
        ["1 Suspenso", f"{susp_map[1]} ({calc_pct(susp_map[1])})"],
        ["2 Suspensos", f"{susp_map[2]} ({calc_pct(susp_map[2])})"],
        ["+2 Suspensos", f"{susp_map[3]} ({calc_pct(susp_map[3])})"]
    ]
    t_prom = Table(data_prom, colWidths=[4*cm, 4*cm])
    t_prom.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.grey),
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey)
    ]))
    elements.append(t_prom)
    elements.append(Spacer(1, 10))
    
    # Insertar gráfica de promoción
    promo_img = RLImage(promo_chart_buf, width=12*cm, height=8*cm)
    elements.append(promo_img)
    elements.append(Spacer(1, 15))
    
    # 3. Asistencia Highlights con Gráfica
    elements.append(Paragraph("Datos de Asistencia Destacados:", styles['Heading3']))
    elements.append(Paragraph(f"• Alumno/a con más faltas: <b>{max_faltas['nombre']}</b> ({max_faltas['num']} faltas)", styles['Normal']))
    elements.append(Paragraph(f"• Alumno/a con más retrasos: <b>{max_retrasos['nombre']}</b> ({max_retrasos['num']} retrasos)", styles['Normal']))
    elements.append(Spacer(1, 10))
    
    # Insertar gráfica de asistencia
    asist_img = RLImage(asist_chart_buf, width=12*cm, height=7*cm)
    elements.append(asist_img)
    elements.append(Spacer(1, 12))
        
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
        
    doc.build(elements)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"Rubricas_{sda_name}.pdf",
        mimetype='application/pdf'
    )
