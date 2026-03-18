from flask import Blueprint, jsonify, request, session
from utils.db import get_db, nivel_a_nota
from datetime import date

evaluacion_bp = Blueprint('evaluacion', __name__)

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

    criterios = cur.execute("""
        SELECT c.id, c.codigo, c.descripcion
        FROM criterios c
        JOIN criterios_periodo cp ON cp.criterio_id = c.id
        WHERE cp.periodo = ? AND c.area_id = ? AND cp.grupo_id = ? AND cp.activo = 1
    """, (periodo, area_id, grupo_id)).fetchall()

    evaluaciones = cur.execute("""
        SELECT alumno_id, criterio_id, nivel
        FROM evaluaciones
        WHERE area_id = ? AND trimestre = ? AND sda_id IS NULL
    """, (area_id, trimestre)).fetchall()

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

    rows = cur.execute("""
        SELECT c.codigo, c.descripcion, AVG(e.nivel) as media
        FROM evaluaciones e
        JOIN criterios c ON c.id = e.criterio_id
        JOIN alumnos a ON e.alumno_id = a.id
        WHERE c.area_id = ? AND e.trimestre = ? AND a.grupo_id = ?
        GROUP BY c.codigo
    """, (area_id, trimestre, grupo_id)).fetchall()

    return jsonify([dict(r) for r in rows])

@evaluacion_bp.route("/clase_hoy")
def clase_hoy():
    fecha_hoy = date.today().isoformat()
    grupo_id = session.get('active_group_id')
    
    db = get_db()
    cur = db.cursor()
    
    # 1. Obtener la primera sesión del día para el grupo
    cur.execute("""
        SELECT pd.id, pd.descripcion as actividad, pd.criterio_id, pd.sda_id, c.codigo as criterio_codigo, c.descripcion as criterio_desc
        FROM programacion_diaria pd
        LEFT JOIN criterios c ON pd.criterio_id = c.id
        WHERE pd.fecha = ?
        LIMIT 1
    """, (fecha_hoy,))
    
    sesion = cur.fetchone()
    
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
        cur.execute("""
            SELECT alumno_id, nivel
            FROM evaluaciones
            WHERE criterio_id = ? AND trimestre = ? AND sda_id IS NULL
        """, (sesion["criterio_id"], trimestre))
        evals = {r["alumno_id"]: r["nivel"] for r in cur.fetchall()}
        
        for a in alumnos:
            a["nivel"] = evals.get(a["id"])
            
    return jsonify({
        "sesion": dict(sesion) if sesion else None,
        "alumnos": alumnos,
        "trimestre": trimestre,
        "fecha": fecha_hoy,
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
        SELECT c.codigo, c.descripcion, e.nivel, c.comentario_base
        FROM evaluaciones e
        JOIN criterios c ON e.criterio_id = c.id
        WHERE e.alumno_id = ? AND e.trimestre = ?
    """, (alumno_id, trimestre))
    
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
