"""
Evaluación Híbrida Unificada - Opción C

Este módulo proporciona un endpoint unificado que detecta automáticamente
el modo de evaluación del área (POR_ACTIVIDADES, POR_SA, POR_CRITERIOS_DIRECTOS)
y devuelve los datos apropiados para la evaluación.

Detecta la etapa educativa (Infantil/Primaria) desde el grupo seleccionado
y adapta los niveles de logro y escalas de evaluación correspondientes.

Autor: App Evaluar
Fecha: 2026
"""
from flask import Blueprint, jsonify, request, session
from utils.db import get_db, nivel_a_nota
from datetime import date

evaluacion_cuaderno_bp = Blueprint('evaluacion_cuaderno', __name__)


@evaluacion_cuaderno_bp.route("/cuaderno")
def cuaderno_unificado():
    """
    Endpoint unificado que devuelve datos para evaluación híbrida.
    
    Detecta automáticamente:
    - El modo de evaluación del área
    - La etapa educativa desde el grupo (Infantil/Primaria)
    - La escala de evaluación apropiada (NI/EP/CO, PA/AD/MA o 1-4)

    Parámetros:
        - area_id: ID del área a evaluar
        - trimestre: 1, 2 o 3
        - grupo_id: ID del grupo (opcional, usa sesión si no se pasa)
        - sda_id: ID de la SDA (opcional, filtra por SDA específica)
        - alumno_id: ID del alumno (opcional, si no se pasa devuelve todos los alumnos)

    Respuesta:
        {
            "modo": "POR_ACTIVIDADES" | "POR_SA" | "POR_CRITERIOS_DIRECTOS",
            "etapa": "Infantil" | "Primaria" | "Secundaria",
            "area": { id, nombre, tipo_escala, modo_evaluacion },
            "escala_evaluacion": {
                "tipo": "INFANTIL_NI_EP_C" | "INFANTIL_PA_A_MA" | "NUMERICA_1_4",
                "niveles": [1, 2, 3] | [1, 2, 3, 4],
                "labels": ["NI", "EP", "CO"] | ["PA", "AD", "MA"] | ["1", "2", "3", "4"]
            },
            "alumnos": [ { id, nombre } ],
            "criterios": [ { id, codigo, descripcion } ],
            "actividades": [ { id, nombre, sda_id, sda_nombre, criterio_ids } ],
            "sdas": [ { id, nombre, criterio_ids } ],
            "evaluaciones": { "{alumno_id}_{criterio_id}": nivel },
            "medias": { "{alumno_id}": { "criterios": {...}, "area": media } }
        }
    """
    area_id = request.args.get("area_id")
    trimestre = request.args.get("trimestre")
    grupo_id = request.args.get("grupo_id") or session.get('active_group_id')
    sda_id = request.args.get("sda_id")
    alumno_id = request.args.get("alumno_id")  # Opcional

    if not area_id or not trimestre or not grupo_id:
        return jsonify({"error": "Faltan parámetros: area_id, trimestre, grupo_id"}), 400

    db = get_db()
    cur = db.cursor()

    # 1. Obtener información del grupo (para detectar etapa)
    grupo = cur.execute("""
        SELECT id, nombre, etapa_id 
        FROM grupos 
        WHERE id = ?
    """, (grupo_id,)).fetchone()
    
    if not grupo:
        return jsonify({"error": "Grupo no encontrado"}), 404
    
    etapa_id = grupo["etapa_id"]
    etapa_nombre = cur.execute("""
        SELECT nombre FROM etapas WHERE id = ?
    """, (etapa_id,)).fetchone()
    etapa_nombre = etapa_nombre["nombre"] if etapa_nombre else "Primaria"
    
    # 2. Obtener información del área (incluye modo_evaluacion y tipo_escala)
    area = cur.execute("""
        SELECT id, nombre, tipo_escala, modo_evaluacion, etapa_id as area_etapa_id
        FROM areas
        WHERE id = ?
    """, (area_id,)).fetchone()

    if not area:
        return jsonify({"error": "Área no encontrada"}), 404

    modo = area["modo_evaluacion"] or "POR_SA"
    
    # 3. Determinar la escala de evaluación según etapa del grupo
    # Si el grupo es de Infantil, forzar escala infantil
    tipo_escala = area["tipo_escala"] or "NUMERICA_1_4"
    
    if etapa_nombre == "Infantil":
        # Forzar escala de Infantil según configuración del área
        if "INFANTIL" not in tipo_escala:
            # Si el área no tiene escala infantil definida, usar NI/EP/CO por defecto
            tipo_escala = "INFANTIL_NI_EP_C"
    else:
        # Primaria/Secundaria: usar escala numérica
        if tipo_escala.startswith("INFANTIL_"):
            tipo_escala = "NUMERICA_1_4"
    
    # Configurar labels según la escala
    if tipo_escala == "INFANTIL_PA_A_MA":
        escala_labels = ["NI/PA", "EP/AD", "CO/MA"]
        escala_niveles = [1, 2, 3]
    elif tipo_escala == "INFANTIL_NI_EP_C":
        escala_labels = ["NI/PA", "EP/AD", "CO/MA"]
        escala_niveles = [1, 2, 3]
    else:
        escala_labels = ["1", "2", "3", "4"]
        escala_niveles = [1, 2, 3, 4]
    
    # 2. Obtener alumnos del grupo
    if alumno_id:
        alumnos = cur.execute("""
            SELECT id, nombre FROM alumnos WHERE id = ? AND grupo_id = ?
        """, (alumno_id, grupo_id)).fetchall()
    else:
        alumnos = cur.execute("""
            SELECT id, nombre FROM alumnos WHERE grupo_id = ? ORDER BY nombre
        """, (grupo_id,)).fetchall()
    
    alumno_ids = [a["id"] for a in alumnos]
    
    # 3. Obtener criterios según el modo
    criterios = []
    sdas = []
    actividades = []
    
    if modo == "POR_ACTIVIDADES":
        # Obtener todas las actividades de las SDAs del área/trimestre
        if sda_id and sda_id not in ('', 'null', '0'):
            actividades_rows = cur.execute("""
                SELECT a.id, a.nombre, a.descripcion, a.codigo_actividad,
                       s.id as sda_id, s.nombre as sda_nombre,
                       (SELECT MIN(fecha) FROM sesiones_actividad WHERE actividad_id = a.id) as min_fecha
                FROM actividades_sda a
                JOIN sda s ON a.sda_id = s.id
                WHERE s.area_id = ? AND (s.trimestre = ? OR s.trimestre IS NULL) AND a.sda_id = ?
                  AND (s.grupo_id = ? OR s.grupo_id IS NULL)
                ORDER BY s.nombre, min_fecha, a.id
            """, (area_id, trimestre, sda_id, grupo_id)).fetchall()
        else:
            actividades_rows = cur.execute("""
                SELECT a.id, a.nombre, a.descripcion, a.codigo_actividad,
                       s.id as sda_id, s.nombre as sda_nombre,
                       (SELECT MIN(fecha) FROM sesiones_actividad WHERE actividad_id = a.id) as min_fecha
                FROM actividades_sda a
                JOIN sda s ON a.sda_id = s.id
                WHERE s.area_id = ? AND (s.trimestre = ? OR s.trimestre IS NULL)
                  AND (s.grupo_id = ? OR s.grupo_id IS NULL)
                ORDER BY s.nombre, min_fecha, a.id
            """, (area_id, trimestre, grupo_id)).fetchall()
        
        actividades = [dict(a) for a in actividades_rows]
        actividad_ids = [a["id"] for a in actividades]

        # Obtener TODAS las SDAs del área/trimestre para el dropdown (siempre todas, no solo la seleccionada)
        sdas_rows = cur.execute("""
            SELECT DISTINCT s.id, s.nombre, s.trimestre
            FROM sda s
            JOIN actividades_sda a ON a.sda_id = s.id
            WHERE s.area_id = ? AND (s.trimestre = ? OR s.trimestre IS NULL)
              AND (s.grupo_id = ? OR s.grupo_id IS NULL)
            ORDER BY s.nombre
        """, (area_id, trimestre, grupo_id)).fetchall()

        sdas = []
        for s in sdas_rows:
            sda_dict = dict(s)
            # Formatear nombre con trimestre para el frontend
            if s["trimestre"]:
                sda_dict["nombre"] = f"[T{s['trimestre']}] {s['nombre']}"
            sdas.append(sda_dict)
        
        # Obtener criterios del área (para mostrar en resumen)
        criterios = cur.execute("""
            SELECT id, codigo, descripcion
            FROM criterios
            WHERE area_id = ? AND activo = 1
            ORDER BY codigo
        """, (area_id,)).fetchall()
        
        # Obtener mapeo actividad→criterios para cada actividad
        if actividad_ids:
            placeholders = ",".join("?" * len(actividad_ids))
            mapeo = cur.execute(f"""
                SELECT actividad_id, criterio_id
                FROM actividad_criterio
                WHERE actividad_id IN ({placeholders})
            """, actividad_ids).fetchall()
            
            # Añadir criterio_ids a cada actividad
            for act in actividades:
                act["criterio_ids"] = [
                    m["criterio_id"] for m in mapeo if m["actividad_id"] == act["id"]
                ]
        else:
            for act in actividades:
                act["criterio_ids"] = []
        
        # Calcular medias (esto puebla medias[alumno_id]["criterios"])
        medias = _calcular_medias_actividades(cur, alumno_ids, area_id, trimestre, area["tipo_escala"], sda_id)

        # Obtener evaluaciones de actividades para mostrar en el cuaderno
        evaluaciones = {}
        
        if actividad_ids and alumno_ids:
            act_placeholders = ",".join("?" * len(actividad_ids))
            alum_placeholders = ",".join("?" * len(alumno_ids))
            
            evals = cur.execute(f"""
                SELECT alumno_id, actividad_id, nivel
                FROM evaluaciones_actividad
                WHERE actividad_id IN ({act_placeholders})
                  AND alumno_id IN ({alum_placeholders})
                  AND trimestre = ?
            """, actividad_ids + alumno_ids + [trimestre]).fetchall()
            
            evaluaciones = {
                f"{e['alumno_id']}_{e['actividad_id']}": e['nivel']
                for e in evals
            }

    elif modo == "POR_SA":
        # Obtener SDAs del área/trimestre
        # Obtener TODAS las SDAs del área/trimestre para el dropdown (siempre todas, no solo la seleccionada)
        sdas_rows = cur.execute("""
            SELECT s.id, s.nombre, s.trimestre
            FROM sda s
            WHERE s.area_id = ? AND (s.trimestre = ? OR s.trimestre IS NULL)
              AND (s.grupo_id = ? OR s.grupo_id IS NULL)
            ORDER BY s.nombre
        """, (area_id, trimestre, grupo_id)).fetchall()

        sdas = []
        for s in sdas_rows:
            sda_dict = dict(s)
            # Formatear nombre con trimestre para el frontend
            if s["trimestre"]:
                sda_dict["nombre"] = f"[T{s['trimestre']}] {s['nombre']}"
            sdas.append(sda_dict)
        sda_ids = [s["id"] for s in sdas]
        
        # Obtener criterios de las SDAs
        if sda_ids:
            sda_placeholders = ",".join("?" * len(sda_ids))
            criterios = cur.execute(f"""
                SELECT DISTINCT c.id, c.codigo, c.descripcion
                FROM criterios c
                JOIN sda_criterios sc ON c.id = sc.criterio_id
                WHERE sc.sda_id IN ({sda_placeholders})
                  AND c.activo = 1
                ORDER BY c.codigo
            """, sda_ids).fetchall()
            
            # Añadir criterio_ids a cada SDA
            mapeo = cur.execute(f"""
                SELECT sda_id, criterio_id
                FROM sda_criterios
                WHERE sda_id IN ({sda_placeholders})
            """, sda_ids).fetchall()
            
            for sda in sdas:
                sda["criterio_ids"] = [
                    m["criterio_id"] for m in mapeo if m["sda_id"] == sda["id"]
                ]
        else:
            criterios = cur.execute("""
                SELECT id, codigo, descripcion
                FROM criterios
                WHERE area_id = ? AND activo = 1
                ORDER BY codigo
            """, (area_id,)).fetchall()
        
        criterio_ids = [c["id"] for c in criterios]
        
        # Obtener evaluaciones (de la tabla evaluaciones)
        if criterio_ids and alumno_ids:
            crit_placeholders = ",".join("?" * len(criterio_ids))
            alum_placeholders = ",".join("?" * len(alumno_ids))

            if sda_id and sda_id not in ('', 'null', '0'):
                # Evaluaciones para una SDA específica
                evals = cur.execute(f"""
                    SELECT alumno_id, criterio_id, nivel
                    FROM evaluaciones
                    WHERE criterio_id IN ({crit_placeholders})
                      AND alumno_id IN ({alum_placeholders})
                      AND sda_id = ?
                      AND trimestre = ?
                """, criterio_ids + alumno_ids + [sda_id, trimestre]).fetchall()
            elif sda_ids:
                # Evaluaciones para todas las SDAs del área/trimestre
                sda_placeholders = ",".join("?" * len(sda_ids))
                evals = cur.execute(f"""
                    SELECT alumno_id, criterio_id, nivel
                    FROM evaluaciones
                    WHERE criterio_id IN ({crit_placeholders})
                      AND alumno_id IN ({alum_placeholders})
                      AND area_id = ?
                      AND trimestre = ?
                      AND sda_id IN ({sda_placeholders})
                """, criterio_ids + alumno_ids + [area_id, trimestre] + sda_ids).fetchall()
            else:
                # Sin SDAs, buscar evaluaciones generales del área
                evals = cur.execute(f"""
                    SELECT alumno_id, criterio_id, nivel
                    FROM evaluaciones
                    WHERE criterio_id IN ({crit_placeholders})
                      AND alumno_id IN ({alum_placeholders})
                      AND area_id = ?
                      AND trimestre = ?
                """, criterio_ids + alumno_ids + [area_id, trimestre]).fetchall()

            evaluaciones = {
                f"{e['alumno_id']}_{e['criterio_id']}": e['nivel']
                for e in evals
            }
            
            # También obtener evaluaciones directas de SDA (criterio_id = NULL)
            if sda_ids and alumno_ids:
                sda_placeholders_direct = ",".join("?" * len(sda_ids))
                alum_placeholders_direct = ",".join("?" * len(alumno_ids))
                evals_direct = cur.execute(f"""
                    SELECT alumno_id, sda_id, nivel
                    FROM evaluaciones
                    WHERE criterio_id IS NULL
                      AND alumno_id IN ({alum_placeholders_direct})
                      AND area_id = ?
                      AND trimestre = ?
                      AND sda_id IN ({sda_placeholders_direct})
                """, alumno_ids + [area_id, trimestre] + sda_ids).fetchall()
                
                for e in evals_direct:
                    # Usar una clave especial para evaluaciones directas de SDA
                    evaluaciones[f"{e['alumno_id']}_sda_{e['sda_id']}"] = e['nivel']
        else:
            evaluaciones = {}

        # Calcular medias
        medias = _calcular_medias_sda(cur, alumno_ids, area_id, trimestre, sda_id)

    else:  # POR_CRITERIOS_DIRECTOS
        # Obtener criterios activados para el periodo
        periodo = f"T{trimestre}"
        
        # Primero obtener criterios activados para este grupo+área+periodo
        cp_rows = cur.execute("""
            SELECT criterio_id
            FROM criterios_periodo
            WHERE grupo_id = ? AND area_id = ? AND periodo = ?
        """, (grupo_id, area_id, periodo)).fetchall()
        
        active_ids = [r["criterio_id"] for r in cp_rows]
        
        if active_ids:
            crit_placeholders = ",".join("?" * len(active_ids))
            criterios = cur.execute(f"""
                SELECT id, codigo, descripcion
                FROM criterios
                WHERE id IN ({crit_placeholders}) AND activo = 1
                ORDER BY codigo
            """, active_ids).fetchall()
        else:
            # Si no hay activación específica, mostrar todos los activos del área
            criterios = cur.execute("""
                SELECT id, codigo, descripcion
                FROM criterios
                WHERE area_id = ? AND activo = 1
                ORDER BY codigo
            """, (area_id,)).fetchall()
        
        criterio_ids = [c["id"] for c in criterios]
        
        # Obtener evaluaciones directas
        if criterio_ids and alumno_ids:
            crit_placeholders = ",".join("?" * len(criterio_ids))
            alum_placeholders = ",".join("?" * len(alumno_ids))
            evals = cur.execute(f"""
                SELECT alumno_id, criterio_id, nivel
                FROM evaluacion_criterios
                WHERE criterio_id IN ({crit_placeholders})
                  AND alumno_id IN ({alum_placeholders})
                  AND periodo = ?
            """, criterio_ids + alumno_ids + [periodo]).fetchall()
            
            evaluaciones = {
                f"{e['alumno_id']}_{e['criterio_id']}": e['nivel']
                for e in evals
            }
        else:
            evaluaciones = {}
        
        # Calcular medias
        medias = _calcular_medias_directas(cur, alumno_ids, area_id, periodo)

    try:
        return jsonify({
            "modo": modo,
            "etapa": etapa_nombre,
            "grupo": grupo["nombre"] if grupo else "N/A",
            "area": dict(area) if area else {},
            "escala_evaluacion": {
                "tipo": tipo_escala,
                "niveles": escala_niveles,
                "labels": escala_labels
            },
            "alumnos": [dict(a) for a in alumnos],
            "criterios": [dict(c) for c in criterios],
            "actividades": actividades,
            "sdas": sdas,
            "evaluaciones": evaluaciones,
            "medias": medias
        })
    except Exception as e:
        print(f"[ERROR] Cuaderno Unificado: {str(e)}")
        return jsonify({"error": str(e), "ok": False}), 500


def _calcular_medias_actividades(cur, alumno_ids, area_id, trimestre, tipo_escala, sda_id=None):
    """
    Calcula las medias para el modo POR_ACTIVIDADES.
    Para cada alumno:
    1. Calcula media de actividades por criterio
    2. Calcula media del área como promedio de criterios
    """
    medias = {}
    
    # Obtener todos los criterios del área
    criterios = cur.execute("""
        SELECT id FROM criterios WHERE area_id = ? AND activo = 1
    """, (area_id,)).fetchall()
    criterio_ids = [c["id"] for c in criterios]
    
    # Normalizar sda_id
    if sda_id in ('', 'null', '0', 'None'):
        sda_id = None
    
    for alumno_id in alumno_ids:
        medias_alumno = {"criterios": {}, "area": None}
        
        suma_medias = 0
        cuenta_criterios = 0
        
        for criterio_id in criterio_ids:
            # Construir la consulta base según si hay sda_id o no
            if target_sda := sda_id:
                # Filtrar solo por actividades de la SA seleccionada
                stats = cur.execute("""
                    SELECT AVG(ea.nota) as media_nota
                    FROM evaluaciones_actividad ea
                    JOIN actividades_sda a ON ea.actividad_id = a.id
                    JOIN actividad_criterio ac ON ac.actividad_id = a.id
                    WHERE ea.alumno_id = ? AND ea.trimestre = ? AND ac.criterio_id = ? AND a.sda_id = ?
                """, (alumno_id, trimestre, criterio_id, target_sda)).fetchone()
            else:
                # Comportamiento anterior: Promediar todas las actividades del área
                stats = cur.execute("""
                    SELECT AVG(ea.nota) as media_nota
                    FROM evaluaciones_actividad ea
                    JOIN actividades_sda a ON ea.actividad_id = a.id
                    JOIN actividad_criterio ac ON ac.actividad_id = a.id
                    JOIN sda s ON a.sda_id = s.id
                    WHERE ea.alumno_id = ? AND ea.trimestre = ? AND ac.criterio_id = ?
                      AND s.area_id = ?
                """, (alumno_id, trimestre, criterio_id, area_id)).fetchone()
            
            if stats["media_nota"] is not None:
                medias_alumno["criterios"][str(criterio_id)] = round(stats["media_nota"], 2)
                suma_medias += stats["media_nota"]
                cuenta_criterios += 1
        
        if cuenta_criterios > 0:
            medias_alumno["area"] = round(suma_medias / cuenta_criterios, 2)
        
        medias[str(alumno_id)] = medias_alumno
    
    return medias


def _calcular_medias_sda(cur, alumno_ids, area_id, trimestre, sda_id=None):
    """
    Calcula las medias para el modo POR_SA.
    """
    medias = {}
    
    for alumno_id in alumno_ids:
        medias_alumno = {"criterios": {}, "area": None}
        
        # 1. Calcular media por criterio para este alumno
        if target_sda := sda_id:
            # Solo evaluaciones vinculadas a esta SDA concreta
            rows_crit = cur.execute("""
                SELECT criterio_id, AVG(nota) as media_crit
                FROM evaluaciones
                WHERE alumno_id = ? AND sda_id = ? AND trimestre = ? AND criterio_id IS NOT NULL
                GROUP BY criterio_id
            """, (alumno_id, target_sda, trimestre)).fetchall()
        else:
            # Toda el área (Todas las SDAs + Evaluaciones directas)
            rows_crit = cur.execute("""
                SELECT criterio_id, AVG(nota) as media_crit
                FROM evaluaciones
                WHERE alumno_id = ? AND area_id = ? AND trimestre = ? AND criterio_id IS NOT NULL
                GROUP BY criterio_id
            """, (alumno_id, area_id, trimestre)).fetchall()
        
        for rc in rows_crit:
            medias_alumno["criterios"][str(rc["criterio_id"])] = round(rc["media_crit"], 2)

        # 2. Obtener media del área directamente (Promedio de todas las notas del área)
        if sda_id:
            row = cur.execute("""
                SELECT ROUND(AVG(nota), 2) as media
                FROM evaluaciones
                WHERE alumno_id = ? AND sda_id = ? AND trimestre = ?
            """, (alumno_id, sda_id, trimestre)).fetchone()
        else:
            # Si no hay SDA específica, promedia TODO lo del área y trimestre para el alumno
            row = cur.execute("""
                SELECT ROUND(AVG(nota), 2) as media
                FROM evaluaciones
                WHERE alumno_id = ? AND area_id = ? AND trimestre = ?
            """, (alumno_id, area_id, trimestre)).fetchone()
        
        medias_alumno["area"] = row["media"] if row["media"] else None
        medias[str(alumno_id)] = medias_alumno
    
    return medias


def _calcular_medias_directas(cur, alumno_ids, area_id, periodo):
    """
    Calcula las medias para el modo POR_CRITERIOS_DIRECTOS.
    """
    medias = {}
    
    for alumno_id in alumno_ids:
        medias_alumno = {"criterios": {}, "area": None}
        
        # Obtener media del área desde evaluacion_criterios
        row = cur.execute("""
            SELECT ROUND(AVG(ec.nota), 2) as media
            FROM evaluacion_criterios ec
            JOIN criterios c ON ec.criterio_id = c.id
            WHERE ec.alumno_id = ? AND c.area_id = ? AND ec.periodo = ?
        """, (alumno_id, area_id, periodo)).fetchone()
        
        medias_alumno["area"] = row["media"] if row["media"] else None
        medias[str(alumno_id)] = medias_alumno
    
    return medias


@evaluacion_cuaderno_bp.route("/guardar_unificado", methods=["POST"])
def guardar_unificado():
    """
    Endpoint unificado para guardar evaluaciones.
    Detecta automáticamente el modo y guarda en la tabla correspondiente.
    
    Body:
    {
        "area_id": int,
        "trimestre": int,
        "evaluaciones": [
            {
                "alumno_id": int,
                "criterio_id": int,  # Para POR_SA o POR_CRITERIOS_DIRECTOS
                "actividad_id": int,  # Para POR_ACTIVIDADES
                "nivel": int|null
            }
        ]
    }
    """
    data = request.json
    area_id = data.get("area_id")
    trimestre = data.get("trimestre")
    evaluaciones = data.get("evaluaciones", [])
    
    if not area_id or not trimestre or not evaluaciones:
        return jsonify({"ok": False, "error": "Faltan parámetros"}), 400
    
    db = get_db()
    cur = db.cursor()
    
    # Obtener modo del área
    area = cur.execute("""
        SELECT modo_evaluacion, tipo_escala FROM areas WHERE id = ?
    """, (area_id,)).fetchone()
    
    if not area:
        return jsonify({"ok": False, "error": "Área no encontrada"}), 404
    
    modo = area["modo_evaluacion"] or "POR_SA"
    tipo_escala = area["tipo_escala"]
    
    try:
        cur.execute("BEGIN")
        
        for ev in evaluaciones:
            alumno_id = ev.get("alumno_id")
            nivel = ev.get("nivel")  # Puede ser None para borrar
            
            if modo == "POR_ACTIVIDADES" and "actividad_id" in ev:
                # Guardar en evaluaciones_actividad
                actividad_id = ev["actividad_id"]
                
                if nivel is None:
                    cur.execute("""
                        DELETE FROM evaluaciones_actividad
                        WHERE alumno_id = ? AND actividad_id = ? AND trimestre = ?
                    """, (alumno_id, actividad_id, trimestre))
                else:
                    nota = nivel_a_nota(nivel, tipo_escala)
                    cur.execute("""
                        INSERT INTO evaluaciones_actividad (alumno_id, actividad_id, nivel, nota, trimestre, fecha)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(alumno_id, actividad_id, trimestre)
                        DO UPDATE SET nivel = excluded.nivel, nota = excluded.nota, fecha = excluded.fecha
                    """, (alumno_id, actividad_id, int(nivel), nota, trimestre, date.today().isoformat()))
                    
                    # Propagar a criterios
                    act_info = cur.execute("""
                        SELECT sda_id FROM actividades_sda WHERE id = ?
                    """, (actividad_id,)).fetchone()
                    
                    if act_info:
                        _propagar_actividades_a_criterios(
                            cur, alumno_id, act_info["sda_id"], area_id, tipo_escala, trimestre
                        )
            
            elif "criterio_id" in ev:
                criterio_id = ev["criterio_id"]
                periodo = f"T{trimestre}"
                
                if nivel is None:
                    if modo == "POR_CRITERIOS_DIRECTOS":
                        cur.execute("""
                            DELETE FROM evaluacion_criterios
                            WHERE alumno_id = ? AND criterio_id = ? AND periodo = ?
                        """, (alumno_id, criterio_id, periodo))
                    else:
                        # POR_SA - borrar de evaluaciones
                        sda_id = ev.get("sda_id")
                        if sda_id:
                            cur.execute("""
                                DELETE FROM evaluaciones
                                WHERE alumno_id = ? AND criterio_id = ? AND sda_id = ? AND trimestre = ?
                            """, (alumno_id, criterio_id, sda_id, trimestre))
                        else:
                            cur.execute("""
                                DELETE FROM evaluaciones
                                WHERE alumno_id = ? AND criterio_id = ? AND area_id = ? AND trimestre = ? AND sda_id IS NULL
                            """, (alumno_id, criterio_id, area_id, trimestre))
                else:
                    nota = nivel_a_nota(nivel, tipo_escala)
                    
                    if modo == "POR_CRITERIOS_DIRECTOS":
                        cur.execute("""
                            INSERT INTO evaluacion_criterios (alumno_id, criterio_id, periodo, nivel, nota)
                            VALUES (?, ?, ?, ?, ?)
                            ON CONFLICT(alumno_id, criterio_id, periodo)
                            DO UPDATE SET nivel = excluded.nivel, nota = excluded.nota
                        """, (alumno_id, criterio_id, periodo, int(nivel), nota))
                    else:
                        # POR_SA
                        sda_id = ev.get("sda_id")
                        if sda_id:
                            cur.execute("""
                                INSERT INTO evaluaciones (alumno_id, area_id, trimestre, sda_id, criterio_id, nivel, nota)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                                ON CONFLICT(alumno_id, criterio_id, sda_id, trimestre)
                                DO UPDATE SET nivel = excluded.nivel, nota = excluded.nota
                            """, (alumno_id, area_id, trimestre, sda_id, criterio_id, int(nivel), nota))
                        else:
                            cur.execute("""
                                INSERT INTO evaluaciones (alumno_id, area_id, trimestre, sda_id, criterio_id, nivel, nota)
                                VALUES (?, ?, ?, NULL, ?, ?, ?)
                                ON CONFLICT(alumno_id, criterio_id, trimestre, area_id)
                                DO UPDATE SET nivel = excluded.nivel, nota = excluded.nota
                            """, (alumno_id, area_id, trimestre, criterio_id, int(nivel), nota))
        
        db.commit()
        return jsonify({"ok": True})
    
    except Exception as e:
        db.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


def _propagar_actividades_a_criterios(cur, alumno_id, sda_id, area_id, escala, trimestre):
    """
    Propaga las notas de actividades a la tabla evaluaciones (sda_id=NULL).
    """
    if not sda_id:
        return
    
    # Obtener criterios del área
    criterios = cur.execute("""
        SELECT DISTINCT sc.criterio_id
        FROM sda_criterios sc
        JOIN sda s ON sc.sda_id = s.id
        WHERE s.area_id = ?
    """, (area_id,)).fetchall()
    
    for row in criterios:
        criterio_id = row["criterio_id"]
        
        # Verificar mapeo actividad_criterio
        cur.execute("SELECT COUNT(*) as cuenta FROM actividad_criterio WHERE criterio_id = ?", (criterio_id,))
        tiene_mapeo = cur.fetchone()["cuenta"] > 0
        
        if tiene_mapeo:
            stats = cur.execute("""
                SELECT AVG(ea.nivel) as media_nivel, AVG(ea.nota) as media_nota
                FROM evaluaciones_actividad ea
                JOIN actividades_sda a ON ea.actividad_id = a.id
                JOIN actividad_criterio ac ON ac.actividad_id = a.id
                WHERE ea.alumno_id = ? AND ea.trimestre = ? AND ac.criterio_id = ?
            """, (alumno_id, trimestre, criterio_id)).fetchone()
        else:
            stats = cur.execute("""
                SELECT AVG(ea.nivel) as media_nivel, AVG(ea.nota) as media_nota
                FROM evaluaciones_actividad ea
                JOIN actividades_sda a ON ea.actividad_id = a.id
                JOIN sda_criterios sc ON sc.sda_id = a.sda_id
                WHERE ea.alumno_id = ? AND ea.trimestre = ? AND sc.criterio_id = ?
            """, (alumno_id, trimestre, criterio_id)).fetchone()
        
        if stats["media_nivel"] is None:
            # Borrar entrada
            cur.execute("""
                DELETE FROM evaluaciones
                WHERE alumno_id = ? AND criterio_id = ? AND sda_id IS NULL AND trimestre = ? AND area_id = ?
            """, (alumno_id, criterio_id, trimestre, area_id))
        else:
            media_nivel = int(round(stats["media_nivel"]))
            media_nota = round(stats["media_nota"], 2)
            
            # Eliminar y insertar (UPSERT)
            cur.execute("""
                DELETE FROM evaluaciones
                WHERE alumno_id = ? AND criterio_id = ? AND sda_id IS NULL AND trimestre = ? AND area_id = ?
            """, (alumno_id, criterio_id, trimestre, area_id))
            
            cur.execute("""
                INSERT INTO evaluaciones (alumno_id, area_id, trimestre, sda_id, criterio_id, nivel, nota)
                VALUES (?, ?, ?, NULL, ?, ?, ?)
            """, (alumno_id, area_id, trimestre, criterio_id, media_nivel, media_nota))


@evaluacion_cuaderno_bp.route("/areas")
def listar_areas_por_etapa():
    """
    Lista todas las áreas de una etapa educativa.
    Parámetros: etapa_id (opcional)
    """
    etapa_id = request.args.get("etapa_id")
    db = get_db()
    cur = db.cursor()
    
    if etapa_id:
        areas = cur.execute("""
            SELECT id, nombre, tipo_escala, modo_evaluacion, activa
            FROM areas
            WHERE etapa_id = ? AND activa = 1
            ORDER BY nombre
        """, (etapa_id,)).fetchall()
    else:
        areas = cur.execute("""
            SELECT id, nombre, tipo_escala, modo_evaluacion, activa, etapa_id
            FROM areas
            WHERE activa = 1
            ORDER BY nombre
        """).fetchall()
    
    return jsonify([dict(a) for a in areas])
