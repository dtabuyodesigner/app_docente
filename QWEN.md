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
- **APP_EVALUAR - Pendientes Actas (para próximo día):**
1. BUG: No aparecen nombres de profesores en checkboxes (endpoint /api/actas/equipo_docente devuelve vacío o undefined)
2. BUG: Campo firmante no se rellena con nombre del tutor
3. FEATURE: PDF del acta necesita saltos de párrafo entre puntos (1., 2., 3.) en la descripción para mejor legibilidad
- **PENDIENTE: Cosas a probar después de cada sesión** (fecha: 2026-04-08):

## COSAS A PROBAR (8 abril 2026)

### 1. ACTA DE CICLO - Corchetes en Asistentes y Firma del Tutor
**Archivos modificados:** `routes/informes.py` (líneas ~1743-1806)

**Problema reportado:**
- En el PDF del acta de ciclo, los nombres de asistentes aparecen con corchetes: `["Noelia Socas Pimentel","Daniel Tabuyo de las Peñas"]`
- La firma del tutor pone solo "Tutor/a" en vez de "Tutor/a 1º" o "Tutor/a 1ºA"

**Cambios realizados:**
- Reemplazado el parseo simple de newlines por función `parsear_lista()` que maneja:
  - JSON arrays: `["nombre1", "nombre2"]`
  - Listas entre corchetes: `["nombre1","nombre2"]` (sin parsear JSON válido)
  - Listas separadas por newlines
- Añadido logging debug con `[DEBUG]` para ver el formato real de los datos
- Obtenido `grupo_curso` de la tabla grupos para mostrar en firma del tutor
- Si el firmante es identificado como tutor, ahora muestra "Tutor/a {curso}" (ej: "Tutor/a 1ºA")

**PENDIENTE DE PROBAR:**
1. Generar acta de ciclo desde Evaluación → Informes
2. Revisar logs del servidor para ver output `[DEBUG]` y confirmar formato de datos
3. Verificar que PDF ya NO muestra corchetes en asistentes
4. Verificar que firma del tutor muestra el curso (ej: "Tutor/a 1º")
5. Si persisten los corchetes, ajustar `parsear_lista()` según formato real visto en logs

### 2. DARK MODE - Visibilidad en modo oscuro
**Archivos modificados:** `static/reuniones.html` (línea ~434), `static/css/dark-mode.css`

**Problema reportado:**
- Calendario en reuniones.html no se ve bien en modo oscuro (fondo blanco hardcoded)

**Cambios realizados:**
- Eliminado `background: white` inline del `#calendarContainer` en reuniones.html
- Añadidas reglas extensivas a dark-mode.css:
  - FullCalendar components (`.fc`, `.fc-toolbar`, `.fc-button`, etc.)
  - Divs/sections con `background: white` inline (attribute selectors `[style*="..."]`)
  - Modales con fondos inline
  - Tabs, attendees grids, meeting cards
  - Botones y selects con fondos blancos inline
  - Cajas de advertencia/info con fondos claros

**PENDIENTE DE PROBAR:**
1. Activar modo oscuro (icono luna en navbar)
2. Navegar a Reuniones → verificar calendario visible
3. Probar modales en modo oscuro
4. Probar otras páginas (Informes, Configuración, Alumnos) en modo oscuro
5. Si algún elemento sigue mal, añadir selector CSS específico a dark-mode.css

### 3. GIT - Commit pendiente
**TODO:**
1. Crear rama: `git checkout -b feature/fix-acta-ciclo-y-dark-mode`
2. Commit cambios: `routes/informes.py`, `static/reuniones.html`, `static/css/dark-mode.css`
3. Mensaje sugerido: `Fix: Acta de ciclo sin corchetes + Dark mode completo`
4. NO hacer merge a main hasta probar en navegador

