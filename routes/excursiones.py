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

        cur.execute("""
            INSERT INTO excursiones
                (tipo, titulo, fecha, destino, descripcion, grupo_ids, grupos_extra,
                 requiere_autorizacion, requiere_pago, coste, fecha_limite, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'activa')
        """, (tipo, titulo, fecha, destino, descripcion, grupo_ids, grupos_extra,
              requiere_autorizacion, requiere_pago, coste, fecha_limite))
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
               SUM(ea.autorizado) AS total_autorizados,
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
               SUM(CASE WHEN e.requiere_autorizacion=1 AND ea.autorizado=0 THEN 1 ELSE 0 END) AS pendientes_auto,
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
        estado = d.get("estado", "activa")

        cur.execute("""
            UPDATE excursiones SET
                tipo=?, titulo=?, fecha=?, destino=?, descripcion=?, grupo_ids=?,
                grupos_extra=?, requiere_autorizacion=?, requiere_pago=?,
                coste=?, fecha_limite=?, estado=?
            WHERE id=?
        """, (tipo, titulo, fecha, destino, descripcion, grupo_ids,
              grupos_extra, requiere_autorizacion, requiere_pago,
              coste, fecha_limite, estado, excursion_id))

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

    if "autorizado" in d:
        updates.append("autorizado=?")
        params.append(1 if d["autorizado"] else 0)
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

        cur.execute("""
            INSERT INTO autorizaciones_alumno
                (alumno_id, tipo, etiqueta, estado, fecha_recibida, observaciones)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (alumno_id, tipo, etiqueta, estado, fecha_recibida, observaciones))
        conn.commit()
        return jsonify({"ok": True, "id": cur.lastrowid})

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

    if not alumno_ids:
        return jsonify({"ok": False, "error": "No hay alumnos seleccionados"}), 400

    creadas = 0
    for alumno_id in alumno_ids:
        cur.execute("""
            INSERT INTO autorizaciones_alumno
                (alumno_id, tipo, etiqueta, estado, fecha_recibida, observaciones)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (alumno_id, tipo, etiqueta, estado, fecha_recibida, observaciones))
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

    cur.execute("""
        UPDATE autorizaciones_alumno SET
            tipo=?, etiqueta=?, estado=?, fecha_recibida=?, observaciones=?
        WHERE id=?
    """, (tipo, etiqueta, estado, fecha_recibida, observaciones, item_id))
    conn.commit()
    return jsonify({"ok": True})


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

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
