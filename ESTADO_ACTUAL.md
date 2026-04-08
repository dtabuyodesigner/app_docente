# 📍 ESTADO DEL PROYECTO - APP_EVALUAR

**Fecha:** 8 de Abril 2026
**Versión:** `v1.1.29`
**Rama activa:** `master`

---

## ✅ FIXES Y MEJORAS POST-RELEASE (v1.1.29)

### Acta de Reunión de Ciclo — label tutor con curso
- La celda "Tutor/a:" en el PDF ahora incluye el nombre del grupo (ej: "Tutor/a 1º Primaria")
- Fuente: nombre del ciclo en `config_ciclo` (regex `\d+[ºª]`) → fallback al nombre del grupo activo en sesión
- Fix: `sqlite3.Row` no tiene `.get()` → usar `reunion["ciclo_id"] if "ciclo_id" in reunion.keys() else None`
- Archivos: `routes/reuniones.py`

### Coordinador/a de Ciclo en grupos
- Nuevo campo `coordinador_ciclo TEXT` en tabla `grupos` (migración automática en `db.py`)
- Visible en **Configuración → Nuevo Grupo** y **Editar Grupo**, debajo del Equipo Docente
- En el PDF de reunión de ciclo: si hay coordinador guardado, aparece su nombre en cursiva bajo "El/La Coordinador/a:"; si no, mantiene la línea punteada para firma
- Archivos: `routes/db.py`, `routes/main.py`, `routes/reuniones.py`, `static/configuracion.html`

### Dark mode — mejoras masivas
- Añadidas reglas CSS para cubrir colores hardcodeados en todas las páginas:
  - Textos oscuros: `#333`, `#444`, `#555`, `#666`, `#777`, `#888`, `#999`, `#000`, `black` y variantes Tailwind (`#1e293b`, `#374151`, etc.)
  - Fondos claros neutros: `#f8f9fa`, `#f8fafc`, `#f9f9f9`, `#f0f4f8`, `#f1f5f9`, `#fdfdfd` y más de 15 variantes
  - Fondos semánticos: verdes (`#e8f5e9`, `#d4edda`, `#dcfce7`) → verde oscuro; rojos (`#f8d7da`, `#fee2e2`) → rojo oscuro; azules (`#e7f3fe`, `#e3f2fd`) → azul oscuro; amarillos → warning oscuro
  - `tr`/`td` con fondos inline en tablas alternadas
  - `input`/`textarea`/`select` con `background: white` inline
  - Gradientes con `#003366` → gradiente oscuro
  - Bordes `#ddd`, `#ccc`, `#e9ecef` → `var(--gray-300)`
  - Labels de formulario → `#ffffff` (antes `#d0d0e0`, demasiado tenue)
  - Eventos del calendario FullCalendar → texto blanco (`color: #ffffff !important`)
- Archivos: `static/css/dark-mode.css`

---

## ✅ FIXES ADICIONALES (v1.1.29 — post-release anteriores)

### Fix versión en Panel de Control (automático)
- El badge de versión en el Panel de Control llamaba a `/api/version` (endpoint inexistente) → ahora llama a `/api/admin/version`
- Eliminada la `'v'` extra que se añadía en JS (`'v' + d.version` cuando `APP_VERSION` ya la incluye)
- **La versión se lee dinámicamente del servidor al cargar la página** — no hay que tocar el HTML para actualizarla
- Archivos: `static/index.html`

### Menú comedor — lightbox con zoom interactivo
- Modal rediseñado como lightbox de 92vw × 92vh
- **Zoom con rueda del ratón** directamente sobre la imagen
- **Botones +/−** y **↺ Reset** en la cabecera con indicador de porcentaje
- **Arrastrar** con el ratón para mover la imagen cuando está ampliada
- **Pellizco táctil** (móvil) para zoom
- Se cierra con ✕ o haciendo clic fuera del panel
- Archivos: `static/asistencia.html`

---

## ✅ LO COMPLETADO EN v1.1.29

### Actas de Incidencia — Mejoras completas

- **PDF: celda separada por docente** — cada profesor marcado tiene su propia celda de firma en el PDF
- **PDF: firma del tutor** — imagen de firma del tutor aparece en su celda (fix: `nombre_tutor` no se cargaba en config → fuzzy match siempre fallaba)
- **PDF: nombres en formato natural** — "Apellidos, Nombre" → "Nombre Apellidos" en las celdas de firma
- **PDF: firma del alumno/a opcional** — checkbox en el formulario; solo aparece en el PDF si se marca
- **PDF: separador `\n` entre firmantes** — evita colisión con la coma dentro de "Apellidos, Nombre"
- **PDF: fecha de generación** — "Documento generado el DD/MM/YYYY" al pie, estilo reuniones
- **Formulario: textarea más grande** — `rows=18`, `min-height: 220px`, fuente más legible
- **Historial: texto más legible** — `.hist-texto` de 0.88rem → 0.93rem con más interlineado
- **Banner de actualización: solo verde** — eliminado el banner rojo fijo de la barra de navegación; solo queda el banner verde del panel de control
- **Banner verde: botón Omitir** — nuevo botón para cerrar el banner sin actualizar
- **Archivos:** `routes/actas.py`, `static/diario.html`, `static/index.html`, `static/js/navigation.js`, `version.py`

---

## ✅ LO COMPLETADO EN v1.1.28

### Sistema de Actas de Incidencia
- **Creación rápida desde Diario:** botón 📝 en cada ficha de alumno
- **Campos:** Fecha del hecho, Lugar, Profesor implicado, Descripción, Firmante
- **PDF automático:** genera acta formal con logos del centro (izq/dcha) y firma del tutor
- **Mejoras de formato PDF (⚡):**
  - Soporte para **negritas** (`<b>`) en todas las celdas de la tabla de datos.
  - Firma del tutor/docente movida a la **izquierda** (con su nombre) y espacio para firma del alumno a la derecha.
  - Eliminación de **numeración automática** en la descripción (respeta el formato original).
- **Cabecera PDF:** logos del centro configurados en Ajustes > Logos
- **Selector de docentes:** campos Profesor y Firmante cargan lista de usuarios del centro
- **Firma automática:** si no se especifica firmante, usa la firma del tutor configurada
- **Layout modal:** cabecera y botones fijos, cuerpo con scroll independiente
- **Historial → Acta:** botón "Convertir a Acta" en cada observación del historial
- **Base de datos:** nueva tabla `actas_incidencias`
- **Archivos:** `routes/actas.py`, `static/diario.html`, `utils/db.py`

### Historial de Observaciones
- **Botón "Historial"** en la barra de controles del Diario
- **Filtros rápidos:** búsqueda por texto, rango de fechas, alumno y área
- **Carga eficiente:** últimas 200 observaciones con filtrado en frontend
- **Layout Flexbox:** cabecera y filtros fijos, cuerpo con scroll
- **Endpoint nuevo:** `/api/observaciones/historial`
- **Archivos modificados:** `routes/observaciones.py`, `static/diario.html`

### Banner de Actualización Directa
- **Banner verde** en Panel de Control si hay actualización disponible
- **Actualización directa** al pulsar el banner (sin ir a configuración)
- **Carga automática** de versión al abrir sección Actualizaciones
- **Archivos modificados:** `static/index.html`, `static/configuracion.html`

### Renombrado de Scripts
- `arrancar.sh` → `cuadernodeltutor.sh` (nombre más descriptivo)
- Actualizado `CuadernoDelTutor.desktop`

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

**Última actualización:** 8 Abril 2026 — Fix curso tutor en ciclo (COMMITEADO ✅ v4 - commit `944a102`)
**Estado:** ✅ Commiteado — ⬜ PENDIENTE PROBAR (app corriendo en puerto 5000)
**Rama:** `feature/fix-acta-ciclo-y-dark-mode` — ✅ Subida a GitHub

---

## 📋 PENDIENTE DE PROBAR Y HACER (8 Abril 2026)

### 🔥 PRIORITARIO — Para próximo día

#### 1. ACTA DE CICLO — Corchetes en Asistentes y Firma del Tutor
**Archivos modificados:** `routes/informes.py` (líneas ~1743-1806)

**Problema reportado:**
- En el PDF del acta de ciclo, los nombres de asistentes aparecen con corchetes: `["Noelia Socas Pimentel","Daniel Tabuyo de las Peñas"]`
- La firma del tutor pone solo "Tutor/a" en vez de "Tutor/a 1º" o "Tutor/a 1ºA"

**Cambios realizados:**
- Función `parsear_lista()` que maneja múltiples formatos:
  - JSON arrays válidos: `["nombre1", "nombre2"]`
  - Listas entre corchetes sin parsear: `["nombre1","nombre2"]`
  - Listas separadas por comas con corchetes
  - Listas separadas por newlines (formato tradicional)
- **Logging debug añadido** con `[DEBUG]` para ver formato real de los datos
- Obtenido `grupo_curso` de la tabla grupos para mostrar en firma del tutor
- Si el firmante es identificado como tutor, ahora muestra "Tutor/a {curso}"

**PASOS PARA PROBAR:**
1. Abrir app → Evaluación → Informes → Generar acta de ciclo
2. Revisar logs del servidor (terminal donde se ejecuta `python app.py`)
3. Buscar líneas que empiecen con `[DEBUG]`
4. Verificar qué formato tienen los datos y cómo se parsean
5. Abrir PDF generado y comprobar:
   - ✅ Nombres de asistentes SIN corchetes
   - ✅ Firma del tutor muestra "Tutor/a 1º" o "Tutor/a 1ºA"
6. Si persisten los corchetes, copiar el output `[DEBUG]` y ajustar `parsear_lista()` según formato real

**ARCHIVOS A COMMITTEAR:** `routes/informes.py`

---

#### 2. DARK MODE — Visibilidad completa en modo oscuro
**Archivos modificados:** `static/reuniones.html` (línea ~434), `static/css/dark-mode.css`

**Problema reportado:**
- Calendario en reuniones.html no se veía bien en modo oscuro (fondo blanco hardcoded)
- Múltiples elementos con `background: white` inline en toda la app

**Cambios realizados:**
- Eliminado `background: white` inline del `#calendarContainer` en reuniones.html
- Añadidas reglas extensivas a `dark-mode.css` (~100 nuevas líneas):
  - FullCalendar components (`.fc`, `.fc-toolbar`, `.fc-button`, `.fc-daygrid-event`, etc.)
  - Divs/sections con `background: white` inline (attribute selectors `[style*="..."]`)
  - Modales con fondos inline (`.modal-content`, `.modal`)
  - Tabs, attendees grids, meeting cards
  - Botones y selects con fondos blancos inline
  - Cajas de advertencia/info con fondos claros (`#fff8e1`, `#fff3e0`, etc.)
  - Contenedores con box-shadow y background inline

**PASOS PARA PROBAR:**
1. Activar modo oscuro (icono 🌙 en navbar)
2. Navegar a Reuniones → verificar calendario visible y legible
3. Probar abrir modales (Nueva reunión, Configurar ciclo) → verificar fondos oscuros
4. Probar otras páginas en modo oscuro:
   - Informes
   - Configuración
   - Alumnos
   - Programación
   - Diario
5. Si algún elemento sigue con fondo blanco o texto ilegible:
   - Identificar el selector CSS del elemento
   - Añadir regla específica a `dark-mode.css`

**ARCHIVOS A COMMITTEAR:** `static/reuniones.html`, `static/css/dark-mode.css`

---

#### 3. GIT — Commit pendiente (CREAR RAMA Y SUBIR)
**TODO:**
```bash
cd /home/danito73/Documentos/APP_EVALUAR
git checkout -b feature/fix-acta-ciclo-y-dark-mode
git add routes/informes.py static/reuniones.html static/css/dark-mode.css
git commit -m "Fix: Acta de ciclo sin corchetes + Dark mode completo

- Parseo inteligente de equipo_docente (JSON, comas, newlines)
- Firma del tutor incluye curso (ej: Tutor/a 1ºA)
- Dark mode para calendario, modales, cards y elementos inline
- Logging debug para depuración de formato de datos"
git push origin feature/fix-acta-ciclo-y-dark-mode
```

**NO hacer merge a main hasta probar en navegador**

---

### 🐛 BUGS PENDIENTES (sin empezar)

| Bug | Archivos | Prioridad |
|-----|----------|-----------|
| Gestión de Criterios no borra | `static/evaluacion.html`, `routes/criterios_api.py` | 🔴 Alta |
| Cuaderno de Evaluación no muestra nada | `static/cuaderno_evaluacion.html`, `routes/evaluacion_cuaderno.py` | 🔴 Alta |
| Actas: No aparecen nombres profesores en checkboxes | `static/diario.html`, `routes/actas.py` | 🟡 Media |
| Actas: Campo firmante no se rellena con nombre del tutor | `static/diario.html`, `routes/actas.py` | 🟡 Media |

---

### 💡 FEATURES PENDIENTES

| Feature | Descripción | Archivos |
|---------|-------------|----------|
| Rellenador masivo Infantil | Botones EP/CO o AD/MA en Clase de Hoy | `static/clase_hoy.html` |
| Plan Reuniones | CRUD para Claustro, CCP, Comisiones | `routes/reuniones.py` |
| Estadísticas y gráficas | Panel de progreso por alumno/grupo | Nuevo módulo |
| Exportación masiva | Excel/CSV por trimestre | Nuevo endpoint |

---

### 🧪 TESTS POR CONFIRMAR (Sistema Dual)

| Test | Descripción | Estado |
|------|-------------|--------|
| Test 8 | Rejilla POR_CRITERIOS_DIRECTOS → botones EP/CO se iluminan y guardan | ⬜ Pendiente |
| Test 9 | Rellenar EP en rejilla → medias del área se recalculan | ⬜ Pendiente |
| Test 10 | Clic en píldora activa → la borra de `evaluacion_criterios` | ⬜ Pendiente |
| Test 11 | Evaluar en POR_ACTIVIDADES → cambiar a POR_SA → criterios aparecen | ⬜ Pendiente |
| Test 12 | Editar criterio → Guardar → sin error de validación | ⬜ Pendiente |
| Test 13 | Seleccionar todo en lista → Borrar → solo borra sin evaluaciones | ⬜ Pendiente |

---

## 🧪 CÓMO ARRANCAR

```bash
cd /home/danito73/Documentos/APP_EVALUAR
./cuadernodeltutor.sh
# o manualmente:
python app.py
```

Abrir: `http://localhost:5000` (o el puerto que indique la terminal)

---

## 🔗 COMANDOS ÚTILES

```bash
# Estado del repo
git status
git log --oneline -5

# Crear rama para fix actual
git checkout -b feature/fix-acta-ciclo-y-dark-mode

# Commit cambios probadas
git add routes/informes.py static/reuniones.html static/css/dark-mode.css
git commit -m "Fix: Acta de ciclo sin corchetes + Dark mode completo"

# Merge a main (SOLO después de probar)
git checkout main
git merge feature/fix-acta-ciclo-y-dark-mode
git push origin main
```

---

**Documentado:** 8 Abril 2026
**Próximo paso:** Probar acta de ciclo y dark mode → ajustar según logs → commit a rama → merge a main
