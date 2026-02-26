import os
from flask import Blueprint, request, jsonify, send_from_directory, session
from werkzeug.utils import secure_filename
from utils.db import get_db

programacion_docs_bp = Blueprint('programacion_docs', __name__)
UPLOAD_FOLDER = 'PROGRAMACIONES'

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'odt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_group_folder(grupo_id):
    folder = os.path.join(UPLOAD_FOLDER, f'grupo_{grupo_id}')
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder

@programacion_docs_bp.route("/api/programacion_docs/<int:grupo_id>", methods=["GET"])
def list_docs(grupo_id):
    if not session.get('logged_in'):
        return jsonify({"ok": False, "error": "No autorizado"}), 401
    
    # Check if user has access to group
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT p.id FROM profesores p WHERE p.usuario_id = ?", (session.get("user_id"),))
    prof = cur.fetchone()
    if not prof:
        return jsonify({"ok": False, "error": "Profesor no encontrado"}), 404
        
    cur.execute("SELECT id FROM grupos WHERE id = ? AND profesor_id = ?", (grupo_id, prof["id"]))
    if not cur.fetchone():
        return jsonify({"ok": False, "error": "Grupo no encontrado o no autorizado"}), 404
        
    folder = get_group_folder(grupo_id)
    files = []
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            if os.path.isfile(os.path.join(folder, filename)):
                files.append({
                    "name": filename,
                    "url": f"/api/programacion_docs/{grupo_id}/download/{filename}",
                    "is_pdf": filename.lower().endswith('.pdf')
                })
                
    return jsonify(files)

@programacion_docs_bp.route("/api/programacion_docs/<int:grupo_id>", methods=["POST"])
def upload_doc(grupo_id):
    if not session.get('logged_in'):
        return jsonify({"ok": False, "error": "No autorizado"}), 401
        
    if 'file' not in request.files:
        return jsonify({"ok": False, "error": "No se partió el archivo"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"ok": False, "error": "No file selected"}), 400
        
    if file and allowed_file(file.filename):
        # Verify access
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT p.id FROM profesores p WHERE p.usuario_id = ?", (session.get("user_id"),))
        prof = cur.fetchone()
        if not prof: return jsonify({"ok": False, "error": "Profesor no encontrado"}), 404
        
        cur.execute("SELECT id FROM grupos WHERE id = ? AND profesor_id = ?", (grupo_id, prof["id"]))
        if not cur.fetchone(): return jsonify({"ok": False, "error": "No autorizado"}), 404
        
        filename = secure_filename(file.filename)
        folder = get_group_folder(grupo_id)
        
        # Avoid overwriting
        base, extension = os.path.splitext(filename)
        counter = 1
        final_filename = filename
        while os.path.exists(os.path.join(folder, final_filename)):
            final_filename = f"{base}_{counter}{extension}"
            counter += 1
            
        file.save(os.path.join(folder, final_filename))
        return jsonify({"ok": True, "filename": final_filename})
        
    return jsonify({"ok": False, "error": "Tipo de archivo no permitido"}), 400

@programacion_docs_bp.route("/api/programacion_docs/<int:grupo_id>/<filename>", methods=["DELETE"])
def delete_doc(grupo_id, filename):
    if not session.get('logged_in'):
        return jsonify({"ok": False, "error": "No autorizado"}), 401
        
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT p.id FROM profesores p WHERE p.usuario_id = ?", (session.get("user_id"),))
    prof = cur.fetchone()
    if not prof: return jsonify({"ok": False, "error": "Profesor no encontrado"}), 404
    cur.execute("SELECT id FROM grupos WHERE id = ? AND profesor_id = ?", (grupo_id, prof["id"]))
    if not cur.fetchone(): return jsonify({"ok": False, "error": "No autorizado"}), 404
    
    folder = get_group_folder(grupo_id)
    file_path = os.path.join(folder, secure_filename(filename))
    
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            return jsonify({"ok": True})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500
    else:
        return jsonify({"ok": False, "error": "Archivo no encontrado"}), 404

@programacion_docs_bp.route("/api/programacion_docs/<int:grupo_id>/download/<filename>", methods=["GET"])
def get_doc(grupo_id, filename):
    if not session.get('logged_in'):
        return jsonify({"ok": False, "error": "No autorizado"}), 401
        
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT p.id FROM profesores p WHERE p.usuario_id = ?", (session.get("user_id"),))
    prof = cur.fetchone()
    if not prof: return jsonify({"ok": False, "error": "Profesor no encontrado"}), 404
    cur.execute("SELECT id FROM grupos WHERE id = ? AND profesor_id = ?", (grupo_id, prof["id"]))
    if not cur.fetchone(): return jsonify({"ok": False, "error": "No autorizado"}), 404
    
    folder = get_group_folder(grupo_id)
    # Get absolute path for send_from_directory
    abs_folder = os.path.abspath(folder)
    return send_from_directory(abs_folder, secure_filename(filename))
