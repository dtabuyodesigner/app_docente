from flask import Blueprint, jsonify, request, session
from utils.db import get_db, nivel_a_nota

evaluacion_directa_bp = Blueprint('evaluacion_directa', __name__)

@evaluacion_directa_bp.route("/", methods=["POST"])
def guardar_evaluacion_directa():
    d = request.json
    nivel = d.get("nivel")
    periodo = d.get("periodo", "T1")
    alumno_id = d["alumno_id"]
    criterio_id = d["criterio_id"]
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        if nivel is None:
            cur.execute("""
                DELETE FROM evaluacion_criterios
                WHERE alumno_id = ? AND criterio_id = ? AND periodo = ?
            """, (alumno_id, criterio_id, periodo))
        else:
            nivel = int(nivel)
            nota = nivel_a_nota(nivel)
            cur.execute("""
                INSERT INTO evaluacion_criterios (alumno_id, criterio_id, periodo, nivel, nota)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(alumno_id, criterio_id, periodo)
                DO UPDATE SET nivel = excluded.nivel, nota = excluded.nota
            """, (alumno_id, criterio_id, periodo, nivel, nota))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


@evaluacion_directa_bp.route("/guardar_masivo", methods=["POST"])
def guardar_masivo_directa():
    data = request.json
    periodo = data["periodo"]
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        for item in data["evaluaciones"]:
            alumno_id = item["alumno_id"]
            criterio_id = item["criterio_id"]
            nivel = item.get("nivel")
            if nivel is None:
                cur.execute("""
                    DELETE FROM evaluacion_criterios
                    WHERE alumno_id = ? AND criterio_id = ? AND periodo = ?
                """, (alumno_id, criterio_id, periodo))
            else:
                nivel = int(nivel)
                nota = nivel_a_nota(nivel)
                cur.execute("""
                    INSERT INTO evaluacion_criterios (alumno_id, criterio_id, periodo, nivel, nota)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(alumno_id, criterio_id, periodo)
                    DO UPDATE SET nivel = excluded.nivel, nota = excluded.nota
                """, (alumno_id, criterio_id, periodo, nivel, nota))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@evaluacion_directa_bp.route("/alumno")
def evaluacion_directa_alumno():
    alumno_id = request.args.get("alumno_id")
    area_id   = request.args.get("area_id")
    trimestre = request.args.get("trimestre")
    periodo   = f"T{trimestre}"
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT ec.criterio_id, ec.nivel 
        FROM evaluacion_criterios ec
        JOIN criterios c ON ec.criterio_id = c.id
        WHERE ec.alumno_id = ? AND c.area_id = ? AND ec.periodo = ?
    """, (alumno_id, area_id, periodo))
    datos = cur.fetchall()
    return jsonify({str(c["criterio_id"]): c["nivel"] for c in datos})

@evaluacion_directa_bp.route("/media")
def media_directa():
    alumno_id = request.args.get("alumno_id")
    area_id = request.args.get("area_id")
    trimestre = request.args.get("trimestre")
    periodo = f"T{trimestre}"
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT ROUND(AVG(ec.nota), 2)
        FROM evaluacion_criterios ec
        JOIN criterios c ON ec.criterio_id = c.id
        WHERE ec.alumno_id = ? AND c.area_id = ? AND ec.periodo = ?
    """, (alumno_id, area_id, periodo))
    media = cur.fetchone()[0]
    return jsonify({"media": media if media is not None else 0})

@evaluacion_directa_bp.route("/", methods=["DELETE"])
def borrar_evaluacion_directa():
    alumno_id = request.args.get("alumno_id")
    trimestre = request.args.get("trimestre")
    area_id = request.args.get("area_id")
    if not (alumno_id and trimestre and area_id):
        return jsonify({"ok": False, "error": "Faltan parametros"}), 400
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            DELETE FROM evaluacion_criterios 
            WHERE alumno_id = ? AND periodo = ? AND criterio_id IN (
                SELECT id FROM criterios WHERE area_id = ?
            )
        """, (alumno_id, f"T{trimestre}", area_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
    return jsonify({"ok": True})

@evaluacion_directa_bp.route("/tipo_grupo")
def tipo_grupo_activo():
    grupo_id = session.get('active_group_id')
    if not grupo_id: return jsonify({"tipo": "primaria"})
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT tipo_evaluacion FROM grupos WHERE id = ?", (grupo_id,))
    row = cur.fetchone()
    tipo = row["tipo_evaluacion"] if row and row["tipo_evaluacion"] else "primaria"
    return jsonify({"tipo": tipo})
