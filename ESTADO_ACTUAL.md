# ESTADO DEL PROYECTO — APP_EVALUAR

**Versión:** `v1.4.0`
**Rama activa:** `master`
**Historial completo:** ver [CHANGELOG.md](CHANGELOG.md)

---

## ✅ Acceso desde móvil/tablet por WiFi local (v1.4.0)

**Fecha:** 13 de Abril 2026 — 23:00

### Qué se hizo
- Servidor escucha en `0.0.0.0` (todas las interfaces) en vez de solo `127.0.0.1`
- Muestra IP local al arrancar para acceder desde móvil/tablet
- Funciones `get_local_ip()` en `desktop.py` y `app.py`
- `start_app.sh` también muestra la IP de red local
- App accesible desde cualquier dispositivo en la misma red WiFi

### Cómo usar
1. Arrancar la app con `./start_app.sh` o `desktop.py`
2. Ver la IP que muestra (ej: `http://192.168.1.42:5000`)
3. Abrir esa URL en el navegador del móvil/tablet conectado al mismo WiFi

### Archivos modificados
- `app.py` — bind a `0.0.0.0`, mostrar IP local
- `desktop.py` — función `get_local_ip()`, bind a `0.0.0.0`, mostrar URLs
- `start_app.sh` — mostrar IP de red local
- `VERSION`, `version.py` — bump a v1.4.0

---

## ✅ Dark mode Asistencia: textos y botones legibles (v1.3.1)

**Fecha:** 13 de Abril 2026 — 22:45

### Qué se hizo
- Textos en botones "Presente", "Retraso", "Justif.", "No Justif." ahora blancos en modo oscuro
- Botones "Encargado", "Nota", "Ver" con texto blanco y fondo oscuro
- Tarjetas de estado con fondos oscuros adaptados (verde, naranja, azul, rojo oscuros)
- Tarjeta "Encargado del día" con gradiente amarillo oscuro (no brillante)
- Stat cards del dashboard con fondo oscuro y títulos legibles
- Badge "Encargado" con fondo oscuro y texto dorado

### Archivos modificados
- `static/css/dark-mode.css` — reglas para `.btn-status`, `.btn-icon`, `.card.presente/retraso/justificada/nojustificada`, `.card.encargado-hoy`, `.stat-card`
- `VERSION`, `version.py` — bump a v1.3.1

---

## ✅ Auditoría de Seguridad Completa + Frontend Audit (v1.3.0)

**Fecha:** 13 de Abril 2026 — 16:50

### Qué se hizo — Seguridad (15 fixes)

**Críticos (2):**
- `SECRET_KEY` obligatoria — eliminado fallback `"dev-key-change-in-prod"`; ahora falla si no hay env var
- Restore backup externo valida esquema SQLite + integridad antes de reemplazar la BD

**Altos (4):**
- Debug mode desactivado por defecto (`FLASK_DEBUG=true` para activar)
- Eliminados endpoints `emergency_reset` y `exit` de `routes/main.py`
- Backup restore: validación de tablas esenciales + `PRAGMA integrity_check` antes de reemplazar

**Medios (6):**
- `secure_filename` en uploads (configuración, alumnos, horario, comedor)
- Header `Content-Security-Policy` añadido a `app.py`
- `MAX_CONTENT_LENGTH` 5MB configurado
- `SESSION_COOKIE_SECURE = True`
- Auth middleware bypass `.csv` restringido a `/static/`
- Error messages genéricos (no `str(e)`) en `routes/main.py`

**Bajos (3):**
- Rate limiting en recuperación de contraseña (5 intentos/5min, bloqueo 10min)
- Enumeración de usuarios prevenida (misma respuesta siempre)
- `requests>=2.32.2` (CVE-2024-35195)

### Qué se hizo — Frontend (3 fixes)

**Críticos:**
- Viewport meta añadido en 8 páginas (evaluacion, programacion, horario, rubricas, tareas, diario, configuracion, alumnos)

**Altos:**
- `debug.js` creado: wrapper `dbg.log/warn/error` silencioso por defecto
- `window.DEBUG = false` en `navigation.js` — console.log desactivados en producción
- `lang="es"` añadido en 4 páginas (evaluacion, evaluar_todo, progreso_clase, clase_hoy)

### Archivos modificados
- `app.py` — SECRET_KEY obligatoria, CSP, MAX_CONTENT_LENGTH, SESSION_COOKIE_SECURE, auth bypass csv
- `routes/main.py` — eliminados emergency_reset/exit, rate limiting recovery, error genérico
- `routes/admin.py` — backup restore con validación de esquema + integridad
- `routes/configuracion.py` — secure_filename en uploads
- `routes/alumnos.py` — secure_filename + check grupo en ficha alumno
- `routes/horario.py`, `routes/comedor.py` — secure_filename
- `requirements.txt` — requests>=2.32.2
- `static/js/debug.js` — **nuevo**: wrapper logging condicional
- `static/js/navigation.js` — window.DEBUG = false
- `static/` — viewport meta en 8 HTML, lang="es" en 4 HTML

### Qué se eliminó
- `QWEN.md` — fusionado en INSTRUCCIONES.md
- `CLAUDE.md` — fusionado en INSTRUCCIONES.md
- `static/cuaderno_evaluacion.html` — integrado como pestaña en evaluacion.html
- Endpoints `emergency_reset` y `exit` — eliminados por seguridad

### INSTRUCCIONES.md actualizado
- Fusionado contenido de CLAUDE.md (workflow git, versiones, checklist merge) + contenido original (reglas generales, CSV, agentes)
- Archivo único de referencia para todos los asistentes de código

---

## ✅ Auditoría Frontend — Pendiente para próximo día

**Rama:** `fix/frontend-audit` (no mergeada a master aún)

| # | Fix | Estado | Esfuerzo |
|---|-----|--------|----------|
| 1 | ✅ Viewport meta en 8 páginas | **HECHO** | 5 min |
| 2 | Eliminar `:root` inline de 27 páginas | Pendiente | 30 min |
| 3 | Reemplazar `background: white` por `var(--bg-page)` | Pendiente | 1h |
| 4 | ✅ Wrapper `debug.js` + `window.DEBUG=false` | **HECHO** | 10 min |
| 5 | ✅ `lang="es"` en 4 páginas | **HECHO** | 5 min |

**Pendientes adicionales:**
- CDN sin fallback (chart.js, fullcalendar)
- `catch (e) {}` vacíos — feedback al usuario
- Aria-labels básicos en formularios y modales
- Transición `*` en dark-mode.css → solo elementos interactivos

---

## ✅ Auditoría de Seguridad — Completada

| Severidad | Total | Arreglados | Pendientes |
|-----------|-------|------------|------------|
| 🔴 Crítico | 2 | 2 | 0 |
| 🟠 Alto | 4 | 4 | 0 |
| 🟡 Medio | 6 | 6 | 0 |
| 🟢 Bajo | 4 | 3 | 1 (requests outdated) |
| ℹ️ Info | 2 | 0 | 0 |

**Pendientes de bajo riesgo:**
- PII en Sentry (solo relevante si se expone a internet)
- Magic bytes en uploads (app local, un solo usuario)

---

## ✅ Todos los pendientes resueltos

**Fecha:** 13 de Abril 2026

Los siguientes pendientes de QWEN.md están **confirmados como hechos**:

| # | Item | Estado |
|---|------|--------|
| 1 | Gestión de Criterios no borra criterios | ✅ Arreglado (schema EXCLUDE) |
| 2 | Cuaderno de Evaluación no muestra nada | ✅ Arreglado (integrado como pestaña) |
| 3 | Actas - Firmas no muestra tutor automáticamente | ✅ Hecho |
| 4 | Rellenador masivo Infantil en Clase de Hoy | ✅ Hecho |
| 5 | Commit feature/fix-acta-ciclo-y-dark-mode | ✅ Hecho |

---

## ✅ Dark mode Excursiones: botones de acción visibles (v1.2.8)

**Fecha:** 12 de Abril 2026 — 15:45

### Qué se hizo
- Botones de acción en tarjetas de excursiones ("Editar", "Autorización", "Cerrar") ahora visibles en dark mode
- Fondo gris oscuro, borde visible, texto blanco
- Iconos SVG también adaptados al tema oscuro

### Archivos modificados
- `static/css/dark-mode.css` — reglas para `.card-actions`, `.btn-outline`, `.btn-sm`
- `VERSION`, `version.py` — bump a v1.2.8

---

## ✅ Dark mode general: Excursiones, Alumnos y Diario (v1.2.7)

**Fecha:** 12 de Abril 2026 — 15:30

### Qué se hizo
- **Excursiones**: tarjetas con fondo oscuro, títulos en blanco, metadatos en gris claro
- **Alumnos**: nombres en blanco en la lista de alumnos
- **Diario**: nombres de alumnos en blanco, teléfonos en gris claro visible

### Archivos modificados
- `static/css/dark-mode.css` — reglas para `.excursion-card`, `.alumno-item`, diario
- `VERSION`, `version.py` — bump a v1.2.7

---

## ✅ Dark mode Autorizaciones: alumno seleccionado con fondo azul (v1.2.6)

**Fecha:** 12 de Abril 2026 — 15:10

### Qué se hizo
- Corregido fondo del alumno seleccionado: ahora fondo azul (#2563eb) con texto blanco
- Contenedor `.lista-alumnos` con fondo oscuro explícito
- Badge del seleccionado también adaptado (fondo semitransparente, texto blanco)

### Archivos modificados
- `static/css/dark-mode.css` — reglas mejoradas para `.alumno-item`, `.activo`, `.badge-count`
- `VERSION`, `version.py` — bump a v1.2.6

---

## ✅ Dark mode en Autorizaciones: lista de alumnos legible (v1.2.5)

**Fecha:** 12 de Abril 2026 — 15:00

### Qué se hizo
- Añadidas reglas CSS en `dark-mode.css` para `.alumno-item` en modo oscuro
- Texto de alumnos ahora visible (gris claro `#e0e0e0` sobre fondo oscuro)
- Hover y seleccionado con fondos adaptados al tema oscuro
- Badge de conteo con fondo oscuro y texto claro

### Archivos modificados
- `static/css/dark-mode.css` — reglas para `.alumno-item`, hover, activo y badges
- `VERSION`, `version.py` — bump a v1.2.5

---

## ✅ Texto tarjetas Dashboard: "Autorización" en lugar de "Sin Auto." (v1.2.4)

**Fecha:** 12 de Abril 2026 — 14:30

### Qué se hizo
- Cambiadas etiquetas de tarjetas en Dashboard: "Sin Auto. Imágenes" → **"Autorización Imágenes"**, "Sin Auto. Salidas" → **"Autorización Salidas"**
- Mensaje más positivo y claro: muestra las autorizaciones gestionadas, no las pendientes
- Actualizada ayuda (`ayuda.html`) para reflejar el nuevo nombre

### Archivos modificados
- `static/index.html` — títulos de tarjetas de autorizaciones anuales
- `static/ayuda.html` — documentación actualizada
- `VERSION`, `version.py` — bump a v1.2.4

---

## ✅ Limpieza de documentación: tests pendientes eliminados (v1.2.3)

**Fecha:** 12 de Abril 2026 — 14:00

### Qué se hizo
- Eliminada sección "Tests por confirmar" de ESTADO_ACTUAL.md (7 tests de evaluación que nunca se implementaron como tests automatizados)
- Documentación actualizada para reflejar el estado real del proyecto

### Archivos modificados
- `ESTADO_ACTUAL.md` — eliminada tabla de tests pendientes
- `VERSION`, `version.py` — bump a v1.2.3

---

## ✅ Fix PDF autorización — formato de grupos (v1.2.3)

**Fecha:** 11 de Abril 2026 — 18:45

### Qué se hizo
- `grupos_extra` del campo libre ahora se divide por comas en grupos individuales antes de formatear
- Lista de grupos con formato español: "A y B" para 2 grupos, "A, B y C" para 3 o más
- Rama: `fix/pdf-grupos-formato` → merge a `master`

### Archivos modificados
- `routes/excursiones.py` — función `fmt_grupos()` y split de `grupos_extra`

---

## ✅ Accesos rápidos Excursiones y Autorizaciones (v1.2.2)

**Fecha:** 11 de Abril 2026 — 18:30

### Qué se hizo
- Añadidas tarjetas **🚌 Excursiones** y **✍️ Autorizaciones** al grid de accesos rápidos del Panel de Control, posicionadas justo después de Horario
- Grid ampliado de 9 a 10 columnas (2 filas × 10 tarjetas); breakpoint 1200px ajustado a 5 columnas
- Rama: `feat/accesos-rapidos-excursiones` → merge a `master`

### Archivos modificados
- `static/index.html` — nuevas tarjetas en el grid de navegación, CSS grid 9→10 columnas
- `VERSION`, `version.py` — bump a v1.2.2

---

## ✅ Fixes dashboard y ayuda (v1.2.1)

**Fecha:** 11 de Abril 2026 — tarde

### Qué se hizo
- **Tarjetas autorizaciones anuales**: cuando no hay pendientes muestran "✓ Al día" en verde en lugar del número 0
- **Resumen anual filtrado por grupo**: el endpoint `/api/autorizaciones/resumen-anual` ahora filtra por `active_group_id` de la sesión, igual que el resto del dashboard
- **Ayuda actualizada**: nueva sección "Excursiones y Autorizaciones" con descripción completa del flujo; sección Dashboard ampliada con todas las tarjetas

### Archivos modificados
- `routes/excursiones.py` — filtro por grupo activo en resumen-anual
- `static/index.html` — estado visual "✓ Al día" en tarjetas de autorizaciones
- `static/ayuda.html` — nueva sección excursiones, dashboard actualizado
- `VERSION`, `version.py` — bump a v1.2.1

---

## ✅ Hardening de Seguridad (v1.2.0)

**Fecha:** 11 de Abril 2026 — sesión actual

### Qué se hizo
- **Eliminado fallback APP_PASSWORD**: borrado el backdoor de login que permitía acceso con variable de entorno `APP_PASSWORD`; autenticación solo vía DB con hash
- **CSRF protection global**: eliminadas las 6 exemptions de blueprints (curricular, alumnos, criterios, evaluacion_actividades, evaluacion_cuaderno, reuniones); todas las mutaciones requieren token CSRF
- **reuniones.html actualizado**: añadido meta tag `csrf-token` y carga de `api.js` para interceptor CSRF global
- **Rate limiting en login**: bloqueo tras 5 intentos fallidos consecutivos en ventana de 5 minutos; bloqueo de 10 minutos; logging de seguridad
- **Expiración de sesiones**: sesiones con lifetime de 24h de inactividad; auto-renovación en cada request
- **Headers de seguridad**: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Strict-Transport-Security

### Archivos modificados
- `routes/main.py` — eliminado fallback APP_PASSWORD, añadido rate limiting, validación CSRF manual para login
- `app.py` — CSRF protection global, expiración de sesiones (24h), headers de seguridad, auto-renovación de sesión
- `static/reuniones.html` — añadido meta csrf-token y api.js interceptor
- `VERSION` — actualizado a 1.2.0
- `version.py` — actualizado a v1.2.0

---

## ✅ Autorizaciones: mejoras PDF, ficha alumno y dashboard (v1.1.39)

**Fecha:** 11 de Abril 2026 — sesión actual

### Qué se hizo
- **1.1 PDF grupos**: corrección de XML escaping + lógica robusta para incluir siempre grupos_extra junto a los grupos seleccionados en el PDF de autorización
- **1.2 Autorizaciones anuales en ficha del alumno**: sección "Autorizaciones anuales" en Datos Personales con chips clickeables (fotos_interno, fotos_rrss, salidas_entorno, datos/LOPD) que ciclan entre Pendiente → Autorizada → No autoriza. Endpoint `/api/autorizaciones/<id>/anual` para upsert
- **1.3 Dashboard**: grid ampliado de 4 a 5 columnas; tarjetas más compactas (padding reducido); añadidas 2 tarjetas nuevas: "Sin Auto. Imágenes" y "Sin Auto. Salidas". Endpoint `/api/autorizaciones/resumen-anual` para conteos
- **Versión**: sincronizado de v1.1.33 a v1.1.39 (incluye cambios v1.1.34–1.1.38 ya en git que no tenían VERSION actualizado)

### Archivos modificados
- `routes/excursiones.py` — fix PDF XML escaping, nuevos endpoints anual y resumen-anual
- `static/alumnos.html` — sección autorizaciones anuales en ficha
- `static/index.html` — grid 5 col, tarjetas compactas, 2 nuevas tarjetas
- `VERSION`, `version.py` — v1.1.39

---

## ✅ ÚLTIMO CAMBIO — Mejora Tests Automatizados (v1.1.33)

**Fecha:** 11 Abril 2026 — 18:35

### Qué se hizo
- Corregido test `test_serve_uploads_404` (ahora verifica 302 redirect)
- Añadidos tests de seguridad: auth, rutas protegidas, CSRF, static files
- Añadidos tests de API: validación de schemas, auth, endpoints
- Añadidos tests de funcionalidad: alumnos, evaluación
- Tests pasan: 20 passed, 1 skipped

### Archivos modificados
- `tests/test_uploads.py` — corregido test fallido
- `tests/test_security.py` — nuevos tests de seguridad
- `tests/test_api.py` — nuevos tests de API y funcionalidad

---

## ✅ ÚLTIMO CAMBIO — Dashboard: Excursiones y Autorizaciones Pendientes (v1.1.32)

**Fecha:** 10 Abril 2026

### Qué se hizo
- Card "Excursiones Pendientes": muestra excursiones activas, redirige a `/excursiones`
- Card "Autorizaciones Pendientes": suma alumnos sin autorización firmada, redirige a `/autorizaciones`
- Cuenta solo excursiones con `requiere_autorizacion=1` y `autorizado=0`

### Archivos modificados
- `static/index.html` — cards nuevas + función `loadExcursionesPendientes()`

---

## 📋 PENDIENTE

### 🔒 Seguridad — Auditoría completa (auditoría KILO + verificación propia)

> Fecha auditoría: 11 Abril 2026. Los falsos positivos de SQLi (24 puntos) fueron descartados: todos los f-strings construyen placeholders `?`, los valores siempre van parametrizados.

| # | Severidad | Problema | Archivos | Fix necesario |
|---|-----------|----------|----------|---------------|
| 1 | 🔴 CRITICAL | **Restore backup path traversal**: `filename` sin validar permite escribir fuera de `backups/` | `routes/admin.py` | `os.path.realpath()` + `os.path.commonpath()` para validar que el path queda dentro de `BACKUP_DIR` |
| 2 | 🟠 HIGH | **CSRF faltante en Excursiones y Autorizaciones**: ambos HTML no tienen meta csrf-token ni cargan api.js; POST/PUT/DELETE/PATCH fallarán con CSRF global | `static/excursiones.html`, `static/autorizaciones.html` | Añadir `<meta name="csrf-token">` y `<script src="/static/js/api.js">` (mismo patrón que reuniones.html) |
| 3 | 🟠 HIGH | **Password "1234" hardcodeado** en emergency reset | `routes/main.py`, `scripts/recover_admin.py` | Generar contraseña aleatoria segura en vez de "1234" fijo |
| 4 | 🟡 MEDIUM | **IDOR Excursiones**: cualquier usuario autenticado puede modificar/borrar excursiones de otros profesores | `routes/excursiones.py` | Verificar que el usuario es creador o pertenece al grupo |
| 5 | 🟡 MEDIUM | **IDOR Reuniones**: mismo problema | `routes/reuniones.py` | Verificar ownership |
| 6 | 🟡 MEDIUM | **IDOR Informe alumno**: acceso a PDF de cualquier alumno sin verificar tutoría | `routes/informes.py` | Verificar que el alumno pertenece a grupo del profesor |
| 7 | 🟢 LOW | **SECRET_KEY fallback hardcodeado** ("dev-key-change-in-prod") | `app.py` | Log warning si no hay SECRET_KEY en .env; considerar fallar si no existe |
| 8 | 🟢 LOW | **File upload sin validación de magic bytes**: solo se valida extensión, no contenido real | `routes/configuracion.py` | Validar magic bytes de imagen (PNG/JPG/GIF/WebP) |
| 9 | 🟢 LOW | **PII en Sentry**: `send_default_pii=True` envía datos de sesión a Sentry | `app.py` | Poner a `False` o eliminar si Sentry no es necesario |
| 10 | 🟢 LOW | **Debug print() en producción**: `_sync_auto_to_excursion` tiene prints de debug | `routes/excursiones.py` | Reemplazar por `security_logger.info()` |

### Backlog de mejoras
- Ver [Mejoras Pendientes — Backlog](.claude/projects/-home-danito73-Documentos-APP-EVALUAR/memory/project_mejoras_pendientes.md)
- Plan Reuniones (Claustro, CCP, Comisiones): schema, CRUDs y auto-populate pendiente
- Enviar CSVs T3 a Pilar: `data/pilar_t3_DEE/CRR/CA.csv` listos, falta compartir

---

## 🧪 CÓMO ARRANCAR

```bash
cd /home/danito73/Documentos/APP_EVALUAR
./start_app.sh
```

Abrir: `http://localhost:5000`

---

## 🔗 COMANDOS ÚTILES

```bash
# Estado del repo
git status
git log --oneline -5

# Nuevo release (bump versión + commit + push)
./release.sh

# Tests
python -m pytest tests/
```

---

## 📚 DOCUMENTACIÓN

| Documento | Descripción |
|-----------|-------------|
| `CHANGELOG.md` | Historial completo de cambios por versión |
| `SISTEMA_DUAL_EVALUACION.md` | Arquitectura técnica completa |
| `EVALUACION_INFANTIL.md` | Guía específica Infantil |
| `NOMENCLATURA_CRITERIOS.md` | Nomenclatura y vinculación de criterios |
| `/ayuda` (en app) | Ayuda integrada |

---

**Última actualización:** 13 Abril 2026 — v1.4.0: Acceso móvil/tablet por WiFi local
