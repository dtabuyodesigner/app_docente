from flask import Blueprint, jsonify, request
from utils.db import get_db
import json

excursiones_bp = Blueprint('excursiones', __name__)


# ─────────────────────────────────────────────
# PÁGINAS HTML
# ─────────────────────────────────────────────

@excursiones_bp.route("/excursiones")
def page_excursiones():
    from flask import send_from_directory
    return send_from_directory('static', 'excursiones.html')


@excursiones_bp.route("/autorizaciones")
def page_autorizaciones():
    from flask import send_from_directory
    return send_from_directory('static', 'autorizaciones.html')


# ─────────────────────────────────────────────
# API EXCURSIONES
# ─────────────────────────────────────────────

@excursiones_bp.route("/api/excursiones", methods=["GET", "POST"])
def api_excursiones():
    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        d = request.json or {}
        titulo = d.get("titulo", "").strip()
        if not titulo:
            return jsonify({"ok": False, "error": "El título es obligatorio"}), 400

        tipo = d.get("tipo", "excursion")
        fecha = d.get("fecha")
        destino = d.get("destino", "")
        descripcion = d.get("descripcion", "")
        grupo_ids_list = d.get("grupo_ids", [])
        grupo_ids = json.dumps(grupo_ids_list)
        grupos_extra = d.get("grupos_extra", "")
        requiere_autorizacion = 1 if d.get("requiere_autorizacion", True) else 0
        requiere_pago = 1 if d.get("requiere_pago", False) else 0
        coste = d.get("coste")
        fecha_limite = d.get("fecha_limite")
        hora_salida = d.get("hora_salida", "")
        hora_regreso = d.get("hora_regreso", "")

        cur.execute("""
            INSERT INTO excursiones
                (tipo, titulo, fecha, destino, descripcion, grupo_ids, grupos_extra,
                 requiere_autorizacion, requiere_pago, coste, fecha_limite, estado,
                 hora_salida, hora_regreso)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'activa', ?, ?)
        """, (tipo, titulo, fecha, destino, descripcion, grupo_ids, grupos_extra,
              requiere_autorizacion, requiere_pago, coste, fecha_limite,
              hora_salida, hora_regreso))
        conn.commit()
        excursion_id = cur.lastrowid

        # Generar filas en excursion_alumnos para los grupos indicados
        alumno_ids = _alumnos_de_grupos(cur, grupo_ids_list)
        for aid in alumno_ids:
            cur.execute("""
                INSERT OR IGNORE INTO excursion_alumnos (excursion_id, alumno_id)
                VALUES (?, ?)
            """, (excursion_id, aid))
        conn.commit()

        return jsonify({"ok": True, "id": excursion_id})

    # GET — lista con estadísticas
    rows = cur.execute("""
        SELECT e.*,
               COUNT(ea.id) AS total_alumnos,
               SUM(CASE WHEN ea.estado_auto='autorizado' THEN 1 ELSE 0 END) AS total_autorizados,
               SUM(ea.pagado) AS total_pagados
        FROM excursiones e
        LEFT JOIN excursion_alumnos ea ON ea.excursion_id = e.id
        GROUP BY e.id
        ORDER BY e.fecha DESC, e.created_at DESC
    """).fetchall()

    return jsonify([dict(r) for r in rows])


@excursiones_bp.route("/api/excursiones/dashboard")
def api_excursiones_dashboard():
    """Resumen de pendientes para el dashboard."""
    conn = get_db()
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT e.id, e.titulo, e.fecha, e.tipo,
               e.requiere_autorizacion, e.requiere_pago,
               COUNT(ea.id) AS total,
               SUM(CASE WHEN e.requiere_autorizacion=1 AND (ea.estado_auto IS NULL OR ea.estado_auto='pendiente') THEN 1 ELSE 0 END) AS pendientes_auto,
               SUM(CASE WHEN e.requiere_pago=1 AND ea.pagado=0 THEN 1 ELSE 0 END) AS pendientes_pago
        FROM excursiones e
        LEFT JOIN excursion_alumnos ea ON ea.excursion_id = e.id
        WHERE e.estado = 'activa'
        GROUP BY e.id
        HAVING (pendientes_auto > 0 OR pendientes_pago > 0)
        ORDER BY e.fecha ASC
    """).fetchall()

    return jsonify([dict(r) for r in rows])


@excursiones_bp.route("/api/excursiones/<int:excursion_id>", methods=["GET", "PUT", "DELETE"])
def api_excursion_detalle(excursion_id):
    conn = get_db()
    cur = conn.cursor()

    if request.method == "DELETE":
        cur.execute("DELETE FROM excursiones WHERE id=?", (excursion_id,))
        conn.commit()
        return jsonify({"ok": True})

    if request.method == "PUT":
        d = request.json or {}
        titulo = d.get("titulo", "").strip()
        if not titulo:
            return jsonify({"ok": False, "error": "El título es obligatorio"}), 400

        tipo = d.get("tipo", "excursion")
        fecha = d.get("fecha")
        destino = d.get("destino", "")
        descripcion = d.get("descripcion", "")
        grupo_ids_list = d.get("grupo_ids", [])
        grupo_ids = json.dumps(grupo_ids_list)
        grupos_extra = d.get("grupos_extra", "")
        requiere_autorizacion = 1 if d.get("requiere_autorizacion", True) else 0
        requiere_pago = 1 if d.get("requiere_pago", False) else 0
        coste = d.get("coste")
        fecha_limite = d.get("fecha_limite")
        hora_salida = d.get("hora_salida", "")
        hora_regreso = d.get("hora_regreso", "")
        estado = d.get("estado", "activa")

        cur.execute("""
            UPDATE excursiones SET
                tipo=?, titulo=?, fecha=?, destino=?, descripcion=?, grupo_ids=?,
                grupos_extra=?, requiere_autorizacion=?, requiere_pago=?,
                coste=?, fecha_limite=?, hora_salida=?, hora_regreso=?, estado=?
            WHERE id=?
        """, (tipo, titulo, fecha, destino, descripcion, grupo_ids,
              grupos_extra, requiere_autorizacion, requiere_pago,
              coste, fecha_limite, hora_salida, hora_regreso, estado,
              excursion_id))

        # Sincronizar alumnos: añadir los de grupos nuevos (no eliminar existentes)
        alumno_ids_nuevos = _alumnos_de_grupos(cur, grupo_ids_list)
        for aid in alumno_ids_nuevos:
            cur.execute("""
                INSERT OR IGNORE INTO excursion_alumnos (excursion_id, alumno_id)
                VALUES (?, ?)
            """, (excursion_id, aid))
        conn.commit()
        return jsonify({"ok": True})

    # GET — datos + alumnos
    row = cur.execute("SELECT * FROM excursiones WHERE id=?", (excursion_id,)).fetchone()
    if not row:
        return jsonify({"ok": False, "error": "No encontrada"}), 404

    alumnos = cur.execute("""
        SELECT ea.*, a.nombre
        FROM excursion_alumnos ea
        JOIN alumnos a ON a.id = ea.alumno_id
        WHERE ea.excursion_id = ?
        ORDER BY a.nombre
    """, (excursion_id,)).fetchall()

    data = dict(row)
    data["alumnos"] = [dict(a) for a in alumnos]
    return jsonify(data)


@excursiones_bp.route("/api/excursiones/<int:excursion_id>/alumnos/<int:alumno_id>", methods=["PATCH"])
def api_toggle_alumno(excursion_id, alumno_id):
    """Toggle autorizado / pagado de un alumno en una excursión."""
    conn = get_db()
    cur = conn.cursor()
    d = request.json or {}

    updates = []
    params = []

    if "estado_auto" in d:
        estado_auto = d["estado_auto"]
        updates.append("estado_auto=?")
        params.append(estado_auto)
        updates.append("autorizado=?")
        params.append(1 if estado_auto == "autorizado" else 0)
        updates.append("fecha_autorizacion=?")
        from datetime import date as _date
        params.append(_date.today().isoformat() if estado_auto != "pendiente" else None)
    elif "autorizado" in d:
        updates.append("autorizado=?")
        params.append(1 if d["autorizado"] else 0)
        updates.append("estado_auto=?")
        params.append("autorizado" if d["autorizado"] else "pendiente")
        updates.append("fecha_autorizacion=?")
        params.append(d.get("fecha_autorizacion") if d["autorizado"] else None)

    if "pagado" in d:
        updates.append("pagado=?")
        params.append(1 if d["pagado"] else 0)
        updates.append("fecha_pago=?")
        params.append(d.get("fecha_pago") if d["pagado"] else None)

    if "observaciones" in d:
        updates.append("observaciones=?")
        params.append(d["observaciones"])

    if not updates:
        return jsonify({"ok": False, "error": "Nada que actualizar"}), 400

    params += [excursion_id, alumno_id]
    cur.execute(f"""
        UPDATE excursion_alumnos SET {', '.join(updates)}
        WHERE excursion_id=? AND alumno_id=?
    """, params)

    # Sincronizar → autorizaciones_alumno si cambió el estado de autorización
    if "estado_auto" in d:
        _sync_excursion_to_auto(cur, excursion_id, alumno_id, d["estado_auto"])

    conn.commit()
    return jsonify({"ok": True})


@excursiones_bp.route("/api/excursiones/<int:excursion_id>/alumnos/bulk", methods=["PATCH"])
def api_bulk_toggle(excursion_id):
    """Marcar todos los alumnos de una excursión como autorizados o pagados."""
    conn = get_db()
    cur = conn.cursor()
    d = request.json or {}

    campo = d.get("campo")  # 'autorizado' | 'pagado'
    valor = 1 if d.get("valor", True) else 0
    if campo not in ("autorizado", "pagado"):
        return jsonify({"ok": False, "error": "Campo inválido"}), 400

    fecha_campo = "fecha_autorizacion" if campo == "autorizado" else "fecha_pago"
    from datetime import date
    fecha_hoy = date.today().isoformat() if valor else None

    if campo == "autorizado":
        cur.execute("""
            UPDATE excursion_alumnos SET autorizado=?, fecha_autorizacion=?, estado_auto=?
            WHERE excursion_id=?
        """, (valor, fecha_hoy, "autorizado" if valor else "pendiente", excursion_id))
    else:
        cur.execute(f"""
            UPDATE excursion_alumnos SET {campo}=?, {fecha_campo}=?
            WHERE excursion_id=?
        """, (valor, fecha_hoy, excursion_id))
    conn.commit()
    return jsonify({"ok": True})


@excursiones_bp.route("/api/excursiones/<int:excursion_id>/alumnos/añadir", methods=["POST"])
def api_añadir_alumno(excursion_id):
    """Añadir alumnos individuales a una excursión."""
    conn = get_db()
    cur = conn.cursor()
    d = request.json or {}
    alumno_ids = d.get("alumno_ids", [])
    for aid in alumno_ids:
        cur.execute("""
            INSERT OR IGNORE INTO excursion_alumnos (excursion_id, alumno_id)
            VALUES (?, ?)
        """, (excursion_id, aid))
    conn.commit()
    return jsonify({"ok": True})


# ─────────────────────────────────────────────
# API AUTORIZACIONES GENERALES
# ─────────────────────────────────────────────

@excursiones_bp.route("/api/autorizaciones/<int:alumno_id>", methods=["GET", "POST"])
def api_autorizaciones(alumno_id):
    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        d = request.json or {}
        tipo = d.get("tipo", "otro")
        etiqueta = d.get("etiqueta", "")
        estado = d.get("estado", "pendiente")
        fecha_recibida = d.get("fecha_recibida")
        observaciones = d.get("observaciones", "")
        excursion_id_val = d.get("excursion_id")

        # Fallback: enlazar por título si no llega excursion_id
        if not excursion_id_val and tipo == 'excursion' and etiqueta:
            ex_match = cur.execute(
                "SELECT id FROM excursiones WHERE titulo=?", (etiqueta,)
            ).fetchone()
            if ex_match:
                excursion_id_val = ex_match['id']

        cur.execute("""
            INSERT INTO autorizaciones_alumno
                (alumno_id, tipo, etiqueta, estado, fecha_recibida, observaciones, excursion_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (alumno_id, tipo, etiqueta, estado, fecha_recibida, observaciones, excursion_id_val))
        new_id = cur.lastrowid

        if excursion_id_val:
            _sync_auto_to_excursion(cur, alumno_id, excursion_id_val, estado, fecha_recibida)

        conn.commit()
        return jsonify({"ok": True, "id": new_id})

    rows = cur.execute("""
        SELECT * FROM autorizaciones_alumno
        WHERE alumno_id=?
        ORDER BY created_at DESC
    """, (alumno_id,)).fetchall()

    return jsonify([dict(r) for r in rows])


@excursiones_bp.route("/api/autorizaciones/bulk", methods=["POST"])
def api_autorizaciones_bulk():
    """Crea la misma autorización para varios alumnos a la vez."""
    conn = get_db()
    cur = conn.cursor()
    d = request.json or {}

    alumno_ids = d.get("alumno_ids", [])
    tipo = d.get("tipo", "otro")
    etiqueta = d.get("etiqueta", "")
    estado = d.get("estado", "pendiente")
    fecha_recibida = d.get("fecha_recibida")
    observaciones = d.get("observaciones", "")
    excursion_id_val = d.get("excursion_id")

    if not alumno_ids:
        return jsonify({"ok": False, "error": "No hay alumnos seleccionados"}), 400

    creadas = 0
    for alumno_id in alumno_ids:
        cur.execute("""
            INSERT INTO autorizaciones_alumno
                (alumno_id, tipo, etiqueta, estado, fecha_recibida, observaciones, excursion_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (alumno_id, tipo, etiqueta, estado, fecha_recibida, observaciones, excursion_id_val))
        if excursion_id_val:
            _sync_auto_to_excursion(cur, alumno_id, excursion_id_val, estado, fecha_recibida)
        creadas += 1

    conn.commit()
    return jsonify({"ok": True, "creadas": creadas})


@excursiones_bp.route("/api/autorizaciones/item/<int:item_id>", methods=["PUT", "DELETE"])
def api_autorizacion_item(item_id):
    conn = get_db()
    cur = conn.cursor()

    if request.method == "DELETE":
        cur.execute("DELETE FROM autorizaciones_alumno WHERE id=?", (item_id,))
        conn.commit()
        return jsonify({"ok": True})

    d = request.json or {}
    tipo = d.get("tipo", "otro")
    etiqueta = d.get("etiqueta", "")
    estado = d.get("estado", "pendiente")
    fecha_recibida = d.get("fecha_recibida")
    observaciones = d.get("observaciones", "")
    excursion_id_val = d.get("excursion_id")

    # Fallback: si no hay excursion_id pero tipo=excursion y hay etiqueta, buscar por título
    if not excursion_id_val and tipo == 'excursion' and etiqueta:
        ex_match = cur.execute(
            "SELECT id FROM excursiones WHERE titulo=?", (etiqueta,)
        ).fetchone()
        if ex_match:
            excursion_id_val = ex_match['id']

    cur.execute("""
        UPDATE autorizaciones_alumno SET
            tipo=?, etiqueta=?, estado=?, fecha_recibida=?, observaciones=?, excursion_id=?
        WHERE id=?
    """, (tipo, etiqueta, estado, fecha_recibida, observaciones, excursion_id_val, item_id))

    if excursion_id_val:
        row = cur.execute(
            "SELECT alumno_id FROM autorizaciones_alumno WHERE id=?", (item_id,)
        ).fetchone()
        if row:
            _sync_auto_to_excursion(cur, row['alumno_id'], excursion_id_val, estado, fecha_recibida)

    conn.commit()
    return jsonify({"ok": True})


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

@excursiones_bp.route("/api/excursiones/<int:excursion_id>/pdf-autorizacion")
def pdf_autorizacion(excursion_id):
    """Genera el PDF de autorización familiar para una excursión."""
    from flask import send_file
    from utils.db import get_app_data_dir
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable)
    from reportlab.platypus import Image as RLImage
    import os

    conn = get_db()
    cur = conn.cursor()

    ex = cur.execute("SELECT * FROM excursiones WHERE id=?", (excursion_id,)).fetchone()
    if not ex:
        return jsonify({"ok": False, "error": "No encontrada"}), 404

    # Config del centro
    cur.execute("""
        SELECT clave, valor FROM config
        WHERE clave LIKE 'logo_%' OR clave IN ('nombre_centro', 'curso_escolar')
    """)
    cfg = {r["clave"]: r["valor"] for r in cur.fetchall()}
    uploads_dir = os.path.join(get_app_data_dir(), "uploads")
    nombre_centro = cfg.get("nombre_centro", "")
    curso_escolar = cfg.get("curso_escolar", "")

    # Nombres de grupos
    grupo_ids = json.loads(ex["grupo_ids"] or "[]")
    grupos_rows = []
    if grupo_ids:
        ph = ",".join("?" * len(grupo_ids))
        grupos_rows = cur.execute(
            f"SELECT nombre FROM grupos WHERE id IN ({ph})", grupo_ids
        ).fetchall()
    nombres_grupos = [r["nombre"] for r in grupos_rows]
    if ex["grupos_extra"]:
        nombres_grupos.append(ex["grupos_extra"])
    grupos_str = ", ".join(nombres_grupos) if nombres_grupos else ""

    # Formatear fecha
    def fmt_fecha(iso):
        if not iso:
            return ""
        try:
            d, m, y = iso.split("-")[2], iso.split("-")[1], iso.split("-")[0]
            return f"{d} de {['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'][int(m)-1]} de {y}"
        except Exception:
            return iso

    fecha_larga = fmt_fecha(ex["fecha"])
    fecha_corta = f"{ex['fecha'].split('-')[2]}/{ex['fecha'].split('-')[1]}/{ex['fecha'].split('-')[0]}" if ex["fecha"] else ""

    # Construir PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=1.5*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    elements = []

    s_title = ParagraphStyle('ETitle', parent=styles['Normal'],
                             fontSize=14, fontName='Helvetica-Bold',
                             alignment=1, spaceAfter=6, leading=18)
    s_subtitle = ParagraphStyle('ESub', parent=styles['Normal'],
                                fontSize=11, fontName='Helvetica-Bold',
                                alignment=1, spaceAfter=10, textColor=colors.HexColor('#003366'))
    s_body = ParagraphStyle('EBody', parent=styles['Normal'],
                            fontSize=10, leading=16, spaceAfter=6)
    s_bold = ParagraphStyle('EBold', parent=styles['Normal'],
                            fontSize=10, fontName='Helvetica-Bold', spaceAfter=4)
    s_small = ParagraphStyle('ESmall', parent=styles['Normal'],
                             fontSize=9, textColor=colors.grey)
    s_firma = ParagraphStyle('EFirma', parent=styles['Normal'],
                             fontSize=10, leading=22, spaceAfter=4)

    # ── CABECERA con logos ──
    def make_logo(lado):
        fn = cfg.get(f"logo_{lado}_filename")
        if fn:
            p = os.path.join(uploads_dir, fn)
            if os.path.exists(p):
                try:
                    return RLImage(p, width=3*cm, height=2*cm)
                except Exception:
                    pass
        return Paragraph(" ", styles['Normal'])

    centro_txt = f"<b>{nombre_centro}</b>"
    if curso_escolar:
        centro_txt += f"<br/>Curso {curso_escolar}"
    col_centro = Paragraph(centro_txt,
                           ParagraphStyle('hdr', parent=styles['Normal'],
                                          alignment=1, fontSize=11,
                                          fontName='Helvetica-Bold', leading=16))
    hdr = Table([[make_logo("izda"), col_centro, make_logo("dcha")]],
                colWidths=[4*cm, 9*cm, 4*cm])
    hdr.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
    ]))
    elements.append(hdr)
    elements.append(Spacer(1, 0.4*cm))
    elements.append(HRFlowable(width="100%", thickness=1.5,
                               color=colors.HexColor('#003366')))
    elements.append(Spacer(1, 0.3*cm))

    # ── TÍTULO (del CRUD) ──
    elements.append(Paragraph(ex["titulo"].upper(), s_title))
    elements.append(Spacer(1, 0.2*cm))

    # ── CUERPO ──
    elements.append(Paragraph("Estimadas familias:", s_body))
    elements.append(Spacer(1, 0.1*cm))

    # Párrafo principal
    partes = []
    if fecha_larga:
        partes.append(f"El día <b>{fecha_larga}</b>")
    else:
        partes.append("Próximamente")
    if grupos_str:
        partes[0] += f", los alumnos de <b>{grupos_str}</b>"
    else:
        partes[0] += ", nuestros alumnos"
    if ex["destino"]:
        partes[0] += f" realizaremos una salida educativa a <b>{ex['destino']}</b>."
    else:
        partes[0] += " realizaremos una salida educativa."
    elements.append(Paragraph(partes[0], s_body))
    elements.append(Spacer(1, 0.2*cm))

    # Horario y precio
    if ex["hora_salida"] or ex["hora_regreso"] or ex["requiere_pago"]:
        elements.append(Paragraph("<b>Información de la actividad:</b>", s_bold))
        if ex["hora_salida"]:
            elements.append(Paragraph(f"• Salida del colegio: <b>{ex['hora_salida']} h</b>", s_body))
        if ex["hora_regreso"]:
            elements.append(Paragraph(f"• Regreso aproximado al colegio: <b>{ex['hora_regreso']} h</b>", s_body))
        if ex["requiere_pago"] and ex["coste"]:
            elements.append(Paragraph(f"• Coste de la actividad: <b>{float(ex['coste']):.2f} €</b>", s_body))
        elif ex["requiere_pago"]:
            elements.append(Paragraph("• La actividad tiene coste (pendiente de confirmar importe).", s_body))
        elements.append(Spacer(1, 0.2*cm))

    # Descripción (si existe)
    if ex["descripcion"]:
        elements.append(Paragraph(ex["descripcion"], s_body))
        elements.append(Spacer(1, 0.2*cm))

    # ── SEPARADOR DE RECORTE ──
    elements.append(Spacer(1, 0.5*cm))
    cut_style = TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.grey),
    ])
    cut_row = Table(
        [["- - - - - - - - - - - ✂ - - - - - - - - - - - - - - - ✂ - - - - - - - - - - - - - ✂ - - - - - - - - - - -"]],
        colWidths=[17*cm]
    )
    cut_row.setStyle(cut_style)
    elements.append(cut_row)
    elements.append(Spacer(1, 0.4*cm))

    # ── SECCIÓN DE AUTORIZACIÓN ──
    elements.append(Paragraph("<b>AUTORIZACIÓN</b>", s_subtitle))
    elements.append(Spacer(1, 0.2*cm))

    # "Yo, ___"
    yo_line = "Yo, &nbsp;" + "_" * 55
    elements.append(Paragraph(yo_line, s_firma))
    dni_line = "(DNI/NIE: &nbsp;" + "_" * 30 + ")"
    elements.append(Paragraph(dni_line, s_firma))
    elements.append(Spacer(1, 0.1*cm))

    auth_txt = "autorizo a mi hijo/a &nbsp;" + "_" * 48
    elements.append(Paragraph(auth_txt, s_firma))
    elements.append(Spacer(1, 0.1*cm))

    # Texto de la autorización
    detalle = "a participar en "
    if ex["destino"]:
        detalle += f"<b>{ex['titulo']}</b> ({ex['destino']})"
    else:
        detalle += f"<b>{ex['titulo']}</b>"
    if fecha_corta:
        detalle += f" el día <b>{fecha_corta}</b>"
    if ex["hora_salida"]:
        detalle += f", con salida del colegio a las <b>{ex['hora_salida']} h</b>"
    if ex["hora_regreso"]:
        detalle += f" y regreso aproximado a las <b>{ex['hora_regreso']} h</b>"
    detalle += "."
    if ex["requiere_pago"] and ex["coste"]:
        detalle += f" Adjunto el importe de <b>{float(ex['coste']):.2f} €</b>."
    elif ex["requiere_pago"]:
        detalle += " Adjunto el importe correspondiente."
    elements.append(Paragraph(detalle, s_body))
    elements.append(Spacer(1, 0.6*cm))

    # Firma y fecha
    firma_tbl = Table(
        [["Firmado: " + "_"*30,  "Fecha: " + "_"*20]],
        colWidths=[10*cm, 7*cm]
    )
    firma_tbl.setStyle(TableStyle([
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(firma_tbl)
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph(
        "Nombre y apellidos del padre/madre/tutor legal",
        s_small
    ))

    doc.build(elements)
    buffer.seek(0)
    nombre_archivo = f"autorizacion_{ex['titulo'][:30].replace(' ', '_')}.pdf"
    return send_file(buffer, mimetype='application/pdf',
                     as_attachment=True, download_name=nombre_archivo)


@excursiones_bp.route("/api/grupos/todos")
def api_grupos_todos():
    """Devuelve todos los grupos del centro (para excursiones multi-grupo)."""
    conn = get_db()
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT g.id, g.nombre, g.curso, COUNT(a.id) as num_alumnos
        FROM grupos g
        LEFT JOIN alumnos a ON g.id = a.grupo_id AND a.deleted_at IS NULL
        GROUP BY g.id
        ORDER BY g.curso ASC, g.nombre ASC
    """).fetchall()
    return jsonify([dict(r) for r in rows])


def _alumnos_de_grupos(cur, grupo_ids):
    """Devuelve lista de alumno_ids para los grupos dados."""
    if not grupo_ids:
        return []
    placeholders = ",".join("?" * len(grupo_ids))
    rows = cur.execute(f"""
        SELECT id FROM alumnos
        WHERE grupo_id IN ({placeholders}) AND deleted_at IS NULL
    """, grupo_ids).fetchall()
    return [r[0] for r in rows]


def _sync_auto_to_excursion(cur, alumno_id, excursion_id, estado_aut, fecha_recibida):
    """Sincroniza el estado de autorizaciones_alumno → excursion_alumnos."""
    estado_map = {'autorizada': 'autorizado', 'no_autoriza': 'no_autoriza', 'retirada': 'pendiente'}
    estado_ex = estado_map.get(estado_aut, 'pendiente')
    existing = cur.execute(
        "SELECT id FROM excursion_alumnos WHERE excursion_id=? AND alumno_id=?",
        (excursion_id, alumno_id)
    ).fetchone()
    if existing:
        cur.execute("""
            UPDATE excursion_alumnos SET estado_auto=?, autorizado=?, fecha_autorizacion=?
            WHERE excursion_id=? AND alumno_id=?
        """, (estado_ex, 1 if estado_ex == 'autorizado' else 0,
              fecha_recibida if estado_ex != 'pendiente' else None,
              excursion_id, alumno_id))


def _sync_excursion_to_auto(cur, excursion_id, alumno_id, estado_auto):
    """Sincroniza el estado de excursion_alumnos → autorizaciones_alumno."""
    from datetime import date
    ex_row = cur.execute("SELECT titulo FROM excursiones WHERE id=?", (excursion_id,)).fetchone()
    if not ex_row:
        return
    estado_map = {'autorizado': 'autorizada', 'no_autoriza': 'no_autoriza', 'pendiente': 'pendiente'}
    estado_aut = estado_map.get(estado_auto, 'pendiente')
    fecha_sync = date.today().isoformat() if estado_auto != 'pendiente' else None
    existing = cur.execute(
        "SELECT id FROM autorizaciones_alumno WHERE alumno_id=? AND excursion_id=?",
        (alumno_id, excursion_id)
    ).fetchone()
    if existing:
        cur.execute(
            "UPDATE autorizaciones_alumno SET estado=?, fecha_recibida=? WHERE id=?",
            (estado_aut, fecha_sync, existing['id'])
        )
    else:
        cur.execute("""
            INSERT INTO autorizaciones_alumno
                (alumno_id, tipo, etiqueta, estado, fecha_recibida, excursion_id)
            VALUES (?, 'excursion', ?, ?, ?, ?)
        """, (alumno_id, ex_row['titulo'], estado_aut, fecha_sync, excursion_id))
