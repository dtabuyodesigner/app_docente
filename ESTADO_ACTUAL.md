# 📍 ESTADO DEL PROYECTO - APP_EVALUAR

**Fecha:** 10 de Abril 2026
**Versión:** `v1.1.30`
**Rama activa:** `master`

---

## ✅ OPTIMIZACIÓN DIPLOMA BIBLIOTECA — IMPRESIÓN A4 COMPLETA (v1.1.30)

### Diploma de Honor (Lectómetro)
- **Tamaño:** ocupa casi todo el folio A4 vertical (era medio folio antes)
- **Tipografía escalada:** títulos 2.4rem, nombre alumno 3.8rem, icono corona 3.5rem
- **Formato vertical:** eliminada opción horizontal/landscape (no existía, solo existía la versión reducida)
- **Control de página:** `page-break-inside: avoid` garantiza que el diploma cabe en una sola hoja
- **Margen @page:** 0.8cm para maximizar espacio útil
- **Popup blocker:** detección y mensaje amigable si el navegador bloquea la ventana de impresión
- **Código limpio:** eliminado template duplicado sin usar (~35 líneas muertas)
- **Archivos modificados:** `static/biblioteca.html`, `version.py`, `VERSION`, `ESTADO_ACTUAL.md`

---

## ✅ MÓDULO REUNIONES — REFACTORING COMPLETO (v1.1.29)

### Wizard de nueva reunión
- **Título dinámico al seleccionar tipo:** "Nueva Reunión de Ciclo", "Nueva Reunión de CCP", "Nueva Comisión", etc.
- **Doble clic en tarjeta** avanza automáticamente al paso siguiente
- **Botones sin flechas:** "Siguiente" y "Atrás"
- **FAMILIAS/PADRES paso 2:** muestra solo el tutor pre-marcado; el resto del claustro se añade con el dropdown "Añadir asistente"
- **PADRES paso 2:** selector de alumno/a integrado en el paso de asistentes
- **COMISIONES paso 2:** selector de comisión con carga automática de miembros pre-marcados
- **Botones Todos/Ninguno** ocultos para FAMILIAS/PADRES
- **Añadir asistente:** dropdown con el claustro completo + campo libre de texto
- **Campo "Familiar asistente"** (solo FAMILIAS/PADRES): nombre del familiar que acude a la reunión

### Selección masiva
- Checkbox en cada tarjeta de la lista
- Barra de acción azul con contador al marcar una o más
- Checkbox "seleccionar todo" con estado indeterminate
- Botón "Eliminar seleccionadas" con confirmación; borra en serie vía API
- Click en tarjeta con selección activa activa su checkbox en vez de abrir el detalle

### PDF por tipo de reunión
- **Cabecera adaptada:** "ACTA DE REUNION - CCP", "ACTA DE REUNION - COMISIÓN", etc.
- **Título dinámico:** "Reunión de CCP", "Comisión: Carnaval", "Entrevista: Nombre Alumno"
- **Firma izquierda:** "Tutor/a 1º Primaria" solo en FAMILIAS/PADRES → resto "El/La Maestro/a"
- **Firma derecha por tipo:**
  - FAMILIAS/PADRES → "El/La Padre/Madre/Tutor Legal" + nombre del familiar si se indicó
  - CICLO → "El/La Coordinador/a de Ciclo"
  - CCP / CLAUSTRO → "El/La Director/a"
  - COMISIONES → "El/La Coordinador/a de Comisión"
  - Resto → "El/La Jefe/a de Estudios"
- **Resto de tipos:** una caja de firma por asistente guardado (grid de 3 columnas)
- **LEFT JOIN plantillas_reunion** para mostrar nombre de comisión en PDF

### Editar reuniones
- Botón "✏ Editar" en modal de detalle abre el wizard pre-rellenado con todos los campos
- Usa PUT `/api/reuniones/<id>` en lugar de POST
- Salta directo al paso 3 con los datos, conservando asistentes guardados
- Errores de apertura reportados con `console.error` + alert descriptivo

### Configuración → Reuniones
- **Roles del claustro actualizados:** Maestro/a, Infantil, Esp. Inglés, Esp. Ed. Física, Esp. Música, Esp. Francés, Esp. Religión, AL, PT, Orientador/a, Director/a, Jefe/a de Estudios, Secretario/a, Otro
- Quitado "Coordinador/a" como rol del claustro (todos son docentes)
- **Ciclo Infantil** añadido al dropdown de ciclos en reuniones de ciclo

### DB
- Nueva columna: `reuniones.familiar_asistente TEXT`
- Nuevo ciclo: `config_ciclo` → "Infantil"
- PUT `/api/reuniones/<id>` actualiza todos los campos incluyendo `familiar_asistente`

### Fixes
- `global_groups.js` añadido a `reuniones.html` (selector de grupo se quedaba en "Cargando")
- `editarReunion` declarada como `async` (fallaba por `await` sin `async`)

### Firma del tutor en grid de asistentes
- En actas de tipo CICLO, CCP, CLAUSTRO, NIVEL, COMISIONES: si el nombre del tutor configurado coincide con un asistente de la lista, su caja de firma muestra la imagen de firma almacenada en el almacén de logos
- Comparación fuzzy (contains bidireccional, case-insensitive) para tolerar variaciones de nombre
- **Fix:** la lista de nombres para firmas se extrae antes de escapar para HTML, evitando que `&amp;` o `&lt;` rompieran la comparación fuzzy

### Archivos modificados
- `routes/reuniones.py` — PDF completo por tipo, PUT con todos los campos, firma tutor en grid
- `static/reuniones.html` — wizard, selección masiva, edición, campo familiar
- `static/configuracion.html` — roles actualizados con Infantil
- `static/reuniones_plantillas.html` — roles actualizados
- `utils/db.py` — migración `familiar_asistente`

---

---

## ✅ MEJORAS REUNIONES DE CICLO (v1.1.30)

### PDF de Reuniones de Ciclo
- **Tutor con curso:** Muestra "Tutor/a 1º", "Tutor/a 2º", etc. en lugar de solo "Tutor/a"
- **Coordinador con nombre:** Si hay coordinador configurado en el grupo, muestra su nombre en la firma
- **Asistentes sin corchetes:** Parsea el formato JSON y muestra texto plano separado por comas

### Selector de Ciclo
- Añadido dropdown para seleccionar ciclo en reuniones de tipo CICLO
- Se guarda el `ciclo_id` en la reunión

### Título Dinámico
- El modal de nueva reunión muestra "Nueva Reunión de Ciclo", "Nueva Reunión de Nivel", etc.

### Diseño del Claustro (Configuración > Reuniones)
- Dropdown editable para cambiar el rol de cada docente después de importarlo
- Opciones de rol: Docente, Coordinador/a, Director/a, Jefe de Estudios, Secretario/a, Orientador/a, AL, PT, Infantil
- Diseño en formato tabla/grid con columnas centradas
- Encabezado: Nombre | Rol | Cambiar rol | Activo | Eliminar

### Archivos modificados
- `routes/reuniones.py` - PDF con tutor curso, coordinador nombre, parseo asistentes
- `static/reuniones.html` - Selector ciclo, título dinámico
- `static/configuracion.html` - Dropdown editable roles claustro

---

## ✅ FIXES ADICIONALES (v1.1.29 — post-release)

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

### Programación SDA + IA (Abril 2026)
- Plantilla oficial SDA unificada en `static/plantilla_sda.csv` (separador `;`)
- Cabecera oficial aplicada:
  `Etapa;Area;Trimestre;SDA_ID;SDA_Titulo;Duracion_Semanas;Criterio_Codigo;Criterio_Descriptor;Competencia_Codigo;Competencia_Descriptor;Saberes_Basicos;Actividad_ID;Actividad_Titulo;Actividad_Descripcion;Actividad_Sesiones;Semana_Numero;Semana_Titulo;Dia;Fecha;Sesion_Numero;Sesion_Titulo;Descripcion_Sesion;Material;Evaluable`
- Plantilla incluye 2 filas de ejemplo listas para referencia.
- Eliminada plantilla duplicada antigua en raíz (`plantilla_sda.csv`) para evitar confusión.
- Se mantiene una sola descarga oficial desde Programación: `/static/plantilla_sda.csv`.

### Modal IA en Programación (nuevo flujo)
- Botón único `🤖 Generar SDA con IA` en la pestaña de SDA.
- Modal renovado con 2 prompts listos:
  - `Prompt 1`: generar SDA completa en formato Word (estructura didáctica completa para Primaria/Canarias).
  - `Prompt 2`: convertir SDA en texto Word a CSV exacto compatible con la app.
- Ambos prompts incluyen:
  - Copiar al portapapeles.
  - Abrir directamente en ChatGPT, Claude y Gemini.
- Instrucciones visibles en UI:
  - Descargar plantilla oficial.
  - Pedir a la IA borrar datos de ejemplo y dejar solo cabeceras antes de rellenar.

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

**Última actualización:** 9 Abril 2026 — flujo IA SDA (Word + Word→CSV) y plantilla oficial unificada  
**Estado:** ✅ Rama feature en desarrollo
