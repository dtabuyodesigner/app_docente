from flask import Blueprint, jsonify, request, session
from utils.db import get_db, nivel_a_nota

evaluacion_sda_bp = Blueprint('evaluacion_sda', __name__)

@evaluacion_sda_bp.route("/lista")
def listar_sdas():
    area_id = request.args.get("area_id")
    trimestre = request.args.get("trimestre")
    grupo_id = session.get('active_group_id')
    conn = get_db()
    cur = conn.cursor()
    query = "SELECT id, nombre, trimestre FROM sda WHERE area_id = ?"
    params = [area_id]
    if trimestre:
        query += " AND (trimestre = ? OR trimestre IS NULL)"
        params.append(trimestre)
    if grupo_id:
        query += " AND (grupo_id = ? OR grupo_id IS NULL)"
        params.append(grupo_id)
    query += " ORDER BY id"
    cur.execute(query, params)
    return jsonify([{"id": r["id"], "nombre": f"[T{r['trimestre']}] {r['nombre']}" if r['trimestre'] else r['nombre']} for r in cur.fetchall()])

@evaluacion_sda_bp.route("/criterios/<int:sda_id>")
def get_sda_criterios(sda_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.id, c.codigo, c.descripcion
        FROM criterios c
        JOIN sda_criterios sc ON sc.criterio_id = c.id
        WHERE sc.sda_id = ?
        ORDER BY c.id
    """, (sda_id,))
    return jsonify([dict(r) for r in cur.fetchall()])

@evaluacion_sda_bp.route("/", methods=["POST"])
def guardar_evaluacion_sda():
    d = request.json
    nivel = int(d["nivel"])
    nota = nivel_a_nota(nivel)
    sda_id = d.get("sda_id")
    # Si sda_id es 'null' (string de JS) o está vacío, tratarlo como None (NULL en DB)
    if sda_id == 'null' or sda_id == '': sda_id = None
    
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        cur.execute("""
            INSERT INTO evaluaciones (alumno_id, area_id, trimestre, sda_id, criterio_id, nivel, nota)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(alumno_id, criterio_id, sda_id, trimestre)
            DO UPDATE SET nivel = excluded.nivel, nota = excluded.nota
        """, (d["alumno_id"], d["area_id"], d["trimestre"], sda_id, d["criterio_id"], nivel, nota))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@evaluacion_sda_bp.route("/alumno")
def evaluacion_sda_alumno():
    alumno_id = request.args.get("alumno_id")
    sda_id    = request.args.get("sda_id")
    trimestre = request.args.get("trimestre")
    area_id   = request.args.get("area_id")
    conn = get_db()
    cur = conn.cursor()
    if sda_id and sda_id != 'null' and sda_id != 'None':
        cur.execute("""
            SELECT criterio_id, nivel FROM evaluaciones
            WHERE alumno_id = ? AND sda_id = ? AND trimestre = ?
        """, (alumno_id, sda_id, trimestre))
    else:
        cur.execute("""
            SELECT criterio_id, nivel FROM evaluaciones
            WHERE alumno_id = ? AND sda_id IS NULL AND trimestre = ? AND area_id = ?
        """, (alumno_id, trimestre, area_id))
    datos = cur.fetchall()
    return jsonify({str(c["criterio_id"]): c["nivel"] for c in datos})

@evaluacion_sda_bp.route("/media")
def media_sda():
    alumno_id = request.args.get("alumno_id")
    sda_id    = request.args.get("sda_id")
    trimestre = request.args.get("trimestre")
    area_id   = request.args.get("area_id")
    conn = get_db()
    cur = conn.cursor()
    if sda_id and sda_id != 'null' and sda_id != 'None':
        cur.execute("""
            SELECT ROUND(AVG(nota), 2) FROM evaluaciones
            WHERE alumno_id = ? AND sda_id = ? AND trimestre = ?
        """, (alumno_id, sda_id, trimestre))
    else:
        cur.execute("""
            SELECT ROUND(AVG(nota), 2) FROM evaluaciones
            WHERE alumno_id = ? AND sda_id IS NULL AND trimestre = ? AND area_id = ?
        """, (alumno_id, trimestre, area_id))
    media = cur.fetchone()[0]
    return jsonify({"media": media if media is not None else 0})

@evaluacion_sda_bp.route("/media_area")
def media_area():
    alumno_id = request.args.get("alumno_id")
    area_id = request.args.get("area_id")
    trimestre = request.args.get("trimestre")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT modo_evaluacion, tipo_escala FROM areas WHERE id = ?", (area_id,))
    area_row = cur.fetchone()
    if not area_row: return jsonify({"media": 0})
    
    if area_row["modo_evaluacion"] == "POR_CRITERIOS_DIRECTOS":
        cur.execute("""
            SELECT ROUND(AVG(ec.nota), 2)
            FROM evaluacion_criterios ec
            JOIN criterios c ON ec.criterio_id = c.id
            WHERE ec.alumno_id = ? AND c.area_id = ? AND ec.periodo = ?
        """, (alumno_id, area_id, f"T{trimestre}"))
    else:
        cur.execute("""
            SELECT ROUND(AVG(nota), 2)
            FROM evaluaciones
            WHERE alumno_id = ? AND area_id = ? AND trimestre = ?
        """, (alumno_id, area_id, trimestre))
    media = cur.fetchone()[0]
    return jsonify({"media": media if media is not None else 0, "tipo_escala": area_row["tipo_escala"]})

@evaluacion_sda_bp.route("/resumen_areas")
def resumen_areas_alumno():
    alumno_id = request.args.get("alumno_id")
    trimestre = request.args.get("trimestre")
    periodo = f"T{trimestre}"
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.nombre, ROUND(AVG(val.nota), 2) as media, a.tipo_escala
        FROM (
            SELECT area_id, nota FROM evaluaciones WHERE alumno_id = ? AND trimestre = ?
            UNION ALL
            SELECT c.area_id, ec.nota 
            FROM evaluacion_criterios ec
            JOIN criterios c ON ec.criterio_id = c.id
            WHERE ec.alumno_id = ? AND ec.periodo = ?
        ) val
        JOIN areas a ON val.area_id = a.id
        GROUP BY a.id, a.nombre, a.tipo_escala
        ORDER BY a.nombre
    """, (alumno_id, trimestre, alumno_id, periodo))
    rows = cur.fetchall()
    return jsonify([{"area": r["nombre"], "media": r["media"], "tipo_escala": r["tipo_escala"]} for r in rows])

@evaluacion_sda_bp.route("/", methods=["DELETE"])
def borrar_evaluacion():
    alumno_id = request.args.get("alumno_id")
    sda_id    = request.args.get("sda_id")
    trimestre = request.args.get("trimestre")
    area_id   = request.args.get("area_id")
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        if area_id:
            cur.execute("SELECT modo_evaluacion FROM areas WHERE id = ?", (area_id,))
            ar = cur.fetchone()
            if ar and ar["modo_evaluacion"] == "POR_CRITERIOS_DIRECTOS":
                cur.execute("""
                    DELETE FROM evaluacion_criterios 
                    WHERE alumno_id = ? AND periodo = ? AND criterio_id IN (
                        SELECT id FROM criterios WHERE area_id = ?
                    )
                """, (alumno_id, f"T{trimestre}", area_id))
                conn.commit()
                return jsonify({"ok": True})
        if sda_id and sda_id != 'null' and sda_id != 'None':
            cur.execute("DELETE FROM evaluaciones WHERE alumno_id = ? AND sda_id = ? AND trimestre = ?", (alumno_id, sda_id, trimestre))
        else:
            cur.execute("DELETE FROM evaluaciones WHERE alumno_id = ? AND sda_id IS NULL AND trimestre = ? AND area_id = ?", (alumno_id, trimestre, area_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
    return jsonify({"ok": True})

@evaluacion_sda_bp.route("/tabla")
def datos_tabla_evaluacion():
    area_id = request.args.get("area_id")
    sda_id = request.args.get("sda_id")
    trimestre = request.args.get("trimestre")
    grupo_id = session.get('active_group_id')
    
    if sda_id == 'null' or sda_id == '': sda_id = None
    
    conn = get_db()
    cur = conn.cursor()
    
    # 1. Alumnos del grupo
    cur.execute("SELECT id, nombre FROM alumnos WHERE grupo_id = ? ORDER BY nombre", (grupo_id,))
    alumnos = [dict(r) for r in cur.fetchall()]
    
    # 2. Criterios de la SDA o del Área/Periodo (Directa)
    if sda_id:
        cur.execute("""
            SELECT c.id, c.codigo, c.descripcion
            FROM criterios c
            JOIN sda_criterios sc ON sc.criterio_id = c.id
            WHERE sc.sda_id = ?
            ORDER BY c.id
        """, (sda_id,))
    else:
        # Criterios directos para el área y periodo (T1, T2, T3)
        periodo = f"T{trimestre}"
        cur.execute("""
            SELECT c.id, c.codigo, c.descripcion
            FROM criterios c
            JOIN criterios_periodo cp ON cp.criterio_id = c.id
            WHERE cp.grupo_id = ? AND cp.periodo = ? AND c.area_id = ? AND cp.activo = 1
            ORDER BY c.id
        """, (grupo_id, periodo, area_id))
    
    criterios = [dict(r) for r in cur.fetchall()]
    
    # 3. Evaluaciones actuales
    if sda_id:
        cur.execute("""
            SELECT alumno_id, criterio_id, nivel 
            FROM evaluaciones
            WHERE sda_id = ? AND trimestre = ?
        """, (sda_id, trimestre))
    else:
        cur.execute("""
            SELECT alumno_id, criterio_id, nivel 
            FROM evaluaciones
            WHERE sda_id IS NULL AND area_id = ? AND trimestre = ?
        """, (area_id, trimestre))
    
    evals = cur.fetchall()
    eval_map = {}
    for ev in evals:
        key = f"{ev['alumno_id']}_{ev['criterio_id']}"
        eval_map[key] = ev["nivel"]
        
    return jsonify({
        "alumnos": alumnos,
        "criterios": criterios,
        "evaluaciones": eval_map
    })

@evaluacion_sda_bp.route("/resumen_clase")
def resumen_clase():
    area_id = request.args.get("area_id")
    trimestre = request.args.get("trimestre")
    grupo_id = session.get('active_group_id')
    
    conn = get_db()
    cur = conn.cursor()
    
    # Calcular media por criterio para el grupo y trimestre
    cur.execute("""
        SELECT c.codigo as criterio, ROUND(AVG(e.nivel), 2) as media
        FROM evaluaciones e
        JOIN criterios c ON e.criterio_id = c.id
        JOIN alumnos a ON e.alumno_id = a.id
        WHERE a.grupo_id = ? AND e.area_id = ? AND e.trimestre = ?
        GROUP BY e.criterio_id
        ORDER BY c.codigo
    """, (grupo_id, area_id, trimestre))
    
    rows = cur.fetchall()
    return jsonify([dict(r) for r in rows])
