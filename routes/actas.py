from flask import Blueprint, jsonify, request, session, send_file
from utils.db import get_db
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
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
    
    # Estilo título
    style_title = ParagraphStyle('ActaTitle', parent=styles['Normal'],
                                fontSize=14, fontName='Helvetica-Bold',
                                alignment=1, spaceAfter=12)
    
    # Cabecera
    elements.append(Paragraph("ACTA DE INCIDENCIA", style_title))
    
    # Datos básicos
    datos = [
        ["Fecha del hecho:", acta["fecha_hecho"]],
        ["Lugar:", acta["lugar"] or "No especificado"],
        ["Profesor/a implicado/a:", acta["profesor"] or "No especificado"],
    ]
    if acta["alumno_nombre"]:
        datos.append(["Alumno/a afectado/a:", acta["alumno_nombre"]])
        
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
    elements.append(Spacer(1, 20))
    
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
