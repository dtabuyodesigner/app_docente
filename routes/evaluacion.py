from utils.db import get_db, nivel_a_nota
from datetime import date
import csv
import json
from io import StringIO, BytesIO
from flask import send_file, Blueprint, request, jsonify, session
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

evaluacion_bp = Blueprint('evaluacion_curricular', __name__)

@evaluacion_bp.route("/areas")
def listar_areas():
    """
    Lista las áreas filtradas por etapa para el cuaderno de evaluación.
    Similar a criterios_api.listar_areas pero bajo el prefijo /api/evaluacion
    """
    etapa_id = request.args.get('etapa_id')
    conn = get_db()
    cur = conn.cursor()
    
    query = """
        SELECT a.id, a.nombre, a.etapa_id, a.tipo_escala, a.modo_evaluacion
        FROM areas a
        WHERE a.activa = 1
    """
    params = []
    if etapa_id:
        query += " AND a.etapa_id = ?"
        params.append(etapa_id)
    
    query += " ORDER BY a.nombre ASC"
    cur.execute(query, params)
    return jsonify([dict(row) for row in cur.fetchall()])

@evaluacion_bp.route("/resumen_areas")
def resumen_areas_alumno():
    alumno_id = request.args.get("alumno_id")
    trimestre = request.args.get("trimestre")
    periodo = f"T{trimestre}"
    if not alumno_id or not trimestre:
        return jsonify([])
    conn = get_db()
    cur = conn.cursor()

    # Medias por área
    cur.execute("""
        SELECT a.id, a.nombre, ROUND(AVG(val.nota), 2) as media, a.tipo_escala
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
    areas = cur.fetchall()

    result = []
    for area in areas:
        # Criterios de esta área (por SDA)
        cur.execute("""
            SELECT c.codigo, c.descripcion, ROUND(AVG(e.nota), 2) as nota
            FROM evaluaciones e
            JOIN criterios c ON e.criterio_id = c.id
            WHERE e.alumno_id = ? AND e.trimestre = ? AND e.area_id = ?
            GROUP BY c.id, c.codigo, c.descripcion
            ORDER BY CAST(SUBSTR(c.codigo, INSTR(c.codigo,'.')+1) AS INTEGER), c.codigo
        """, (alumno_id, trimestre, area["id"]))
        criterios_sda = cur.fetchall()

        # Criterios directos
        cur.execute("""
            SELECT c.codigo, c.descripcion, ROUND(AVG(ec.nota), 2) as nota
            FROM evaluacion_criterios ec
            JOIN criterios c ON ec.criterio_id = c.id
            WHERE ec.alumno_id = ? AND ec.periodo = ? AND c.area_id = ?
            GROUP BY c.id, c.codigo, c.descripcion
            ORDER BY CAST(SUBSTR(c.codigo, INSTR(c.codigo,'.')+1) AS INTEGER), c.codigo
        """, (alumno_id, periodo, area["id"]))
        criterios_dir = cur.fetchall()

        criterios = [{"codigo": r["codigo"], "descripcion": r["descripcion"], "nota": r["nota"]} 
                     for r in (list(criterios_sda) + list(criterios_dir))]
        # Deduplicar por código
        seen = set()
        criterios_uniq = []
        for c in criterios:
            if c["codigo"] not in seen:
                seen.add(c["codigo"])
                criterios_uniq.append(c)

        result.append({
            "area": area["nombre"],
            "media": area["media"],
            "tipo_escala": area["tipo_escala"],
            "criterios": criterios_uniq
        })

    return jsonify(result)

@evaluacion_bp.route("/resumen_sda_todos")
def resumen_sda_todos():
    alumno_id = request.args.get("alumno_id")
    trimestre = request.args.get("trimestre")
    if not alumno_id or not trimestre:
        return jsonify([])
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.nombre as area, s.nombre as sda, ROUND(AVG(e.nota), 2) as media, a.tipo_escala
        FROM evaluaciones e
        JOIN sda s ON e.sda_id = s.id
        JOIN areas a ON s.area_id = a.id
        WHERE e.alumno_id = ? AND e.trimestre = ? AND e.sda_id IS NOT NULL
        GROUP BY s.id, s.nombre, a.nombre, a.tipo_escala
        ORDER BY a.nombre, s.nombre
    """, (alumno_id, trimestre))
    rows = cur.fetchall()
    return jsonify([{"area": r["area"], "sda": r["sda"], "media": r["media"], "tipo_escala": r["tipo_escala"]} for r in rows])

@evaluacion_bp.route("/criterio_clase")
def criterio_clase():
    criterio_id = request.args.get("criterio_id")
    grupo_id = request.args.get("grupo_id") or session.get('active_group_id')
    periodo = request.args.get("periodo")
    
    if not criterio_id or not grupo_id or not periodo:
        return jsonify({"error": "Faltan parámetros"}), 400

    trimestre = int(periodo.replace('T', ''))
    db = get_db()
    cur = db.cursor()

    sda_id = request.args.get("sda_id")
    if sda_id == 'null' or sda_id == 'directo' or not sda_id: sda_id = None

    alumnos = cur.execute("""
        SELECT id, nombre
        FROM alumnos
        WHERE grupo_id = ?
        ORDER BY nombre
    """, (grupo_id,)).fetchall()

    if sda_id:
        evaluaciones = cur.execute("""
            SELECT alumno_id, nivel
            FROM evaluaciones
            WHERE criterio_id = ? AND trimestre = ? AND sda_id = ?
        """, (criterio_id, trimestre, sda_id)).fetchall()
    else:
        evaluaciones = cur.execute("""
            SELECT alumno_id, nivel
            FROM evaluaciones
            WHERE criterio_id = ? AND trimestre = ? AND sda_id IS NULL
        """, (criterio_id, trimestre)).fetchall()

    return jsonify({
        "alumnos": [dict(a) for a in alumnos],
        "evaluaciones": [dict(e) for e in evaluaciones]
    })

@evaluacion_bp.route("/guardar_masivo", methods=["POST"])
def guardar_masivo():
    data = request.json
    periodo = data["periodo"]
    trimestre = int(periodo.replace('T', ''))
    
    db = get_db()
    cur = db.cursor()

    try:
        cur.execute("BEGIN")
        print(f"[DEBUG] Guardar masivo: periodo={periodo}, evaluaciones={len(data['evaluaciones'])}")
        
        for item in data["evaluaciones"]:
            alumno_id = item["alumno_id"]
            criterio_id = item["criterio_id"]
            nivel = item.get("nivel")
            sda_id = item.get("sda_id")
            if sda_id == 'null' or sda_id == 'directo' or not sda_id: sda_id = None

            if nivel is None:
                # Si el nivel es None, borramos la evaluación para este criterio/trimestre/alumno/sda
                # Y también borramos el historial (logs) para este contexto
                print(f"[DEBUG] Borrando evaluación y logs para alumno_id={alumno_id}, criterio_id={criterio_id}, trimestre={trimestre}, sda={sda_id}")
                if sda_id:
                    cur.execute("DELETE FROM evaluaciones_log WHERE alumno_id = ? AND criterio_id = ? AND trimestre = ? AND sda_id = ?", (alumno_id, criterio_id, trimestre, sda_id))
                    cur.execute("DELETE FROM evaluaciones WHERE alumno_id = ? AND criterio_id = ? AND trimestre = ? AND sda_id = ?", (alumno_id, criterio_id, trimestre, sda_id))
                else:
                    cur.execute("DELETE FROM evaluaciones_log WHERE alumno_id = ? AND criterio_id = ? AND trimestre = ? AND sda_id IS NULL", (alumno_id, criterio_id, trimestre))
                    cur.execute("DELETE FROM evaluaciones WHERE alumno_id = ? AND criterio_id = ? AND trimestre = ? AND sda_id IS NULL", (alumno_id, criterio_id, trimestre))
                continue

            # Obtener area_id y tipo_escala del criterio
            cur.execute("""
                SELECT c.area_id, a.tipo_escala 
                FROM criterios c 
                JOIN areas a ON c.area_id = a.id 
                WHERE c.id = ?
            """, (criterio_id,))
            row = cur.fetchone()
            if not row: 
                print(f"[WARN] Criterio {criterio_id} no encontrado")
                continue
            area_id = row["area_id"]
            tipo_escala = row["tipo_escala"]

            nota = nivel_a_nota(nivel, escala=tipo_escala)

            # 1. Insertar el Log (Historial) - Evitamos duplicados el mismo día
            # Borramos si ya existe hoy para este contexto antes de insertar
            hoy = date.today().isoformat()
            if sda_id:
                cur.execute("DELETE FROM evaluaciones_log WHERE alumno_id = ? AND criterio_id = ? AND sda_id = ? AND trimestre = ? AND fecha = ?", (alumno_id, criterio_id, sda_id, trimestre, hoy))
                cur.execute("""
                    INSERT INTO evaluaciones_log (alumno_id, area_id, trimestre, sda_id, criterio_id, nivel, nota, fecha)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (alumno_id, area_id, trimestre, sda_id, criterio_id, nivel, nota, hoy))
            else:
                cur.execute("DELETE FROM evaluaciones_log WHERE alumno_id = ? AND criterio_id = ? AND sda_id IS NULL AND trimestre = ? AND fecha = ?", (alumno_id, criterio_id, trimestre, hoy))
                cur.execute("""
                    INSERT INTO evaluaciones_log (alumno_id, area_id, trimestre, sda_id, criterio_id, nivel, nota, fecha)
                    VALUES (?, ?, ?, NULL, ?, ?, ?, ?)
                """, (alumno_id, area_id, trimestre, criterio_id, nivel, nota, hoy))

            # 2. Calcular la MEDIA desde los logs
            if sda_id:
                cur.execute("""
                    SELECT AVG(nota) as media_nota, AVG(nivel) as media_nivel
                    FROM evaluaciones_log
                    WHERE alumno_id = ? AND criterio_id = ? AND sda_id = ? AND trimestre = ?
                """, (alumno_id, criterio_id, sda_id, trimestre))
            else:
                cur.execute("""
                    SELECT AVG(nota) as media_nota, AVG(nivel) as media_nivel
                    FROM evaluaciones_log
                    WHERE alumno_id = ? AND criterio_id = ? AND sda_id IS NULL AND trimestre = ?
                """, (alumno_id, criterio_id, trimestre))
            
            stats = cur.fetchone()
            media_nota = stats["media_nota"]
            # Redondeamos el nivel al entero más cercano (1-4)
            media_nivel = int(round(stats["media_nivel"] or 0))

            print(f"[DEBUG] Guardando MEDIA: alumno={alumno_id}, crit={criterio_id}, sda={sda_id}, nivel_avg={media_nivel}, nota_avg={media_nota}")
            
            # 3. Actualizar la tabla principal de evaluaciones (Borrar + Insertar para manejar NULLs en sda_id)
            if sda_id:
                cur.execute("DELETE FROM evaluaciones WHERE alumno_id = ? AND criterio_id = ? AND sda_id = ? AND trimestre = ?", (alumno_id, criterio_id, sda_id, trimestre))
                cur.execute("""
                    INSERT INTO evaluaciones (alumno_id, criterio_id, area_id, trimestre, sda_id, nivel, nota)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (alumno_id, criterio_id, area_id, trimestre, sda_id, media_nivel, media_nota))
            else:
                cur.execute("DELETE FROM evaluaciones WHERE alumno_id = ? AND criterio_id = ? AND sda_id IS NULL AND trimestre = ?", (alumno_id, criterio_id, trimestre))
                cur.execute("""
                    INSERT INTO evaluaciones (alumno_id, criterio_id, area_id, trimestre, sda_id, nivel, nota)
                    VALUES (?, ?, ?, ?, NULL, ?, ?)
                """, (alumno_id, criterio_id, area_id, trimestre, media_nivel, media_nota))

            # --- AUTO-POPULATE criterios_periodo ---
            cur.execute("SELECT grupo_id FROM alumnos WHERE id = ?", (alumno_id,))
            a_row = cur.fetchone()
            if a_row:
                g_id = a_row["grupo_id"]
                cur.execute("""
                    INSERT INTO criterios_periodo (criterio_id, grupo_id, periodo, activo)
                    VALUES (?, ?, ?, 1)
                    ON CONFLICT(criterio_id, grupo_id, periodo) DO UPDATE SET activo=1
                """, (criterio_id, g_id, periodo))
        
        db.commit()
        return jsonify({"ok": True, "status": "ok"})
    except Exception as e:
        print(f"[ERROR] Error en guardar_masivo: {str(e)}")
        db.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@evaluacion_bp.route("/cuaderno", methods=["GET"])
def obtener_cuaderno():
    grupo_id = request.args.get("grupo_id") or session.get('active_group_id')
    area_id = request.args.get("area_id")
    periodo = request.args.get("periodo")

    if not grupo_id or not area_id or not periodo:
        return jsonify({"error": "Faltan parámetros"}), 400

    trimestre = int(periodo.replace('T', ''))
    db = get_db()
    cur = db.cursor()

    alumnos = cur.execute("""
        SELECT id, nombre
        FROM alumnos
        WHERE grupo_id = ?
        ORDER BY nombre
    """, (grupo_id,)).fetchall()

    # Fetch criteria. For Infantil (etapa_id=1), we show all active criteria of the area.
    # Otherwise, we use the criterios_periodo table for fine-grained selection.
    cur.execute("SELECT etapa_id FROM areas WHERE id = ?", (area_id,))
    area_row = cur.fetchone()
    etapa_id = area_row["etapa_id"] if area_row else None

    if etapa_id == 1: # Infantil
        criterios = cur.execute("""
            SELECT id, codigo, descripcion
            FROM criterios
            WHERE area_id = ? AND activo = 1
            ORDER BY codigo
        """, (area_id,)).fetchall()
    else:
        criterios = cur.execute("""
            SELECT c.id, c.codigo, c.descripcion
            FROM criterios c
            JOIN criterios_periodo cp ON cp.criterio_id = c.id
            WHERE cp.periodo = ? AND c.area_id = ? AND cp.grupo_id = ? AND cp.activo = 1
            ORDER BY c.codigo
        """, (periodo, area_id, grupo_id)).fetchall()

    evaluaciones = cur.execute("""
        SELECT alumno_id, criterio_id, nivel
        FROM evaluaciones
        WHERE area_id = ? AND trimestre = ? AND sda_id IS NULL
        UNION ALL
        SELECT ec.alumno_id, ec.criterio_id, ec.nivel
        FROM evaluacion_criterios ec
        JOIN criterios c ON ec.criterio_id = c.id
        WHERE c.area_id = ? AND ec.periodo = ?
    """, (area_id, trimestre, area_id, periodo)).fetchall()

    eval_map = {}
    for ev in evaluaciones:
        eval_map[f"{ev['alumno_id']}_{ev['criterio_id']}"] = ev["nivel"]

    return jsonify({
        "alumnos": [dict(a) for a in alumnos],
        "criterios": [dict(c) for c in criterios],
        "evaluaciones": eval_map
    })

@evaluacion_bp.route("/resumen_clase")
def resumen_clase():
    area_id = request.args.get("area_id")
    periodo = request.args.get("periodo")
    grupo_id = session.get('active_group_id')
    
    if not periodo or not area_id:
        return jsonify([])

    trimestre = int(periodo.replace('T', ''))
    db = get_db()
    cur = db.cursor()

    # UNIFIED: Get data from both evaluaciones (SDA) and evaluacion_criterios (Direct)
    rows = cur.execute("""
        SELECT c.codigo, c.descripcion, AVG(val.nivel) as media
        FROM (
            SELECT criterio_id, nivel FROM evaluaciones WHERE area_id = ? AND trimestre = ?
            UNION ALL
            SELECT criterio_id, nivel FROM evaluacion_criterios WHERE periodo = ?
        ) val
        JOIN criterios c ON c.id = val.criterio_id
        JOIN (SELECT id FROM alumnos WHERE grupo_id = ?) a ON val.criterio_id IN (SELECT id FROM criterios WHERE area_id = ?) -- This is just to ensure we only get relevant data
        WHERE c.area_id = ?
        GROUP BY c.codigo
    """, (area_id, trimestre, periodo, grupo_id, area_id, area_id)).fetchall()
    
    # Actually simpler:
    cur.execute("""
        SELECT c.codigo, c.descripcion, AVG(v.nivel) as media
        FROM criterios c
        LEFT JOIN (
            SELECT criterio_id, nivel, alumno_id FROM evaluaciones WHERE area_id = ? AND trimestre = ?
            UNION ALL
            SELECT criterio_id, nivel, alumno_id FROM evaluacion_criterios WHERE periodo = ?
        ) v ON c.id = v.criterio_id
        JOIN alumnos a ON v.alumno_id = a.id
        WHERE c.area_id = ? AND a.grupo_id = ?
        GROUP BY c.id, c.codigo, c.descripcion
        HAVING media IS NOT NULL
    """, (area_id, trimestre, periodo, area_id, grupo_id))
    
    rows = cur.fetchall()
    return jsonify([dict(r) for r in rows])

@evaluacion_bp.route("/directa/", methods=["GET"])
def get_directa():
    alumno_id = request.args.get("alumno_id")
    area_id = request.args.get("area_id")
    periodo = request.args.get("periodo")
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT ec.criterio_id, ec.nivel
        FROM evaluacion_criterios ec
        JOIN criterios c ON ec.criterio_id = c.id
        WHERE ec.alumno_id = ? AND ec.periodo = ? AND c.area_id = ?
    """, (alumno_id, periodo, area_id))
    rows = cur.fetchall()
    return jsonify({r["criterio_id"]: r["nivel"] for r in rows})

@evaluacion_bp.route("/directa/", methods=["POST"])
def save_directa():
    data = request.json
    alumno_id = data.get("alumno_id")
    criterio_id = data.get("criterio_id")
    periodo = data.get("periodo")
    nivel = data.get("nivel")
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("SELECT area_id, tipo_escala FROM areas WHERE id = (SELECT area_id FROM criterios WHERE id = ?)", (criterio_id,))
        area_row = cur.fetchone()
        area_id = area_row["area_id"]
        escala = area_row["tipo_escala"]
        nota = nivel_a_nota(nivel, escala)
        cur.execute("DELETE FROM evaluacion_criterios WHERE alumno_id = ? AND criterio_id = ? AND periodo = ?", (alumno_id, criterio_id, periodo))
        if nivel > 0:
            cur.execute("""
                INSERT INTO evaluacion_criterios (alumno_id, criterio_id, periodo, nivel, nota)
                VALUES (?, ?, ?, ?, ?)
            """, (alumno_id, criterio_id, periodo, nivel, nota))
        db.commit()
        return jsonify({"ok": True})
    except Exception as e:
        db.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@evaluacion_bp.route("/area/<int:area_id>/criterios_completos")
def get_criterios_completos_area(area_id):
    db = get_db()
    cur = db.cursor()
    rows = cur.execute("SELECT id, codigo, descripcion FROM criterios WHERE area_id = ? AND activo = 1", (area_id,)).fetchall()
    return jsonify([dict(r) for r in rows])

@evaluacion_bp.route("/criterio_extra", methods=["POST"])
def post_criterio_extra():
    """Vincular un criterio extra al grupo y trimestre actual."""
    data = request.json
    area_id = data.get("area_id")
    trimestre = data.get("trimestre")
    criterio_id = data.get("criterio_id")
    grupo_id = session.get('active_group_id')
    periodo = f"T{trimestre}"
    
    if not (area_id and trimestre and criterio_id and grupo_id):
        return jsonify({"ok": False, "error": "Faltan parámetros o grupo no activo"}), 400
        
    db = get_db()
    cur = db.cursor()
    try:
        # Lógica compatible con todas las versiones de SQLite (evitamos ON CONFLICT)
        cur.execute("SELECT id FROM criterios_periodo WHERE criterio_id=? AND grupo_id=? AND periodo=?", (criterio_id, grupo_id, periodo))
        exists = cur.fetchone()
        
        if exists:
            cur.execute("UPDATE criterios_periodo SET activo = 1 WHERE id = ?", (exists["id"],))
        else:
            cur.execute("""
                INSERT INTO criterios_periodo (criterio_id, grupo_id, periodo, activo)
                VALUES (?, ?, ?, 1)
            """, (criterio_id, grupo_id, periodo))
            
        db.commit()
        return jsonify({"ok": True, "sda_id": "directo"})
    except Exception as e:
        db.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@evaluacion_bp.route("/sda/resumen_areas")
def resumen_areas_sda_alumno():
    # Placeholder for the endpoint requested by frontend (line 1051)
    # Actually should be unified
    return resumen_areas_alumno() # Reuse existing logic


@evaluacion_bp.route("/clase_hoy")
def clase_hoy():
    fecha_hoy = date.today().isoformat()
    grupo_id = session.get('active_group_id')
    
    db = get_db()
    cur = db.cursor()
    session_id = request.args.get("session_id")
    
    # 1. Obtener todas las sesiones del día para el grupo activo
    cur.execute("""
        SELECT pd.id, pd.descripcion as actividad, pd.criterio_id, pd.sda_id, 
               c.codigo as criterio_codigo, c.descripcion as criterio_desc,
               c.area_id, a.nombre as area_nombre
        FROM programacion_diaria pd
        LEFT JOIN criterios c ON pd.criterio_id = c.id
        LEFT JOIN sda s ON pd.sda_id = s.id
        LEFT JOIN areas a ON c.area_id = a.id
        WHERE pd.fecha = ? AND (s.grupo_id = ? OR s.grupo_id IS NULL OR pd.actividad_id IS NULL)
        ORDER BY 
            (CASE WHEN s.grupo_id = ? THEN 0 ELSE 1 END) ASC,
            (CASE WHEN pd.criterio_id IS NOT NULL THEN 0 ELSE 1 END) ASC,
            pd.id ASC
    """, (fecha_hoy, grupo_id, grupo_id))
    
    sesiones = [dict(r) for r in cur.fetchall()]
    
    if session_id:
        target_ses = next((s for s in sesiones if str(s["id"]) == session_id), None)
        sesion = target_ses if target_ses else (sesiones[0] if sesiones else None)
    else:
        sesion = sesiones[0] if sesiones else None
    
    # 2. Alumnos y su asistencia hoy (SIEMPRE se cargan si hay grupo_id)
    if not grupo_id:
        return jsonify({"ok": False, "error": "No hay grupo activo seleccionado"}), 400

    cur.execute("""
        SELECT a.id, a.nombre, COALESCE(ast.estado, 'presente') as asistencia
        FROM alumnos a
        LEFT JOIN asistencia ast ON a.id = ast.alumno_id AND ast.fecha = ?
        WHERE a.grupo_id = ?
        ORDER BY a.nombre
    """, (fecha_hoy, grupo_id))
    alumnos = [dict(r) for r in cur.fetchall()]
    
    # 3. Evaluaciones para el criterio de hoy (si hay)
    mes = date.today().month
    # T1: Sept (9) a Dic (12)
    # T2: Ene (1) a Marzo (3)
    # T3: Abril (4) a Junio (6)
    if 9 <= mes <= 12: trimestre = 1
    elif 1 <= mes <= 3: trimestre = 2
    else: trimestre = 3
    
    if sesion and sesion["criterio_id"]:
        sda_id = sesion["sda_id"]
        if sda_id:
            cur.execute("""
                SELECT alumno_id, nivel
                FROM evaluaciones
                WHERE criterio_id = ? AND trimestre = ? AND sda_id = ?
            """, (sesion["criterio_id"], trimestre, sda_id))
        else:
            cur.execute("""
                SELECT alumno_id, nivel
                FROM evaluaciones
                WHERE criterio_id = ? AND trimestre = ? AND sda_id IS NULL
            """, (sesion["criterio_id"], trimestre))
        
        evals = {r["alumno_id"]: r["nivel"] for r in cur.fetchall()}
        
        for a in alumnos:
            a["nivel"] = evals.get(a["id"])
            
    etapa_id = None
    if sesion and sesion["area_id"]:
        cur.execute("SELECT etapa_id FROM areas WHERE id = ?", (sesion["area_id"],))
        area_row = cur.fetchone()
        if area_row: etapa_id = area_row["etapa_id"]

    return jsonify({
        "sesiones": sesiones,
        "sesion": dict(sesion) if sesion else None,
        "alumnos": alumnos,
        "trimestre": trimestre,
        "fecha": fecha_hoy,
        "etapa_id": etapa_id,
        "ok": True
    })

@evaluacion_bp.route("/informe/alumno")
def informe_alumno():
    alumno_id = request.args.get("alumno_id")
    trimestre = request.args.get("trimestre")
    
    if not alumno_id or not trimestre:
        return jsonify({"error": "Faltan parámetros"}), 400
        
    db = get_db()
    cur = db.cursor()
    
    cur.execute("""
        SELECT c.codigo, c.descripcion, v.nivel, c.comentario_base
        FROM (
            SELECT criterio_id, nivel FROM evaluaciones WHERE alumno_id = ? AND trimestre = ?
            UNION ALL
            SELECT criterio_id, nivel FROM evaluacion_criterios WHERE alumno_id = ? AND periodo = ?
        ) v
        JOIN criterios c ON v.criterio_id = c.id
    """, (alumno_id, trimestre, alumno_id, f"T{trimestre}"))
    
    evaluaciones = cur.fetchall()
    comentarios = []
    
    for ev in evaluaciones:
        nivel = ev["nivel"]
        desc = ev["descripcion"]
        base = ev["comentario_base"] or ""
        
        comment = ""
        if nivel == 1:
            comment = f"Necesita apoyo en {desc}."
        elif nivel == 2:
            comment = f"Está en proceso de mejorar en {desc}."
        elif nivel == 3:
            comment = f"Comprende y aplica adecuadamente {desc}."
        elif nivel == 4:
            comment = f"Destaca especialmente en {desc}."
            
        if base:
            comment += f" {base}"
            
        comentarios.append(comment)
        
    return jsonify({
        "alumno_id": alumno_id,
        "trimestre": trimestre,
        "comentarios": comentarios
    })

def get_cuaderno_data(cur, area_id, periodo):
    """Helper to fetch notebook data for exports."""
    cur.execute("SELECT id, nombre FROM alumnos WHERE grupo_id = (SELECT id FROM grupos WHERE activo = 1) ORDER BY nombre")
    alumnos = [dict(row) for row in cur.fetchall()]
    
    cur.execute("SELECT id, codigo, descripcion FROM criterios WHERE area_id = ? ORDER BY codigo", (area_id,))
    criterios = [dict(row) for row in cur.fetchall()]
    
    trimestre = periodo.replace('T', '')
    cur.execute("""
        SELECT alumno_id, criterio_id, nivel FROM evaluaciones WHERE area_id = ? AND trimestre = ? AND sda_id IS NULL
        UNION ALL
        SELECT alumno_id, criterio_id, nivel FROM evaluacion_criterios WHERE periodo = ?
    """, (area_id, trimestre, periodo))
    rows = cur.fetchall()
    evaluaciones = {f"{r['alumno_id']}_{r['criterio_id']}": r['nivel'] for r in rows}
    
    return {"alumnos": alumnos, "criterios": criterios, "evaluaciones": evaluaciones}

@evaluacion_bp.route("/cuaderno/csv")
def cuaderno_csv():
    area_id = request.args.get("area_id")
    periodo = request.args.get("periodo", "T1")
    if not area_id: return "Falta area_id", 400
    conn = get_db()
    cur = conn.cursor()
    data = get_cuaderno_data(cur, area_id, periodo)
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Alumno"] + [c["codigo"] for c in data["criterios"]])
    for a in data["alumnos"]:
        row = [a["nombre"]]
        for c in data["criterios"]:
            nivel = data["evaluaciones"].get(f"{a['id']}_{c['id']}", "")
            row.append(nivel)
        writer.writerow(row)
    output.seek(0)
    return send_file(BytesIO(output.getvalue().encode('utf-8-sig')), mimetype="text/csv", as_attachment=True, download_name=f"Cuaderno_{area_id}_{periodo}.csv")

@evaluacion_bp.route("/cuaderno/pdf")
def cuaderno_pdf():
    area_id = request.args.get("area_id")
    periodo = request.args.get("periodo", "T1")
    if not area_id: return "Falta area_id", 400
    conn = get_db()
    cur = conn.cursor()
    data = get_cuaderno_data(cur, area_id, periodo)
    cur.execute("SELECT nombre FROM areas WHERE id = ?", (area_id,))
    area_nombre = cur.fetchone()["nombre"]
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    elements = []
    styles = getSampleStyleSheet()
    elements.append(Paragraph(f"Cuaderno de Evaluación: {area_nombre} ({periodo})", styles['Title']))
    elements.append(Spacer(1, 12))
    table_data = [["Alumno"] + [c["codigo"] for c in data["criterios"]]]
    for a in data["alumnos"]:
        row = [a["nombre"]]
        for c in data["criterios"]:
            nivel = data["evaluaciones"].get(f"{a['id']}_{c['id']}", "-")
            row.append(str(nivel))
        table_data.append(row)
    t = Table(table_data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 8)
    ]))
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, mimetype="application/pdf", as_attachment=True, download_name=f"Cuaderno_{area_nombre}.pdf")
