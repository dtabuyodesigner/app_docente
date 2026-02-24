from flask import Blueprint, jsonify, request
from utils.db import get_db
from datetime import date
import json

asistencia_bp = Blueprint('asistencia', __name__)

@asistencia_bp.route("/api/asistencia/hoy")
def asistencia_hoy():
    fecha = request.args.get("fecha", date.today().isoformat())
    conn = get_db()
    cur = conn.cursor()

    day_of_week = str(date.fromisoformat(fecha).weekday())

    cur.execute("""
        SELECT 
            a.id,
            a.nombre,
            a.no_comedor,
            a.comedor_dias,
            COALESCE(asist.estado, 'presente') AS estado,
            asist.id AS asistencia_id,
            asist.comedor AS asist_comedor,
            asist.tipo_ausencia,
            asist.horas_ausencia
        FROM alumnos a
        LEFT JOIN asistencia asist
            ON asist.alumno_id = a.id
           AND asist.fecha = ?
        ORDER BY a.nombre
    """, (fecha,))

    datos = cur.fetchall()

    resultado = []
    for row in datos:
        if row["asistencia_id"] is not None:
             final_comedor = row["asist_comedor"]
             tipo_ausencia = row["tipo_ausencia"]
             horas_ausencia = row["horas_ausencia"]
        else:
             tipo_ausencia = "dia"
             horas_ausencia = None
             if row["comedor_dias"]:
                 if day_of_week in row["comedor_dias"].split(','):
                     final_comedor = 1
                 else:
                     final_comedor = 0
             else:
                 final_comedor = 0 if row["no_comedor"] == 1 else 1

        resultado.append({
            "id": row["id"],
            "nombre": row["nombre"],
            "estado": row["estado"],
            "comedor": final_comedor,
            "no_comedor": row["no_comedor"],
            "tipo_ausencia": tipo_ausencia,
            "horas_ausencia": horas_ausencia
        })

    return jsonify(resultado)

@asistencia_bp.route("/api/asistencia", methods=["POST"])
def guardar_asistencia():
    d = request.json
    alumno_id = d["alumno_id"]
    fecha = d.get("fecha", date.today().isoformat())
    
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT no_comedor FROM alumnos WHERE id = ?", (alumno_id,))
    row_alumno = cur.fetchone()
    no_comedor = row_alumno["no_comedor"] if row_alumno else 0

    cur.execute("SELECT estado, comedor FROM asistencia WHERE alumno_id = ? AND fecha = ?", (alumno_id, fecha))
    row = cur.fetchone()
    
    current_estado = row["estado"] if row else "presente"
    current_comedor = row["comedor"] if row else (0 if no_comedor == 1 else 1)

    new_estado = d.get("estado", current_estado)
    new_comedor = d.get("comedor", current_comedor)
    tipo_ausencia = d.get("tipo_ausencia", "dia")
    horas_ausencia = d.get("horas_ausencia")

    if new_estado in ("falta_justificada", "falta_no_justificada"):
        if tipo_ausencia == "dia":
            new_comedor = 0

    cur.execute("""
        INSERT INTO asistencia (alumno_id, fecha, estado, comedor, tipo_ausencia, horas_ausencia)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(alumno_id, fecha)
        DO UPDATE SET
            estado = excluded.estado,
            comedor = excluded.comedor,
            tipo_ausencia = excluded.tipo_ausencia,
            horas_ausencia = excluded.horas_ausencia
    """, (alumno_id, fecha, new_estado, new_comedor, tipo_ausencia, horas_ausencia))

    conn.commit()

    return jsonify({"ok": True})

@asistencia_bp.route("/api/asistencia/mes")
def asistencia_mes():
    mes = request.args.get("mes", date.today().strftime("%Y-%m"))
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            a.nombre,
            asist.estado,
            asist.fecha
        FROM alumnos a
        JOIN asistencia asist ON asist.alumno_id = a.id
        WHERE strftime('%Y-%m', asist.fecha) = ?
          AND asist.estado IN ('retraso', 'falta_justificada', 'falta_no_justificada')
        ORDER BY a.nombre, asist.fecha
    """, (mes,))

    datos = cur.fetchall()

    resumen = {}
    for row in datos:
        nombre = row["nombre"]
        if nombre not in resumen:
            resumen[nombre] = {
                "nombre": nombre,
                "retrasos": 0,
                "justificadas": 0,
                "injustificadas": 0,
                "detalles": []
            }
        
        entry = resumen[nombre]
        if row["estado"] == 'retraso':
            entry['retrasos'] += 1
        elif row["estado"] == 'falta_justificada':
            entry['justificadas'] += 1
        elif row["estado"] == 'falta_no_justificada':
            entry['injustificadas'] += 1
        
        entry['detalles'].append({
            "fecha": row["fecha"],
            "estado": row["estado"]
        })

    lista = list(resumen.values())
    lista.sort(key=lambda x: (x['injustificadas'] + x['justificadas'] + x['retrasos']), reverse=True)

    return jsonify(lista)

@asistencia_bp.route("/api/asistencia/resumen")
def resumen_asistencia():
    fecha = request.args.get("fecha", date.today().isoformat())
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            a.nombre,
            COALESCE(asist.estado, 'presente') as estado,
            asist.tipo_ausencia,
            asist.horas_ausencia
        FROM alumnos a
        LEFT JOIN asistencia asist
            ON asist.alumno_id = a.id
           AND asist.fecha = ?
    """, (fecha,))

    filas = cur.fetchall()

    presentes = 0
    retrasos = 0
    faltas = 0
    faltas_justificadas = 0
    faltas_injustificadas = 0
    lista_faltan = []

    for row in filas:
        if row["estado"] == "presente":
            presentes += 1
        elif row["estado"] == "retraso":
            presentes += 1
            retrasos += 1
        elif row["estado"] == "falta_justificada":
            faltas += 1
            faltas_justificadas += 1
            label = row["nombre"]
            if row["tipo_ausencia"] == "horas" and row["horas_ausencia"]:
                h_list = json.loads(row["horas_ausencia"])
                label += f" ({len(h_list)}h J)"
            else:
                label += " (J)"
            lista_faltan.append(label)
        elif row["estado"] == "falta_no_justificada":
            faltas += 1
            faltas_injustificadas += 1
            label = row["nombre"]
            if row["tipo_ausencia"] == "horas" and row["horas_ausencia"]:
                h_list = json.loads(row["horas_ausencia"])
                label += f" ({len(h_list)}h NJ)"
            else:
                label += " (NJ)"
            lista_faltan.append(label)
        else:
            faltas += 1
            faltas_injustificadas += 1
            lista_faltan.append(row["nombre"])

    return jsonify({
        "presentes": presentes,
        "retrasos": retrasos,
        "faltan": faltas,
        "faltas_justificadas": faltas_justificadas,
        "faltas_injustificadas": faltas_injustificadas,
        "lista_faltan": lista_faltan
    })

@asistencia_bp.route("/api/asistencia/encargado")
def get_encargado():
    fecha = request.args.get("fecha", date.today().isoformat())
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.id, a.nombre 
        FROM encargados e
        JOIN alumnos a ON e.alumno_id = a.id
        WHERE e.fecha = ?
    """, (fecha,))
    row = cur.fetchone()
    
    if row:
        return jsonify({"id": row["id"], "nombre": row["nombre"]})
    return jsonify(None)

@asistencia_bp.route("/api/asistencia/encargado/seleccionar", methods=["POST"])
def seleccionar_encargado():
    import random
    data = request.json
    fecha = data.get("fecha", date.today().isoformat())
    
    conn = get_db()
    cur = conn.cursor()
    
    # 1. Get present students for this day
    cur.execute("""
        SELECT a.id, a.nombre
        FROM alumnos a
        LEFT JOIN asistencia asist ON asist.alumno_id = a.id AND asist.fecha = ?
        WHERE COALESCE(asist.estado, 'presente') IN ('presente', 'retraso')
    """, (fecha,))
    presentes = cur.fetchall()
    
    if not presentes:
        return jsonify({"error": "No hay alumnos presentes hoy"}), 400
    
    # 2. Count how many times each present student has been encargado
    cur.execute("""
        SELECT alumno_id, COUNT(*) as veces
        FROM encargados
        GROUP BY alumno_id
    """)
    conteos = {row["alumno_id"]: row["veces"] for row in cur.fetchall()}
    
    # 3. Find the minimum count among present students
    present_counts = [(p["id"], p["nombre"], conteos.get(p["id"], 0)) for p in presentes]
    min_veces = min(c[2] for c in present_counts)
    
    # 4. Filter candidates (those with the minimum count)
    candidatos = [c for c in present_counts if c[2] == min_veces]
    
    # 5. Pick one randomly
    elegido = random.choice(candidatos)
    alumno_id, nombre = elegido[0], elegido[1]
    
    # 6. Save (overwrite if exists for that date)
    cur.execute("""
        INSERT INTO encargados (fecha, alumno_id) 
        VALUES (?, ?)
        ON CONFLICT(fecha) DO UPDATE SET alumno_id = excluded.alumno_id
    """, (fecha, alumno_id))
    
    conn.commit()
    
    return jsonify({"id": alumno_id, "nombre": nombre})

@asistencia_bp.route("/api/asistencia/encargado/reiniciar", methods=["POST"])
def reiniciar_encargados():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM encargados")
    conn.commit()
    return jsonify({"ok": True})

@asistencia_bp.route("/api/asistencia/encargado/historial")
def historial_encargados():
    conn = get_db()
    cur = conn.cursor()
    
    # Get total active students
    cur.execute("SELECT COUNT(*) as total FROM alumnos")
    total_alumnos = cur.fetchone()["total"]
    
    cur.execute("""
        SELECT e.fecha, a.nombre 
        FROM encargados e
        JOIN alumnos a ON e.alumno_id = a.id
        ORDER BY e.fecha DESC
    """)
    datos = cur.fetchall()
    
    return jsonify({
        "total_alumnos": total_alumnos,
        "historial": [{"fecha": row["fecha"], "nombre": row["nombre"]} for row in datos]
    })
