import sqlite3
import json

def test_query():
    conn = sqlite3.connect('app_evaluar.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    grupo_id = 1
    ultimo_tri = 1

    # Get areas for the group
    cur.execute("""
        SELECT id, nombre, tipo_escala, modo_evaluacion 
        FROM areas 
        WHERE id IN (
            SELECT DISTINCT e.area_id FROM evaluaciones e JOIN alumnos a ON a.id = e.alumno_id WHERE a.grupo_id = ?
            UNION
            SELECT DISTINCT c.area_id FROM evaluacion_criterios ec JOIN criterios c ON c.id = ec.criterio_id JOIN alumnos a ON a.id = ec.alumno_id WHERE a.grupo_id = ?
        )
    """, (grupo_id, grupo_id))
    areas_activas = [dict(row) for row in cur.fetchall()]

    distribucion_por_area = {}

    for area in areas_activas:
        area_nombre = area['nombre']
        distribucion_por_area[area_nombre] = {}

        if area['tipo_escala'] == 'INFANTIL_NI_EP_C' or area['modo_evaluacion'] == 'POR_CRITERIOS_DIRECTOS':
            # Query for direct criteria (Infantil)
            cur.execute("""
                SELECT 
                    CASE 
                        WHEN ec.nivel = 1 THEN 'NI'
                        WHEN ec.nivel = 2 THEN 'EP'
                        WHEN ec.nivel = 3 THEN 'C'
                        ELSE 'Sincro'
                    END as rango,
                    COUNT(*) as count
                FROM (
                    SELECT ec.alumno_id, ROUND(AVG(ec.nivel)) as nivel
                    FROM evaluacion_criterios ec
                    JOIN criterios c ON c.id = ec.criterio_id
                    JOIN alumnos a ON a.id = ec.alumno_id
                    WHERE c.area_id = ? AND a.grupo_id = ? AND ec.periodo = ?
                    GROUP BY ec.alumno_id
                ) ec
                GROUP BY 
                    CASE 
                        WHEN ec.nivel = 1 THEN 'NI'
                        WHEN ec.nivel = 2 THEN 'EP'
                        WHEN ec.nivel = 3 THEN 'C'
                        ELSE 'Sincro'
                    END
            """, (area['id'], grupo_id, f"T{ultimo_tri}"))
            rows = cur.fetchall()
            for r in rows:
                distribucion_por_area[area_nombre][r['rango']] = r['count']
        
        else:
            # Query for numeric evaluations (Primaria/Secundaria)
            cur.execute("""
                SELECT 
                    CASE 
                        WHEN e.nota < 5 THEN 'Insuficiente'
                        WHEN e.nota < 7 THEN 'Suficiente/Bien'
                        WHEN e.nota < 9 THEN 'Notable'
                        ELSE 'Sobresaliente'
                    END as rango,
                    COUNT(*) as count
                FROM (
                    SELECT e.alumno_id, AVG(e.nota) as nota
                    FROM evaluaciones e
                    JOIN alumnos a ON a.id = e.alumno_id
                    WHERE e.trimestre = ? AND a.grupo_id = ? AND e.area_id = ?
                    GROUP BY e.alumno_id
                ) e
                GROUP BY 
                    CASE 
                        WHEN e.nota < 5 THEN 'Insuficiente'
                        WHEN e.nota < 7 THEN 'Suficiente/Bien'
                        WHEN e.nota < 9 THEN 'Notable'
                        ELSE 'Sobresaliente'
                    END
            """, (ultimo_tri, grupo_id, area['id']))
            rows = cur.fetchall()
            for r in rows:
                distribucion_por_area[area_nombre][r['rango']] = r['count']

    print(json.dumps(distribucion_por_area, indent=2))

if __name__ == '__main__':
    test_query()
