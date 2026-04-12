# CHANGELOG — APP_EVALUAR / Cuaderno del Tutor

Historial de cambios ordenado por versión. El estado actual del proyecto está en `ESTADO_ACTUAL.md`.

---

## [v1.2.7] — 12 Abril 2026
### Dark mode general: Excursiones, Alumnos, Diario
- Tarjetas de excursiones con fondo oscuro y texto blanco/gris claro
- Nombres de alumnos en blanco en lista de Alumnos
- Nombres y teléfonos visibles en Diario (blanco y gris claro)
- **Archivos:** `static/css/dark-mode.css`, `VERSION`, `version.py`

---

## [v1.2.6] — 12 Abril 2026
### Dark mode Autorizaciones: alumno seleccionado visible
- Alumno seleccionado ahora tiene fondo azul (#2563eb) con texto blanco (antes fondo blanco con texto oscuro)
- Contenedor de lista con fondo oscuro explícito
- **Archivos:** `static/css/dark-mode.css`, `VERSION`, `version.py`

---

## [v1.2.5] — 12 Abril 2026
### Dark mode en Autorizaciones
- Lista de alumnos ahora legible en modo oscuro (texto gris claro sobre fondo oscuro)
- Hover, seleccionado y badges adaptados al tema oscuro
- **Archivos:** `static/css/dark-mode.css`, `VERSION`, `version.py`

---

## [v1.2.4] — 12 Abril 2026
### Mejora de texto en Dashboard
- Tarjetas de autorizaciones anuales renombradas: "Sin Auto. Imágenes" → "Autorización Imágenes", "Sin Auto. Salidas" → "Autorización Salidas"
- Texto más positivo: refleja las autorizaciones gestionadas, no las pendientes
- **Archivos:** `static/index.html`, `static/ayuda.html`, `VERSION`, `version.py`

---

## [v1.2.3] — 12 Abril 2026
### Limpieza de documentación
- Eliminada sección "Tests por confirmar" de ESTADO_ACTUAL.md (tests que nunca se implementaron)
- **Archivos:** `ESTADO_ACTUAL.md`, `VERSION`, `version.py`

---

## [v1.2.2] — 11 Abril 2026
### Accesos rápidos Excursiones y Autorizaciones
- Tarjetas 🚌 Excursiones y ✍️ Autorizaciones añadidas al grid del Panel de Control, tras Horario
- Grid ampliado de 9 a 10 columnas para 2 filas exactas de 10 tarjetas
- **Archivos:** `static/index.html`, `VERSION`, `version.py`

---

## [v1.2.1] — 11 Abril 2026
### Fixes dashboard y documentación
- **Resumen anual filtrado por grupo**: `/api/autorizaciones/resumen-anual` filtra por `active_group_id` (antes contaba todos los alumnos del sistema)
- **Tarjetas autorizaciones**: cuando no hay pendientes muestran "✓ Al día" en verde
- **Ayuda**: nueva sección "🚌 Excursiones y Autorizaciones" con flujo completo, tipos anuales y chips de estado; sección Dashboard ampliada con todas las tarjetas
- **Archivos:** `routes/excursiones.py`, `static/index.html`, `static/ayuda.html`, `VERSION`, `version.py`

---

## [v1.2.0] — 11 Abril 2026
### Hardening de Seguridad
- **Eliminado fallback APP_PASSWORD**: ya no existe backdoor de login vía variable de entorno; autenticación solo vía base de datos con hash
- **CSRF protection activada en todos los blueprints**: eliminadas 6 exemptions (curricular, alumnos, criterios, evaluacion_actividades, evaluacion_cuaderno, reuniones); token CSRF requerido en todas las mutaciones
- **Frontend actualizado**: `reuniones.html` ahora carga `api.js` (interceptor CSRF global) y tiene meta tag `csrf-token`
- **Rate limiting en login**: bloqueo tras 5 intentos fallidos en 5 minutos; bloqueo de 10 minutos; logging de intentos
- **Expiración de sesiones**: sesiones permanentes con lifetime de 24h; auto-renovación en cada request para usuarios logueados
- **Headers de seguridad**: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Strict-Transport-Security
- **Archivos:** `routes/main.py`, `app.py`, `static/reuniones.html`, `VERSION`, `version.py`

---

## [v1.1.39] — 11 Abril 2026
### Autorizaciones: mejoras PDF, ficha alumno y dashboard
- **PDF grupos**: XML escaping correcto; se incluyen siempre grupos seleccionados + grupos escritos a mano (`grupos_extra`)
- **Autorizaciones anuales en ficha alumno**: chips interactivos en Datos Personales para fotos (interno/RRSS), salidas al entorno y LOPD; click cicla el estado; se persiste vía upsert
- **Dashboard**: grid 5 columnas (antes 4); tarjetas más compactas; 2 nuevas tarjetas "Sin Auto. Imágenes" y "Sin Auto. Salidas al entorno"
- **Nuevos endpoints**: `POST /api/autorizaciones/<id>/anual`, `GET /api/autorizaciones/resumen-anual`
- **Versión sincronizada**: `VERSION`/`version.py` actualizados a v1.1.39
- **Archivos:** `routes/excursiones.py`, `static/alumnos.html`, `static/index.html`, `VERSION`, `version.py`

---

## [v1.1.33] — 11 Abril 2026
### Mejora Tests Automatizados
- Corregido test `test_serve_uploads_404` (ahora verifica 302 redirect)
- Añadidos tests de seguridad: auth, rutas protegidas, CSRF, static files
- Añadidos tests de API: validación de schemas, auth, endpoints
- Añadidos tests de funcionalidad: alumnos, evaluación
- **Archivos:** `tests/test_security.py`, `tests/test_api.py`, `tests/test_uploads.py`

---

## [v1.1.32] — 10 Abril 2026
### Dashboard — Excursiones y Autorizaciones Pendientes
- Card "Excursiones Pendientes": muestra excursiones activas, redirige a `/excursiones`
- Card "Autorizaciones Pendientes": suma alumnos sin autorización firmada, redirige a `/autorizaciones`
- **Archivos:** `static/index.html`

---

## [v1.1.31]
### Modal Eventos de Hoy — Cerrar con Enter
- Foco automático al botón "Entendido" al abrir el modal
- `onkeydown` captura Enter para cerrar sin clic
- **Archivos:** `static/index.html`

---

## [v1.1.30]
### Diploma Biblioteca — Impresión A4 completa
- Diploma ocupa folio A4 completo (era medio folio)
- Tipografía escalada, `page-break-inside: avoid`, detección popup blocker
- **Archivos:** `static/biblioteca.html`, `version.py`, `VERSION`, `ESTADO_ACTUAL.md`

### Mejoras Reuniones de Ciclo
- PDF: tutor con curso ("Tutor/a 1º"), coordinador con nombre, asistentes sin corchetes
- Selector de ciclo en reuniones tipo CICLO
- Dropdown editable para rol de cada docente en Configuración > Reuniones
- **Archivos:** `routes/reuniones.py`, `static/reuniones.html`, `static/configuracion.html`

---

## [v1.1.29]
### Módulo Reuniones — Refactoring completo
- Wizard de nueva reunión con título dinámico, doble clic para avanzar
- Selección masiva con barra de acción, checkbox indeterminate, borrado en serie
- PDF por tipo: cabecera y firmas adaptadas por tipo de reunión (CICLO, CCP, FAMILIAS, etc.)
- Editar reuniones: wizard pre-rellenado con PUT `/api/reuniones/<id>`
- Configuración > Reuniones: roles actualizados, Ciclo Infantil añadido
- Nueva columna: `reuniones.familiar_asistente`
- Firma del tutor en grid de asistentes (fuzzy match)
- **Archivos:** `routes/reuniones.py`, `static/reuniones.html`, `static/configuracion.html`, `static/reuniones_plantillas.html`, `utils/db.py`

### Fixes adicionales (post-release v1.1.29)
- Fix versión en Panel de Control: `/api/version` → `/api/admin/version`
- Menú comedor: lightbox con zoom (rueda ratón, botones +/−, arrastrar, pellizco táctil)
- **Archivos:** `static/index.html`, `static/asistencia.html`

---

## [v1.1.28]
### Sistema de Actas de Incidencia
- Creación rápida desde Diario, campos: Fecha, Lugar, Profesor, Descripción, Firmante
- PDF con logos del centro y firma del tutor
- Selector de docentes, firma automática si no se especifica firmante
- Botón "Convertir a Acta" en historial de observaciones
- Nueva tabla: `actas_incidencias`
- **Archivos:** `routes/actas.py`, `static/diario.html`, `utils/db.py`

### Historial de Observaciones
- Botón "Historial" en Diario, filtros por texto/fechas/alumno/área
- Últimas 200 observaciones, layout con scroll
- Nuevo endpoint: `/api/observaciones/historial`
- **Archivos:** `routes/observaciones.py`, `static/diario.html`

### Banner de Actualización
- Banner verde en Panel de Control con actualización directa
- **Archivos:** `static/index.html`, `static/configuracion.html`

---

## [v1.1.27]
### Fix banner de actualizaciones
- "Omitir" usa `localStorage` (antes `sessionStorage`), persiste entre sesiones
- Comparación contra rama `master` en lugar de rama feature
- **Archivos:** `static/js/navigation.js`, `routes/admin.py`

---

## [v1.1.26]
### Mejoras UX/UI
- Modo Oscuro: toggle 🌙/☀️, persistencia localStorage, detección preferencia sistema
- Responsive móvil: media queries para 1024/768/480px, botones táctiles 44px mínimo
- Atajos de teclado: Ctrl+S, Ctrl+F, Esc, Ctrl+N
- **Archivos nuevos:** `static/css/dark-mode.css`, `static/js/dark-mode.js`, `static/js/shortcuts.js`

---

## [v1.1.25]
- Fix Enter en campo devolución biblioteca
- Fix doble tick verde al guardar préstamo

---

## [v1.1.24]
- Mensaje de error detallado al borrar criterios con evaluaciones asociadas

---

## [v1.1.22]
- Medias SDA/Área en tiempo real (cross-mode POR_SA ↔ POR_ACTIVIDADES)
- Fix editar criterio: error de validación `activo` boolean vs int
- Fix rellenador masivo POR_CRITERIOS_DIRECTOS escribía en tabla errónea

---

## [Anteriores a v1.1.22]
### Sistema Dual de Evaluación (merge feature/refactor-evaluacion-curricular → master, 6 Abril 2026)
- Modos: POR_ACTIVIDADES | POR_SA | POR_CRITERIOS_DIRECTOS
- Etapas: Infantil (detección automática) | Primaria
- Escalas: NI/EP/CO | PA/AD/MA | NUMÉRICA 1–4
- Rellenador Masivo y Borrado Masivo en rejilla
- Importador SDA con columna `Criterios_Vinculados`, fix COLLATE NOCASE
- Sistema de versiones: `VERSION` + `release.sh`
- Generador SDA con IA (Claude / ChatGPT / Gemini)
- Módulos estables: Dashboard (18 tarjetas), Biblioteca, Lectura, Reuniones, Biblioteca, Cumpleaños, Horario
- Fix rejilla vacía sin SDAs en trimestre
- Fix Cuaderno de Evaluación vacío (error silencioso JS)
- Fix firma del tutor en Acta
- Fix CSRF bloqueaba DELETE en criterios
