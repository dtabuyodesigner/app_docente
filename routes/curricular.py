from flask import Blueprint, jsonify, request, session
from utils.db import get_db

curricular_bp = Blueprint('curricular', __name__)

@curricular_bp.route("/etapas")
def listar_etapas():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre FROM etapas ORDER BY id")
    return jsonify([dict(r) for r in cur.fetchall()])

@curricular_bp.route("/areas")
def listar_areas():
    etapa_id = request.args.get("etapa_id")
    conn = get_db()
    cur = conn.cursor()
    if etapa_id:
        cur.execute("SELECT id, nombre, modo_evaluacion, tipo_escala, etapa_id FROM areas WHERE etapa_id = ? AND activa = 1 ORDER BY nombre", (etapa_id,))
    else:
        cur.execute("SELECT id, nombre, modo_evaluacion, tipo_escala, etapa_id FROM areas WHERE activa = 1 ORDER BY nombre")
    return jsonify([dict(r) for r in cur.fetchall()])

@curricular_bp.route("/rubricas/<int:criterio_id>")
def obtener_rubrica(criterio_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT nivel, descriptor FROM rubricas WHERE criterio_id = ? ORDER BY nivel", (criterio_id,))
    rows = cur.fetchall()
    return jsonify({str(r["nivel"]): r["descriptor"] for r in rows})

@curricular_bp.route("/rubricas", methods=["POST"])
def guardar_rubrica():
    d = request.json
    criterio_id = d.get("criterio_id")
    descriptores = d.get("descriptores")
    if not criterio_id or not descriptores: return jsonify({"ok": False, "error": "Faltan datos"}), 400
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
        return jsonify({"ok": False, "error": str(e)}), 500

@curricular_bp.route("/rubricas/<int:criterio_id>", methods=["DELETE"])
def borrar_rubrica_criterio(criterio_id):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM rubricas WHERE criterio_id = ?", (criterio_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
    return jsonify({"ok": True})

@curricular_bp.route("/sa", methods=["POST"])
def crear_sa():
    d = request.json
    nombre = d.get("nombre", "").strip()
    area_id = d.get("area_id")
    trimestre = d.get("trimestre")
    criterios = d.get("criterios", [])
    competencias = d.get("competencias", [])
    actividades = d.get("actividades", [])
    if not nombre or not area_id or not trimestre: return jsonify({"ok": False, "error": "Faltan datos"}), 400
    conn = get_db()
    cur = conn.cursor()
    grupo_id = session.get('active_group_id')
    try:
        cur.execute("BEGIN")
        cur.execute("INSERT INTO sda (nombre, area_id, trimestre, grupo_id) VALUES (?, ?, ?, ?)", (nombre, area_id, trimestre, grupo_id))
        sda_id = cur.lastrowid
        for c in criterios:
            codigo, desc = c.get("codigo", "").strip(), c.get("descripcion", "").strip()
            if not codigo: continue
            cur.execute("SELECT id FROM criterios WHERE codigo = ? AND area_id = ?", (codigo, area_id))
            row = cur.fetchone()
            crit_id = row["id"] if row else None
            if not crit_id:
                cur.execute("INSERT INTO criterios (codigo, descripcion, area_id) VALUES (?, ?, ?)", (codigo, desc, area_id))
                crit_id = cur.lastrowid
            cur.execute("INSERT OR IGNORE INTO sda_criterios (sda_id, criterio_id) VALUES (?, ?)", (sda_id, crit_id))
        for c in competencias:
            codigo, desc = c.get("codigo", "").strip(), c.get("descripcion", "").strip()
            if not codigo: continue
            cur.execute("SELECT id FROM competencias_especificas WHERE codigo = ? AND area_id = ?", (codigo, area_id))
            row = cur.fetchone()
            comp_id = row["id"] if row else None
            if not comp_id:
                cur.execute("INSERT INTO competencias_especificas (codigo, descripcion, area_id) VALUES (?, ?, ?)", (codigo, desc, area_id))
                comp_id = cur.lastrowid
            cur.execute("INSERT OR IGNORE INTO sda_competencias (sda_id, competencia_id) VALUES (?, ?)", (sda_id, comp_id))
        for a in actividades:
            a_nom, a_desc, a_ses = a.get("nombre", "").strip(), a.get("descripcion", "").strip(), int(a.get("sesiones", 1))
            if not a_nom: continue
            cur.execute("INSERT INTO actividades_sda (sda_id, nombre, sesiones, descripcion) VALUES (?, ?, ?, ?)", (sda_id, a_nom, a_ses, a_desc))
        conn.commit()
        return jsonify({"ok": True, "sda_id": sda_id})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@curricular_bp.route("/sa/<int:sda_id>", methods=["PUT"])
def actualizar_sa(sda_id):
    d = request.json
    nombre, area_id, trimestre = d.get("nombre", "").strip(), d.get("area_id"), d.get("trimestre")
    criterios, competencias, actividades = d.get("criterios", []), d.get("competencias", []), d.get("actividades", [])
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        cur.execute("UPDATE sda SET nombre = ?, area_id = ?, trimestre = ? WHERE id = ?", (nombre, area_id, trimestre, sda_id))
        cur.execute("DELETE FROM sda_criterios WHERE sda_id = ?", (sda_id,))
        for c in criterios:
            codigo, desc = c.get("codigo", "").strip(), c.get("descripcion", "").strip()
            if not codigo: continue
            cur.execute("SELECT id FROM criterios WHERE codigo = ? AND area_id = ?", (codigo, area_id))
            row = cur.fetchone()
            crit_id = row["id"] if row else None
            if not crit_id:
                cur.execute("INSERT INTO criterios (codigo, descripcion, area_id) VALUES (?, ?, ?)", (codigo, desc, area_id))
                crit_id = cur.lastrowid
            cur.execute("INSERT OR IGNORE INTO sda_criterios (sda_id, criterio_id) VALUES (?, ?)", (sda_id, crit_id))
        cur.execute("DELETE FROM sda_competencias WHERE sda_id = ?", (sda_id,))
        for c in competencias:
            codigo, desc = c.get("codigo", "").strip(), c.get("descripcion", "").strip()
            if not codigo: continue
            cur.execute("SELECT id FROM competencias_especificas WHERE codigo = ? AND area_id = ?", (codigo, area_id))
            row = cur.fetchone()
            comp_id = row["id"] if row else None
            if not comp_id:
                cur.execute("INSERT INTO competencias_especificas (codigo, descripcion, area_id) VALUES (?, ?, ?)", (codigo, desc, area_id))
                comp_id = cur.lastrowid
            cur.execute("INSERT OR IGNORE INTO sda_competencias (sda_id, competencia_id) VALUES (?, ?)", (sda_id, comp_id))
        act_ids = [int(a["id"]) for a in actividades if a.get("id")]
        if act_ids:
            placeholders = ','.join('?' for _ in act_ids)
            cur.execute(f"DELETE FROM actividades_sda WHERE sda_id = ? AND id NOT IN ({placeholders})", [sda_id] + act_ids)
        else:
            cur.execute("DELETE FROM actividades_sda WHERE sda_id = ?", (sda_id,))
        for a in actividades:
            a_id, a_nom, a_desc, a_ses = a.get("id"), a.get("nombre", "").strip(), a.get("descripcion", "").strip(), int(a.get("sesiones", 1))
            if not a_nom: continue
            if a_id: cur.execute("UPDATE actividades_sda SET nombre = ?, sesiones = ?, descripcion = ? WHERE id = ?", (a_nom, a_ses, a_desc, a_id))
            else: cur.execute("INSERT INTO actividades_sda (sda_id, nombre, sesiones, descripcion) VALUES (?, ?, ?, ?)", (sda_id, a_nom, a_ses, a_desc))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@curricular_bp.route("/sa/<int:sda_id>", methods=["DELETE"])
def eliminar_sa(sda_id):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        cur.execute("DELETE FROM evaluaciones WHERE sda_id = ?", (sda_id,))
        cur.execute("DELETE FROM sda_criterios WHERE sda_id = ?", (sda_id,))
        cur.execute("DELETE FROM sda_competencias WHERE sda_id = ?", (sda_id,))
        cur.execute("DELETE FROM actividades_sda WHERE sda_id = ?", (sda_id,))
        cur.execute("DELETE FROM sda WHERE id = ?", (sda_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
    return jsonify({"ok": True})

@curricular_bp.route("/full")
def curricular_full():
    conn = get_db()
    cur = conn.cursor()
    grupo_id = session.get('active_group_id')
    etapa_id = None
    if grupo_id:
        cur.execute("SELECT etapa_id FROM grupos WHERE id = ?", (grupo_id,))
        g = cur.fetchone()
        if g: etapa_id = g["etapa_id"]
    if etapa_id: cur.execute("SELECT id, nombre, modo_evaluacion, tipo_escala FROM areas WHERE activa = 1 AND etapa_id = ? ORDER BY nombre", (etapa_id,))
    else: cur.execute("SELECT id, nombre, modo_evaluacion, tipo_escala FROM areas WHERE activa = 1 ORDER BY nombre")
    areas = [dict(a) for a in cur.fetchall()]
    for area in areas:
        if grupo_id: cur.execute("SELECT id, nombre, trimestre FROM sda WHERE area_id = ? AND (grupo_id = ? OR grupo_id IS NULL) ORDER BY trimestre, id", (area["id"], grupo_id))
        else: cur.execute("SELECT id, nombre, trimestre FROM sda WHERE area_id = ? ORDER BY trimestre, id", (area["id"],))
        sdas = [dict(s) for s in cur.fetchall()]
        for sda in sdas:
            cur.execute("SELECT id, nombre, sesiones, descripcion FROM actividades_sda WHERE sda_id = ? ORDER BY id", (sda["id"],))
            sda["actividades"] = [dict(act) for act in cur.fetchall()]
            cur.execute("SELECT c.id, c.codigo, c.descripcion FROM criterios c JOIN sda_criterios sc ON sc.criterio_id = c.id WHERE sc.sda_id = ?", (sda["id"],))
            sda["criterios"] = [dict(c) for c in cur.fetchall()]
        area["sdas"] = sdas
    return jsonify(areas)

@curricular_bp.route("/importar_todo", methods=["POST"])
def importar_todo():
    import csv as csv_lib
    import io
    d = request.json
    csv_text = d.get("csv", "")
    if not csv_text: return jsonify({"ok": False, "error": "No hay CSV"}), 400
    conn = get_db()
    cur = conn.cursor()
    grupo_id = session.get('active_group_id')
    count = 0
    try:
        cur.execute("BEGIN")
        f = io.StringIO(csv_text)
        reader = csv_lib.DictReader(f, delimiter=';')
        for row in reader:
            area_nom, sda_nom, trim = row.get("Area"), row.get("SDA"), row.get("Trimestre")
            crit_cod, crit_des, act_nom = row.get("Codigo Criterio"), row.get("Desc. Criterio"), row.get("Actividad")
            if not (area_nom and sda_nom): continue
            cur.execute("SELECT id FROM areas WHERE nombre = ?", (area_nom,))
            r = cur.fetchone()
            if r: area_id = r["id"]
            else:
                cur.execute("INSERT INTO areas (nombre, activa) VALUES (?, 1)", (area_nom,))
                area_id = cur.lastrowid
            cur.execute("SELECT id FROM sda WHERE nombre = ? AND area_id = ? AND (grupo_id = ? OR grupo_id IS NULL)", (sda_nom, area_id, grupo_id))
            r = cur.fetchone()
            if r: sda_id = r["id"]
            else:
                cur.execute("INSERT INTO sda (nombre, area_id, trimestre, grupo_id) VALUES (?, ?, ?, ?)", (sda_nom, area_id, trim, grupo_id))
                sda_id = cur.lastrowid
            if crit_cod:
                cur.execute("SELECT id FROM criterios WHERE codigo = ? AND area_id = ?", (crit_cod, area_id))
                r = cur.fetchone()
                if r: crit_id = r["id"]
                else:
                    cur.execute("INSERT INTO criterios (codigo, descripcion, area_id) VALUES (?, ?, ?)", (crit_cod, crit_des, area_id))
                    crit_id = cur.lastrowid
                cur.execute("INSERT OR IGNORE INTO sda_criterios (sda_id, criterio_id) VALUES (?, ?)", (sda_id, crit_id))
            if act_nom: cur.execute("INSERT INTO actividades_sda (sda_id, nombre) VALUES (?, ?)", (sda_id, act_nom))
            count += 1
        conn.commit()
        return jsonify({"ok": True, "count": count})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
