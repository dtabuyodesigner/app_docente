## Qwen Added Memories
- Proyecto APP_EVALUAR: Implementado sistema dual de evaluación (Opción C) con soporte para Infantil/Primaria. Commit 6fe9470 en rama feature/refactor-evaluacion-curricular. Archivos clave: routes/evaluacion_cuaderno.py (endpoint unificado), static/evaluacion.html (UI adaptativa), static/ayuda.html (documentación). Pendiente: pruebas en navegador y merge a main cuando esté estable.
- APP_EVALUAR - Pendientes para próximo día:
1. BUG: Gestión de Criterios no borra criterios (revisar evaluacion.html y routes/criterios_api.py)
2. FEATURE: Rellenador masivo para Infantil con botones EP/CO o AD/MA en Clase de Hoy (adaptar rellenarTodos() de evaluacion.html a clase_hoy.html)
- APP_EVALUAR - Bugs pendientes:
1. Gestión de Criterios no borra (evaluacion.html + criterios_api.py)
2. Cuaderno de Evaluación no muestra nada (revisar endpoint /api/evaluacion/cuaderno y cargarCuadernoUnificado())
3. Feature: Rellenador masivo Infantil en Clase de Hoy
- APP_EVALUAR - Bugs pendientes:
1. Gestión de Criterios no borra (evaluacion.html + criterios_api.py)
2. Cuaderno de Evaluación no muestra nada (revisar endpoint /api/evaluacion/cuaderno y cargarCuadernoUnificado())
3. Informe de Acta - Firmas no muestra firma del tutor automáticamente desde Logos (informes.py)
4. Feature: Rellenador masivo Infantil en Clase de Hoy
- **FEATURE COMPLETADO**: Sistema de Actas de Incidencia desde el Diario. Permite crear actas formales con fecha, lugar, profesor implicado, descripción y firma. Genera PDF automático con logos y firma del tutor si está configurada. Tabla `actas_incidencias` añadida a la BD. Archivos: `routes/actas.py`, `static/diario.html`.
