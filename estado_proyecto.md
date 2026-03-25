# Cuaderno del Tutor — Estado del Proyecto
*Actualizado: 20/03/2026*

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
- Diario / Observaciones
- Evaluación (criterios, notas, SDA)
- Informes individuales (PDF, Excel)
- Informe de grupo + Acta Oficial
- Biblioteca (catálogo, préstamos, devoluciones, diplomas, lectómetro)
- Programación
- Dashboard
- Configuración (logos, actualizaciones, rol especialista)

---

## 🔴 BUGS CONOCIDOS PENDIENTES

1. **Exportar CSV alumnos** — incluye columna ID
2. **Logos en Configuración** — 404 en preview (están en AppData)
3. **Horario** — mejoras futuras: asignaturas editables, más opciones
4. **Dashboard** — widget últimas reuniones no carga
5. **Reuniones de Ciclo** — config_ciclo vacía en BD nueva

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
