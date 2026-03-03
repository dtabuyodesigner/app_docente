import csv
import io
from flask import Blueprint, request, jsonify, session
from utils.db import get_db

criterios_bp = Blueprint('criterios_api', __name__)

@criterios_bp.route("/api/criterios", methods=["GET"])
def listar_criterios():
    if not session.get('logged_in'):
        return jsonify({"ok": False, "error": "No autorizado"}), 401
        
    area_id = request.args.get('area_id')
    etapa = request.args.get('etapa')
    
    conn = get_db()
    cur = conn.cursor()
    
    query = """
        SELECT c.id, c.codigo, c.descripcion, c.etapa, c.area_id, c.materia_id, c.activo, c.oficial, a.nombre as area_nombre
        FROM criterios c
        LEFT JOIN areas a ON c.area_id = a.id
        WHERE 1=1
    """
    params = []
    
    if area_id:
        query += " AND c.area_id = ?"
        params.append(area_id)
    if etapa:
        query += " AND c.etapa = ?"
        params.append(etapa)
        
    query += " ORDER BY c.codigo"
    
    cur.execute(query, params)
    rows = cur.fetchall()
    
    return jsonify([{
        "id": r["id"],
        "codigo": r["codigo"],
        "descripcion": r["descripcion"],
        "etapa": r["etapa"],
        "area_id": r["area_id"],
        "materia_id": r["materia_id"],
        "activo": bool(r["activo"]),
        "oficial": bool(r["oficial"]),
        "area_nombre": r["area_nombre"]
    } for r in rows])

@criterios_bp.route("/api/criterios", methods=["POST"])
def crear_criterio():
    if not session.get('logged_in'):
        return jsonify({"ok": False, "error": "No autorizado"}), 401
        
    d = request.json
    required = ["codigo", "descripcion", "etapa", "area_id"]
    if not all(k in d for k in required):
        return jsonify({"ok": False, "error": "Faltan datos obligatorios"}), 400
        
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO criterios (codigo, descripcion, etapa, area_id, materia_id, activo, oficial)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            d["codigo"], d["descripcion"], d["etapa"], d["area_id"], 
            d.get("materia_id"), d.get("activo", True), d.get("oficial", False)
        ))
        conn.commit()
        return jsonify({"ok": True, "id": cur.lastrowid})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@criterios_bp.route("/api/criterios/<int:criterio_id>", methods=["PUT"])
def actualizar_criterio(criterio_id):
    if not session.get('logged_in'):
        return jsonify({"ok": False, "error": "No autorizado"}), 401
        
    d = request.json
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE criterios
            SET codigo = ?, descripcion = ?, etapa = ?, area_id = ?, materia_id = ?, activo = ?, oficial = ?
            WHERE id = ?
        """, (
            d["codigo"], d["descripcion"], d["etapa"], d["area_id"], 
            d.get("materia_id"), d.get("activo", True), d.get("oficial", False),
            criterio_id
        ))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@criterios_bp.route("/api/criterios/import_csv", methods=["POST"])
def importar_criterios_csv():
    if not session.get('logged_in'):
        return jsonify({"ok": False, "error": "No autorizado"}), 401
        
    if 'file' not in request.files:
        return jsonify({"ok": False, "error": "No se subió ningún archivo"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"ok": False, "error": "Archivo vacío"}), 400
        
    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        reader = csv.reader(stream, delimiter=';')
        
        # Saltar cabecera si la hay (codigo;descripcion;etapa;area_id)
        # Asumimos que si la primera fila no tiene números en codigo o id, es cabecera.
        
        conn = get_db()
        cur = conn.cursor()
        
        first_row = True
        inserted = 0
        for row in reader:
            if not row or len(row) < 4: continue
            
            codigo = row[0].strip()
            descripcion = row[1].strip()
            etapa = row[2].strip()
            area_id_str = row[3].strip()
            
            if first_row and (codigo.lower() == 'codigo' or area_id_str.lower() == 'area_id'):
                first_row = False
                continue
                
            first_row = False
            
            if not area_id_str.isdigit():
                # Podemos buscar el ID del área por nombre si no es un número.
                cur.execute("SELECT id FROM areas WHERE nombre LIKE ?", (f"%{area_id_str}%",))
                res = cur.fetchone()
                if res:
                    area_id = res["id"]
                else:
                    return jsonify({"ok": False, "error": f"Área no encontrada para: {area_id_str}"}), 400
            else:
                area_id = int(area_id_str)
                
            cur.execute("""
                INSERT INTO criterios (codigo, descripcion, etapa, area_id, activo, oficial)
                VALUES (?, ?, ?, ?, 1, 1)
            """, (codigo, descripcion, etapa, area_id))
            inserted += 1
            
        conn.commit()
        return jsonify({"ok": True, "inserted": inserted})
    except Exception as e:
        return jsonify({"ok": False, "error": "Error procesando CSV: " + str(e)}), 500
