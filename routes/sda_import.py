import csv
import io
from flask import Blueprint, request, jsonify, session
from utils.db import get_db

sda_import_bp = Blueprint('sda_import', __name__)

@sda_import_bp.route("/api/sda/import_csv", methods=["POST"])
def import_sda_csv():
    if not session.get('logged_in'):
        return jsonify({"ok": False, "error": "No autorizado"}), 401
    
    if 'file' not in request.files:
        return jsonify({"ok": False, "error": "No se subió ningún archivo"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"ok": False, "error": "No se seleccionó ningún archivo"}), 400

    grupo_id = session.get('active_group_id')
    if not grupo_id:
        return jsonify({"ok": False, "error": "Debes seleccionar un grupo antes de importar"}), 400

    try:
        stream = io.StringIO(file.stream.read().decode("utf-8"), newline=None)
        reader = csv.DictReader(stream)
        
        # Validar cabeceras mínimas
        required_cols = ['Etapa', 'Area', 'Trimestre', 'SDA_ID', 'SDA_Titulo', 'Actividad_ID', 'Sesion_Numero', 'Sesion_Titulo']
        for col in required_cols:
            if col not in reader.fieldnames:
                return jsonify({"ok": False, "error": f"Falta la columna obligatoria: {col}"}), 400

        conn = get_db()
        cur = conn.cursor()

        # Obtener información del grupo para validar etapa
        cur.execute("SELECT etapa_id FROM grupos WHERE id = ?", (grupo_id,))
        grupo_info = cur.fetchone()
        if not grupo_info:
            return jsonify({"ok": False, "error": "Grupo no encontrado"}), 404
            
        cur.execute("SELECT id, nombre FROM etapas")
        etapas_db = {r["nombre"]: r["id"] for r in cur.fetchall()}

        stats = {
            "sda": 0,
            "actividades": 0,
            "sesiones": 0,
            "criterios": 0,
            "errores": 0
        }

        # Cache para evitar redundancia en el mismo proceso
        cache_areas = {}
        cache_sda = {}
        cache_criterios = {}
        cache_actividades = {}

        for row in reader:
            try:
                etapa_name = row['Etapa'].strip()
                area_name = row['Area'].strip()
                trim_str = row['Trimestre'].strip() # T1, T2, T3
                trim_num = int(trim_str[1]) if len(trim_str) > 1 and trim_str[1].isdigit() else 1
                
                sda_code = row['SDA_ID'].strip()
                sda_title = row['SDA_Titulo'].strip()
                duracion = row.get('Duracion_Semanas', '').strip()
                duracion = int(duracion) if duracion.isdigit() else None
                
                # 1. Obtener Area ID
                area_key = (area_name, etapa_name)
                if area_key not in cache_areas:
                    etapa_id = etapas_db.get(etapa_name)
                    if not etapa_id:
                        raise Exception(f"Etapa desconocida: {etapa_name}")
                    
                    cur.execute("SELECT id FROM areas WHERE nombre = ? AND etapa_id = ?", (area_name, etapa_id))
                    area_row = cur.fetchone()
                    if not area_row:
                        # Si no existe, la creamos (o podrías decidir fallar)
                        cur.execute("INSERT INTO areas (nombre, etapa_id, es_oficial, activa) VALUES (?, ?, 0, 1)", (area_name, etapa_id))
                        area_id = cur.lastrowid
                    else:
                        area_id = area_row["id"]
                    cache_areas[area_key] = area_id
                else:
                    area_id = cache_areas[area_key]

                # 2. Upsert SDA
                sda_key = (sda_code, area_id, grupo_id)
                if sda_key not in cache_sda:
                    cur.execute("SELECT id FROM sda WHERE (codigo_sda = ? OR nombre = ?) AND area_id = ? AND grupo_id = ?", 
                                (sda_code, sda_title, area_id, grupo_id))
                    sda_row = cur.fetchone()
                    if not sda_row:
                        cur.execute("""
                            INSERT INTO sda (nombre, area_id, trimestre, grupo_id, codigo_sda, duracion_semanas)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (sda_title, area_id, trim_num, grupo_id, sda_code, duracion))
                        sda_id = cur.lastrowid
                        stats["sda"] += 1
                    else:
                        sda_id = sda_row["id"]
                        cur.execute("UPDATE sda SET codigo_sda = ?, duracion_semanas = ? WHERE id = ?", 
                                    (sda_code, duracion, sda_id))
                    cache_sda[sda_key] = sda_id
                else:
                    sda_id = cache_sda[sda_key]

                # 3. Registrar Criterios (si vienen en la fila)
                crit_code = row.get('Criterio_Codigo', '').strip()
                if crit_code:
                    crit_desc = row.get('Criterio_Descriptor', '').strip()
                    crit_key = (crit_code, area_id)
                    if crit_key not in cache_criterios:
                        cur.execute("SELECT id FROM criterios WHERE codigo = ? AND area_id = ?", (crit_code, area_id))
                        crit_row = cur.fetchone()
                        if not crit_row:
                            cur.execute("INSERT INTO criterios (codigo, descripcion, area_id) VALUES (?, ?, ?)", 
                                        (crit_code, crit_desc, area_id))
                            crit_id = cur.lastrowid
                            stats["criterios"] += 1
                        else:
                            crit_id = crit_row["id"]
                        cache_criterios[crit_key] = crit_id
                    else:
                        crit_id = cache_criterios[crit_key]
                    
                    # Relacionar con SDA
                    cur.execute("INSERT OR IGNORE INTO sda_criterios (sda_id, criterio_id) VALUES (?, ?)", (sda_id, crit_id))
                    
                    # Activar para el periodo/trimestre
                    cur.execute("""
                        INSERT OR IGNORE INTO criterios_periodo (criterio_id, grupo_id, periodo)
                        VALUES (?, ?, ?)
                    """, (crit_id, grupo_id, trim_str))

                # 4. Upsert Actividad
                act_code = row['Actividad_ID'].strip()
                act_title = row.get('Actividad_Titulo', sda_title).strip()
                act_key = (act_code, sda_id)
                if act_key not in cache_actividades:
                    cur.execute("SELECT id FROM actividades_sda WHERE (codigo_actividad = ? OR nombre = ?) AND sda_id = ?", 
                                (act_code, act_title, sda_id))
                    act_row = cur.fetchone()
                    if not act_row:
                        cur.execute("INSERT INTO actividades_sda (sda_id, nombre, codigo_actividad) VALUES (?, ?, ?)", 
                                    (sda_id, act_title, act_code))
                        act_id = cur.lastrowid
                        stats["actividades"] += 1
                    else:
                        act_id = act_row["id"]
                        cur.execute("UPDATE actividades_sda SET codigo_actividad = ? WHERE id = ?", (act_code, act_id))
                    cache_actividades[act_key] = act_id
                else:
                    act_id = cache_actividades[act_key]

                # 5. Crear Sesión
                sesion_num = row['Sesion_Numero'].strip()
                sesion_title = row['Sesion_Titulo'].strip()
                sesion_desc = row.get('Descripcion_Sesion', '').strip()
                sesion_fecha = row.get('Fecha', '').strip() # DD-MM format usually or YYYY-MM-DD
                # Intentar normalizar fecha si es necesario, por ahora la guardamos como texto si viene
                
                # Para evitar duplicar sesiones en la misma actividad con mismo número/título
                cur.execute("SELECT id FROM sesiones_actividad WHERE actividad_id = ? AND (numero_sesion = ? OR descripcion = ?)", 
                            (act_id, sesion_num, sesion_title))
                if not cur.fetchone():
                    cur.execute("""
                        INSERT INTO sesiones_actividad (actividad_id, numero_sesion, descripcion, fecha)
                        VALUES (?, ?, ?, ?)
                    """, (act_id, sesion_num, sesion_title, sesion_fecha))
                    stats["sesiones"] += 1

            except Exception as e:
                print(f"Error procesando fila: {e}")
                stats["errores"] += 1

        conn.commit()
        return jsonify({"ok": True, "stats": stats})

    except Exception as e:
        return jsonify({"ok": False, "error": f"Error general: {str(e)}"}), 500
