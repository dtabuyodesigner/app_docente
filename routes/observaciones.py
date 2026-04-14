import os
from flask import Blueprint, jsonify, request, session
from werkzeug.utils import secure_filename
from utils.db import get_db, get_app_data_dir

observaciones_bp = Blueprint('observaciones', __name__)

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}


def _allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _notas_dir():
    d = os.path.join(get_app_data_dir(), 'uploads', 'notas')
    os.makedirs(d, exist_ok=True)
    return d


@observaciones_bp.route("/api/observaciones", methods=["POST"])
def guardar_observacion():
    d = request.json
    alumno_id = d["alumno_id"]
    fecha = d.get("fecha")
    texto = d.get("texto", "")
    area_id = d.get("area_id")
    if area_id == "" or area_id is None:
        area_id = None
    else:
        try:
            area_id = int(area_id)
        except Exception:
            area_id = None

    conn = get_db()
    cur = conn.cursor()

    if not texto.strip():
        # Solo borrar si tampoco hay foto
        if area_id:
            row = cur.execute(
                "SELECT id, foto FROM observaciones WHERE alumno_id=? AND fecha=? AND area_id=?",
                (alumno_id, fecha, area_id)
            ).fetchone()
        else:
            row = cur.execute(
                "SELECT id, foto FROM observaciones WHERE alumno_id=? AND fecha=? AND area_id IS NULL",
                (alumno_id, fecha)
            ).fetchone()

        if row and not row["foto"]:
            try:
                cur.execute("DELETE FROM observaciones WHERE id=?", (row["id"],))
                conn.commit()
                return jsonify({"ok": True, "deleted": True})
            except Exception as e:
                conn.rollback()
                return jsonify({"ok": False, "error": str(e)}), 500
        elif not row:
            return jsonify({"ok": True, "deleted": True})
        # Si hay foto, actualizar solo el texto (vacío)
    try:
        if area_id:
            row = cur.execute(
                "SELECT id FROM observaciones WHERE alumno_id=? AND fecha=? AND area_id=?",
                (alumno_id, fecha, area_id)
            ).fetchone()
        else:
            row = cur.execute(
                "SELECT id FROM observaciones WHERE alumno_id=? AND fecha=? AND area_id IS NULL",
                (alumno_id, fecha)
            ).fetchone()

        if row:
            cur.execute("UPDATE observaciones SET texto=? WHERE id=?", (texto, row["id"]))
        else:
            cur.execute(
                "INSERT INTO observaciones (alumno_id, fecha, texto, area_id) VALUES (?,?,?,?)",
                (alumno_id, fecha, texto, area_id)
            )
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


@observaciones_bp.route("/api/observaciones/foto", methods=["POST"])
def subir_foto_observacion():
    """Sube una foto y la asocia a la observación del alumno en esa fecha."""
    alumno_id = request.form.get("alumno_id")
    fecha = request.form.get("fecha")
    area_id = request.form.get("area_id") or None
    if area_id:
        try:
            area_id = int(area_id)
        except Exception:
            area_id = None

    if not alumno_id or not fecha:
        return jsonify({"ok": False, "error": "Faltan alumno_id o fecha"}), 400

    file = request.files.get("foto")
    if not file or not file.filename:
        return jsonify({"ok": False, "error": "No se recibió ninguna foto"}), 400
    if not _allowed(file.filename):
        return jsonify({"ok": False, "error": "Formato no permitido"}), 400

    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = secure_filename(f"nota_{alumno_id}_{fecha}_{area_id or 0}.{ext}")
    filepath = os.path.join(_notas_dir(), filename)
    file.save(filepath)
    foto_path = f"notas/{filename}"

    conn = get_db()
    cur = conn.cursor()
    try:
        if area_id:
            row = cur.execute(
                "SELECT id, foto FROM observaciones WHERE alumno_id=? AND fecha=? AND area_id=?",
                (alumno_id, fecha, area_id)
            ).fetchone()
        else:
            row = cur.execute(
                "SELECT id, foto FROM observaciones WHERE alumno_id=? AND fecha=? AND area_id IS NULL",
                (alumno_id, fecha)
            ).fetchone()

        if row:
            # Borrar foto anterior si existía
            if row["foto"]:
                old = os.path.join(get_app_data_dir(), 'uploads', row["foto"])
                if os.path.exists(old):
                    os.remove(old)
            cur.execute("UPDATE observaciones SET foto=? WHERE id=?", (foto_path, row["id"]))
            obs_id = row["id"]
        else:
            cur.execute(
                "INSERT INTO observaciones (alumno_id, fecha, texto, area_id, foto) VALUES (?,?,?,?,?)",
                (alumno_id, fecha, "", area_id, foto_path)
            )
            obs_id = cur.lastrowid

        conn.commit()
        return jsonify({"ok": True, "foto": foto_path, "obs_id": obs_id})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


@observaciones_bp.route("/api/observaciones/foto/<int:obs_id>", methods=["DELETE"])
def borrar_foto_observacion(obs_id):
    """Elimina la foto de una observación (pero mantiene el texto si lo hay)."""
    conn = get_db()
    cur = conn.cursor()
    row = cur.execute("SELECT id, texto, foto FROM observaciones WHERE id=?", (obs_id,)).fetchone()
    if not row:
        return jsonify({"ok": False, "error": "No encontrado"}), 404
    try:
        if row["foto"]:
            filepath = os.path.join(get_app_data_dir(), 'uploads', row["foto"])
            if os.path.exists(filepath):
                os.remove(filepath)
        if not row["texto"] or not row["texto"].strip():
            cur.execute("DELETE FROM observaciones WHERE id=?", (obs_id,))
        else:
            cur.execute("UPDATE observaciones SET foto=NULL WHERE id=?", (obs_id,))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


@observaciones_bp.route("/api/observaciones/dia")
def obtener_observaciones_dia():
    fecha = request.args.get("fecha")
    area_id = request.args.get("area_id")

    conn = get_db()
    cur = conn.cursor()
    grupo_id = session.get('active_group_id')

    if area_id:
        cur.execute("""
            SELECT a.id, a.nombre, a.foto, o.id as obs_id, o.texto, o.foto as obs_foto, asi.estado,
                   f.madre_telefono, f.padre_telefono, f.madre_email, f.padre_email
            FROM alumnos a
            LEFT JOIN observaciones o ON o.alumno_id = a.id AND o.fecha = ? AND o.area_id = ?
            LEFT JOIN asistencia asi ON asi.alumno_id = a.id AND asi.fecha = ?
            LEFT JOIN ficha_alumno f ON f.alumno_id = a.id
            WHERE a.grupo_id = ?
            ORDER BY a.nombre
        """, (fecha, area_id, fecha, grupo_id))
    else:
        cur.execute("""
            SELECT a.id, a.nombre, a.foto, o.id as obs_id, o.texto, o.foto as obs_foto, asi.estado,
                   f.madre_telefono, f.padre_telefono, f.madre_email, f.padre_email
            FROM alumnos a
            LEFT JOIN observaciones o ON o.alumno_id = a.id AND o.fecha = ? AND o.area_id IS NULL
            LEFT JOIN asistencia asi ON asi.alumno_id = a.id AND asi.fecha = ?
            LEFT JOIN ficha_alumno f ON f.alumno_id = a.id
            WHERE a.grupo_id = ?
            ORDER BY a.nombre
        """, (fecha, fecha, grupo_id))

    data = []
    for row in cur.fetchall():
        data.append({
            "id": row["id"],
            "nombre": row["nombre"],
            "foto": row["foto"] or "",
            "obs_id": row["obs_id"],
            "observacion": row["texto"] or "",
            "obs_foto": row["obs_foto"] or "",
            "asistencia": row["estado"] or "presente",
            "madre_tel": row["madre_telefono"] or "",
            "padre_tel": row["padre_telefono"] or "",
            "madre_email": row["madre_email"] or "",
            "padre_email": row["padre_email"] or ""
        })
    return jsonify(data)


@observaciones_bp.route("/api/observaciones/<int:alumno_id>")
def ver_observaciones(alumno_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, fecha, texto, foto
        FROM observaciones
        WHERE alumno_id = ?
        ORDER BY fecha DESC
    """, (alumno_id,))
    datos = cur.fetchall()
    return jsonify([
        {"id": r["id"], "fecha": r["fecha"], "texto": r["texto"], "foto": r["foto"] or ""}
        for r in datos
    ])


@observaciones_bp.route("/api/observaciones/<int:obs_id>", methods=["PUT"])
def editar_observacion(obs_id):
    d = request.json
    texto = d.get("texto", "")
    conn = get_db()
    cur = conn.cursor()
    try:
        row = cur.execute("SELECT foto FROM observaciones WHERE id=?", (obs_id,)).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "No encontrado"}), 404
        if not texto.strip() and not row["foto"]:
            cur.execute("DELETE FROM observaciones WHERE id=?", (obs_id,))
            conn.commit()
            return jsonify({"ok": True, "deleted": True})
        cur.execute("UPDATE observaciones SET texto=? WHERE id=?", (texto, obs_id))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


@observaciones_bp.route("/api/observaciones/<int:obs_id>", methods=["DELETE"])
def borrar_observacion(obs_id):
    conn = get_db()
    cur = conn.cursor()
    try:
        row = cur.execute("SELECT foto FROM observaciones WHERE id=?", (obs_id,)).fetchone()
        if row and row["foto"]:
            filepath = os.path.join(get_app_data_dir(), 'uploads', row["foto"])
            if os.path.exists(filepath):
                os.remove(filepath)
        cur.execute("DELETE FROM observaciones WHERE id=?", (obs_id,))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


@observaciones_bp.route("/api/observaciones/historial")
def historial_observaciones():
    alumno_id = request.args.get("alumno_id")
    fecha_desde = request.args.get("fecha_desde")
    fecha_hasta = request.args.get("fecha_hasta")
    area_id = request.args.get("area_id")

    conn = get_db()
    cur = conn.cursor()

    query = """
        SELECT o.id, o.alumno_id, o.area_id, o.fecha, o.texto, o.foto,
               a.nombre as alumno_nombre, ar.nombre as area_nombre
        FROM observaciones o
        INNER JOIN alumnos a ON o.alumno_id = a.id
        LEFT JOIN areas ar ON o.area_id = ar.id
        WHERE 1=1
    """
    params = []

    if alumno_id:
        query += " AND o.alumno_id = ?"
        params.append(alumno_id)
    if fecha_desde:
        query += " AND o.fecha >= ?"
        params.append(fecha_desde)
    if fecha_hasta:
        query += " AND o.fecha <= ?"
        params.append(fecha_hasta)
    if area_id:
        query += " AND o.area_id = ?"
        params.append(area_id)

    query += " ORDER BY o.fecha DESC, o.id DESC LIMIT 200"

    cur.execute(query, params)
    return jsonify([dict(r) for r in cur.fetchall()])
