from flask import Blueprint, jsonify, request, session, send_file
from utils.db import get_db
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, HRFlowable
from reportlab.lib import colors
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

@actas_bp.route("/api/actas/<int:acta_id>/pdf")
def generar_pdf_acta(acta_id):
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
    cur.execute("SELECT clave, valor FROM config WHERE clave LIKE 'logo_%' OR clave = 'tutor_firma_filename' OR clave = 'nombre_centro'")
    config = {r["clave"]: r["valor"] for r in cur.fetchall()}

    from utils.db import get_app_data_dir
    uploads_dir = os.path.join(get_app_data_dir(), "uploads")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           leftMargin=2*cm, rightMargin=2*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    elements = []
    styles = getSampleStyleSheet()

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

    # Cabecera con logos
    header_data = []
    header_styles = []

    if logo_izda and logo_dcha:
        # Dos logos
        try:
            img_izda = RLImage(logo_izda, width=3*cm, height=2*cm, kind='proportional')
            img_dcha = RLImage(logo_dcha, width=3*cm, height=2*cm, kind='proportional')
        except:
            img_izda = Paragraph("Logo", styles['Normal'])
            img_dcha = Paragraph("Logo", styles['Normal'])
            
        header_data = [[img_izda, Paragraph("ACTA DE INCIDENCIA", ParagraphStyle('HeaderTitle', parent=styles['Normal'],
                                fontSize=16, fontName='Helvetica-Bold', alignment=1)), img_dcha]]
        header_styles = [('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                        ('ALIGN', (0, 0), (0, 0), pos_izda.upper()),
                        ('ALIGN', (2, 0), (2, 0), pos_dcha.upper())]
    elif logo_izda:
        try:
            img_izda = RLImage(logo_izda, width=3*cm, height=2*cm, kind='proportional')
        except:
            img_izda = Paragraph("Logo", styles['Normal'])
        header_data = [[img_izda, Paragraph("ACTA DE INCIDENCIA", ParagraphStyle('HeaderTitle', parent=styles['Normal'],
                                fontSize=16, fontName='Helvetica-Bold', alignment=1))]]
        header_styles = [('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                        ('ALIGN', (0, 0), (0, 0), pos_izda.upper())]
    elif logo_dcha:
        try:
            img_dcha = RLImage(logo_dcha, width=3*cm, height=2*cm, kind='proportional')
        except:
            img_dcha = Paragraph("Logo", styles['Normal'])
        header_data = [[Paragraph("ACTA DE INCIDENCIA", ParagraphStyle('HeaderTitle', parent=styles['Normal'],
                                fontSize=16, fontName='Helvetica-Bold', alignment=1)), img_dcha]]
        header_styles = [('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                        ('ALIGN', (1, 0), (1, 0), pos_dcha.upper())]
    else:
        header_data = [[Paragraph("ACTA DE INCIDENCIA", ParagraphStyle('HeaderTitle', parent=styles['Normal'],
                                fontSize=16, fontName='Helvetica-Bold', alignment=1))]]

    if header_data:
        if logo_izda and logo_dcha:
            col_widths = [3*cm, None, 3*cm]
        elif logo_izda:
            col_widths = [3*cm, None]
        elif logo_dcha:
            col_widths = [None, 3*cm]
        else:
            col_widths = [None]
        t_header = Table(header_data, colWidths=col_widths)
        t_header.setStyle(TableStyle(header_styles + [
            ('LEFTPADDING', (0, 0), (-1, 0), 0),
            ('RIGHTPADDING', (0, 0), (-1, 0), 0),
        ]))
        elements.append(t_header)
        elements.append(Spacer(1, 10))

    # Línea separadora
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#003366'), spaceAfter=15))

    # Datos básicos
    datos = [
        ["Fecha del hecho:", acta["fecha_hecho"]],
        ["Lugar:", acta["lugar"] or "No especificado"],
        ["Profesor/a implicado/a:", acta["profesor"] or "No especificado"],
    ]
    if acta["alumno_nombre"]:
        datos.append(["Alumno/a afectado/a:", acta["alumno_nombre"]])
    if acta["firmante"]:
        datos.append(["Firmante:", acta["firmante"]])

    t = Table(datos, colWidths=[5*cm, 10*cm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 12))

    # Descripción
    elements.append(Paragraph("<b>Descripción de los hechos:</b>", styles['Normal']))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(acta["descripcion"] or "Sin descripción.", styles['Normal']))
    elements.append(Spacer(1, 30))

    # Firmas
    elements.append(Spacer(1, 20))
    firmas_data = [["", ""]]

    # Firma del firmante
    firmante_nombre = acta["firmante"] or "El/La Tutor/a"
    firmas_data[0][0] = Paragraph(f"<b>{firmante_nombre}</b>", styles['Normal'])

    # Si hay firma escaneada, incluirla
    firma_fn = acta["firma_filename"]
    if firma_fn:
        firma_path = os.path.join(uploads_dir, firma_fn)
        if os.path.exists(firma_path):
            try:
                img = RLImage(firma_path, width=4*cm, height=2*cm, kind='proportional')
                firmas_data[0][0] = Table([[firmas_data[0][0]], [img]])
            except:
                pass

    t_firmas = Table(firmas_data, colWidths=[8*cm, 8*cm])
    t_firmas.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(t_firmas)

    doc.build(elements)
    buffer.seek(0)

    return send_file(buffer, download_name=f"Acta_{acta_id}.pdf", as_attachment=True)
