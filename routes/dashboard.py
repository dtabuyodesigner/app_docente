from flask import Blueprint, jsonify, session
from utils.db import get_db
from datetime import date, timedelta
from routes.comedor import calculate_comedor_total

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route("/api/dashboard/resumen")
def dashboard_resumen():
    fecha_hoy = date.today().isoformat()
    # MM-DD match for birthdays
    hoy_mm_dd = date.today().strftime("%m-%d")

    conn = get_db()
    cur = conn.cursor()

    grupo_id = session.get('active_group_id')
    
    # 1. Asistencia
    cur.execute("""
        SELECT 
            SUM(CASE WHEN COALESCE(asist.estado, 'presente') IN ('presente', 'retraso') THEN 1 ELSE 0 END) as presentes,
            SUM(CASE WHEN asist.estado IN ('falta_justificada', 'falta_no_justificada') THEN 1 ELSE 0 END) as faltas
        FROM alumnos a
        LEFT JOIN asistencia asist ON asist.alumno_id = a.id AND asist.fecha = ?
        WHERE a.grupo_id = ?
    """, (fecha_hoy, grupo_id))
    asist_stats = cur.fetchone()

    # 2. Comedor
    comedor_total = calculate_comedor_total(conn, fecha_hoy, grupo_id)

    # 3. Cumpleaños
    cur.execute("""
        SELECT a.nombre 
        FROM ficha_alumno f
        JOIN alumnos a ON a.id = f.alumno_id
        WHERE strftime('%m-%d', f.fecha_nacimiento) = ? AND a.grupo_id = ?
    """, (hoy_mm_dd, grupo_id))
    cumples = [r["nombre"] for r in cur.fetchall()]

    # 4. Media Clase (último trimestre con datos)
    cur.execute("SELECT MAX(e.trimestre) FROM evaluaciones e JOIN alumnos a ON a.id=e.alumno_id WHERE a.grupo_id=?", (grupo_id,))
    row_tri = cur.fetchone()
    ultimo_tri = row_tri[0] if row_tri and row_tri[0] else 1
    
    cur.execute("SELECT AVG(e.nota) FROM evaluaciones e JOIN alumnos a ON a.id=e.alumno_id WHERE e.trimestre = ? AND a.grupo_id=?", (ultimo_tri, grupo_id))
    row_media = cur.fetchone()
    media_clase = row_media[0] if row_media and row_media[0] else 0

    # 5. Asistencia Semanal (Últimos 7 días omitiendo fines de semana)
    cur.execute("SELECT COUNT(*) FROM alumnos WHERE grupo_id=?", (grupo_id,))
    total_a = cur.fetchone()[0] or 1

    fechas = []
    for i in range(6, -1, -1):
        d = date.today() - timedelta(days=i)
        if d.weekday() < 5:  # 0-4 son Lunes a Viernes
            fechas.append(d.isoformat())

    asist_semanal = []
    for f in fechas:
        cur.execute("""
            SELECT a.nombre 
            FROM asistencia ast
            JOIN alumnos a ON a.id = ast.alumno_id
            WHERE ast.fecha = ? AND ast.estado IN ('falta_justificada', 'falta_no_justificada')
              AND a.grupo_id = ?
        """, (f, grupo_id))
        nombres_faltan = [r[0] for r in cur.fetchall()]
        faltas = len(nombres_faltan)
        
        porcentaje = max(0, 100.0 - (faltas * 100.0 / total_a))
        asist_semanal.append({
            "fecha": f, 
            "porcentaje": round(porcentaje, 1), 
            "faltas": faltas,
            "faltan_nombres": nombres_faltan
        })

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
            SELECT e.alumno_id, AVG(e.nota) as nota
            FROM evaluaciones e
            JOIN alumnos a ON a.id = e.alumno_id
            WHERE e.trimestre = ? AND a.grupo_id = ?
            GROUP BY e.alumno_id
        )
        GROUP BY 
            CASE 
                WHEN nota < 5 THEN 'Insuficiente'
                WHEN nota < 7 THEN 'Suficiente/Bien'
                WHEN nota < 9 THEN 'Notable'
                ELSE 'Sobresaliente'
            END
    """, (ultimo_tri, grupo_id))
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
          AND a.grupo_id = ?
        GROUP BY a.id, a.nombre
        HAVING COUNT(*) >= 3
    """, (mes_actual, grupo_id))
    for row in cur.fetchall():
        alertas.append(f"⚠️ {row['nombre']} tiene {row['count']} faltas este mes.")

    # Alertas Notas
    cur.execute("""
        SELECT a.nombre, AVG(e.nota) as media
        FROM evaluaciones e
        JOIN alumnos a ON a.id = e.alumno_id
        WHERE e.trimestre = ? AND a.grupo_id = ?
        GROUP BY a.id, a.nombre
        HAVING AVG(e.nota) < 5
    """, (ultimo_tri, grupo_id))
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
          AND a.grupo_id = ?
        ORDER BY r.fecha DESC
        LIMIT 5
    """, (fecha_hoy, grupo_id))
    
    ultimas_reuniones = []
    for r in cur.fetchall():
        ultimas_reuniones.append({
            "fecha": r["fecha"],
            "alumno": r["nombre"],
            "temas": r["temas"] or ""
        })


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
        "ultimas_reuniones": ultimas_reuniones,
        "user_role": session.get("role", "profesor")
    })

@dashboard_bp.route("/api/dashboard/ultimas_observaciones")
def ultimas_observaciones():
    conn = get_db()
    cur = conn.cursor()
    grupo_id = session.get('active_group_id')
    # Get last 5 observations
    cur.execute("""
        SELECT o.fecha, a.nombre as alumno, ar.nombre as area, o.texto
        FROM observaciones o
        JOIN alumnos a ON a.id = o.alumno_id
        LEFT JOIN areas ar ON ar.id = o.area_id
        WHERE a.grupo_id = ?
        ORDER BY o.fecha DESC, o.id DESC
        LIMIT 5
    """, (grupo_id,))
    rows = cur.fetchall()
    
    return jsonify([{
        "fecha": r["fecha"],
        "alumno": r["alumno"],
        "area": r["area"] or "General",
        "texto": r["texto"]
    } for r in rows])
