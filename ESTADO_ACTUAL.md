# ESTADO DEL PROYECTO — APP_EVALUAR

**Versión:** `v1.2.8`
**Rama activa:** `master`
**Historial completo:** ver [CHANGELOG.md](CHANGELOG.md)

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

**Última actualización:** 12 Abril 2026 — Botones excursiones visibles en dark mode
