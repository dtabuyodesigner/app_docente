from flask import Blueprint, jsonify, request, session
from utils.db import get_db, nivel_a_nota

evaluacion_bp = Blueprint('evaluacion', __name__)

@evaluacion_bp.route("/api/evaluacion", methods=["DELETE"])
def borrar_evaluacion():
    alumno_id = request.args.get("alumno_id")
    sda_id = request.args.get("sda_id")
    trimestre = request.args.get("trimestre")
    if not (alumno_id and sda_id and trimestre):
        return jsonify({"ok": False, "error": "Faltan parametros"}), 400

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM evaluaciones WHERE alumno_id = ? AND sda_id = ? AND trimestre = ?", (alumno_id, sda_id, trimestre))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Error en borrar_evaluacion:", str(e))
        return jsonify({"ok": False, "error": "Error interno al borrar."}), 500
    return jsonify({"ok": True})

@evaluacion_bp.route("/api/evaluacion", methods=["POST"])
def guardar_evaluacion():
    d = request.json

    nivel = int(d["nivel"])
    nota = nivel_a_nota(nivel)

    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("BEGIN")
        cur.execute("""
            INSERT INTO evaluaciones (
                alumno_id, area_id, trimestre, sda_id, criterio_id,
                nivel, nota
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(alumno_id, criterio_id, sda_id, trimestre)
            DO UPDATE SET
                nivel = excluded.nivel,
                nota = excluded.nota
        """, (
            d["alumno_id"],
            d["area_id"],
            d["trimestre"],
            d["sda_id"],
            d["criterio_id"],
            nivel,
            nota
        ))

        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Error en guardar_evaluacion:", str(e))
        return jsonify({"ok": False, "error": "Error interno al guardar la evaluación."}), 500

    return jsonify({"ok": True})

@evaluacion_bp.route("/api/evaluacion")
def obtener_evaluacion():
    area_id = request.args["area_id"]
    sda_id = request.args["sda_id"]
    trimestre = request.args["trimestre"]

    conn = get_db()
    cur = conn.cursor()

    grupo_id = session.get('active_group_id')
    cur.execute("""
        SELECT e.alumno_id, e.criterio_id, e.nivel
        FROM evaluaciones e
        JOIN alumnos a ON e.alumno_id = a.id
        WHERE e.area_id = ?
          AND e.sda_id = ?
          AND e.trimestre = ?
          AND a.grupo_id = ?
    """, (area_id, sda_id, trimestre, grupo_id))

    datos = cur.fetchall()

    return jsonify([
        {
            "alumno_id": a,
            "criterio_id": c,
            "nivel": n
        }
        for a, c, n in datos
    ])

@evaluacion_bp.route("/api/evaluacion/areas")
def evaluacion_areas():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id, nombre FROM areas ORDER BY nombre")
    datos = cur.fetchall()

    return jsonify([
        {"id": a["id"], "nombre": a["nombre"]}
        for a in datos
    ])

@evaluacion_bp.route("/api/evaluacion/sda/<int:area_id>")
def evaluacion_sda(area_id):
    trimestre = request.args.get("trimestre")
    conn = get_db()
    cur = conn.cursor()

    if trimestre:
        cur.execute("""
            SELECT id, nombre, trimestre
            FROM sda
            WHERE area_id = ? AND (trimestre = ? OR trimestre IS NULL)
            ORDER BY id
        """, (area_id, trimestre))
    else:
        cur.execute("""
            SELECT id, nombre, trimestre
            FROM sda
            WHERE area_id = ?
            ORDER BY id
        """, (area_id,))

    datos = cur.fetchall()

    return jsonify([
        {"id": s["id"], "nombre": f"[T{s['trimestre']}] {s['nombre']}" if s['trimestre'] else s['nombre']}
        for s in datos
    ])

@evaluacion_bp.route("/api/evaluacion/criterios/<int:sda_id>")
def evaluacion_criterios(sda_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT c.id, c.codigo, c.descripcion
        FROM criterios c
        JOIN sda_criterios sc ON sc.criterio_id = c.id
        WHERE sc.sda_id = ?
        ORDER BY c.id
    """, (sda_id,))

    datos = cur.fetchall()

    return jsonify([
        {"id": c["id"], "codigo": c["codigo"], "descripcion": c["descripcion"]}
        for c in datos
    ])

@evaluacion_bp.route("/api/evaluacion/alumno")
def evaluacion_alumno():
    alumno_id = request.args.get("alumno_id")
    sda_id = request.args.get("sda_id")
    trimestre = request.args.get("trimestre")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT criterio_id, nivel
        FROM evaluaciones
        WHERE alumno_id = ?
          AND sda_id = ?
          AND trimestre = ?
    """, (alumno_id, sda_id, trimestre))

    datos = cur.fetchall()

    return jsonify({
        str(c["criterio_id"]): c["nivel"]
        for c in datos
    })

@evaluacion_bp.route("/api/evaluacion/media")
def media_sda():
    alumno_id = request.args.get("alumno_id")
    sda_id = request.args.get("sda_id")
    trimestre = request.args.get("trimestre")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT ROUND(AVG(nota), 2)
        FROM evaluaciones
        WHERE alumno_id = ?
          AND sda_id = ?
          AND trimestre = ?
    """, (alumno_id, sda_id, trimestre))

    media = cur.fetchone()[0]

    return jsonify({
        "media": media if media is not None else 0
    })

@evaluacion_bp.route("/api/evaluacion/media_area")
def media_area():
    alumno_id = request.args.get("alumno_id")
    area_id = request.args.get("area_id")
    trimestre = request.args.get("trimestre")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT ROUND(AVG(nota), 2)
        FROM evaluaciones
        WHERE alumno_id = ?
          AND area_id = ?
          AND trimestre = ?
    """, (alumno_id, area_id, trimestre))

    media = cur.fetchone()[0]

    return jsonify({
        "media": media if media is not None else 0
    })

@evaluacion_bp.route("/api/evaluacion/resumen_areas")
def resumen_areas_alumno():
    alumno_id = request.args.get("alumno_id")
    trimestre = request.args.get("trimestre")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT a.nombre, ROUND(AVG(e.nota), 2) as media
        FROM evaluaciones e
        JOIN areas a ON e.area_id = a.id
        WHERE e.alumno_id = ?
          AND e.trimestre = ?
        GROUP BY a.id, a.nombre
        ORDER BY a.nombre
    """, (alumno_id, trimestre))

    rows = cur.fetchall()
    
    return jsonify([
         {"area": row["nombre"], "media": row["media"]}
         for row in rows
    ])

@evaluacion_bp.route("/api/evaluacion/resumen_sda_todos")
def resumen_sda_todos():
    alumno_id = request.args.get("alumno_id")
    trimestre = request.args.get("trimestre")
    
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT a.nombre as area, s.nombre as sda, ROUND(AVG(e.nota), 2) as media
        FROM evaluaciones e
        JOIN areas a ON e.area_id = a.id
        JOIN sda s ON e.sda_id = s.id
        WHERE e.alumno_id = ?
          AND e.trimestre = ?
        GROUP BY a.nombre, s.nombre
        ORDER BY a.nombre, s.nombre
    """, (alumno_id, trimestre))
    
    rows = cur.fetchall()
    
    return jsonify([
        {"area": r["area"], "sda": r["sda"], "media": r["media"]}
        for r in rows
    ])

@evaluacion_bp.route("/api/rubricas/<int:criterio_id>")
def obtener_rubrica(criterio_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT nivel, descriptor FROM rubricas WHERE criterio_id = ? ORDER BY nivel", (criterio_id,))
    rows = cur.fetchall()
    
    return jsonify({str(r["nivel"]): r["descriptor"] for r in rows})

@evaluacion_bp.route("/api/rubricas", methods=["POST"])
def guardar_rubrica():
    d = request.json
    criterio_id = d.get("criterio_id")
    descriptores = d.get("descriptores") # Expecting { "1": "text", ... }
    
    if not criterio_id or not descriptores:
         return jsonify({"ok": False, "error": "Faltan datos"}), 400
         
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("BEGIN")
        for nivel_str, texto in descriptores.items():
            cur.execute("""
                INSERT INTO rubricas (criterio_id, nivel, descriptor) 
                VALUES (?, ?, ?)
                ON CONFLICT(criterio_id, nivel) DO UPDATE SET descriptor = excluded.descriptor
            """, (criterio_id, int(nivel_str), texto))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        print("Error en guardar_rubrica:", str(e))
        return jsonify({"ok": False, "error": "Error interno al guardar rúbrica."}), 500

@evaluacion_bp.route("/api/rubricas/<int:criterio_id>", methods=["DELETE"])
def borrar_rubrica_criterio(criterio_id):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM rubricas WHERE criterio_id = ?", (criterio_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Error en borrar_rubrica_criterio:", str(e))
        return jsonify({"ok": False, "error": "Error al borrar la rúbrica."}), 500
    return jsonify({"ok": True})

@evaluacion_bp.route("/api/curricular/full")
def curricular_full():
    conn = get_db()
    cur = conn.cursor()
    
    # Get all areas
    cur.execute("SELECT id, nombre FROM areas ORDER BY nombre")
    areas = [dict(a) for a in cur.fetchall()]
    
    for area in areas:
        # Get SDAs for this area
        cur.execute("SELECT id, nombre, trimestre FROM sda WHERE area_id = ? ORDER BY id", (area["id"],))
        sdas = [dict(s) for s in cur.fetchall()]
        
        for sda in sdas:
            # Get activities for this SDA
            cur.execute("SELECT id, nombre, sesiones, descripcion FROM actividades_sda WHERE sda_id = ? ORDER BY id", (sda["id"],))
            sda["actividades"] = [dict(act) for act in cur.fetchall()]
            
            # Get criteria for this SDA
            cur.execute("""
                SELECT c.codigo, c.descripcion
                FROM criterios c
                JOIN sda_criterios sc ON sc.criterio_id = c.id
                WHERE sc.sda_id = ?
                ORDER BY c.id
            """, (sda["id"],))
            sda["criterios"] = [dict(crit) for crit in cur.fetchall()]
            
            # Get competencies for this SDA
            cur.execute("""
                SELECT c.codigo, c.descripcion
                FROM competencias_especificas c
                JOIN sda_competencias sc ON sc.competencia_id = c.id
                WHERE sc.sda_id = ?
                ORDER BY c.id
            """, (sda["id"],))
            sda["competencias"] = [dict(comp) for comp in cur.fetchall()]
            
        area["sdas"] = sdas
        
    return jsonify(areas)

@evaluacion_bp.route("/api/curricular/sa", methods=["POST"])
def crear_sa():
    d = request.json
    nombre = d.get("nombre", "").strip()
    area_id = d.get("area_id")
    trimestre = d.get("trimestre")
    criterios = d.get("criterios", [])
    competencias = d.get("competencias", [])
    actividades = d.get("actividades", [])
    
    if not nombre or not area_id or not trimestre:
        return jsonify({"ok": False, "error": "Faltan datos obligatorios (nombre, área, trimestre)."}), 400
        
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("BEGIN")
        
        # 1. Crear SA
        cur.execute("INSERT INTO sda (nombre, area_id, trimestre) VALUES (?, ?, ?)", (nombre, area_id, trimestre))
        sda_id = cur.lastrowid
        
        # 2. Gestionar Criterios
        for c in criterios:
            codigo = c.get("codigo", "").strip()
            desc = c.get("descripcion", "").strip()
            if not codigo: continue
            
            # Buscar si el criterio ya existe para esa área
            cur.execute("SELECT id FROM criterios WHERE codigo = ? AND area_id = ?", (codigo, area_id))
            row = cur.fetchone()
            if row:
                crit_id = row["id"]
                # Opcional: actualizar descripción si ha cambiado?
                # cur.execute("UPDATE criterios SET descripcion = ? WHERE id = ?", (desc, crit_id))
            else:
                cur.execute("INSERT INTO criterios (codigo, descripcion, area_id) VALUES (?, ?, ?)", (codigo, desc, area_id))
                crit_id = cur.lastrowid
                
            # Vincular a la SA
            cur.execute("INSERT OR IGNORE INTO sda_criterios (sda_id, criterio_id) VALUES (?, ?)", (sda_id, crit_id))
            
        # 2b. Gestionar Competencias
        for c in competencias:
            codigo = c.get("codigo", "").strip()
            desc = c.get("descripcion", "").strip()
            if not codigo: continue
            
            cur.execute("SELECT id FROM competencias_especificas WHERE codigo = ? AND area_id = ?", (codigo, area_id))
            row = cur.fetchone()
            if row:
                comp_id = row["id"]
            else:
                cur.execute("INSERT INTO competencias_especificas (codigo, descripcion, area_id) VALUES (?, ?, ?)", (codigo, desc, area_id))
                comp_id = cur.lastrowid
                
            cur.execute("INSERT OR IGNORE INTO sda_competencias (sda_id, competencia_id) VALUES (?, ?)", (sda_id, comp_id))
            
        # 3. Gestionar Actividades
        for a in actividades:
            a_nom = a.get("nombre", "").strip()
            a_desc = a.get("descripcion", "").strip()
            a_ses = int(a.get("sesiones", 1))
            if not a_nom: continue
            
            cur.execute("INSERT INTO actividades_sda (sda_id, nombre, sesiones, descripcion) VALUES (?, ?, ?, ?)", (sda_id, a_nom, a_ses, a_desc))
            
        conn.commit()
        return jsonify({"ok": True, "sda_id": sda_id})
    except Exception as e:
        conn.rollback()
        print("Error en crear_sa:", str(e))
        return jsonify({"ok": False, "error": "Error interno al crear SA."}), 500

@evaluacion_bp.route("/api/curricular/sa/<int:sda_id>", methods=["PUT"])
def actualizar_sa(sda_id):
    d = request.json
    nombre = d.get("nombre", "").strip()
    area_id = d.get("area_id")
    trimestre = d.get("trimestre")
    criterios = d.get("criterios", [])
    competencias = d.get("competencias", [])
    actividades = d.get("actividades", [])
    
    if not nombre or not area_id or not trimestre:
        return jsonify({"ok": False, "error": "Faltan datos obligatorios."}), 400
        
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("BEGIN")
        
        # 1. Update SA
        cur.execute("UPDATE sda SET nombre = ?, area_id = ?, trimestre = ? WHERE id = ?", (nombre, area_id, trimestre, sda_id))
        
        # 2. Reset and recreate Criteria links
        cur.execute("DELETE FROM sda_criterios WHERE sda_id = ?", (sda_id,))
        for c in criterios:
            codigo = c.get("codigo", "").strip()
            desc = c.get("descripcion", "").strip()
            if not codigo: continue
            
            cur.execute("SELECT id FROM criterios WHERE codigo = ? AND area_id = ?", (codigo, area_id))
            row = cur.fetchone()
            if row:
                crit_id = row["id"]
                cur.execute("UPDATE criterios SET descripcion = ? WHERE id = ?", (desc, crit_id))
            else:
                cur.execute("INSERT INTO criterios (codigo, descripcion, area_id) VALUES (?, ?, ?)", (codigo, desc, area_id))
                crit_id = cur.lastrowid
                
            cur.execute("INSERT OR IGNORE INTO sda_criterios (sda_id, criterio_id) VALUES (?, ?)", (sda_id, crit_id))
            
        # 2b. Reset and recreate Competencies links
        cur.execute("DELETE FROM sda_competencias WHERE sda_id = ?", (sda_id,))
        for c in competencias:
            codigo = c.get("codigo", "").strip()
            desc = c.get("descripcion", "").strip()
            if not codigo: continue
            
            cur.execute("SELECT id FROM competencias_especificas WHERE codigo = ? AND area_id = ?", (codigo, area_id))
            row = cur.fetchone()
            if row:
                comp_id = row["id"]
                cur.execute("UPDATE competencias_especificas SET descripcion = ? WHERE id = ?", (desc, comp_id))
            else:
                cur.execute("INSERT INTO competencias_especificas (codigo, descripcion, area_id) VALUES (?, ?, ?)", (codigo, desc, area_id))
                comp_id = cur.lastrowid
                
            cur.execute("INSERT OR IGNORE INTO sda_competencias (sda_id, competencia_id) VALUES (?, ?)", (sda_id, comp_id))
            
        # 3. Update Activities (Preserving IDs to keep sessions)
        actividad_ids_to_keep = []
        for a in actividades:
            a_id = a.get("id")
            if a_id and str(a_id).isdigit():
                actividad_ids_to_keep.append(int(a_id))
                
        if actividad_ids_to_keep:
            placeholders = ','.join('?' for _ in actividad_ids_to_keep)
            params = [sda_id] + actividad_ids_to_keep
            cur.execute(f"DELETE FROM actividades_sda WHERE sda_id = ? AND id NOT IN ({placeholders})", params)
        else:
            cur.execute("DELETE FROM actividades_sda WHERE sda_id = ?", (sda_id,))
            
        for a in actividades:
            a_id = a.get("id")
            a_nom = a.get("nombre", "").strip()
            a_desc = a.get("descripcion", "").strip()
            a_ses = int(a.get("sesiones", 1))
            if not a_nom: continue
            
            if a_id and str(a_id).isdigit():
                cur.execute("UPDATE actividades_sda SET nombre = ?, sesiones = ?, descripcion = ? WHERE id = ?", (a_nom, a_ses, a_desc, int(a_id)))
            else:
                cur.execute("INSERT INTO actividades_sda (sda_id, nombre, sesiones, descripcion) VALUES (?, ?, ?, ?)", (sda_id, a_nom, a_ses, a_desc))
            
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        print("Error en actualizar_sa:", str(e))
        return jsonify({"ok": False, "error": "Error interno al actualizar SA."}), 500

@evaluacion_bp.route("/api/curricular/sa/<int:sda_id>", methods=["DELETE"])
def borrar_sa(sda_id):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        
        # Check if SA exists
        cur.execute("SELECT id FROM sda WHERE id = ?", (sda_id,))
        if not cur.fetchone():
            return jsonify({"ok": False, "error": "SA no encontrada."}), 404
            
        # Unlink or delete dependencies
        cur.execute("DELETE FROM sda_criterios WHERE sda_id = ?", (sda_id,))
        cur.execute("DELETE FROM sda_competencias WHERE sda_id = ?", (sda_id,))
        cur.execute("DELETE FROM actividades_sda WHERE sda_id = ?", (sda_id,))
        cur.execute("DELETE FROM evaluaciones WHERE sda_id = ?", (sda_id,))
        cur.execute("UPDATE programacion_diaria SET sda_id = NULL WHERE sda_id = ?", (sda_id,))
        
        # Delete SA
        cur.execute("DELETE FROM sda WHERE id = ?", (sda_id,))
        
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        print("Error en borrar_sa:", str(e))
        return jsonify({"ok": False, "error": "Error interno al borrar SA."}), 500

@evaluacion_bp.route("/api/importar_sda", methods=["POST"])
def importar_sda():
    d = request.json
    csv_text = d.get("csv", "")
    if not csv_text:
        return jsonify({"ok": False, "error": "No hay datos"}), 400
        
    lines = csv_text.strip().split("\n")
    if not lines:
        return jsonify({"ok": False, "error": "El archivo está vacío."}), 400
        
    start_idx = 0
    if lines[0].lower().startswith("area"):
        start_idx = 1
        
    valid_lines = []
    for i in range(start_idx, len(lines)):
        line = lines[i].strip()
        if not line: continue
        parts = line.split(";")
        if len(parts) < 5:
            return jsonify({"ok": False, "error": f"Error en línea {i+1}: Faltan columnas separadas por (;)"}), 400
        try:
            int(parts[2].strip() or 1)
        except ValueError:
            return jsonify({"ok": False, "error": f"Error en línea {i+1}: El trimestre debe ser un número entero."}), 400
        valid_lines.append(parts)
        
    if not valid_lines:
        return jsonify({"ok": False, "error": "No hay datos válidos para procesar."}), 400

    conn = get_db()
    cur = conn.cursor()
    
    imported = 0
    try:
        cur.execute("BEGIN")
        for parts in valid_lines:
            area_name = parts[0].strip()
            sda_name = parts[1].strip()
            trimestre = int(parts[2].strip() or 1)
            crit_code = parts[3].strip()
            crit_desc = parts[4].strip()
            
            # 1. Get/Create Area
            cur.execute("SELECT id FROM areas WHERE nombre = ?", (area_name,))
            row = cur.fetchone()
            if row: 
                area_id = row["id"]
            else:
                cur.execute("INSERT INTO areas (nombre) VALUES (?)", (area_name,))
                area_id = cur.lastrowid
                
            # 2. Get/Create SDA
            cur.execute("SELECT id FROM sda WHERE nombre = ? AND area_id = ?", (sda_name, area_id))
            row = cur.fetchone()
            if row: 
                sda_id = row["id"]
            else:
                cur.execute("INSERT INTO sda (nombre, area_id, trimestre) VALUES (?, ?, ?)", (sda_name, area_id, trimestre))
                sda_id = cur.lastrowid
                
            # 3. Get/Create Criterion
            cur.execute("SELECT id FROM criterios WHERE codigo = ? AND area_id = ?", (crit_code, area_id))
            row = cur.fetchone()
            if row: 
                crit_id = row["id"]
            else:
                cur.execute("INSERT INTO criterios (codigo, descripcion, area_id) VALUES (?, ?, ?)", (crit_code, crit_desc, area_id))
                crit_id = cur.lastrowid
                
            # 4. Link SDA - Criterion
            cur.execute("INSERT OR IGNORE INTO sda_criterios (sda_id, criterio_id) VALUES (?, ?)", (sda_id, crit_id))
            imported += 1
            
        conn.commit()
        return jsonify({"ok": True, "count": imported})
    except Exception as e:
        conn.rollback()
        print("Error en importar_sda:", str(e))
        return jsonify({"ok": False, "error": "Error interno al importar SDA."}), 500

@evaluacion_bp.route("/api/importar_actividades", methods=["POST"])
def importar_actividades():
    d = request.json
    csv_text = d.get("csv", "")
    if not csv_text:
        return jsonify({"ok": False, "error": "No hay datos"}), 400
        
    lines = csv_text.strip().split("\n")
    if not lines:
        return jsonify({"ok": False, "error": "El archivo está vacío."}), 400
        
    start_idx = 0
    if lines[0].lower().startswith("sda"):
        start_idx = 1
        
    valid_lines = []
    for i in range(start_idx, len(lines)):
        line = lines[i].strip()
        if not line: continue
        parts = line.split(";")
        if len(parts) < 2:
            return jsonify({"ok": False, "error": f"Error en línea {i+1}: Faltan columnas (necesita SDA y Actividad)."}), 400
            
        if len(parts) > 2 and parts[2].strip():
            try:
                int(parts[2].strip())
            except ValueError:
                return jsonify({"ok": False, "error": f"Error en línea {i+1}: El número de sesiones debe ser un entero."}), 400
                
        valid_lines.append(parts)
        
    if not valid_lines:
        return jsonify({"ok": False, "error": "No hay datos válidos para procesar."}), 400

    conn = get_db()
    cur = conn.cursor()
    
    imported = 0
    try:
        cur.execute("BEGIN")
        for parts in valid_lines:
            sda_name = parts[0].strip()
            act_name = parts[1].strip()
            sesiones = int(parts[2].strip() if len(parts) > 2 and parts[2].strip() else 1)
            descripcion = parts[3].strip() if len(parts) > 3 else ""
            
            # Find SDA by name
            cur.execute("SELECT id FROM sda WHERE nombre = ?", (sda_name,))
            row = cur.fetchone()
            if not row: continue
            sda_id = row["id"]
            
            # Insert Activity
            cur.execute("""
                INSERT INTO actividades_sda (sda_id, nombre, sesiones, descripcion)
                VALUES (?, ?, ?, ?)
            """, (sda_id, act_name, sesiones, descripcion))
            imported += 1
            
        conn.commit()
        return jsonify({"ok": True, "count": imported})
    except Exception as e:
        conn.rollback()
        print("Error en importar_actividades:", str(e))
        return jsonify({"ok": False, "error": "Error interno al importar actividades."}), 500

@evaluacion_bp.route("/api/actividades/<int:actividad_id>/sesiones", methods=["GET"])
def obtener_sesiones_actividad(actividad_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, numero_sesion, descripcion, fecha FROM sesiones_actividad WHERE actividad_id = ? ORDER BY numero_sesion", (actividad_id,))
    datos = [dict(row) for row in cur.fetchall()]
    return jsonify(datos)

@evaluacion_bp.route("/api/actividades/<int:actividad_id>/sesiones", methods=["POST"])
def guardar_sesiones_actividad(actividad_id):
    d = request.json
    sesiones = d.get("sesiones", [])
    
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        keep_ids = [int(s["id"]) for s in sesiones if s.get("id")]
        if keep_ids:
            placeholders = ','.join('?' for _ in keep_ids)
            cur.execute(f"DELETE FROM sesiones_actividad WHERE actividad_id = ? AND id NOT IN ({placeholders})", [actividad_id] + keep_ids)
        else:
            cur.execute("DELETE FROM sesiones_actividad WHERE actividad_id = ?", (actividad_id,))

        for s in sesiones:
            s_id = s.get("id")
            num = s.get("numero_sesion")
            desc = s.get("descripcion")
            fecha = s.get("fecha")
            
            if s_id:
                cur.execute("UPDATE sesiones_actividad SET numero_sesion=?, descripcion=?, fecha=? WHERE id=?", (num, desc, fecha, s_id))
            else:
                cur.execute("INSERT INTO sesiones_actividad (actividad_id, numero_sesion, descripcion, fecha) VALUES (?, ?, ?, ?)", (actividad_id, num, desc, fecha))
                
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        print("Error guardar_sesiones_actividad:", str(e))
        return jsonify({"ok": False, "error": str(e)}), 500
