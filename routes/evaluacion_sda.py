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
    try:
        alumno_id   = int(d.get("alumno_id"))
        area_id     = int(d.get("area_id"))
        trimestre   = int(d.get("trimestre"))
        criterio_id = d.get("criterio_id")
        if criterio_id is not None and criterio_id != 'null' and criterio_id != '' and criterio_id != 0:
            criterio_id = int(criterio_id)
        else:
            criterio_id = None
        nivel       = d.get("nivel")
        nivel       = int(nivel) if nivel is not None else None
        sda_id      = d.get("sda_id")
        if sda_id in (None, 'null', 'None', '', 0): 
            sda_id = None
        else: 
            sda_id = int(sda_id)
    except (ValueError, TypeError) as e:
        return jsonify({"ok": False, "error": f"Parámetros inválidos: {str(e)}"}), 400

    conn = get_db()
    cur = conn.cursor()

    # Get scale of the area
    cur.execute("SELECT tipo_escala FROM areas WHERE id = ?", (area_id,))
    area_row = cur.fetchone()
    escala = area_row["tipo_escala"] if area_row else None

    nota = nivel_a_nota(nivel, escala)

    try:
        cur.execute("BEGIN")
        
        # Usamos DELETE + INSERT para evitar problemas con ON CONFLICT y NULL sda_id en SQLite
        if criterio_id is not None:
            # Evaluación de criterio específico dentro de una SDA
            if sda_id is not None:
                cur.execute("DELETE FROM evaluaciones WHERE alumno_id = ? AND criterio_id = ? AND sda_id = ? AND trimestre = ?", 
                           (alumno_id, criterio_id, sda_id, trimestre))
                cur.execute("""
                    INSERT INTO evaluaciones (alumno_id, area_id, trimestre, sda_id, criterio_id, nivel, nota)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (alumno_id, area_id, trimestre, sda_id, criterio_id, nivel, nota))
            else:
                cur.execute("DELETE FROM evaluaciones WHERE alumno_id = ? AND criterio_id = ? AND sda_id IS NULL AND trimestre = ?", 
                           (alumno_id, criterio_id, trimestre))
                cur.execute("""
                    INSERT INTO evaluaciones (alumno_id, area_id, trimestre, sda_id, criterio_id, nivel, nota)
                    VALUES (?, ?, ?, NULL, ?, ?, ?)
                """, (alumno_id, area_id, trimestre, criterio_id, nivel, nota))
        else:
            # Evaluación directa de la SDA (sin criterio específico)
            # ADVERTENCIA: La tabla 'evaluaciones' tiene criterio_id NOT NULL en el schema.
            # Si esto falla, es porque se necesita un criterio_id válido o cambiar el schema.
            if sda_id is not None:
                cur.execute("DELETE FROM evaluaciones WHERE alumno_id = ? AND sda_id = ? AND trimestre = ? AND criterio_id IS NULL", 
                           (alumno_id, sda_id, trimestre))
                cur.execute("""
                    INSERT INTO evaluaciones (alumno_id, area_id, trimestre, sda_id, criterio_id, nivel, nota)
                    VALUES (?, ?, ?, ?, NULL, ?, ?)
                """, (alumno_id, area_id, trimestre, sda_id, nivel, nota))
            else:
                # Caso poco probable: sin criterio y sin SDA
                cur.execute("DELETE FROM evaluaciones WHERE alumno_id = ? AND sda_id IS NULL AND trimestre = ? AND criterio_id IS NULL", 
                           (alumno_id, trimestre))
                cur.execute("""
                    INSERT INTO evaluaciones (alumno_id, area_id, trimestre, sda_id, criterio_id, nivel, nota)
                    VALUES (?, ?, ?, NULL, NULL, ?, ?)
                """, (alumno_id, area_id, trimestre, nivel, nota))
        
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        import traceback
        error_detail = traceback.format_exc()
        print(f"[ERROR guardar_evaluacion_sda] {error_detail}")
        return jsonify({"ok": False, "error": str(e)}), 500

@evaluacion_sda_bp.route("/alumno")
def evaluacion_sda_alumno():
    alumno_id = request.args.get("alumno_id")
    sda_id    = request.args.get("sda_id")
    trimestre = request.args.get("trimestre")
    area_id   = request.args.get("area_id")
    
    try:
        if alumno_id: alumno_id = int(alumno_id)
        if trimestre: trimestre = int(trimestre)
        if area_id: area_id = int(area_id)
        if sda_id and sda_id != 'null' and sda_id != 'None':
            sda_id = int(sda_id)
        else:
            sda_id = None
    except (ValueError, TypeError):
        return jsonify({})

    conn = get_db()
    cur = conn.cursor()
    if sda_id:
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

    try:
        if alumno_id: alumno_id = int(alumno_id)
        if trimestre: trimestre = int(trimestre)
        if area_id: area_id = int(area_id)
        if sda_id and sda_id != 'null' and sda_id != 'None':
            sda_id = int(sda_id)
        else:
            sda_id = None
    except (ValueError, TypeError):
        return jsonify({"media": 0})

    conn = get_db()
    cur = conn.cursor()
    if sda_id:
        cur.execute("""
            SELECT ROUND(AVG(nota), 2) FROM evaluaciones
            WHERE alumno_id = ? AND sda_id = ? AND trimestre = ?
        """, (alumno_id, sda_id, trimestre))
    else:
        # Si no hay sda_id, promediar TODO lo del área y trimestre para el alumno
        # Esto asegura que la media global coincida con todos los criterios visibles
        cur.execute("""
            SELECT ROUND(AVG(nota), 2) FROM evaluaciones
            WHERE alumno_id = ? AND area_id = ? AND trimestre = ?
        """, (alumno_id, area_id, trimestre))
    media = cur.fetchone()[0]
    return jsonify({"media": media if media is not None else 0})

@evaluacion_sda_bp.route("/media_area")
def media_area():
    alumno_id = request.args.get("alumno_id")
    area_id = request.args.get("area_id")
    trimestre = request.args.get("trimestre")
    if not all([alumno_id, area_id, trimestre]): return jsonify({"media": 0})
    try:
        alumno_id = int(alumno_id)
        area_id = int(area_id)
        trimestre = int(trimestre)
    except (ValueError, TypeError):
        return jsonify({"media": 0})
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
    if not all([alumno_id, trimestre]): return jsonify([])
    try:
        alumno_id = int(alumno_id)
        trimestre = int(trimestre)
    except (ValueError, TypeError):
        return jsonify([])
    
    periodo = f"T{trimestre}"
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.nombre as area_nombre, a.tipo_escala, val.codigo, val.nota
        FROM (
            SELECT evaluaciones.area_id, CriterionTable.codigo, nota 
            FROM evaluaciones 
            JOIN criterios as CriterionTable ON evaluaciones.criterio_id = CriterionTable.id
            WHERE evaluaciones.alumno_id = ? AND evaluaciones.trimestre = ?
            
            UNION ALL
            
            SELECT c.area_id, c.codigo, ec.nota 
            FROM evaluacion_criterios ec
            JOIN criterios c ON ec.criterio_id = c.id
            WHERE ec.alumno_id = ? AND ec.periodo = ?
        ) val
        JOIN areas a ON val.area_id = a.id
        ORDER BY a.nombre, val.codigo
    """, (alumno_id, trimestre, alumno_id, periodo))
    rows = cur.fetchall()
    
    # Agrupar por área
    resumen = {}
    for r in rows:
        area = r["area_nombre"]
        if area not in resumen:
            resumen[area] = {
                "area": area,
                "tipo_escala": r["tipo_escala"],
                "criterios": [],
                "sum_notas": 0,
                "count_notas": 0
            }
        resumen[area]["criterios"].append({
            "codigo": r["codigo"],
            "nota": r["nota"]
        })
        resumen[area]["sum_notas"] += r["nota"]
        resumen[area]["count_notas"] += 1

    final_data = []
    for area_name in sorted(resumen.keys()):
        item = resumen[area_name]
        item["media"] = round(item["sum_notas"] / item["count_notas"], 2) if item["count_notas"] > 0 else 0
        final_data.append(item)

    return jsonify(final_data)


@evaluacion_sda_bp.route("/", methods=["DELETE"])
def borrar_evaluacion():
    alumno_id = request.args.get("alumno_id")
    sda_id    = request.args.get("sda_id")
    trimestre = request.args.get("trimestre")
    area_id   = request.args.get("area_id")
    
    if not (alumno_id and trimestre and area_id):
        return jsonify({"ok": False, "error": "Faltan parámetros alumno_id, area_id o trimestre"}), 400

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        
        # Determinar si el área es POR_CRITERIOS_DIRECTOS
        cur.execute("SELECT modo_evaluacion FROM areas WHERE id = ?", (area_id,))
        ar = cur.fetchone()
        
        if ar and ar["modo_evaluacion"] == "POR_CRITERIOS_DIRECTOS":
            # Borrar de evaluacion_criterios
            cur.execute("""
                DELETE FROM evaluacion_criterios 
                WHERE alumno_id = ? AND periodo = ? AND criterio_id IN (
                    SELECT id FROM criterios WHERE area_id = ?
                )
            """, (alumno_id, f"T{trimestre}", area_id))
            
            # También borrar de evaluaciones por si acaso hay restos
            cur.execute("DELETE FROM evaluaciones WHERE alumno_id = ? AND area_id = ? AND trimestre = ?", 
                       (alumno_id, area_id, trimestre))
        else:
            # Modo SDA o POR_ACTIVIDADES
            if sda_id and sda_id not in ('null', 'None', '', '0'):
                # Borrar solo de una SDA específica
                cur.execute("DELETE FROM evaluaciones WHERE alumno_id = ? AND sda_id = ? AND trimestre = ?", 
                           (alumno_id, sda_id, trimestre))
            else:
                # Borrar TODAS las evaluaciones del área/trimestre para este alumno (Limpieza completa)
                cur.execute("DELETE FROM evaluaciones WHERE alumno_id = ? AND area_id = ? AND trimestre = ?", 
                           (alumno_id, area_id, trimestre))
        
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        import traceback
        print(f"[ERROR borrar_evaluacion] {traceback.format_exc()}")
        return jsonify({"ok": False, "error": str(e)}), 500

@evaluacion_sda_bp.route("/tabla")
def datos_tabla_evaluacion():
    area_id = request.args.get("area_id")
    sda_id = request.args.get("sda_id")
    trimestre = request.args.get("trimestre")
    grupo_id = session.get('active_group_id')
    
    try:
        area_id = int(area_id)
        trimestre = int(trimestre)
        if sda_id and sda_id != 'null': sda_id = int(sda_id)
        else: sda_id = None
    except (ValueError, TypeError):
        return jsonify({"alumnos": [], "criterios": [], "evaluaciones": {}})
    
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

@evaluacion_sda_bp.route("/cuaderno", methods=["GET"])
def obtener_cuaderno():
    grupo_id = request.args.get("grupo_id") or session.get('active_group_id')
    area_id = request.args.get("area_id")
    periodo = request.args.get("periodo") # e.g., 'T1'

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
        SELECT c.id, c.codigo
        FROM criterios c
        JOIN criterios_periodo cp ON cp.criterio_id = c.id
        WHERE cp.periodo = ? AND c.area_id = ? AND cp.grupo_id = ? AND cp.activo = 1
    """, (periodo, area_id, grupo_id)).fetchall()

    evaluaciones = cur.execute("""
        SELECT alumno_id, criterio_id, nivel
        FROM evaluaciones
        WHERE area_id = ? AND trimestre = ? AND sda_id IS NULL
    """, (area_id, trimestre)).fetchall()

    return jsonify({
        "alumnos": [dict(a) for a in alumnos],
        "criterios": [dict(c) for c in criterios],
        "evaluaciones": [dict(e) for e in evaluaciones]
    })

@evaluacion_sda_bp.route("/guardar", methods=["POST"])
def guardar_evaluacion_rapida():
    data = request.json
    try:
        alumno_id = int(data["alumno_id"])
        criterio_id = int(data["criterio_id"])
        
        # Soportar 'periodo' (TX) o 'trimestre' (X)
        if "periodo" in data and data["periodo"]:
            trimestre = int(str(data["periodo"]).replace('T', ''))
        elif "trimestre" in data and data["trimestre"]:
            trimestre = int(data["trimestre"])
        else:
            return jsonify({"error": "Falta periodo o trimestre"}), 400
            
        nivel = data.get("nivel")
        if nivel is not None: nivel = int(nivel)
        
        sda_id = data.get("sda_id")
        if sda_id in (None, 'null', 'None', '', 0):
            sda_id = None
        else:
            sda_id = int(sda_id)
            
    except (ValueError, KeyError, TypeError) as e:
        return jsonify({"error": f"Parámetros inválidos: {str(e)}"}), 400
    
    db = get_db()
    cur = db.cursor()

    # Obtener area_id y escala del criterio
    cur.execute("""
        SELECT c.area_id, a.tipo_escala 
        FROM criterios c 
        JOIN areas a ON c.area_id = a.id 
        WHERE c.id = ?
    """, (criterio_id,))
    row = cur.fetchone()
    if not row:
        return jsonify({"error": "Criterio no encontrado"}), 404
    
    area_id = row["area_id"]
    escala = row["tipo_escala"]
    nota = nivel_a_nota(nivel, escala) if nivel is not None else None

    try:
        cur.execute("BEGIN")
        
        # Usar DELETE + INSERT para evitar problemas con ON CONFLICT y NULL sda_id en SQLite
        if sda_id is not None:
            cur.execute("DELETE FROM evaluaciones WHERE alumno_id = ? AND criterio_id = ? AND sda_id = ? AND trimestre = ?", 
                       (alumno_id, criterio_id, sda_id, trimestre))
            cur.execute("""
                INSERT INTO evaluaciones (alumno_id, criterio_id, area_id, trimestre, sda_id, nivel, nota)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (alumno_id, criterio_id, area_id, trimestre, sda_id, nivel, nota))
        else:
            cur.execute("DELETE FROM evaluaciones WHERE alumno_id = ? AND criterio_id = ? AND sda_id IS NULL AND trimestre = ?", 
                       (alumno_id, criterio_id, trimestre))
            cur.execute("""
                INSERT INTO evaluaciones (alumno_id, criterio_id, area_id, trimestre, sda_id, nivel, nota)
                VALUES (?, ?, ?, ?, NULL, ?, ?)
            """, (alumno_id, criterio_id, area_id, trimestre, nivel, nota))
            
        db.commit()
        return jsonify({"ok": True, "status": "ok"})
    except Exception as e:
        db.rollback()
        import traceback
        print(f"[ERROR guardar_evaluacion_rapida] {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

@evaluacion_sda_bp.route("/resumen_clase")
def resumen_clase_v2():
    area_id = request.args.get("area_id")
    periodo = request.args.get("periodo") # e.g. 'T1'
    grupo_id = session.get('active_group_id')
    
    if not periodo or not area_id:
        return jsonify([])

    trimestre = int(periodo.replace('T', ''))
    db = get_db()
    cur = db.cursor()

    rows = cur.execute("""
        SELECT c.codigo, AVG(e.nivel) as media
        FROM evaluaciones e
        JOIN criterios c ON c.id = e.criterio_id
        JOIN alumnos a ON e.alumno_id = a.id
        WHERE c.area_id = ? AND e.trimestre = ? AND a.grupo_id = ?
        GROUP BY c.codigo
    """, (area_id, trimestre, grupo_id)).fetchall()

    return jsonify([dict(r) for r in rows])

@evaluacion_sda_bp.route("/criterio_clase")
def criterio_clase():
    criterio_id = request.args.get("criterio_id")
    grupo_id = request.args.get("grupo_id") or session.get('active_group_id')
    periodo = request.args.get("periodo")
    
    if not criterio_id or not grupo_id or not periodo:
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

    evaluaciones = cur.execute("""
        SELECT alumno_id, nivel
        FROM evaluaciones
        WHERE criterio_id = ? AND trimestre = ? AND sda_id IS NULL
    """, (criterio_id, trimestre)).fetchall()

    return jsonify({
        "alumnos": [dict(a) for a in alumnos],
        "evaluaciones": [dict(e) for e in evaluaciones]
    })

@evaluacion_sda_bp.route("/guardar_masivo", methods=["POST"])
def guardar_masivo():
    data = request.json
    periodo = data["periodo"]
    trimestre = int(periodo.replace('T', ''))
    
    db = get_db()
    cur = db.cursor()

    try:
        cur.execute("BEGIN")
        for item in data["evaluaciones"]:
            nivel = item.get("nivel")
            if nivel is None: continue
            
            alumno_id = item["alumno_id"]
            criterio_id = item["criterio_id"]
            
            # Obtener area_id y escala del criterio
            cur.execute("SELECT area_id, tipo_escala FROM areas WHERE id = (SELECT area_id FROM criterios WHERE id = ?)", (criterio_id,))
            row = cur.fetchone()
            if not row: continue
            area_id = row["area_id"]
            escala = row["tipo_escala"]
            
            nota = nivel_a_nota(nivel, escala)

            cur.execute("""
                INSERT INTO evaluaciones (alumno_id, criterio_id, area_id, trimestre, sda_id, nivel, nota)
                VALUES (?, ?, ?, ?, NULL, ?, ?)
                ON CONFLICT(alumno_id, criterio_id, sda_id, trimestre)
                DO UPDATE SET nivel=excluded.nivel, nota=excluded.nota
            """, (alumno_id, criterio_id, area_id, trimestre, nivel, nota))
        
        db.commit()
        return jsonify({"status": "ok"})
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

@evaluacion_sda_bp.route("/aplicar_general", methods=["POST"])
def aplicar_general():
    data = request.json
    grupo_id = data["grupo_id"]
    criterio_id = data["criterio_id"]
    periodo = data["periodo"]
    nivel = data["nivel"]
    
    trimestre = int(periodo.replace('T', ''))
    nota = nivel_a_nota(nivel)
    
    db = get_db()
    cur = db.cursor()

    try:
        cur.execute("BEGIN")
        
        # Obtener area_id y escala
        cur.execute("SELECT area_id, tipo_escala FROM areas WHERE id = (SELECT area_id FROM criterios WHERE id = ?)", (criterio_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Criterio no encontrado"}), 404
        area_id = row["area_id"]
        escala = row["tipo_escala"]

        # Obtener todos los alumnos del grupo
        alumnos = cur.execute("SELECT id FROM alumnos WHERE grupo_id = ?", (grupo_id,)).fetchall()

        for alumno in alumnos:
            cur.execute("""
                INSERT INTO evaluaciones (alumno_id, criterio_id, area_id, trimestre, sda_id, nivel, nota)
                VALUES (?, ?, ?, ?, NULL, ?, ?)
                ON CONFLICT(alumno_id, criterio_id, sda_id, trimestre)
                DO UPDATE SET nivel=excluded.nivel, nota=excluded.nota
            """, (alumno["id"], criterio_id, area_id, trimestre, nivel, nivel_a_nota(nivel, escala)))

        db.commit()
        return jsonify({"status": "ok"})
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
