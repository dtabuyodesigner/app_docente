# ESTADO DEL PROYECTO — APP_EVALUAR

**Versión:** `v1.1.33`
**Rama activa:** `fix/test-uploads-404-y-mas-tests`
**Historial completo:** ver [CHANGELOG.md](CHANGELOG.md)

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

**Última actualización:** 11 Abril 2026 — Mejora tests automatizados
