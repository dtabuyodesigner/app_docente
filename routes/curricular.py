from flask import Blueprint, jsonify, request, session
from utils.db import get_db
import csv
import io
from datetime import datetime
from utils.cache import simple_cache

curricular_bp = Blueprint('curricular', __name__)

@curricular_bp.route("/etapas")
@simple_cache(timeout=300)
def listar_etapas():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre FROM etapas ORDER BY id")
    return jsonify([dict(r) for r in cur.fetchall()])

@curricular_bp.route("/areas")
def listar_areas():
    etapa_id = request.args.get("etapa_id")
    if not etapa_id:
        grupo_id = session.get('active_group_id')
        if grupo_id:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT etapa_id FROM grupos WHERE id = ?", (grupo_id,))
            g = cur.fetchone()
            if g: etapa_id = g["etapa_id"]

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
        cur.execute("DELETE FROM programacion_diaria WHERE sda_id = ?", (sda_id,))
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
            cur.execute("SELECT ce.id, ce.codigo, ce.descripcion FROM competencias_especificas ce JOIN sda_competencias sc ON sc.competencia_id = ce.id WHERE sc.sda_id = ?", (sda["id"],))
            sda["competencias"] = [dict(comp) for comp in cur.fetchall()]
        area["sdas"] = sdas
    return jsonify(areas)

@curricular_bp.route("/importar_todo", methods=["POST"])
def importar_todo():
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
        reader = csv.DictReader(f, delimiter=';')
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

@curricular_bp.route("/sda/import_csv", methods=["POST"])
def importar_sda_csv():
    if not session.get('logged_in'):
        return jsonify({"ok": False, "error": "No autorizado"}), 401
    
    file = request.files.get('file')
    if not file:
        return jsonify({"ok": False, "error": "No se ha subido ningún archivo"}), 400
    
    grupo_id = session.get('active_group_id')
    if not grupo_id:
        return jsonify({"ok": False, "error": "No hay un grupo activo seleccionado"}), 400

    stats = {"sda": 0, "actividades": 0, "sesiones": 0, "criterios": 0, "errores": 0}
    
    try:
        content = file.stream.read().decode("utf-8-sig")
        stream = io.StringIO(content)
        # Intentar detectar delimitador
        sample = stream.read(2048)
        stream.seek(0)
        dialect = 'excel'
        if sample:
            if ';' in sample and ',' not in sample:
                dialect = 'excel-tab'
                reader = csv.DictReader(stream, delimiter=';')
            elif ';' in sample:
                # Manual check
                first_line = sample.split('\n')[0]
                if ';' in first_line:
                    reader = csv.DictReader(stream, delimiter=';')
                else:
                    reader = csv.DictReader(stream)
            else:
                reader = csv.DictReader(stream)
        else:
            reader = csv.DictReader(stream)

        # Pre-procesar para contar sesiones por actividad si no viene el campo Actividad_Sesiones
        rows = list(reader)
        act_counts = {} # (sda_tit, act_tit) -> count
        for row in rows:
            sda_tit = row.get("SDA_Titulo", "").strip()
            act_tit = row.get("Actividad_Titulo", "").strip()
            if sda_tit and act_tit:
                key = (sda_tit, act_tit)
                act_counts[key] = act_counts.get(key, 0) + 1

        conn = get_db()
        cur = conn.cursor()
        
        # Etapas mapping
        cur.execute("SELECT id, nombre FROM etapas")
        etapas_map = {r["nombre"].lower(): r["id"] for r in cur.fetchall()}
        
        cur.execute("BEGIN TRANSACTION")
        
        # Track session numbers manually within the loop for each activity in this import
        act_session_tracker = {} # (sda_id, act_id) -> current_ses_num

        for row in rows:
            try:
                # 1. Etapa y Área
                etapa_nom = row.get("Etapa", "").strip()
                area_nom = row.get("Area", "").strip()
                if not etapa_nom or not area_nom: continue
                
                etapa_id = etapas_map.get(etapa_nom.lower())
                if not etapa_id:
                    cur.execute("INSERT INTO etapas (nombre) VALUES (?)", (etapa_nom,))
                    etapa_id = cur.lastrowid
                    etapas_map[etapa_nom.lower()] = etapa_id
                
                cur.execute("SELECT id FROM areas WHERE nombre = ? AND etapa_id = ?", (area_nom, etapa_id))
                area_row = cur.fetchone()
                if area_row:
                    area_id = area_row["id"]
                else:
                    cur.execute("INSERT INTO areas (nombre, etapa_id, activa) VALUES (?, ?, 1)", (area_nom, etapa_id))
                    area_id = cur.lastrowid
                
                # 2. SDA
                sda_cod = row.get("SDA_ID", "").strip()
                sda_tit = row.get("SDA_Titulo", "").strip()
                trim_str = row.get("Trimestre", "1").strip()
                trim = int(trim_str.replace("T", "")) if trim_str and any(c.isdigit() for c in trim_str) else 1
                duracion = row.get("Duracion_Semanas")
                duracion = int(duracion) if duracion and duracion.isdigit() else None
                
                if not sda_tit: continue
                
                if sda_cod:
                    cur.execute("SELECT id FROM sda WHERE codigo_sda = ? AND grupo_id = ?", (sda_cod, grupo_id))
                else:
                    cur.execute("SELECT id FROM sda WHERE nombre = ? AND grupo_id = ? AND area_id = ?", (sda_tit, grupo_id, area_id))
                
                sda_row = cur.fetchone()
                if sda_row:
                    sda_id = sda_row["id"]
                    cur.execute("UPDATE sda SET nombre = ?, trimestre = ?, duracion_semanas = ? WHERE id = ?", 
                               (sda_tit, trim, duracion, sda_id))
                else:
                    cur.execute("INSERT INTO sda (area_id, nombre, trimestre, grupo_id, codigo_sda, duracion_semanas) VALUES (?, ?, ?, ?, ?, ?)",
                               (area_id, sda_tit, trim, grupo_id, sda_cod, duracion))
                    sda_id = cur.lastrowid
                    stats["sda"] += 1
                
                # 3. Criterios y Competencias
                crit_cod = row.get("Criterio_Codigo", "").strip()
                crit_desc = row.get("Criterio_Descriptor", "").strip()
                if crit_cod:
                    cur.execute("SELECT id FROM criterios WHERE codigo = ? AND area_id = ?", (crit_cod, area_id))
                    c_row = cur.fetchone()
                    if c_row:
                        crit_id = c_row["id"]
                        if crit_desc: cur.execute("UPDATE criterios SET descripcion = ? WHERE id = ?", (crit_desc, crit_id))
                    else:
                        cur.execute("INSERT INTO criterios (codigo, descripcion, area_id) VALUES (?, ?, ?)", 
                                   (crit_cod, crit_desc, area_id))
                        crit_id = cur.lastrowid
                        stats["criterios"] += 1
                    
                    cur.execute("INSERT OR IGNORE INTO sda_criterios (sda_id, criterio_id) VALUES (?, ?)", (sda_id, crit_id))
                    
                    # Activación automática
                    periodo = f"T{trim}"
                    cur.execute("""
                        INSERT OR IGNORE INTO criterios_periodo (criterio_id, grupo_id, periodo, activo)
                        VALUES (?, ?, ?, 1)
                    """, (crit_id, grupo_id, periodo))
                
                comp_cod = row.get("Competencia_Codigo", "").strip()
                comp_desc = row.get("Competencia_Descriptor", "").strip()
                if comp_cod:
                    cur.execute("SELECT id FROM competencias_especificas WHERE codigo = ? AND area_id = ?", (comp_cod, area_id))
                    comp_row = cur.fetchone()
                    if comp_row:
                        comp_id = comp_row["id"]
                    else:
                        cur.execute("INSERT INTO competencias_especificas (codigo, descripcion, area_id) VALUES (?, ?, ?)",
                                   (comp_cod, comp_desc, area_id))
                        comp_id = cur.lastrowid
                    
                    cur.execute("INSERT OR IGNORE INTO sda_competencias (sda_id, competencia_id) VALUES (?, ?)", (sda_id, comp_id))

                # 4. Actividades
                act_cod = row.get("Actividad_ID", "").strip()
                act_tit = row.get("Actividad_Titulo", "").strip()
                act_desc = row.get("Actividad_Descripcion", "").strip()
                act_sesiones_csv = row.get("Actividad_Sesiones")
                
                if act_tit:
                    # Determinar número total de sesiones para esta actividad
                    if act_sesiones_csv and act_sesiones_csv.isdigit():
                        total_sesiones = int(act_sesiones_csv)
                    else:
                        total_sesiones = act_counts.get((sda_tit, act_tit), 1)

                    if act_cod:
                        cur.execute("SELECT id FROM actividades_sda WHERE codigo_actividad = ? AND sda_id = ?", (act_cod, sda_id))
                    else:
                        cur.execute("SELECT id FROM actividades_sda WHERE nombre = ? AND sda_id = ?", (act_tit, sda_id))
                    
                    act_row = cur.fetchone()
                    if act_row:
                        act_id = act_row["id"]
                        cur.execute("UPDATE actividades_sda SET sesiones = ?, descripcion = ? WHERE id = ?", (total_sesiones, act_desc, act_id))
                    else:
                        cur.execute("INSERT INTO actividades_sda (sda_id, nombre, codigo_actividad, sesiones, descripcion) VALUES (?, ?, ?, ?, ?)",
                                   (sda_id, act_tit, act_cod, total_sesiones, act_desc))
                        act_id = cur.lastrowid
                        stats["actividades"] += 1
                    
                    # 5. Sesiones (Programación Diaria)
                    tracker_key = (sda_id, act_id)
                    act_session_tracker[tracker_key] = act_session_tracker.get(tracker_key, 0) + 1
                    
                    ses_num = row.get("Sesion_Numero")
                    ses_num = int(ses_num) if ses_num and ses_num.isdigit() else act_session_tracker[tracker_key]
                    
                    ses_tit = row.get("Sesion_Titulo", "").strip()
                    ses_desc = row.get("Descripcion_Sesion", "").strip()
                    material = row.get("Material", "").strip()
                    evaluable = 1 if row.get("Evaluable", "").lower() in ("si", "sí", "true", "1") else 0
                    fecha = row.get("Fecha", "").strip()
                    
                    # Solo insertamos en programacion_diaria si hay fecha (es obligatoria en el esquema)
                    if fecha:
                        db_fecha = None
                        for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
                            try:
                                db_fecha = datetime.strptime(fecha, fmt).strftime("%Y-%m-%d")
                                break
                            except ValueError: continue
                        
                        if db_fecha:
                            cur.execute("SELECT id FROM programacion_diaria WHERE actividad_id = ? AND numero_sesion = ?", (act_id, ses_num))
                            pd_row = cur.fetchone()
                            
                            desc_final = ses_desc or ses_tit or act_tit
                            
                            if pd_row:
                                cur.execute("""
                                    UPDATE programacion_diaria 
                                    SET descripcion = ?, material = ?, evaluable = ?, sda_id = ?, fecha = ?
                                    WHERE id = ?
                                """, (desc_final, material, evaluable, sda_id, db_fecha, pd_row["id"]))
                            else:
                                cur.execute("""
                                    INSERT INTO programacion_diaria (fecha, sda_id, actividad_id, numero_sesion, descripcion, material, evaluable)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                """, (db_fecha, sda_id, act_id, ses_num, desc_final, material, evaluable))
                                stats["sesiones"] += 1

            except Exception as e:
                print(f"Error procesando fila {reader.line_num}: {e}")
                stats["errores"] += 1
        
        conn.commit()
        return jsonify({"ok": True, "stats": stats})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

# Removed redundant session routes (moved to eventos.py)
