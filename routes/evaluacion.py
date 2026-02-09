from flask import Blueprint, jsonify, request
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
    cur.execute("DELETE FROM evaluaciones WHERE alumno_id = ? AND sda_id = ? AND trimestre = ?", (alumno_id, sda_id, trimestre))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@evaluacion_bp.route("/api/evaluacion", methods=["POST"])
def guardar_evaluacion():
    d = request.json

    nivel = int(d["nivel"])
    nota = nivel_a_nota(nivel)

    conn = get_db()
    cur = conn.cursor()

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
    conn.close()

    return jsonify({"ok": True})

@evaluacion_bp.route("/api/evaluacion")
def obtener_evaluacion():
    area_id = request.args["area_id"]
    sda_id = request.args["sda_id"]
    trimestre = request.args["trimestre"]

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT alumno_id, criterio_id, nivel
        FROM evaluaciones
        WHERE area_id = ?
          AND sda_id = ?
          AND trimestre = ?
    """, (area_id, sda_id, trimestre))

    datos = cur.fetchall()
    conn.close()

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
    conn.close()

    return jsonify([
        {"id": a["id"], "nombre": a["nombre"]}
        for a in datos
    ])

@evaluacion_bp.route("/api/evaluacion/sda/<int:area_id>")
def evaluacion_sda(area_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, nombre
        FROM sda
        WHERE area_id = ?
        ORDER BY id
    """, (area_id,))

    datos = cur.fetchall()
    conn.close()

    return jsonify([
        {"id": s["id"], "nombre": s["nombre"]}
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
    conn.close()

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
    conn.close()

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
    conn.close()

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
    conn.close()

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
    conn.close()
    
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
    conn.close()
    
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
    conn.close()
    
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
        for nivel, texto in descriptores.items():
            cur.execute("""
                INSERT INTO rubricas (criterio_id, nivel, descriptor) 
                VALUES (?, ?, ?)
                ON CONFLICT(criterio_id, nivel) DO UPDATE SET descriptor = excluded.descriptor
            """, (criterio_id, int(nivel), texto))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()

@evaluacion_bp.route("/api/rubricas/<int:criterio_id>", methods=["DELETE"])
def borrar_rubrica_criterio(criterio_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM rubricas WHERE criterio_id = ?", (criterio_id,))
    conn.commit()
    conn.close()
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
            
        area["sdas"] = sdas
        
    conn.close()
    return jsonify(areas)

@evaluacion_bp.route("/api/importar_sda", methods=["POST"])
def importar_sda():
    d = request.json
    csv_text = d.get("csv", "")
    if not csv_text:
        return jsonify({"ok": False, "error": "No hay datos"}), 400
        
    lines = csv_text.strip().split("\n")
    conn = get_db()
    cur = conn.cursor()
    
    imported = 0
    try:
        for line in lines:
            parts = line.split(";")
            if len(parts) < 5: continue
            
            area_name = parts[0].strip()
            sda_name = parts[1].strip()
            trimestre = int(parts[2].strip() or 1)
            crit_code = parts[3].strip()
            crit_desc = parts[4].strip()
            
            # 1. Get/Create Area
            cur.execute("SELECT id FROM areas WHERE nombre = ?", (area_name,))
            row = cur.fetchone()
            if row: area_id = row["id"]
            else:
                cur.execute("INSERT INTO areas (nombre) VALUES (?)", (area_name,))
                area_id = cur.lastrowid
                
            # 2. Get/Create SDA
            cur.execute("SELECT id FROM sda WHERE nombre = ? AND area_id = ?", (sda_name, area_id))
            row = cur.fetchone()
            if row: sda_id = row["id"]
            else:
                cur.execute("INSERT INTO sda (nombre, area_id, trimestre) VALUES (?, ?, ?)", (sda_name, area_id, trimestre))
                sda_id = cur.lastrowid
                
            # 3. Get/Create Criterion
            cur.execute("SELECT id FROM criterios WHERE codigo = ? AND area_id = ?", (crit_code, area_id))
            row = cur.fetchone()
            if row: crit_id = row["id"]
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
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()

@evaluacion_bp.route("/api/importar_actividades", methods=["POST"])
def importar_actividades():
    d = request.json
    csv_text = d.get("csv", "")
    if not csv_text:
        return jsonify({"ok": False, "error": "No hay datos"}), 400
        
    lines = csv_text.strip().split("\n")
    conn = get_db()
    cur = conn.cursor()
    
    imported = 0
    try:
        for line in lines:
            parts = line.split(";")
            if len(parts) < 2: continue
            
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
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()
