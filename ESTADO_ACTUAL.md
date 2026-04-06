# 📍 ESTADO DEL PROYECTO - APP_EVALUAR

**Fecha:** 6 de Abril 2026
**Versión:** `v1.1.27` (pendiente release)
**Último Commit:** `8a1a35c` — Fix dropdown legible en modo oscuro
**Rama activa:** `master`

---

## ✅ LO COMPLETADO EN v1.1.27

### Fix banner de actualizaciones (2)
- **Omitir versión persistente:** botón "Omitir" ahora usa `localStorage` en lugar de `sessionStorage`, guarda la versión omitida y no vuelve a mostrar el banner hasta que haya una versión nueva
- **Comparar contra rama correcta:** cambiado `feature/refactor-evaluacion-curricular` → `master` para comparar versiones, el banner ya no muestra `v1.1.20` incorrectamente
- **Archivos modificados:** `static/js/navigation.js`, `routes/admin.py`

---

## ✅ LO COMPLETADO EN v1.1.26

### Mejora UX/UI (7)
- **Modo Oscuro:** Toggle 🌙/☀️ en navbar, persistencia localStorage, detección automática de preferencia del sistema
- **Fix dropdown:** Texto claro (#e0e0e0) sobre fondo oscuro (#2a2a3d) en menús desplegables
- **Responsive Móvil:** Media queries para tablet (1024px), móvil (768px) y móvil pequeño (480px), botones táctiles 44px mínimo
- **Atajos de Teclado:** Ctrl+S (guardar), Ctrl+F (buscar), Esc (cerrar modal), Ctrl+N (nuevo)
- **Archivos nuevos:** `static/css/dark-mode.css`, `static/js/dark-mode.js`, `static/js/shortcuts.js`

---

## ✅ MERGE COMPLETADO — 6 Abril 2026

La rama `feature/refactor-evaluacion-curricular` ha sido integrada en `master` y subida a GitHub.

- **99 ficheros modificados** — sin conflictos
- **Repositorio remoto actualizado:** `origin/master` en `82916b6`
- **Rama feature:** puede mantenerse o eliminarse (`git branch -d feature/refactor-evaluacion-curricular`)

---

## ✅ LO QUE ESTÁ EN MASTER AHORA

### Sistema Dual de Evaluación
- **Modos:** POR_ACTIVIDADES | POR_SA | POR_CRITERIOS_DIRECTOS
- **Etapas:** Infantil (detección automática) | Primaria
- **Escalas:** NI/EP/CO | PA/AD/MA | NUMÉRICA 1–4
- **Rellenador Masivo (⚡):** rellena todos los criterios visibles en rejilla
- **Borrado Masivo (🗑️):** limpia evaluaciones para recálculo de medias
- **Cross-mode:** evaluaciones visibles desde cualquier modo (POR_SA ↔ POR_ACTIVIDADES)

### Importador SDA
- Formato CSV definitivo con columna `Criterios_Vinculados`
- Fix COLLATE NOCASE en búsqueda de área
- Crea criterios vinculados automáticamente si no existen en la BD
- Aviso UTF-8 para Windows

### Sistema de Versiones y Release
- Archivo `VERSION` como fuente de verdad
- Script `release.sh`: bump automático (patch/minor/major), commit y push interactivo
- Badge de versión dinámico en el Panel de Control (`/api/version`)

### Módulo Biblioteca
- Fix Enter en campo devolución
- Fix doble tick verde al guardar

### Otros módulos estables
- Dashboard con 18 tarjetas
- Cuaderno de Evaluación unificado (`/api/evaluacion/cuaderno`)
- Encargados con estrella iluminada y modos de selección
- Sistema de notificación de actualizaciones (banner + badge)
- Autoarranque Windows
- Generador SDA con IA (Claude / ChatGPT / Gemini)
- Cumpleaños, Horario, Reuniones, Biblioteca, Lectura
- Informes con firma de tutor automática en Acta

---

## 🐛 BUGS CORREGIDOS (historial reciente)

| Bug | Versión Fix |
|-----|-------------|
| Enter en devolución biblioteca + doble tick | v1.1.25 |
| Mensaje de error detallado al borrar criterios con evaluaciones | v1.1.24 |
| Medias SDA/Área en tiempo real (cross-mode) | v1.1.22 |
| Editar criterio — error de validación `activo` boolean vs int | v1.1.22 |
| Rejilla POR_CRITERIOS_DIRECTOS — rellenador masivo escribía en tabla errónea | v1.1.22 |
| Rejilla vacía si no hay SDAs en el trimestre seleccionado | anterior |
| Cuaderno de Evaluación vacío (error silencioso JS) | anterior |
| Firma del tutor no aparecía en Acta | anterior |
| CSRF bloqueaba DELETE en criterios | anterior |

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

#### 🔄 En desarrollo
- Ver [Mejoras Pendientes — Backlog](memory/project_mejoras_pendientes.md)
- Plan Reuniones (Claustro, CCP, Comisiones): schema, CRUDs y auto-populate pendiente
- Enviar CSVs T3 a Pilar: `pilar_t3_DEE/CRR/CA.csv` listos, falta compartir

#### 💡 Ideas para próximas versiones

**Módulo de Reuniones**
- CRUD completo para reuniones (Claustro, CCP, Comisiones)
- Actas y resúmenes automáticos
- Auto-populate con datos del grupo/área

**Exportación/Importación masiva**
- Exportar evaluaciones a Excel/CSV por trimestre
- Backup automático de la base de datos
- Migración entre cursos académicos

**Estadísticas y gráficas**
- Panel de estadísticas por alumno/grupo
- Gráficas de progreso trimestral
- Detección automática de alumnos en riesgo

**Comunicación con familias**
- Generación automática de informes para padres
- Envío de notificaciones (email/SMS)
- Portal de familias (solo lectura)

**Mejoras en Biblioteca**
- Código de barras/QR para préstamos rápidos
- Reserva de libros online
- Historial de lectura por alumno con gráficas

**Automatizaciones**
- Rellenado automático de evaluaciones pendientes
- Sugerencias de criterios basadas en actividades
- Recordatorios de plazos de evaluación

**UX/UI**
- Modo oscuro
- App móvil responsive
- Atajos de teclado

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

# Nuevo release
./release.sh

# Eliminar rama feature si ya no hace falta
git branch -d feature/refactor-evaluacion-curricular
git push origin --delete feature/refactor-evaluacion-curricular
```

---

## 📚 DOCUMENTACIÓN DISPONIBLE

| Documento | Descripción |
|-----------|-------------|
| `SISTEMA_DUAL_EVALUACION.md` | Arquitectura técnica completa |
| `EVALUACION_INFANTIL.md` | Guía específica Infantil |
| `CHANGELOG_SISTEMA_DUAL.md` | Historial de cambios |
| `NOMENCLATURA_CRITERIOS.md` | Nomenclatura y vinculación de criterios |
| `/ayuda` (en app) | Ayuda integrada con sección Sistema Dual |

---

**Última actualización:** 6 Abril 2026 — tras merge a master y push a origin  
**Estado:** ✅ Master actualizado y en producción
