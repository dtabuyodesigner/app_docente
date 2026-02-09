from flask import Blueprint, jsonify
from utils.db import get_db
from datetime import date
from routes.comedor import calculate_comedor_total

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route("/api/dashboard/resumen")
def dashboard_resumen():
    fecha_hoy = date.today().isoformat()
    # MM-DD match for birthdays
    hoy_mm_dd = date.today().strftime("%m-%d")

    conn = get_db()
    cur = conn.cursor()

    # 1. Asistencia
    cur.execute("""
        SELECT 
            SUM(CASE WHEN COALESCE(asist.estado, 'presente') IN ('presente', 'retraso') THEN 1 ELSE 0 END) as presentes,
            SUM(CASE WHEN asist.estado IN ('falta_justificada', 'falta_no_justificada') THEN 1 ELSE 0 END) as faltas
        FROM alumnos a
        LEFT JOIN asistencia asist ON asist.alumno_id = a.id AND asist.fecha = ?
    """, (fecha_hoy,))
    asist_stats = cur.fetchone()

    # 2. Comedor
    conn2 = get_db() # Helper creates new conn
    comedor_total = calculate_comedor_total(conn2, fecha_hoy)
    conn2.close()

    # 3. Cumpleaños
    cur.execute("""
        SELECT a.nombre 
        FROM ficha_alumno f
        JOIN alumnos a ON a.id = f.alumno_id
        WHERE strftime('%m-%d', f.fecha_nacimiento) = ?
    """, (hoy_mm_dd,))
    cumples = [r["nombre"] for r in cur.fetchall()]

    # 4. Media Clase (último trimestre con datos)
    cur.execute("SELECT MAX(trimestre) FROM evaluaciones")
    row_tri = cur.fetchone()
    ultimo_tri = row_tri[0] if row_tri and row_tri[0] else 1
    
    cur.execute("SELECT AVG(nota) FROM evaluaciones WHERE trimestre = ?", (ultimo_tri,))
    row_media = cur.fetchone()
    media_clase = row_media[0] if row_media and row_media[0] else 0

    # 5. Asistencia Semanal (Últimos 7 días)
    cur.execute("""
        SELECT fecha, 
               SUM(CASE WHEN estado IN ('presente', 'retraso') THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
        FROM asistencia
        WHERE fecha >= date('now', '-6 days')
        GROUP BY fecha
        ORDER BY fecha ASC
    """)
    asist_semanal = [{"fecha": r[0], "porcentaje": round(r[1], 1)} for r in cur.fetchall()]

    # 6. Distribución de notas (Global del trimestre actual)
    cur.execute("""
        SELECT 
            CASE 
                WHEN nota < 5 THEN 'Insuficiente'
                WHEN nota < 7 THEN 'Suficiente/Bien'
                WHEN nota < 9 THEN 'Notable'
                ELSE 'Sobresaliente'
            END as rango,
            COUNT(*)
        FROM (
            SELECT alumno_id, AVG(nota) as nota
            FROM evaluaciones 
            WHERE trimestre = ?
            GROUP BY alumno_id
        )
        GROUP BY 
            CASE 
                WHEN nota < 5 THEN 'Insuficiente'
                WHEN nota < 7 THEN 'Suficiente/Bien'
                WHEN nota < 9 THEN 'Notable'
                ELSE 'Sobresaliente'
            END
    """, (ultimo_tri,))
    distribucion = {r[0]: r[1] for r in cur.fetchall()}

    # 7. Alertas
    mes_actual = date.today().strftime("%Y-%m")
    alertas = []

    # Alertas Faltas
    cur.execute("""
        SELECT a.nombre, COUNT(*) as count
        FROM asistencia ast
        JOIN alumnos a ON a.id = ast.alumno_id
        WHERE strftime('%Y-%m', ast.fecha) = ? 
          AND ast.estado IN ('falta_justificada', 'falta_no_justificada')
        GROUP BY a.id, a.nombre
        HAVING COUNT(*) >= 3
    """, (mes_actual,))
    for row in cur.fetchall():
        alertas.append(f"⚠️ {row['nombre']} tiene {row['count']} faltas este mes.")

    # Alertas Notas
    cur.execute("""
        SELECT a.nombre, AVG(e.nota) as media
        FROM evaluaciones e
        JOIN alumnos a ON a.id = e.alumno_id
        WHERE e.trimestre = ?
        GROUP BY a.id, a.nombre
        HAVING AVG(e.nota) < 5
    """, (ultimo_tri,))
    for row in cur.fetchall():
        alertas.append(f"📉 {row['nombre']} tiene media suspensa ({round(row['media'], 1)}).")

    # 8. Próximas Actividades
    cur.execute("""
        SELECT fecha, actividad
        FROM programacion_diaria
        WHERE fecha >= ?
        ORDER BY fecha ASC
        LIMIT 3
    """, (fecha_hoy,))
    proximas = [{"fecha": r["fecha"], "actividad": r["actividad"]} for r in cur.fetchall()]

    # 9. Últimas Reuniones con Padres
    cur.execute("""
        SELECT r.fecha, a.nombre, r.temas
        FROM reuniones r
        JOIN alumnos a ON a.id = r.alumno_id
        WHERE r.tipo = 'PADRES' 
          AND r.fecha <= ?
        ORDER BY r.fecha DESC
        LIMIT 5
    """, (fecha_hoy,))
    
    ultimas_reuniones = []
    for r in cur.fetchall():
        ultimas_reuniones.append({
            "fecha": r["fecha"],
            "alumno": r["nombre"],
            "temas": r["temas"] or ""
        })

    conn.close()

    return jsonify({
        "asistencia": {
            "presentes": asist_stats[0] if asist_stats[0] else 0,
            "faltas": asist_stats[1] if asist_stats[1] else 0
        },
        "comedor": comedor_total,
        "cumples": cumples,
        "media_clase": round(media_clase, 2),
        "trimestre_actual": ultimo_tri,
        "asistencia_semanal": asist_semanal,
        "distribucion_notas": distribucion,
        "alertas": alertas,
        "proximas_actividades": proximas,
        "ultimas_reuniones": ultimas_reuniones
    })

@dashboard_bp.route("/api/dashboard/ultimas_observaciones")
def ultimas_observaciones():
    conn = get_db()
    cur = conn.cursor()
    # Get last 5 observations
    cur.execute("""
        SELECT o.fecha, a.nombre as alumno, ar.nombre as area, o.texto
        FROM observaciones o
        JOIN alumnos a ON a.id = o.alumno_id
        LEFT JOIN areas ar ON ar.id = o.area_id
        ORDER BY o.fecha DESC, o.id DESC
        LIMIT 5
    """)
    rows = cur.fetchall()
    conn.close()
    
    return jsonify([{
        "fecha": r["fecha"],
        "alumno": r["alumno"],
        "area": r["area"] or "General",
        "texto": r["texto"]
    } for r in rows])
