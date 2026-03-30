import csv
import io
import datetime
from flask import Blueprint, request, jsonify, session, Response
from utils.db import get_db
from utils.security import get_security_logger, audit_log
from utils.cache import simple_cache
from schemas.criterios import AreaSchema, CriterioSchema
from marshmallow import ValidationError

criterios_bp = Blueprint('criterios_api', __name__)
security_logger = get_security_logger()

REQUIRED_HEADER = ["Codigo", "Descripcion completa", "Etapa", "Area", "Materia", "Activo (Si/No)"]

# --- ETAPAS ---

@criterios_bp.route("/api/etapas", methods=["GET"])
@simple_cache(timeout=300)
def listar_etapas():
    """
    Lista todas las etapas educativas disponibles.
    ---
    tags:
      - Etapas
    responses:
      200:
        description: Retorna un listado de etapas con su ID y estado activo.
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                description: ID de la etapa
              nombre:
                type: string
                description: Nombre de la etapa (ej. Infantil, Primaria)
              activa:
                type: integer
                description: Estado de la etapa (1=Activa, 0=Inactiva)
      401:
        description: Usuario no autorizado
    """
    if not session.get('logged_in'):
        return jsonify({"ok": False, "error": "No autorizado"}), 401
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre, activa FROM etapas")
    return jsonify([dict(row) for row in cur.fetchall()])

# --- AREAS ---

@criterios_bp.route("/api/areas", methods=["GET"])
@simple_cache(timeout=300)
def listar_areas():
    """
    Lista todas las áreas. Permite filtrar por etapa_id.
    ---
    tags:
      - Áreas
    parameters:
      - in: query
        name: etapa_id
        type: integer
        required: false
        description: ID de la etapa para filtrar las áreas
    responses:
      200:
        description: Retorna un listado de las áreas registradas.
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              nombre:
                type: string
              etapa_id:
                type: integer
              etapa_nombre:
                type: string
              modo_evaluacion:
                type: string
              tipo_escala:
                type: string
              activa:
                type: integer
      401:
        description: Usuario no autorizado
    """
    if not session.get('logged_in'):
        return jsonify({"ok": False, "error": "No autorizado"}), 401
    
    etapa_id = request.args.get('etapa_id')
    conn = get_db()
    cur = conn.cursor()
    
    query = """
        SELECT a.*, e.nombre as etapa_nombre 
        FROM areas a
        JOIN etapas e ON a.etapa_id = e.id
        WHERE 1=1
    """
    params = []
    if etapa_id:
        query += " AND a.etapa_id = ?"
        params.append(etapa_id)
    
    cur.execute(query, params)
    return jsonify([dict(row) for row in cur.fetchall()])

@criterios_bp.route("/api/areas", methods=["POST"])
def crear_area():
    """
    Crea una nueva área.
    ---
    tags:
      - Áreas
    parameters:
      - in: body
        name: body
        schema:
          id: AreaPost
          required:
            - nombre
            - etapa_id
          properties:
            nombre:
              type: string
              description: Nombre del área
            etapa_id:
              type: integer
              description: ID de la etapa a la que pertenece
            modo_evaluacion:
              type: string
              description: Modo de evaluación (ej. 'POR_SA')
            tipo_escala:
              type: string
              description: Tipo de escala
            activa:
              type: integer
              description: Si el área está activa (1 o 0)
    responses:
      200:
        description: Área creada exitosamente
      400:
        description: Errores de validación
      401:
        description: Usuario no autorizado
      403:
        description: Permisos insuficientes (requiere ser admin)
    """
    if not session.get('logged_in'):
        return jsonify({"ok": False, "error": "No autorizado"}), 401
    if session.get('role') != 'admin':
        return jsonify({"ok": False, "error": "Solo administradores"}), 403
        
    try:
        req_data = request.get_json(silent=True) or {}
        d = AreaSchema().load(req_data)
    except ValidationError as err:
        return jsonify({"ok": False, "error": "Errores de validación", "details": err.messages}), 400
        
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO areas (nombre, etapa_id, modo_evaluacion, tipo_escala, activa, es_personalizada)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (
            d["nombre"], d["etapa_id"], 
            d.get("modo_evaluacion", "POR_SA"), 
            d.get("tipo_escala", "NUMERICA_1_4"),
            d.get("activa", 1)
        ))
        conn.commit()
        return jsonify({"ok": True, "id": cur.lastrowid})
    except Exception as e:
        return jsonify({"ok": False, "error": "Ya existe un área con ese nombre en esta etapa" if "UNIQUE" in str(e) else str(e)}), 400

@criterios_bp.route("/api/areas/<int:area_id>", methods=["PUT"])
def actualizar_area(area_id):
    if not session.get('logged_in'):
        return jsonify({"ok": False, "error": "No autorizado"}), 401
    if session.get('role') != 'admin':
        return jsonify({"ok": False, "error": "Solo administradores"}), 403
        
    try:
        # Partial validation for PUT, or maybe full depending on app rules. 
        # Using partial because restricted update doesn't need all fields.
        req_data = request.get_json(silent=True) or {}
        d = AreaSchema(partial=True).load(req_data)
    except ValidationError as err:
        return jsonify({"ok": False, "error": "Errores de validación", "details": err.messages}), 400
        
    conn = get_db()
    cur = conn.cursor()
    
    # Check if has evaluations
    cur.execute("SELECT COUNT(*) as count FROM evaluacion_criterios ec JOIN criterios c ON ec.criterio_id = c.id WHERE c.area_id = ?", (area_id,))
    has_evals = cur.fetchone()["count"] > 0
    
    try:
        if has_evals:
            # Si tiene evals, permitimos nombre, modo_evaluacion y activa, pero quizá restringimos cosas como etapa.
            cur.execute("""
                UPDATE areas SET nombre = ?, activa = ?, modo_evaluacion = ? WHERE id = ?
            """, (d.get("nombre"), d.get("activa", 1), d.get("modo_evaluacion", "POR_SA"), area_id))
        else:
            if "nombre" not in d or "etapa_id" not in d:
                 return jsonify({"ok": False, "error": "Nombre y etapa obligatorios"}), 400
            cur.execute("""
                UPDATE areas 
                SET nombre = ?, etapa_id = ?, modo_evaluacion = ?, tipo_escala = ?, activa = ?
                WHERE id = ?
            """, (
                d["nombre"], d["etapa_id"], d.get("modo_evaluacion", "POR_SA"), 
                d.get("tipo_escala", "NUMERICA_1_4"), d.get("activa", 1), area_id
            ))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@criterios_bp.route("/api/areas/<int:area_id>", methods=["DELETE"])
def eliminar_area(area_id):
    if session.get('role') != 'admin': return jsonify({"ok": False}), 403
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as count FROM evaluacion_criterios ec JOIN criterios c ON ec.criterio_id = c.id WHERE c.area_id = ?", (area_id,))
    if cur.fetchone()["count"] > 0:
        return jsonify({"ok": False, "error": "No se puede eliminar: tiene evaluaciones de alumnos asociadas. Desactívela en su lugar."}), 400
    
    # Si no tiene evaluaciones, borramos en cascada los criterios y luego el área
    cur.execute("DELETE FROM criterios WHERE area_id = ?", (area_id,))
    cur.execute("DELETE FROM areas WHERE id = ?", (area_id,))
    conn.commit()
    return jsonify({"ok": True})

# --- CRITERIOS ---

@criterios_bp.route("/api/criterios", methods=["GET"])
@simple_cache(timeout=300)
def listar_criterios():
    if not session.get('logged_in'): return jsonify({"ok": False}), 401
    area_id = request.args.get('area_id')
    etapa = request.args.get('etapa')
    conn = get_db(); cur = conn.cursor()
    query = "SELECT c.*, a.nombre as area_nombre, e.nombre as etapa_nombre FROM criterios c JOIN areas a ON c.area_id = a.id JOIN etapas e ON a.etapa_id = e.id WHERE 1=1"
    params = []
    if area_id:
        query += " AND c.area_id = ?"
        params.append(area_id)
    if etapa:
        query += " AND e.nombre = ?"
        params.append(etapa)
    query += " ORDER BY c.codigo"
    cur.execute(query, params)
    return jsonify([dict(row) for row in cur.fetchall()])

@criterios_bp.route("/api/criterios", methods=["POST"])
def crear_criterio():
    if session.get('role') != 'admin': return jsonify({"ok": False}), 403
    try:
        req_data = request.get_json(silent=True) or {}
        d = CriterioSchema().load(req_data)
    except ValidationError as err:
        return jsonify({"ok": False, "error": "Errores de validación", "details": err.messages}), 400
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO criterios (codigo, descripcion, area_id, activo, oficial)
            VALUES (?, ?, ?, ?, ?)
        """, (d["codigo"].strip(), d["descripcion"].strip(), d["area_id"], d.get("activo", 1), d.get("oficial", 1)))
        new_id = cur.lastrowid
        audit_log(session.get('username'), "CREATE", "criterio", f"ID: {new_id}, Código: {d['codigo']}")
        conn.commit()
        return jsonify({"ok": True, "id": new_id})
    except Exception as e:
        return jsonify({"ok": False, "error": "Código duplicado en esta área" if "UNIQUE" in str(e) else str(e)}), 400

@criterios_bp.route("/api/criterios/<int:criterio_id>", methods=["PUT"])
def actualizar_criterio(criterio_id):
    if session.get('role') != 'admin': return jsonify({"ok": False}), 403
    try:
        req_data = request.get_json(silent=True) or {}
        d = CriterioSchema(partial=True).load(req_data)
    except ValidationError as err:
        return jsonify({"ok": False, "error": "Errores de validación", "details": err.messages}), 400
        
    conn = get_db(); cur = conn.cursor()
    
    # Check evals
    cur.execute("SELECT COUNT(*) as count FROM evaluacion_criterios WHERE criterio_id = ?", (criterio_id,))
    has_evals = cur.fetchone()["count"] > 0
    
    try:
        if has_evals:
            cur.execute("UPDATE criterios SET descripcion = ?, activo = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                       (d["descripcion"].strip(), d.get("activo", 1), criterio_id))
        else:
            cur.execute("UPDATE criterios SET codigo = ?, descripcion = ?, area_id = ?, activo = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                       (d["codigo"].strip(), d["descripcion"].strip(), d["area_id"], d.get("activo", 1), criterio_id))
        audit_log(session.get('username'), "UPDATE", "criterio", f"ID: {criterio_id}, Código: {d.get('codigo')}")
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@criterios_bp.route("/api/criterios/<int:criterio_id>", methods=["DELETE"])
def eliminar_criterio(criterio_id):
    if session.get('role') != 'admin': return jsonify({"ok": False}), 403
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as count FROM evaluacion_criterios WHERE criterio_id = ?", (criterio_id,))
    if cur.fetchone()["count"] > 0:
        return jsonify({"ok": False, "error": "Este criterio ya tiene evaluaciones. Solo puede desactivarse."}), 400
    cur.execute("DELETE FROM criterios WHERE id = ?", (criterio_id,))
    audit_log(session.get('username'), "DELETE", "criterio", f"ID: {criterio_id}")
    conn.commit()
    return jsonify({"ok": True})

# --- CSV & TEMPLATE ---

@criterios_bp.route("/api/criterios/template", methods=["GET"])
def get_csv_template():
    if not session.get('logged_in'): return "No autorizado", 401
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(REQUIRED_HEADER)
    # Filas de ejemplo — sustituye por tus criterios reales
    # Columna 'Area': área LOMLOE (solo informativa para Infantil, nombre clave para Primaria)
    # Columna 'Materia': asignatura específica (Inglés, Comunicación...). Se usa para buscar en la BD.
    #   Si Materia está vacía, se usa 'Area'.
    # Nombres exactos de áreas Infantil: 'Inglés' | 'Crecimiento en Armonía' | 'Descubrimiento y Exploración del Entorno' | 'Comunicación y Representación de la Realidad'
    writer.writerow(["ING.1.1", "Comprender y responder a instrucciones sencillas en inglés.", "Infantil", "Comunicación y Representación de la Realidad", "Inglés", "Sí"])
    writer.writerow(["ING.1.2", "Reproducir vocabulario básico mediante canciones y juegos.", "Infantil", "Comunicación y Representación de la Realidad", "Inglés", "Sí"])
    writer.writerow(["CRR.5.1", "Escuchar textos literarios sencillos en distintos formatos.", "Infantil", "Comunicación y Representación de la Realidad", "", "Sí"])
    writer.writerow(["LEN.1.1", "Ejemplo criterio Primaria.", "Primaria", "Lengua Castellana y Literatura", "", "Sí"])
    output.seek(0)
    return Response(output.getvalue(), mimetype="text/csv;charset=utf-8",
                    headers={"Content-disposition": "attachment; filename=plantilla_criterios.csv"})

@criterios_bp.route("/api/criterios/import_csv", methods=["POST"])
def importar_criterios_csv():
    if session.get('role') != 'admin': return jsonify({"ok": False}), 403
    file = request.files.get('file')
    if not file: return jsonify({"ok": False, "error": "No file"}), 400

    try:
        content = file.stream.read().decode("utf-8-sig")
        stream = io.StringIO(content)
        reader = csv.reader(stream, delimiter=';')
        raw_header = next(reader, None)
        if not raw_header:
            return jsonify({"ok": False, "error": "Archivo vacío"}), 400
        clean_header = [h.strip() for h in raw_header]

        # Detectar formato: nuevo (Area + Materia separadas) o legado (Area / Materia)
        NEW_HEADER = ["Codigo", "Descripcion completa", "Etapa", "Area", "Materia", "Activo (Si/No)"]
        OLD_HEADER = ["Codigo", "Descripcion completa", "Etapa", "Area / Materia", "Activo (visible en nuevas evaluaciones)"]

        if clean_header == NEW_HEADER:
            formato = 'nuevo'   # 6 columnas: codigo, desc, etapa, area, materia, activo
        elif clean_header == OLD_HEADER:
            formato = 'legado'  # 5 columnas: codigo, desc, etapa, area/materia, activo
        else:
            return jsonify({"ok": False, "error": (
                f"Cabecera no válida. Descarga la plantilla actualizada.\n"
                f"Esperada (nueva): {';'.join(NEW_HEADER)}\n"
                f"O (legada): {';'.join(OLD_HEADER)}"
            )}), 400

        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT id, nombre FROM etapas")
        etapas_map = {row["nombre"].lower(): row["id"] for row in cur.fetchall()}
        cur.execute("SELECT a.id, a.nombre, e.nombre as etapa_nombre FROM areas a JOIN etapas e ON a.etapa_id = e.id")
        areas_map = {(row["nombre"].lower(), row["etapa_nombre"].lower()): row["id"] for row in cur.fetchall()}

        inserted, updated, errors = 0, 0, []
        for i, row in enumerate(reader, start=2):
            if not any(row): continue

            if formato == 'nuevo':
                if len(row) < 6: continue
                codigo, desc, etapa_name, area_col, materia_col, activo_str = [s.strip() for s in row[:6]]
                # Materia tiene prioridad; si está vacía, usar Area
                area_name = materia_col if materia_col else area_col
            else:
                if len(row) < 5: continue
                codigo, desc, etapa_name, area_name, activo_str = [s.strip() for s in row[:5]]

            etapa_id = etapas_map.get(etapa_name.lower())
            if not etapa_id:
                errors.append({"row": i, "reason": f"Etapa '{etapa_name}' no existe", "data": row})
                continue

            area_id = areas_map.get((area_name.lower(), etapa_name.lower()))
            if not area_id:
                errors.append({"row": i, "reason": f"Área/Materia '{area_name}' no existe en '{etapa_name}'", "data": row})
                continue

            activo = 1 if activo_str.lower() in ("sí", "si", "yes", "1") else 0

            try:
                cur.execute("SELECT id FROM criterios WHERE codigo = ? AND area_id = ?", (codigo, area_id))
                exist = cur.fetchone()
                if exist:
                    cur.execute("UPDATE criterios SET descripcion = ?, activo = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (desc, activo, exist["id"]))
                    updated += 1
                else:
                    cur.execute("INSERT INTO criterios (codigo, descripcion, area_id, activo, oficial) VALUES (?, ?, ?, ?, 1)", (codigo, desc, area_id, activo))
                    inserted += 1
            except Exception as e:
                errors.append({"row": i, "reason": str(e), "data": row})

        conn.commit()
        return jsonify({"ok": True, "inserted": inserted, "updated": updated, "errors": errors})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# --- PERIOD ACTIVATION ---

@criterios_bp.route("/api/criterios/periodo", methods=["GET"])
@simple_cache(timeout=300)
def listar_criterios_periodo():
    """Devuelve los criterio_id activos para un grupo y periodo concreto."""
    grupo_id = request.args.get('grupo_id')
    periodo = request.args.get('periodo')  # 'T1', 'T2', 'T3'
    area_id = request.args.get('area_id')  # opcional: filtrar por área
    if not grupo_id or not periodo:
        return jsonify({"active_ids": []})
    conn = get_db(); cur = conn.cursor()
    if area_id:
        cur.execute("""
            SELECT cp.criterio_id FROM criterios_periodo cp
            JOIN criterios c ON cp.criterio_id = c.id
            WHERE cp.grupo_id = ? AND cp.periodo = ? AND cp.activo = 1 AND c.area_id = ?
        """, (grupo_id, periodo, area_id))
    else:
        cur.execute("""
            SELECT criterio_id FROM criterios_periodo 
            WHERE grupo_id = ? AND periodo = ? AND activo = 1
        """, (grupo_id, periodo))
    active_ids = [row["criterio_id"] for row in cur.fetchall()]
    return jsonify({"active_ids": active_ids})

@criterios_bp.route("/api/criterios/periodo", methods=["POST"])
def guardar_criterios_periodo():
    """Activa/desactiva criterios para un grupo y periodo. 
    Body: {grupo_id, area_id, periodo ('T1'/'T2'/'T3'), criterio_ids: [...]}
    """
    if not session.get('logged_in'): return jsonify({"ok": False}), 401
    d = request.json
    grupo_id = d.get("grupo_id")
    area_id = d.get("area_id")
    periodo = d.get("periodo")  # 'T1', 'T2', 'T3'
    ids = d.get("criterio_ids", [])
    
    if not grupo_id or not periodo:
        return jsonify({"ok": False, "error": "grupo_id y periodo son obligatorios"}), 400
    
    conn = get_db(); cur = conn.cursor()
    try:
        # Desactivar criterios del área en ese grupo/periodo
        if area_id:
            cur.execute("""
                UPDATE criterios_periodo SET activo = 0 
                WHERE grupo_id = ? AND periodo = ? 
                AND criterio_id IN (SELECT id FROM criterios WHERE area_id = ?)
            """, (grupo_id, periodo, area_id))
        
        # Activar los seleccionados (upsert para no duplicar)
        for cid in ids:
            cur.execute("""
                INSERT INTO criterios_periodo (criterio_id, grupo_id, periodo, activo)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(criterio_id, grupo_id, periodo) DO UPDATE SET activo = 1
            """, (cid, grupo_id, periodo))
        conn.commit()
        return jsonify({"ok": True, "activados": len(ids)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# --- MODULAR EVALUATION ---

@criterios_bp.route("/api/evaluacion/criterios", methods=["GET"])
def listar_evaluaciones_criterios():
    alumno_id = request.args.get('alumno_id')
    area_id = request.args.get('area_id')
    periodo = request.args.get('periodo')
    conn = get_db(); cur = conn.cursor()
    cur.execute("""
        SELECT ec.* FROM evaluacion_criterios ec
        JOIN criterios c ON ec.criterio_id = c.id
        WHERE ec.alumno_id = ? AND c.area_id = ? AND ec.periodo = ?
    """, (alumno_id, area_id, periodo))
    return jsonify([dict(row) for row in cur.fetchall()])

@criterios_bp.route("/api/evaluacion/criterios", methods=["POST"])
def guardar_evaluacion_criterio():
    """Guarda una evaluación por criterio directo (modo INFANTIL_NI_EP_C o NUMERICA_1_4).
    Body: {alumno_id, criterio_id, periodo ('T1'/'T2'/'T3'), nivel (int), escala (str)}
    """
    if not session.get('logged_in'): return jsonify({"ok": False}), 401
    d = request.json
    conn = get_db(); cur = conn.cursor()
    from utils.db import nivel_a_nota
    nivel = d["nivel"]
    escala = d.get("escala")  # 'INFANTIL_NI_EP_C' o 'NUMERICA_1_4'
    nota = nivel_a_nota(nivel, escala)
    try:
        cur.execute("""
            INSERT INTO evaluacion_criterios (alumno_id, criterio_id, periodo, nivel, nota)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(alumno_id, criterio_id, periodo) DO UPDATE SET 
                nivel = excluded.nivel, nota = excluded.nota, updated_at = CURRENT_TIMESTAMP
        """, (d["alumno_id"], d["criterio_id"], d["periodo"], nivel, nota))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@criterios_bp.route("/api/criterios/sugerir")
def sugerir_criterio():
    texto = request.args.get("texto", "").lower()
    if not texto:
        return jsonify(None)

    db = get_db()
    palabras = texto.split()

    for palabra in palabras:
        # Buscamos una coincidencia exacta de keyword
        criterio = db.execute("""
            SELECT c.id, c.codigo, c.descripcion
            FROM criterios_keywords k
            JOIN criterios c ON c.id = k.criterio_id
            WHERE k.keyword = ?
            LIMIT 1
        """, (palabra,)).fetchone()

        if criterio:
            return jsonify(dict(criterio))

    return jsonify(None)
