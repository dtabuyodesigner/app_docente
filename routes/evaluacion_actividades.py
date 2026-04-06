from flask import Blueprint, jsonify, request, session
from utils.db import get_db, nivel_a_nota
from datetime import date

evaluacion_actividades_bp = Blueprint('evaluacion_actividades', __name__)


@evaluacion_actividades_bp.route("/cuaderno")
def cuaderno_actividades():
    """
    Devuelve alumnos + actividades (agrupadas por SDA) para el modo POR_ACTIVIDADES.
    Parámetros: grupo_id, area_id, trimestre, sda_id (opcional, filtra por SDA).
    """
    grupo_id = request.args.get("grupo_id") or session.get('active_group_id')
    area_id = request.args.get("area_id")
    trimestre = request.args.get("trimestre")
    sda_id = request.args.get("sda_id")

    if not grupo_id or not area_id or not trimestre:
        return jsonify({"error": "Faltan parámetros"}), 400

    db = get_db()
    cur = db.cursor()

    alumnos = cur.execute("""
        SELECT id, nombre FROM alumnos WHERE grupo_id = ? ORDER BY nombre
    """, (grupo_id,)).fetchall()

    # Actividades de las SDAs de esta área y trimestre para este grupo
    if sda_id and sda_id not in ('', 'null', '0'):
        actividades = cur.execute("""
            SELECT a.id, a.nombre, a.descripcion, a.codigo_actividad,
                   s.id as sda_id, s.nombre as sda_nombre,
                   (SELECT MIN(fecha) FROM sesiones_actividad WHERE actividad_id = a.id) as min_fecha
            FROM actividades_sda a
            JOIN sda s ON a.sda_id = s.id
            WHERE s.area_id = ? AND s.trimestre = ? AND a.sda_id = ?
              AND (s.grupo_id = ? OR s.grupo_id IS NULL)
            ORDER BY s.id, min_fecha, a.id
        """, (area_id, trimestre, sda_id, grupo_id)).fetchall()
    else:
        actividades = cur.execute("""
            SELECT a.id, a.nombre, a.descripcion, a.codigo_actividad,
                   s.id as sda_id, s.nombre as sda_nombre,
                   (SELECT MIN(fecha) FROM sesiones_actividad WHERE actividad_id = a.id) as min_fecha
            FROM actividades_sda a
            JOIN sda s ON a.sda_id = s.id
            WHERE s.area_id = ? AND s.trimestre = ?
              AND (s.grupo_id = ? OR s.grupo_id IS NULL)
            ORDER BY s.id, min_fecha, a.id
        """, (area_id, trimestre, grupo_id)).fetchall()

    if not actividades:
        return jsonify({
            "alumnos": [dict(a) for a in alumnos],
            "actividades": [],
            "evaluaciones": {}
        })

    act_ids = [a["id"] for a in actividades]
    alumno_ids = [a["id"] for a in alumnos]

    # Evaluaciones existentes: {alumno_id}_{actividad_id} → nivel
    placeholders = ",".join("?" * len(act_ids))
    evals = cur.execute(f"""
        SELECT alumno_id, actividad_id, nivel
        FROM evaluaciones_actividad
        WHERE actividad_id IN ({placeholders}) AND trimestre = ?
    """, act_ids + [trimestre]).fetchall()

    eval_map = {f"{e['alumno_id']}_{e['actividad_id']}": e['nivel'] for e in evals}

    return jsonify({
        "alumnos": [dict(a) for a in alumnos],
        "actividades": [dict(a) for a in actividades],
        "evaluaciones": eval_map
    })


@evaluacion_actividades_bp.route("/notas_alumno")
def notas_alumno():
    """
    Devuelve las notas de actividades de un alumno concreto.
    Parámetros: alumno_id, area_id, trimestre, sda_id (opcional).
    """
    alumno_id = request.args.get("alumno_id")
    area_id = request.args.get("area_id")
    trimestre = request.args.get("trimestre")
    sda_id = request.args.get("sda_id")

    if not alumno_id or not area_id or not trimestre:
        return jsonify({}), 400

    db = get_db()
    cur = db.cursor()

    if sda_id and sda_id not in ('', 'null', '0'):
        rows = cur.execute("""
            SELECT ea.actividad_id, ea.nivel
            FROM evaluaciones_actividad ea
            JOIN actividades_sda a ON ea.actividad_id = a.id
            JOIN sda s ON a.sda_id = s.id
            WHERE ea.alumno_id = ? AND ea.trimestre = ?
              AND s.area_id = ? AND a.sda_id = ?
        """, (alumno_id, trimestre, area_id, sda_id)).fetchall()
    else:
        rows = cur.execute("""
            SELECT ea.actividad_id, ea.nivel
            FROM evaluaciones_actividad ea
            JOIN actividades_sda a ON ea.actividad_id = a.id
            JOIN sda s ON a.sda_id = s.id
            WHERE ea.alumno_id = ? AND ea.trimestre = ? AND s.area_id = ?
        """, (alumno_id, trimestre, area_id)).fetchall()

    return jsonify({str(r['actividad_id']): r['nivel'] for r in rows})


@evaluacion_actividades_bp.route("/guardar", methods=["POST"])
def guardar_actividad():
    """
    Guarda la evaluación de una actividad para un alumno y propaga la nota
    a los criterios del SDA correspondiente en la tabla evaluaciones.
    """
    d = request.json
    alumno_id = d.get("alumno_id")
    actividad_id = d.get("actividad_id")
    nivel = d.get("nivel")  # None = borrar
    trimestre = d.get("trimestre")

    if not alumno_id or not actividad_id or not trimestre:
        return jsonify({"ok": False, "error": "Faltan parámetros"}), 400

    db = get_db()
    cur = db.cursor()

    # Obtener info de la actividad → SDA → área → escala
    act_info = cur.execute("""
        SELECT a.id, a.sda_id, s.area_id, ar.tipo_escala
        FROM actividades_sda a
        JOIN sda s ON a.sda_id = s.id
        JOIN areas ar ON s.area_id = ar.id
        WHERE a.id = ?
    """, (actividad_id,)).fetchone()

    if not act_info:
        return jsonify({"ok": False, "error": "Actividad no encontrada"}), 404

    sda_id = act_info["sda_id"]
    area_id = act_info["area_id"]
    escala = act_info["tipo_escala"]

    try:
        cur.execute("BEGIN")

        if nivel is None:
            # Borrar evaluación de esta actividad
            cur.execute("""
                DELETE FROM evaluaciones_actividad
                WHERE alumno_id = ? AND actividad_id = ? AND trimestre = ?
            """, (alumno_id, actividad_id, trimestre))
        else:
            nivel = int(nivel)
            nota = nivel_a_nota(nivel, escala)
            cur.execute("""
                INSERT INTO evaluaciones_actividad (alumno_id, actividad_id, nivel, nota, trimestre, fecha)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(alumno_id, actividad_id, trimestre)
                DO UPDATE SET nivel = excluded.nivel, nota = excluded.nota, fecha = excluded.fecha
            """, (alumno_id, actividad_id, nivel, nota, trimestre, date.today().isoformat()))

        # Propagar: recalcular nota de cada criterio del SDA a partir de todas las actividades
        _propagar_actividades_a_criterios(cur, alumno_id, sda_id, area_id, escala, trimestre)

        db.commit()
        return jsonify({"ok": True})
    except Exception as e:
        db.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


def _propagar_actividades_a_criterios(cur, alumno_id, sda_id, area_id, escala, trimestre):
    """
    Calcula la media de las actividades evaluadas en todas las SDAs que contienen
    cada criterio del área, y actualiza la tabla evaluaciones (sda_id=NULL).
    Se llama después de cada cambio en evaluaciones_actividad.
    """
    # Criterios del área que están en alguna SDA evaluable para este alumno/trimestre
    criterios = cur.execute("""
        SELECT DISTINCT sc.criterio_id
        FROM sda_criterios sc
        JOIN sda s ON sc.sda_id = s.id
        WHERE s.area_id = ?
    """, (area_id,)).fetchall()

    for row in criterios:
        criterio_id = row["criterio_id"]

        # Media de todas las actividades del alumno que evalúan este criterio específicamente
        # Si no hay mapeo en actividad_criterio, usamos el comportamiento por defecto (todas las actividades de la SDA)
        cur.execute("SELECT COUNT(*) as cuenta FROM actividad_criterio WHERE criterio_id = ?", (criterio_id,))
        tiene_mapeo = cur.fetchone()["cuenta"] > 0

        if tiene_mapeo:
            stats = cur.execute("""
                SELECT AVG(ea.nivel) as media_nivel, AVG(ea.nota) as media_nota
                FROM evaluaciones_actividad ea
                JOIN actividades_sda a ON ea.actividad_id = a.id
                JOIN actividad_criterio ac ON ac.actividad_id = a.id
                WHERE ea.alumno_id = ? AND ea.trimestre = ?
                  AND ac.criterio_id = ?
            """, (alumno_id, trimestre, criterio_id)).fetchone()
        else:
            stats = cur.execute("""
                SELECT AVG(ea.nivel) as media_nivel, AVG(ea.nota) as media_nota
                FROM evaluaciones_actividad ea
                JOIN actividades_sda a ON ea.actividad_id = a.id
                JOIN sda_criterios sc ON sc.sda_id = a.sda_id
                WHERE ea.alumno_id = ? AND ea.trimestre = ?
                  AND sc.criterio_id = ?
            """, (alumno_id, trimestre, criterio_id)).fetchone()


        if stats["media_nivel"] is None:
            # Sin actividades evaluadas → borrar entrada en evaluaciones (si existe)
            cur.execute("""
                DELETE FROM evaluaciones
                WHERE alumno_id = ? AND criterio_id = ? AND sda_id IS NULL AND trimestre = ?
                  AND area_id = ?
            """, (alumno_id, criterio_id, trimestre, area_id))
        else:
            media_nivel = int(round(stats["media_nivel"]))
            media_nota = round(stats["media_nota"], 2)

            cur.execute("""
                DELETE FROM evaluaciones
                WHERE alumno_id = ? AND criterio_id = ? AND sda_id IS NULL AND trimestre = ?
                  AND area_id = ?
            """, (alumno_id, criterio_id, trimestre, area_id))
            cur.execute("""
                INSERT INTO evaluaciones (alumno_id, area_id, trimestre, sda_id, criterio_id, nivel, nota)
                VALUES (?, ?, ?, NULL, ?, ?, ?)
            """, (alumno_id, area_id, trimestre, criterio_id, media_nivel, media_nota))


@evaluacion_actividades_bp.route("/por_actividad")
def por_actividad():
    """
    Devuelve alumnos del grupo activo + su nivel actual para una actividad concreta.
    Parámetros: actividad_id, trimestre, grupo_id (opcional, usa sesión si no se pasa).
    """
    actividad_id = request.args.get("actividad_id")
    trimestre = request.args.get("trimestre")
    grupo_id = request.args.get("grupo_id") or session.get('active_group_id')

    if not actividad_id or not trimestre or not grupo_id:
        return jsonify({"error": "Faltan parámetros"}), 400

    db = get_db()
    cur = db.cursor()

    # Info de la actividad y su área/escala
    act_info = cur.execute("""
        SELECT a.id, a.nombre, a.sda_id, s.area_id, ar.tipo_escala, ar.modo_evaluacion,
               s.nombre as sda_nombre, ar.nombre as area_nombre
        FROM actividades_sda a
        JOIN sda s ON a.sda_id = s.id
        JOIN areas ar ON s.area_id = ar.id
        WHERE a.id = ?
    """, (actividad_id,)).fetchone()

    if not act_info:
        return jsonify({"error": "Actividad no encontrada"}), 404

    alumnos = cur.execute("""
        SELECT al.id, al.nombre,
               COALESCE(ast.estado, 'presente') as asistencia
        FROM alumnos al
        LEFT JOIN asistencia ast ON al.id = ast.alumno_id AND ast.fecha = date('now')
        WHERE al.grupo_id = ?
        ORDER BY al.nombre
    """, (grupo_id,)).fetchall()

    evals = cur.execute("""
        SELECT alumno_id, nivel
        FROM evaluaciones_actividad
        WHERE actividad_id = ? AND trimestre = ?
    """, (actividad_id, trimestre)).fetchall()

    eval_map = {r["alumno_id"]: r["nivel"] for r in evals}

    result = []
    for a in alumnos:
        row = dict(a)
        row["nivel"] = eval_map.get(a["id"])
        result.append(row)

    return jsonify({
        "alumnos": result,
        "actividad": dict(act_info),
        "trimestre": trimestre
    })


@evaluacion_actividades_bp.route("/media")
def media_actividades():
    """
    Devuelve la media de las actividades evaluadas para un alumno en un área/trimestre.
    Parámetros: alumno_id, area_id, trimestre, sda_id (opcional).
    """
    alumno_id = request.args.get("alumno_id")
    area_id = request.args.get("area_id")
    trimestre = request.args.get("trimestre")
    sda_id = request.args.get("sda_id")

    if not alumno_id or not area_id or not trimestre:
        return jsonify({"media": None})

    db = get_db()
    cur = db.cursor()

    if sda_id and sda_id not in ('', 'null', '0'):
        row = cur.execute("""
            SELECT ROUND(AVG(ea.nota), 2) as media
            FROM evaluaciones_actividad ea
            JOIN actividades_sda a ON ea.actividad_id = a.id
            WHERE ea.alumno_id = ? AND ea.trimestre = ? AND a.sda_id = ?
        """, (alumno_id, trimestre, sda_id)).fetchone()
    else:
        row = cur.execute("""
            SELECT ROUND(AVG(ea.nota), 2) as media
            FROM evaluaciones_actividad ea
            JOIN actividades_sda a ON ea.actividad_id = a.id
            JOIN sda s ON a.sda_id = s.id
            WHERE ea.alumno_id = ? AND ea.trimestre = ? AND s.area_id = ?
        """, (alumno_id, trimestre, area_id)).fetchone()

    return jsonify({"media": row["media"] if row else None})


@evaluacion_actividades_bp.route("/guardar_masivo", methods=["POST"])
def guardar_actividad_masivo():
    """
    Guarda la evaluación de una actividad para múltiples alumnos simultáneamente.
    Útil para rellenado masivo en Infantil.
    Body: {
        "actividad_id": int,
        "trimestre": str,
        "evaluaciones": [
            {"alumno_id": int, "nivel": int},
            ...
        ]
    }
    """
    d = request.json
    actividad_id = d.get("actividad_id")
    trimestre = d.get("trimestre")
    evaluaciones = d.get("evaluaciones", [])

    if not actividad_id or not trimestre:
        return jsonify({"ok": False, "error": "Faltan parámetros"}), 400

    if not evaluaciones:
        return jsonify({"ok": False, "error": "No hay evaluaciones para guardar"}), 400

    db = get_db()
    cur = db.cursor()

    # Obtener info de la actividad → SDA → área → escala (una sola vez)
    act_info = cur.execute("""
        SELECT a.id, a.sda_id, s.area_id, ar.tipo_escala
        FROM actividades_sda a
        JOIN sda s ON a.sda_id = s.id
        JOIN areas ar ON s.area_id = ar.id
        WHERE a.id = ?
    """, (actividad_id,)).fetchone()

    if not act_info:
        return jsonify({"ok": False, "error": "Actividad no encontrada"}), 404

    sda_id = act_info["sda_id"]
    area_id = act_info["area_id"]
    escala = act_info["tipo_escala"]

    try:
        cur.execute("BEGIN")

        for ev in evaluaciones:
            alumno_id = ev.get("alumno_id")
            nivel = ev.get("nivel")

            if not alumno_id or nivel is None:
                continue

            nivel = int(nivel)
            nota = nivel_a_nota(nivel, escala)

            cur.execute("""
                INSERT INTO evaluaciones_actividad (alumno_id, actividad_id, nivel, nota, trimestre, fecha)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(alumno_id, actividad_id, trimestre)
                DO UPDATE SET nivel = excluded.nivel, nota = excluded.nota, fecha = excluded.fecha
            """, (alumno_id, actividad_id, nivel, nota, trimestre, date.today().isoformat()))

            # Propagar para cada alumno
            _propagar_actividades_a_criterios(cur, alumno_id, sda_id, area_id, escala, trimestre)

        db.commit()
        return jsonify({"ok": True, "evaluados": len(evaluaciones)})
    except Exception as e:
        db.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


@evaluacion_actividades_bp.route("/guardar_alumno_masivo", methods=["POST"])
def guardar_alumno_masivo():
    """
    Guarda múltiples actividades para un único alumno simultáneamente.
    Especialmente útil para la funcionalidad 'Rellenar' en la vista individual.
    Body: {
        "alumno_id": int,
        "trimestre": str,
        "evaluaciones": [
            {"actividad_id": int, "nivel": int},
            ...
        ]
    }
    """
    d = request.json
    alumno_id = d.get("alumno_id")
    trimestre = d.get("trimestre")
    evaluaciones = d.get("evaluaciones", [])

    if not alumno_id or not trimestre or not evaluaciones:
        return jsonify({"ok": False, "error": "Faltan parámetros"}), 400

    db = get_db()
    cur = db.cursor()

    try:
        cur.execute("BEGIN")
        # Diccionario para agrupar por área/escala y evitar consultas repetitivas
        cache_area = {}

        for ev in evaluaciones:
            act_id = ev.get("actividad_id")
            nivel = ev.get("nivel")
            if not act_id or nivel is None: continue

            if act_id not in cache_area:
                info = cur.execute("""
                    SELECT s.area_id, ar.tipo_escala, s.id as sda_id
                    FROM actividades_sda a
                    JOIN sda s ON a.sda_id = s.id
                    JOIN areas ar ON s.area_id = ar.id
                    WHERE a.id = ?
                """, (act_id,)).fetchone()
                if info:
                    cache_area[act_id] = info
                else:
                    continue

            info = cache_area[act_id]
            nota = nivel_a_nota(int(nivel), info["tipo_escala"])

            cur.execute("""
                INSERT INTO evaluaciones_actividad (alumno_id, actividad_id, nivel, nota, trimestre, fecha)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(alumno_id, actividad_id, trimestre)
                DO UPDATE SET nivel = excluded.nivel, nota = excluded.nota, fecha = excluded.fecha
            """, (alumno_id, act_id, int(nivel), nota, trimestre, date.today().isoformat()))

            # Propagar al criterio (SDA_ID=NULL en tabla evaluaciones)
            _propagar_actividades_a_criterios(cur, alumno_id, info["sda_id"], info["area_id"], info["tipo_escala"], trimestre)

        db.commit()
        return jsonify({"ok": True})
    except Exception as e:
        db.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


@evaluacion_actividades_bp.route("/limpiar", methods=["DELETE"])
def limpiar_actividades():
    """
    Borra todas las evaluaciones de actividades de un alumno en un área/trimestre.
    Parámetros: alumno_id, area_id, trimestre, sda_id (opcional).
    """
    alumno_id = request.args.get("alumno_id")
    area_id = request.args.get("area_id")
    trimestre = request.args.get("trimestre")
    sda_id = request.args.get("sda_id")

    if not alumno_id or not area_id or not trimestre:
        return jsonify({"ok": False, "error": "Faltan parámetros"}), 400

    db = get_db()
    cur = db.cursor()

    try:
        cur.execute("BEGIN")
        if sda_id and sda_id not in ("null", "directo", "", "0"):
            cur.execute("""
                DELETE FROM evaluaciones_actividad
                WHERE alumno_id = ? AND trimestre = ?
                  AND actividad_id IN (
                      SELECT a.id FROM actividades_sda a
                      JOIN sda s ON a.sda_id = s.id
                      WHERE s.id = ? AND s.area_id = ?
                  )
            """, (alumno_id, trimestre, sda_id, area_id))
        else:
            cur.execute("""
                DELETE FROM evaluaciones_actividad
                WHERE alumno_id = ? AND trimestre = ?
                  AND actividad_id IN (
                      SELECT a.id FROM actividades_sda a
                      JOIN sda s ON a.sda_id = s.id
                      WHERE s.area_id = ?
                  )
            """, (alumno_id, trimestre, area_id))
        db.commit()
        return jsonify({"ok": True})
    except Exception as e:
        db.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
