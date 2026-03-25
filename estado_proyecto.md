# Cuaderno del Tutor — Estado del Proyecto
*Actualizado: 25/03/2026*

---

## ✅ MÓDULOS CERRADOS EN WINDOWS

### 👥 Alumnos
- CRUD completo con foto
- Importar/exportar CSV y JSON
- Ficha completa (fecha nacimiento, dirección, contactos)
- Editar guarda todos los datos incluyendo ficha_alumno
- Transferir entre grupos
- Soft delete + limpiar borrados
- Foto en listado y en ficha individual

### 📋 Asistencia / Pasar Lista
- Marcar presente/falta/retraso/justificada — vista normal y compacta
- Vista compacta: comedor desactivado si falta de día completo
- Comedor actualiza al momento en vista compacta
- Menú del comedor — subir y ver imagen
- Notas individuales (crear, editar, eliminar, ver)
- Historial de faltas
- Historial de encargados
- Exportar CSV

### 📅 Horario
- Vista manual: clase y profesor
- Copiar horario clase → profesor
- Asignaturas filtradas por tipo:
  - Clase: todas las áreas de la etapa del grupo
  - Profesor: solo las áreas asignadas al grupo seleccionado
- Configurar tramos horarios
- Vista imagen: subir y quitar imagen
- Imprimir

---

## 🔄 MÓDULOS PENDIENTES DE PROBAR EN WINDOWS

- Reuniones
- Biblioteca (catálogo, préstamos, devoluciones, diplomas, lectómetro)
- Dashboard
- Configuración (logos, actualizaciones, rol especialista)

### 📊 Evaluación y Currículo (SDA)
- [x] Rejilla de evaluación robusta con ciclo `data-nivel` (`NI/PA`, `EP/A`, `CO/MA`).
- [x] Evaluación masiva reactiva ("Evaluar Todo") con prefijos de API unificados.
- [x] Gestión de SDAs completa (Importación CSV, sesiones múltiples, sincronización de carga).
- [x] Visualización de promedios (SDA y Área) en tiempo real en vista individual.
- [x] Actividades con descripciones completas (`textarea`) y tooltips informativos.
- [x] Selector de etapa inteligente (se oculta si el grupo ya la define).

### 📑 Informes y Diario
- Generación de informes individuales (PDF/Excel) sincronizada
- Diario de clase e incidencias con diseño unificado
- Progreso de clase con preselección automática de etapa y gráficos dinámicos
- Estandarización de inputs y selects (42px) en toda la UI

---

## 🔴 BUGS CONOCIDOS PENDIENTES

1. **Exportar CSV alumnos** — incluye columna ID
2. **Logos en Configuración** — 404 en preview (están en AppData)
3. **Horario** — mejoras futuras: asignaturas editables, más opciones
4. **Dashboard** — widget últimas reuniones no carga
5. **Reuniones de Ciclo** — config_ciclo vacía en BD nueva
6. **Programación duplicados** — algunas sesiones se muestran repetidas en el calendario (refactorizar `obtener_programacion`)

---

## 🔧 MEJORAS TÉCNICAS PENDIENTES

### Alta prioridad
- Micrófono 🎤 en campos de texto largos (observaciones, valoración grupo, informe)
- Completar `run_migrations()` con todas las columnas de todas las tablas

### Media prioridad  
- Filtro áreas por etapa en Horario (ya hecho)
- console=False en .spec para versión final Pilar
- Generar exe/zip final para Pilar cuando todo esté estable

---

## 📁 DATOS CLAVE

- **Repo:** github.com/dtabuyodesigner/app_docente
- **Rama:** feature/refactor-evaluacion-curricular
- **Linux:** ~/Documentos/APP_EVALUAR
- **BD Linux:** ~/.cuadernodeltutor/app_evaluar.db
- **BD Windows:** %APPDATA%\CuadernoDelTutor\app_evaluar.db
- **Stack:** Flask + SQLite + PyInstaller + pywebview(Linux) / webbrowser(Windows)
- **Usuario Windows pruebas:** dtabpen / pilar (admin)
