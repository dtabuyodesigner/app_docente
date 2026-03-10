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
    
    # Si no hay grupo activo, intentar buscar el primero del profesor
    if not grupo_id:
        cur.execute("SELECT id FROM profesores WHERE usuario_id = ?", (session.get("user_id"),))
        prof = cur.fetchone()
        if prof:
            cur.execute("SELECT id FROM grupos WHERE profesor_id = ? ORDER BY id LIMIT 1", (prof["id"],))
            row = cur.fetchone()
            if row:
                grupo_id = row["id"]
                session['active_group_id'] = grupo_id

    # Inicializar respuesta por defecto
    res = {
        "asistencia": {"presentes": 0, "faltas": 0},
        "comedor": 0,
        "cumples": [],
        "proximos_cumples": [],
        "media_clase": 0,
        "trimestre_actual": 1,
        "asistencia_semanal": [],
        "distribucion_notas": {},
        "alertas": [],
        "proximas_actividades": [],
        "ultimas_reuniones": [],
        "material_pendiente": 0,
        "libros_retrasados": 0,
        "user_role": session.get("role", "profesor")
    }

    if not grupo_id:
        return jsonify(res)

    try:
        # 1. Asistencia
        # Las faltas de tipo 'horas' son ausencias PARCIALES: el alumno sí vino, solo faltó unas horas.
        # Se cuentan como presentes. Solo cuenta como falta si tipo_ausencia = 'dia' (o NULL).
        cur.execute("""
            SELECT 
                SUM(CASE WHEN COALESCE(asist.estado, 'presente') IN ('presente', 'retraso')
                              OR (asist.estado IN ('falta_justificada','falta_no_justificada') AND asist.tipo_ausencia = 'horas')
                         THEN 1 ELSE 0 END) as presentes,
                SUM(CASE WHEN asist.estado IN ('falta_justificada', 'falta_no_justificada')
                              AND COALESCE(asist.tipo_ausencia, 'dia') != 'horas'
                         THEN 1 ELSE 0 END) as faltas
            FROM alumnos a
            LEFT JOIN asistencia asist ON asist.alumno_id = a.id AND asist.fecha = ?
            WHERE a.grupo_id = ? AND a.deleted_at IS NULL
        """, (fecha_hoy, grupo_id))
        asist_stats = cur.fetchone()
        if asist_stats:
            res["asistencia"]["presentes"] = asist_stats[0] or 0
            res["asistencia"]["faltas"] = asist_stats[1] or 0

        # 2. Comedor
        res["comedor"] = calculate_comedor_total(conn, fecha_hoy, grupo_id)

        # 3. Cumpleaños (Hoy y Próximos 7 días)
        dias_semana_es = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        for i in range(8): 
            target_date = date.today() + timedelta(days=i)
            target_mm_dd = target_date.strftime("%m-%d")
            cur.execute("""
                SELECT a.nombre 
                FROM ficha_alumno f
                JOIN alumnos a ON a.id = f.alumno_id
                WHERE strftime('%m-%d', f.fecha_nacimiento) = ? AND a.grupo_id = ? AND a.deleted_at IS NULL
            """, (target_mm_dd, grupo_id))
            for r in cur.fetchall():
                if i == 0: res["cumples"].append(r["nombre"])
                else:
                    res["proximos_cumples"].append({
                        "nombre": r["nombre"],
                        "dia": dias_semana_es[target_date.weekday()],
                        "fecha": target_date.strftime("%d/%m")
                    })

        # 4. Media Clase
        cur.execute("SELECT MAX(e.trimestre) FROM evaluaciones e JOIN alumnos a ON a.id=e.alumno_id WHERE a.grupo_id=?", (grupo_id,))
        row_tri = cur.fetchone()
        ultimo_tri = row_tri[0] if row_tri and row_tri[0] else 1
        res["trimestre_actual"] = ultimo_tri
        
        cur.execute("SELECT AVG(e.nota) FROM evaluaciones e JOIN alumnos a ON a.id=e.alumno_id WHERE e.trimestre = ? AND a.grupo_id=?", (ultimo_tri, grupo_id))
        row_media = cur.fetchone()
        res["media_clase"] = round(row_media[0], 2) if row_media and row_media[0] else 0

        # 5. Asistencia Semanal
        cur.execute("SELECT COUNT(*) FROM alumnos WHERE grupo_id=? AND deleted_at IS NULL", (grupo_id,))
        total_a = cur.fetchone()[0] or 1
        fechas = [(date.today() - timedelta(days=i)).isoformat() for i in range(6, -1, -1) if (date.today() - timedelta(days=i)).weekday() < 5]
        for f in fechas:
            cur.execute("""
                SELECT a.nombre FROM asistencia ast JOIN alumnos a ON a.id = ast.alumno_id
                WHERE ast.fecha = ? AND ast.estado IN ('falta_justificada', 'falta_no_justificada')
                  AND COALESCE(ast.tipo_ausencia, 'dia') != 'horas'
                  AND a.grupo_id = ?
            """, (f, grupo_id))
            nombres_faltan = [r[0] for r in cur.fetchall()]
            faltas = len(nombres_faltan)
            res["asistencia_semanal"].append({
                "fecha": f, "porcentaje": round(max(0, 100.0 - (faltas * 100.0 / total_a)), 1), 
                "faltas": faltas, "faltan_nombres": nombres_faltan
            })

        # 6. Distribución de notas
        cur.execute("""
            SELECT DISTINCT a.id, a.nombre, a.tipo_escala, a.modo_evaluacion 
            FROM areas a JOIN criterios c ON c.area_id = a.id
            JOIN alumnos al ON al.grupo_id = ?
            WHERE al.deleted_at IS NULL
        """, (grupo_id,))
        for area in cur.fetchall():
            area_nombre = area['nombre']
            dist = {}
            if area['tipo_escala'] == 'INFANTIL_NI_EP_C' or area['modo_evaluacion'] == 'POR_CRITERIOS_DIRECTOS':
                cur.execute("""
                    SELECT CASE WHEN ec.nivel = 1 THEN 'NI' WHEN ec.nivel = 2 THEN 'EP' WHEN ec.nivel = 3 THEN 'C' ELSE 'Sincro' END as rango, COUNT(*) as count
                    FROM (SELECT ec.alumno_id, ROUND(AVG(ec.nivel)) as nivel FROM evaluacion_criterios ec JOIN criterios c ON c.id = ec.criterio_id JOIN alumnos a ON a.id = ec.alumno_id WHERE c.area_id = ? AND a.grupo_id = ? AND ec.periodo = ? GROUP BY ec.alumno_id) ec GROUP BY rango
                """, (area['id'], grupo_id, f"T{ultimo_tri}"))
            else:
                cur.execute("""
                    SELECT CASE WHEN e.nota < 5 THEN 'Insuficiente' WHEN e.nota < 7 THEN 'Suficiente/Bien' WHEN e.nota < 9 THEN 'Notable' ELSE 'Sobresaliente' END as rango, COUNT(*) as count
                    FROM (SELECT e.alumno_id, AVG(e.nota) as nota FROM evaluaciones e JOIN alumnos a ON a.id = e.alumno_id WHERE e.trimestre = ? AND a.grupo_id = ? AND e.area_id = ? GROUP BY e.alumno_id) e GROUP BY rango
                """, (ultimo_tri, grupo_id, area['id']))
            for r in cur.fetchall(): dist[r['rango']] = r['count']
            if dist: res["distribucion_notas"][area_nombre] = dist

        # 7. Alertas (solo faltas de día completo, no de horas)
        mes_actual = date.today().strftime("%Y-%m")
        cur.execute("SELECT a.nombre, COUNT(*) as count FROM asistencia ast JOIN alumnos a ON a.id = ast.alumno_id WHERE strftime('%Y-%m', ast.fecha) = ? AND ast.estado IN ('falta_justificada', 'falta_no_justificada') AND COALESCE(ast.tipo_ausencia, 'dia') != 'horas' AND a.grupo_id = ? GROUP BY a.id, a.nombre HAVING COUNT(*) >= 3", (mes_actual, grupo_id))
        for row in cur.fetchall(): res["alertas"].append(f"⚠️ {row['nombre']} tiene {row['count']} faltas este mes.")
        cur.execute("SELECT a.nombre, AVG(e.nota) as media FROM evaluaciones e JOIN alumnos a ON a.id = e.alumno_id WHERE e.trimestre = ? AND a.grupo_id = ? GROUP BY a.id, a.nombre HAVING AVG(e.nota) < 5", (ultimo_tri, grupo_id))
        for row in cur.fetchall(): res["alertas"].append(f"📉 {row['nombre']} tiene media suspensa ({round(row['media'], 1)}).")

        # 8. Próximas Actividades (No completadas)
        cur.execute("SELECT id, fecha, descripcion as actividad FROM programacion_diaria WHERE fecha >= ? AND completado = 0 ORDER BY fecha ASC LIMIT 3", (fecha_hoy,))
        res["proximas_actividades"] = [dict(r) for r in cur.fetchall()]

        # 9. Últimas Reuniones (Padres + Ciclo)
        cur.execute("""
            SELECT r.fecha, a.nombre as alumno, r.temas, r.tipo
            FROM reuniones r
            LEFT JOIN alumnos a ON a.id = r.alumno_id
            WHERE (r.tipo = 'CICLO' OR a.grupo_id = ?)
              AND r.fecha <= ?
            ORDER BY r.fecha DESC
            LIMIT 5
        """, (grupo_id, fecha_hoy))
        res["ultimas_reuniones"] = []
        for r in cur.fetchall():
            prefijo = "🤝 " if r["tipo"] == "PADRES" else "🏫 "
            res["ultimas_reuniones"].append({
                "fecha": r["fecha"],
                "alumno": r["alumno"] if r["alumno"] else "Reunión de Ciclo",
                "temas": (prefijo + (r["temas"] or ""))
            })

        # 10. Material Pendiente
        cur.execute("SELECT COUNT(*) as count FROM material_entregado me JOIN alumnos a ON a.id = me.alumno_id WHERE a.grupo_id = ? AND me.entregado = 0", (grupo_id,))
        res["material_pendiente"] = cur.fetchone()[0] or 0

        # 11. Libros con Retraso
        cur.execute("SELECT valor FROM config WHERE clave = 'max_dias_prestamo'")
        row_cfg = cur.fetchone() or (cur.execute("SELECT valor FROM configuracion WHERE clave = 'max_dias_prestamo'").fetchone())
        dias_limite = int(row_cfg["valor"]) if row_cfg else 7
        cur.execute("""
            SELECT a.nombre, l.titulo, CAST(julianday(date('now')) - julianday(pl.fecha_prestamo) AS INTEGER) as dias
            FROM prestamos_libros pl
            JOIN alumnos a ON a.id = pl.alumno_id
            JOIN libros l ON l.id = pl.libro_id
            WHERE a.grupo_id = ? AND pl.estado = 'activo'
              AND (julianday(date('now')) - julianday(pl.fecha_prestamo)) > ?
            ORDER BY dias DESC
        """, (grupo_id, dias_limite))
        libros_rows = cur.fetchall()
        res["libros_retrasados"] = len(libros_rows)
        res["libros_retrasados_lista"] = [
            {"nombre": r["nombre"], "titulo": r["titulo"], "dias": r["dias"]}
            for r in libros_rows
        ]

    except Exception as e:
        print(f"Error en dashboard_resumen: {e}")
        # Retornamos lo que tengamos hasta ahora o el esqueleto básico

    return jsonify(res)

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
