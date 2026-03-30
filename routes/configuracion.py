from flask import Blueprint, jsonify, request, session, send_file
from utils.db import get_db
import os

configuracion_bp = Blueprint('configuracion', __name__)

@configuracion_bp.route("/api/configuracion/logo", methods=["POST"])
def upload_logo():
    """Sube un logo (izda o dcha) a AppData/uploads/logos/"""
    from utils.db import get_app_data_dir
    lado = request.form.get('lado', 'izda')  # izda | dcha
    posicion = request.form.get('posicion', 'left')
    
    if 'logo' not in request.files:
        return jsonify({"ok": False, "error": "No se recibió archivo"}), 400
    
    file = request.files['logo']
    if not file.filename:
        return jsonify({"ok": False, "error": "Archivo vacío"}), 400

    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
        return jsonify({"ok": False, "error": "Formato no permitido"}), 400

    logos_dir = os.path.join(get_app_data_dir(), "uploads", "logos")
    os.makedirs(logos_dir, exist_ok=True)

    filename = f"logo_{lado}.{ext}"
    filepath = os.path.join(logos_dir, filename)
    file.save(filepath)

    # Guardar posición en config
    conn = get_db()
    conn.execute("""
        INSERT INTO config (clave, valor) VALUES (?, ?)
        ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor
    """, (f"logo_{lado}_posicion", posicion))
    conn.execute("""
        INSERT INTO config (clave, valor) VALUES (?, ?)
        ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor
    """, (f"logo_{lado}_filename", f"logos/{filename}"))
    conn.commit()

    return jsonify({"ok": True, "filename": f"logos/{filename}"})


@configuracion_bp.route("/api/configuracion/firma", methods=["POST"])
def upload_firma():
    """Sube la firma del tutor a AppData/uploads/logos/"""
    from utils.db import get_app_data_dir
    
    if 'firma' not in request.files:
        return jsonify({"ok": False, "error": "No se recibió archivo"}), 400
    
    file = request.files['firma']
    if not file.filename:
        return jsonify({"ok": False, "error": "Archivo vacío"}), 400

    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
        return jsonify({"ok": False, "error": "Formato no permitido"}), 400

    logos_dir = os.path.join(get_app_data_dir(), "uploads", "logos")
    os.makedirs(logos_dir, exist_ok=True)

    filename = f"tutor_firma.{ext}"
    filepath = os.path.join(logos_dir, filename)
    file.save(filepath)

    # Guardar en config
    conn = get_db()
    conn.execute("""
        INSERT INTO config (clave, valor) VALUES (?, ?)
        ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor
    """, ("tutor_firma_filename", f"logos/{filename}"))
    conn.commit()

    return jsonify({"ok": True, "filename": f"logos/{filename}"})


@configuracion_bp.route("/api/configuracion/logos", methods=["GET"])
def get_logos():
    """Devuelve los filenames de los logos guardados."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT clave, valor FROM config WHERE clave LIKE 'logo_%'")
    rows = {r["clave"]: r["valor"] for r in cur.fetchall()}
    return jsonify({
        "izda": rows.get("logo_izda_filename"),
        "dcha": rows.get("logo_dcha_filename"),
        "firma": rows.get("tutor_firma_filename"),
        "izda_posicion": rows.get("logo_izda_posicion", "left"),
        "dcha_posicion": rows.get("logo_dcha_posicion", "right"),
    })


@configuracion_bp.route("/api/configuracion/mi_rol", methods=["GET"])
def get_mi_rol():
    """Devuelve el rol y áreas del usuario en el grupo activo."""
    from flask import session
    grupo_id = session.get('active_group_id')
    if not grupo_id:
        return jsonify({"rol": "tutor", "areas": [], "area_nombres": []})
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT clave, valor FROM config WHERE clave IN (?, ?)",
                (f"grupo_{grupo_id}_rol", f"grupo_{grupo_id}_areas"))
    rows = {r["clave"]: r["valor"] for r in cur.fetchall()}
    rol = rows.get(f"grupo_{grupo_id}_rol", "tutor")
    areas_str = rows.get(f"grupo_{grupo_id}_areas", "")
    areas = [a for a in areas_str.split(",") if a] if areas_str else []
    # Obtener nombres de las áreas
    area_nombres = []
    if areas:
        placeholders = ",".join("?" * len(areas))
        cur.execute(f"SELECT id, nombre FROM areas WHERE id IN ({placeholders})", areas)
        area_nombres = [{"id": r["id"], "nombre": r["nombre"]} for r in cur.fetchall()]
    return jsonify({"rol": rol, "areas": areas, "area_nombres": area_nombres})


@configuracion_bp.route("/api/configuracion/grupo_rol", methods=["GET"])
def get_grupo_rol():
    grupo_id = request.args.get("grupo_id")
    if not grupo_id:
        return jsonify({"rol": "tutor", "areas": []})
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT clave, valor FROM config WHERE clave IN (?, ?)",
                (f"grupo_{grupo_id}_rol", f"grupo_{grupo_id}_areas"))
    rows = {r["clave"]: r["valor"] for r in cur.fetchall()}
    rol = rows.get(f"grupo_{grupo_id}_rol", "tutor")
    areas_str = rows.get(f"grupo_{grupo_id}_areas", "")
    areas = areas_str.split(",") if areas_str else []
    return jsonify({"rol": rol, "areas": areas})


@configuracion_bp.route("/api/configuracion/grupo_rol", methods=["POST"])
def save_grupo_rol():
    data = request.json or {}
    grupo_id = data.get("grupo_id")
    rol = data.get("rol", "tutor")
    areas = data.get("areas", [])
    if not grupo_id:
        return jsonify({"ok": False, "error": "Falta grupo_id"}), 400
    conn = get_db()
    conn.execute("INSERT INTO config (clave, valor) VALUES (?, ?) ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor",
                 (f"grupo_{grupo_id}_rol", rol))
    conn.execute("INSERT INTO config (clave, valor) VALUES (?, ?) ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor",
                 (f"grupo_{grupo_id}_areas", ",".join(str(a) for a in areas)))
    conn.commit()
    return jsonify({"ok": True})


@configuracion_bp.route("/api/configuracion", methods=["GET"])
def get_all_config():
    conn = get_db()
    cur = conn.cursor()
    
    # Get from 'config' table
    cur.execute("SELECT clave, valor FROM config")
    config_rows = cur.fetchall()
    config_data = {r["clave"]: r["valor"] for r in config_rows}
    
    # Get from 'configuracion' table (specifically for library)
    cur.execute("SELECT clave, valor FROM configuracion")
    config_old_rows = cur.fetchall()
    for r in config_old_rows:
        if r["clave"] not in config_data:
            config_data[r["clave"]] = r["valor"]
            
    return jsonify(config_data)

@configuracion_bp.route("/api/configuracion", methods=["POST"])
def save_config():
    data = request.json
    if not data:
        return jsonify({"ok": False, "error": "No hay datos"}), 400
        
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("BEGIN")
        for clave, valor in data.items():
            # Save to 'config' table as the primary store
            cur.execute("""
                INSERT INTO config (clave, valor) VALUES (?, ?)
                ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor
            """, (clave, str(valor)))
            
            # Special case: Sync to 'configuracion' table to maintain compatibility with lectura.py
            if clave == 'max_dias_prestamo':
                cur.execute("""
                    INSERT INTO configuracion (clave, valor) VALUES (?, ?)
                    ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor
                """, (clave, str(valor)))
                
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
