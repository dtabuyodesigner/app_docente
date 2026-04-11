# ESTADO DEL PROYECTO — APP_EVALUAR

**Versión:** `v1.2.1`
**Rama activa:** `master`
**Historial completo:** ver [CHANGELOG.md](CHANGELOG.md)

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

### Tests por confirmar

| Test | Descripción | Estado |
|------|-------------|--------|
| Test 8 | Rejilla POR_CRITERIOS_DIRECTOS → botones EP/CO se iluminan y guardan en `evaluacion_criterios` | ⬜ Pendiente |
| Test 9 | Rellenar EP en rejilla POR_CRITERIOS_DIRECTOS → medias del área se recalculan | ⬜ Pendiente |
| Test 10 | Clic en píldora activa en rejilla → la borra de `evaluacion_criterios` | ⬜ Pendiente |
| Test 11 | Evaluar alumno en POR_ACTIVIDADES → cambiar a POR_SA → criterios evaluados aparecen | ⬜ Pendiente |
| Test 12 | Editar criterio → Guardar → sin error de validación | ⬜ Pendiente |
| Test 13 | Seleccionar todo en lista criterios → Borrar → borra solo los sin evaluaciones | ⬜ Pendiente |

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

**Última actualización:** 11 Abril 2026 — Hardening de Seguridad (v1.2.0)
