# Manual de Usuario: Cuaderno del Tutor (V2.0)

Bienvenido a la versión actualizada del **Cuaderno del Tutor**. Este manual te guiará a través de todas las funcionalidades, incluyendo las nuevas mejoras de informes, reuniones y horarios.

## Índice
1. [Inicio y Dashboard](#1-inicio-y-dashboard)
2. [Gestión de Estudiantes](#2-gestión-de-estudiantes)
3. [Asistencia y Comedor](#3-asistencia-y-comedor)
4. [Evaluación y SDAs](#4-evaluación-y-sdas)
5. [Programación y Agenda](#5-programación-y-agenda)
6. [Gestión de Reuniones](#6-gestión-de-reuniones)
7. [Horario Dual](#7-horario-dual)
8. [Informes y Exportación](#8-informes-y-exportación)
9. [Notificaciones y Actualizaciones](#9-notificaciones-y-actualizaciones)
10. [Créditos y Autoría](#10-créditos-y-autoría)

---

## 1. Inicio y Dashboard
El panel principal ahora está organizado en **5 pestañas**: *Frecuentes*, *Gestión*, *Docencia*, *Evaluación* y *Recursos*. Cada pestaña agrupa tarjetas de acceso rápido a los módulos más usados. Además, se ha añadido una **sección de Acceso Rápido** con las 5 tarjetas más utilizadas, visible siempre en la parte superior. La barra de navegación superior es más legible y uniforme en todas las secciones.

---
---

## 2. Gestión de Estudiantes
En la pestaña **Alumnos**, puedes gestionar las fichas individuales.
- **Fotos**: Ahora puedes subir fotos de perfil para cada alumno.
- **Importación**: Sigue disponible la carga masiva mediante CSV.

---

## 3. Asistencia y Comedor
Registra las faltas y retrasos diariamente.
- **Comedor**: Marca quién se queda al comedor con un solo clic.
- **Histórico**: Consulta el resumen mensual para ver patrones de asistencia.
- **Gestión de Encargados ⭐**:
  - **Resaltado Visual**: El alumno encargado del día ahora aparece con la "Estrella Encendida" (borde dorado, fondo especial y badge de estrella) para identificarlo rápidamente en la cuadrícula.
  - **Modo Aleatorio 🎲**: El sistema elige automáticamente entre los alumnos que han sido encargados menos veces, rotando de forma justa.
  - **Modo Orden de Lista 📋**: Sigue el orden alfabético de la clase, pero respetando siempre que todos participen antes de repetir ciclo.
  - **Modo Manual ⭐️**: Permite al docente asignar el encargado directamente pulsando el botón "⭐️ Encargado" en la tarjeta de cualquier alumno.
  - **Gestión de Ciclos**: El sistema detecta cuando todos han participado y reinicia el ciclo automáticamente, informando si algún alumno faltó en su turno para reasignarlo cuando asista.

---

## 4. Evaluación y SDAs
Basado en Situciones de Aprendizaje (SDA) y criterios oficiales.
- **Notas**: Introduce calificaciones del 1 al 10 o usa niveles de logro.
- **Rúbricas**: Consulta las definiciones de niveles para una evaluación más objetiva.

---

## 5. Programación y Agenda
Gestiona tu calendario docente y tareas pendientes.

### Calendario
- **Sincronización con Google**: Ahora más robusta. Si es la primera vez que conectas, se te pedirá permiso explícito para que la conexión no caduque.
- **Eventos**: Crea exámenes, excursiones o clases directamente en el calendario.

### Tareas Pendientes
Nueva funcionalidad para gestionar tus tareas docentes:
- **Crear Tareas**: Escribe una tarea y opcionalmente añade una fecha límite.
- **Marcar Completadas**: Haz clic en el checkbox para marcar una tarea como hecha.
- **Editar**: Usa el botón ✏️ para modificar el texto o la fecha de cualquier tarea.
- **Borrar**: Elimina tareas individuales con el botón 🗑️ o todas las completadas con "Borrar Completadas".
- **Alertas de Vencimiento**: Las tareas vencidas aparecen con borde rojo y el indicador ⚠️ VENCIDA. Al cargar la página, recibirás una notificación si hay tareas vencidas pendientes.

---

## 6. Gestión de Reuniones
Registra todo lo hablado con familias o compañeros.
- **Reuniones de Padres**: Actas individuales por alumno.
- **Reuniones de Ciclo**: Actas compartidas para coordinación docente.
- **PDF**: Genera actas formales con espacio para firmas y el nombre del tutor.

---

## 7. Horario Dual
Visualiza dos horarios a la vez.
- **Horario de Clase**: Ideal para mostrar a los alumnos.
- **Horario del Profesor**: Tu agenda personal de sesiones.
- **Subida**: Puedes subir una imagen distinta para cada tipo de horario.

---

## 8. Informes y Exportación
Genera la documentación necesaria al final del trimestre.

### Informe Individual
- **PDF Elegante**: Documento profesional con todas las notas y observaciones del alumno.
- **Detalle de Rendimiento**: Incluye una gráfica de barras horizontal mostrando las notas por área, y un desglose específico de los Criterios evaluados organizados por Situaciones de Aprendizaje (SDA).
- **Validación**: El sistema verifica que hayas seleccionado un alumno antes de generar el PDF.

### Informe Grupal
- **Autocompletado**: Posibilidad de sugerir una conclusión general y pedagógica del grupo de forma automática según los resultados del trimestre.
- **PDF Global**: Comparativa de toda la clase con estadísticas de promoción, asistencia y gráficas visuales.
  - Gráfico circular de promoción (aprobados/suspensos)
  - Gráfico de barras de asistencia (faltas justificadas, injustificadas, retrasos)
- **Excel Completo**: Descarga en múltiples hojas con:
  - Notas por trimestre
  - Valoración del grupo
  - Estadísticas de promoción con gráfico
  - Alumnos con suspensos
  - Datos de asistencia con gráfico
  - Rendimiento por áreas con gráfico de barras

---

### Soporte Técnico
Si encuentras algún problema con la conexión a Google, recuerda que puedes volver a conectar desde la pestaña de Programación para renovar los permisos.

## 9. Notificaciones y Actualizaciones

- **Banner de Actualización**: Aparece en la parte superior de la página de Configuración cuando hay una nueva versión disponible. Al pulsar “Actualizar ahora” el usuario es llevado directamente a la sección **Actualizaciones** mediante un enlace con hash `#actualizaciones`.
- **Globo rojo (badge)**: En la barra de navegación y en la tarjeta “Ajustes” del dashboard se muestra un globo rojo pulsante que indica la disponibilidad de una actualización.
- **Navegación profunda**: La aplicación ahora gestiona el hash `#actualizaciones` en `configuracion.html`, mostrando automáticamente la pestaña de Actualizaciones al cargar la página.
- **Desactivación**: El usuario puede omitir el banner con el botón “Omitir”, que lo elimina de la vista.

## 10. Créditos y Autoría

Este proyecto ha sido desarrollado con el objetivo de facilitar la labor docente diaria.

- **Autor**: Daniel Tabuyo de las Peñas
- **Contacto**: [dtabuyodesigner@gmail.com](mailto:dtabuyodesigner@gmail.com)
- **Propósito**: Herramienta gratuita para la comunidad docente.

Para cualquier sugerencia de mejora, reporte de errores o colaboración, no dudes en contactar a través del correo electrónico mencionado.
