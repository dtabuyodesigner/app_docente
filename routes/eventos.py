from flask import Blueprint, jsonify, request, session
from utils.db import get_db

eventos_bp = Blueprint('eventos', __name__)

@eventos_bp.route("/api/programacion")
def obtener_programacion():
    start = request.args.get("start")
    end = request.args.get("end")

    conn = get_db()
    cur = conn.cursor()

    # Consulta unificada para evitar duplicados
    # Priorizamos mostrar la información de la actividad vinculada si existe
    sql = """
        SELECT 
            pd.id, pd.fecha, pd.descripcion as pd_desc, pd.tipo, pd.color, pd.evaluable, pd.criterio_id, pd.numero_sesion,
            pd.sda_id as pd_sda_id, pd.actividad_id,
            act.nombre as act_nombre, 
            sda.nombre as sda_nombre, sda.id as sda_id
        FROM programacion_diaria pd
        LEFT JOIN actividades_sda act ON pd.actividad_id = act.id
        LEFT JOIN sda ON (act.sda_id = sda.id OR pd.sda_id = sda.id)
        WHERE 1=1
    """
    params = []

    if start:
        sql += " AND pd.fecha >= ?"
        params.append(start)
    if end:
        sql += " AND pd.fecha <= ?"
        params.append(end)

    # Agrupar por el id de programacion_diaria para evitar filas duplicadas por los joins
    sql += " GROUP BY pd.id"

    cur.execute(sql, params)
    rows = cur.fetchall()
    
    events = []
    for r in rows:
        sda_name = r["sda_nombre"] or ""
        act_name = r["act_nombre"] or ""
        desc = r["pd_desc"] or ""
        
        # Construir título inteligente
        if r["actividad_id"]:
            title = f"[{sda_name}] {act_name}"
            if r["numero_sesion"]: title += f" - Ses. {r['numero_sesion']}"
            if desc and desc != act_name: title += f": {desc}"
            color = "#17a2b8" # Teal para sesiones
            tipo = "sesion_actividad"
        else:
            title = desc if desc else (f"[{sda_name}]" if sda_name else "(Sin título)")
            color = r["color"] or "#3788d8" # Blue para general
            tipo = r["tipo"] or "general"

        events.append({
            "id": r["id"],
            "title": title,
            "start": r["fecha"],
            "color": color,
            "extendedProps": {
                "tipo": tipo,
                "sda_id": r["sda_id"] or r["pd_sda_id"],
                "actividad_id": r["actividad_id"],
                "numero_sesion": r["numero_sesion"],
                "evaluable": r["evaluable"],
                "criterio_id": r["criterio_id"],
                "observaciones": desc,
                "sda_nombre": sda_name,
                "act_nombre": act_name
            }
        })
        
    return jsonify(events)

@eventos_bp.route("/api/programacion", methods=["POST"])
def guardar_evento():
    d = request.json
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        cur.execute("""
            INSERT INTO programacion_diaria (fecha, descripcion, tipo, color, sda_id, evaluable, criterio_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (d["fecha"], d.get("actividad") or d.get("descripcion"), d.get("tipo", "general"), d.get("color", "#3788d8"), d.get("sda_id") or None, d.get("evaluable", 0), d.get("criterio_id") or None))
        new_id = cur.lastrowid
        
        # Auto-generate evaluations if evaluable
        if d.get("evaluable") == 1 and d.get("criterio_id"):
            grupo_id = request.args.get("grupo_id") or session.get('active_group_id')
            criterio_id = d["criterio_id"]
            sda_id = d.get("sda_id")
            
            # Determine area_id and trimestre
            if sda_id:
                cur.execute("SELECT area_id, trimestre FROM sda WHERE id = ?", (sda_id,))
                sda_row = cur.fetchone()
                area_id = sda_row["area_id"]
                trimestre = sda_row["trimestre"]
            else:
                cur.execute("SELECT area_id FROM criterios WHERE id = ?", (criterio_id,))
                area_id = cur.fetchone()["area_id"]
                # Derive trimester from date if no SDA
                mes = int(d["fecha"].split('-')[1])
                trimestre = 1 if mes >= 9 or mes <= 12 else (2 if mes >= 1 and mes <= 3 else 3)
                if mes >= 1 and mes <= 3: trimestre = 2
                elif mes >= 4 and mes <= 6: trimestre = 3
                else: trimestre = 1

            cur.execute("""
                INSERT OR IGNORE INTO evaluaciones (alumno_id, area_id, trimestre, sda_id, criterio_id, nivel, nota)
                SELECT id, ?, ?, ?, ?, NULL, NULL
                FROM alumnos
                WHERE grupo_id = ?
            """, (area_id, trimestre, sda_id or None, criterio_id, grupo_id))

        conn.commit()
        return jsonify({"ok": True, "id": new_id})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@eventos_bp.route("/api/programacion/<int:event_id>", methods=["PUT"])
def actualizar_evento(event_id):
    d = request.json
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        cur.execute("""
            UPDATE programacion_diaria
            SET fecha = ?, descripcion = ?, tipo = ?, color = ?, sda_id = ?, evaluable = ?, criterio_id = ?
            WHERE id = ?
        """, (d["fecha"], d.get("actividad") or d.get("descripcion"), d.get("tipo", "general"), d.get("color", "#3788d8"), d.get("sda_id") or None, d.get("evaluable", 0), d.get("criterio_id") or None, event_id))
        
        # Auto-generate evaluations if changed to evaluable
        if d.get("evaluable") == 1 and d.get("criterio_id"):
            grupo_id = request.args.get("grupo_id") or session.get('active_group_id')
            criterio_id = d["criterio_id"]
            sda_id = d.get("sda_id")
            
            # Determine area_id and trimestre
            if sda_id:
                cur.execute("SELECT area_id, trimestre FROM sda WHERE id = ?", (sda_id,))
                sda_row = cur.fetchone()
                area_id = sda_row["area_id"]
                trimestre = sda_row["trimestre"]
            else:
                cur.execute("SELECT area_id FROM criterios WHERE id = ?", (criterio_id,))
                area_id = cur.fetchone()["area_id"]
                mes = int(d["fecha"].split('-')[1])
                if mes >= 9 or mes <= 12: trimestre = 1
                if mes >= 1 and mes <= 3: trimestre = 2
                elif mes >= 4 and mes <= 6: trimestre = 3
                else: trimestre = 1

            cur.execute("""
                INSERT OR IGNORE INTO evaluaciones (alumno_id, area_id, trimestre, sda_id, criterio_id, nivel, nota)
                SELECT id, ?, ?, ?, ?, NULL, NULL
                FROM alumnos
                WHERE grupo_id = ?
            """, (area_id, trimestre, sda_id or None, criterio_id, grupo_id))

        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@eventos_bp.route("/api/programacion/<int:event_id>/completado", methods=["PATCH"])
def patch_evento_completado(event_id):
    d = request.json
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        cur.execute("UPDATE programacion_diaria SET completado = ? WHERE id = ?", (d.get("completado", 1), event_id))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@eventos_bp.route("/api/programacion/<int:event_id>", methods=["DELETE"])
def borrar_evento(event_id):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        cur.execute("DELETE FROM programacion_diaria WHERE id = ?", (event_id,))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
@eventos_bp.route("/api/actividades/<int:act_id>/sesiones", methods=["GET", "POST"])
def api_sesiones_actividad(act_id):
    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        d = request.get_json(silent=True) or {}
        sesiones = d.get("sesiones", [])

        # Obtener sda_id de la actividad
        cur.execute("SELECT sda_id FROM actividades_sda WHERE id = ?", (act_id,))
        act_row = cur.fetchone()
        if not act_row:
            return jsonify({"ok": False, "error": "Actividad no encontrada"}), 404
        sda_id = act_row["sda_id"]

        try:
            cur.execute("BEGIN")
            for s in sesiones:
                s_id = s.get("id")
                num = int(s.get("numero_sesion", 1))
                desc = s.get("descripcion", "").strip()
                guia = s.get("guia_sesion", "").strip()
                fecha = s.get("fecha") or ""
                material = s.get("material", "").strip()
                evaluable = int(s.get("evaluable", 0))
                criterio_id = s.get("criterio_id")

                if s_id:
                    # Preserve existing evaluable/criterio if not provided
                    cur.execute("SELECT evaluable, criterio_id, material FROM programacion_diaria WHERE id = ?", (s_id,))
                    old = cur.fetchone()

                    if "evaluable" not in s and old: evaluable = old["evaluable"]
                    if "criterio_id" not in s and old: criterio_id = old["criterio_id"]
                    if "material" not in s and old: material = old["material"]

                    cur.execute("""
                        UPDATE programacion_diaria
                        SET descripcion = ?, guia_sesion = ?, fecha = ?, material = ?, evaluable = ?, criterio_id = ?
                        WHERE id = ?
                    """, (desc, guia, fecha, material, evaluable, criterio_id, s_id))
                else:
                    # Comprobar si ya existe para esta actividad y número de sesión
                    cur.execute("""
                        SELECT id, evaluable, criterio_id, material FROM programacion_diaria
                        WHERE actividad_id = ? AND numero_sesion = ?
                    """, (act_id, num))
                    existing = cur.fetchone()
                    if existing:
                        if "evaluable" not in s: evaluable = existing["evaluable"]
                        if "criterio_id" not in s: criterio_id = existing["criterio_id"]
                        if "material" not in s: material = existing["material"]

                        cur.execute("""
                            UPDATE programacion_diaria
                            SET descripcion = ?, guia_sesion = ?, fecha = ?, material = ?, evaluable = ?, criterio_id = ?
                            WHERE id = ?
                        """, (desc, guia, fecha, material, evaluable, criterio_id, existing["id"]))
                    else:
                        cur.execute("""
                            INSERT INTO programacion_diaria
                                (sda_id, actividad_id, numero_sesion, descripcion, guia_sesion, fecha, material, evaluable, criterio_id)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (sda_id, act_id, num, desc, guia, fecha, material, evaluable, criterio_id))
            conn.commit()
            return jsonify({"ok": True})
        except Exception as e:
            conn.rollback()
            return jsonify({"ok": False, "error": str(e)}), 500

    # GET
    cur.execute("""
        SELECT sa.id, sa.fecha, sa.descripcion, sa.guia_sesion, sa.numero_sesion, sa.actividad_id, sa.evaluable, sa.criterio_id, sa.material
        FROM programacion_diaria sa
        WHERE sa.actividad_id = ?
        ORDER BY sa.numero_sesion
    """, (act_id,))
    rows = cur.fetchall()
    return jsonify([dict(r) for r in rows])
