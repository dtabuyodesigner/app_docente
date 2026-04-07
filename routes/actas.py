from flask import Blueprint, jsonify, request, session, send_file
from utils.db import get_db
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, HRFlowable
from reportlab.lib.units import cm
import os
from datetime import datetime

actas_bp = Blueprint('actas', __name__)

@actas_bp.route("/api/actas", methods=["POST"])
def crear_acta():
    d = request.json
    alumno_id = d.get("alumno_id")
    fecha_hecho = d.get("fecha_hecho")
    lugar = d.get("lugar", "")
    profesor = d.get("profesor", "")
    descripcion = d.get("descripcion", "")
    firmante = d.get("firmante", "")
    
    # Obtener firma del tutor si no se especifica una
    firma_filename = d.get("firma_filename")
    if not firma_filename:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT valor FROM config WHERE clave = 'tutor_firma_filename'")
        row = cur.fetchone()
        if row:
            firma_filename = row["valor"]
            
    fecha_creacion = datetime.now().strftime("%Y-%m-%d")
    
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO actas_incidencias (fecha_creacion, fecha_hecho, lugar, profesor, alumno_id, descripcion, firmante, firma_filename)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (fecha_creacion, fecha_hecho, lugar, profesor, alumno_id, descripcion, firmante, firma_filename))
        conn.commit()
        return jsonify({"ok": True, "id": cur.lastrowid})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@actas_bp.route("/api/actas", methods=["GET"])
def listar_actas():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.*, al.nombre as alumno_nombre 
        FROM actas_incidencias a
        LEFT JOIN alumnos al ON a.alumno_id = al.id
        ORDER BY a.fecha_hecho DESC
    """)
    data = cur.fetchall()
    return jsonify([dict(r) for r in data])

@actas_bp.route("/api/actas/<int:acta_id>", methods=["DELETE"])
def borrar_acta(acta_id):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM actas_incidencias WHERE id = ?", (acta_id,))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@actas_bp.route("/api/actas/equipo_docente", methods=["GET"])
def get_equipo_docente():
    """Devuelve el equipo docente del grupo activo y el tutor."""
    grupo_id = session.get('active_group_id')
    if not grupo_id:
        return jsonify({"ok": False, "error": "No hay grupo activo"}), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT equipo_docente FROM grupos WHERE id = ?", (grupo_id,))
    row = cur.fetchone()

    equipo_docente = []
    if row and row["equipo_docente"]:
        equipo_docente = [
            line.strip()
            for line in row["equipo_docente"].replace('\r', '').split('\n')
            if line.strip()
        ]

    # El tutor real viene de la config global (Ajustes → Datos del Tutor/a)
    cur.execute("SELECT valor FROM config WHERE clave = 'nombre_tutor'")
    cfg_row = cur.fetchone()
    nombre_tutor = cfg_row["valor"] if cfg_row and cfg_row["valor"] else ""

    return jsonify({
        "ok": True,
        "equipo_docente": equipo_docente,
        "nombre_tutor": nombre_tutor
    })

@actas_bp.route("/api/actas/<int:acta_id>/pdf")
def generar_pdf_acta(acta_id):
    """Genera el PDF del Acta de Incidencia con estilo formal."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.*, al.nombre as alumno_nombre
        FROM actas_incidencias a
        LEFT JOIN alumnos al ON a.alumno_id = al.id
        WHERE a.id = ?
    """, (acta_id,))
    acta = cur.fetchone()
    if not acta:
        return "Acta no encontrada", 404

    # Configuración de logos y firmas
    cur.execute("SELECT clave, valor FROM config WHERE clave LIKE 'logo_%' OR clave LIKE 'tutor_%' OR clave = 'nombre_centro' OR clave = 'curso_escolar'")
    config = {r["clave"]: r["valor"] for r in cur.fetchall()}

    from utils.db import get_app_data_dir
    uploads_dir = os.path.join(get_app_data_dir(), "uploads")

    # Obtener nombre del grupo
    cur.execute("SELECT g.nombre, g.equipo_docente FROM grupos g JOIN alumnos a ON a.grupo_id = g.id WHERE a.id = ?", (acta["alumno_id"],))
    grupo_row = cur.fetchone()
    grupo_nombre = grupo_row["nombre"] if grupo_row else ""

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           leftMargin=2*cm, rightMargin=2*cm,
                           topMargin=1.5*cm, bottomMargin=2*cm)
    elements = []
    styles = getSampleStyleSheet()

    # Estilos personalizados
    style_label = ParagraphStyle('ActaLabel', parent=styles['Normal'],
                                fontSize=10, fontName='Helvetica-Bold', spaceAfter=4)
    style_desc = ParagraphStyle('ActaDesc', parent=styles['Normal'],
                                fontSize=10, leading=18, spaceAfter=8,
                                leftIndent=10)

    # Función auxiliar para cargar logos
    def get_logo_path(lado):
        fn = config.get(f"logo_{lado}_filename")
        if fn:
            p = os.path.join(uploads_dir, fn)
            if os.path.exists(p):
                return p
        return None

    logo_izda = get_logo_path("izda")
    logo_dcha = get_logo_path("dcha")
    pos_izda = config.get("logo_izda_posicion", "left")
    pos_dcha = config.get("logo_dcha_posicion", "right")

    # Obtener firma del tutor
    firma_fn = acta["firma_filename"] or config.get("tutor_firma_filename")
    firma_path = None
    if firma_fn:
        p = os.path.join(uploads_dir, firma_fn)
        if os.path.exists(p):
            firma_path = p

    # Obtener nombre del tutor desde config
    tutor_nombre_config = config.get("nombre_tutor", "")
    
    # Determinar firmante
    firmante_nombre = acta["firmante"] or tutor_nombre_config or "El/La Tutor/a"

    # Obtener nombre del centro
    nombre_centro = config.get("nombre_centro", "CEIP")
    curso_escolar = config.get("curso_escolar", "")

    # Construir cabecera con logos (estilo acta evaluación)
    from reportlab.platypus import Table as RLTable, TableStyle as RLTableStyle
    from reportlab.lib import colors as rl_colors

    logo_izda_el = None
    logo_dcha_el = None
    if logo_izda and os.path.exists(logo_izda):
        try:
            logo_izda_el = RLImage(logo_izda, width=3*cm, height=2*cm)
            logo_izda_el.hAlign = pos_izda.upper()
        except:
            logo_izda_el = None
    if logo_dcha and os.path.exists(logo_dcha):
        try:
            logo_dcha_el = RLImage(logo_dcha, width=3*cm, height=2*cm)
            logo_dcha_el.hAlign = pos_dcha.upper()
        except:
            logo_dcha_el = None

    col_izda = logo_izda_el if logo_izda_el else Paragraph(" ", styles['Normal'])
    col_centro = Paragraph(
        f"<b>{nombre_centro}</b><br/><b>ACTA DE INCIDENCIA</b>{('<br/>Curso ' + curso_escolar) if curso_escolar else ''}",
        ParagraphStyle('h', parent=styles['Normal'], alignment=1, fontSize=11, fontName='Helvetica-Bold', leading=16)
    )
    col_dcha = logo_dcha_el if logo_dcha_el else Paragraph(" ", styles['Normal'])

    header_tbl = RLTable([[col_izda, col_centro, col_dcha]], colWidths=[3.5*cm, 10*cm, 3.5*cm])
    header_tbl.setStyle(RLTableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
    ]))
    elements.append(header_tbl)
    elements.append(HRFlowable(width="100%", thickness=1, color=rl_colors.black, spaceAfter=10))

    # Datos básicos del acta
    fecha_hecho = acta["fecha_hecho"] or "No especificada"
    # Formatear fecha si viene como YYYY-MM-DD
    try:
        from datetime import datetime
        fecha_obj = datetime.strptime(fecha_hecho, "%Y-%m-%d")
        fecha_hecho_fmt = fecha_obj.strftime("%d/%m/%Y")
    except:
        fecha_hecho_fmt = fecha_hecho

    lugar_str = acta["lugar"] or "No especificado"
    alumno_nombre = acta["alumno_nombre"] or "No especificado"
    profesor_str = acta["profesor"] or "No especificado"

    # Sección de datos informativos
    elements.append(Paragraph("<b>DATOS DE LA INCIDENCIA</b>", style_label))
    elements.append(Spacer(1, 6))

    # Usar Paragraph para que funcionen las negritas en las celdas
    style_cell = ParagraphStyle('TableCell', parent=styles['Normal'], fontSize=10)
    
    datos_basicos = [
        [Paragraph("<b>Alumno/a:</b>", style_cell), Paragraph(alumno_nombre, style_cell)],
        [Paragraph("<b>Grupo:</b>", style_cell), Paragraph(grupo_nombre, style_cell)],
        [Paragraph("<b>Fecha del hecho:</b>", style_cell), Paragraph(fecha_hecho_fmt, style_cell)],
        [Paragraph("<b>Lugar:</b>", style_cell), Paragraph(lugar_str, style_cell)],
        [Paragraph("<b>Profesor/a implicado/a:</b>", style_cell), Paragraph(profesor_str, style_cell)],
    ]
    
    t_datos = RLTable(datos_basicos, colWidths=[5.5*cm, 11*cm])
    t_datos.setStyle(RLTableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (-1, -2), 0.3, rl_colors.lightgrey),
    ]))
    elements.append(t_datos)
    elements.append(Spacer(1, 12))

    # Descripción con saltos de párrafo
    elements.append(Paragraph("<b>DESCRIPCIÓN DE LOS HECHOS</b>", style_label))
    elements.append(Spacer(1, 6))

    descripcion_raw = acta["descripcion"] or "Sin descripción."
    
    # Procesar la descripción conservando los saltos de línea (sin añadir numeración auto)
    lineas = [l.strip() for l in descripcion_raw.replace('\r\n', '\n').replace('\r', '\n').split('\n') if l.strip()]
    
    for linea in lineas:
        elements.append(Paragraph(linea, style_desc))
    
    elements.append(Spacer(1, 20))

    # Sección de firmas
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("<b>FIRMAS</b>", style_label))
    elements.append(Spacer(1, 10))

    # Construir tabla de firmas (Firma a la izquierda con el nombre)
    sig_data = [["Firma del/la Tutor/a o Docente", "Firma del/la Alumno/a"]]
    
    style_firma_nombre = ParagraphStyle('firmaNombre', parent=styles['Normal'],
                                        fontSize=9, alignment=1, textColor=rl_colors.grey)
    
    # Celda izquierda: Imagen de firma + Nombre
    celda_firma_izda_content = []
    if firma_path:
        try:
            img_f = RLImage(firma_path, width=4.5*cm, height=1.5*cm, kind='proportional')
            img_f.hAlign = 'CENTER'
            celda_firma_izda_content.append(img_f)
        except Exception as e:
            print(f"[ERROR] No se pudo cargar la firma: {e}")
    celda_firma_izda_content.append(Paragraph(f"<b>{firmante_nombre}</b>", style_firma_nombre))

    # Celda derecha: Espacio para firma del alumno
    celda_firma_dcha_content = [Spacer(1, 1*cm), Paragraph("(Firma del alumno/a)", style_firma_nombre)]

    sig_data.append([celda_firma_izda_content, celda_firma_dcha_content])

    t_sig = RLTable(sig_data, colWidths=[8*cm, 8*cm],
                    rowHeights=[0.7*cm, 2.5*cm])
    t_sig.setStyle(RLTableStyle([
        ('GRID', (0, 0), (-1,-1), 0.5, rl_colors.black),
        ('BACKGROUND', (0,0), (-1,0), rl_colors.lightgrey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 1), (-1, 1), 5),
    ]))
    elements.append(t_sig)

    doc.build(elements)
    buffer.seek(0)

    return send_file(buffer, download_name=f"Acta_Incidencia_{acta_id}.pdf", as_attachment=True)
