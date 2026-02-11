# Documentación Técnica: Cuaderno del Tutor

## 1. Visión General
**Cuaderno del Tutor** es una solución integral para la gestión docente. La aplicación ha evolucionado hacia una arquitectura modular en el backend para facilitar su mantenimiento y escalabilidad.

### Stack Tecnológico
*   **Backend**: Python 3 con Flask.
*   **Arquitectura**: Modular (Blueprints de Flask).
*   **Base de Datos**: SQLite (`app_evaluar.db`).
*   **Frontend**: HTML5, JavaScript (Vanilla), CSS3.
*   **Sincronización**: Google Calendar API (v3).

---

## 2. Estructura del Proyecto (Arquitectura Modular)

El proyecto se organiza en módulos lógicos para separar responsabilidades:

```
/
├── app.py                 # Inicialización de la app y registro de Blueprints
├── routes/                # Lógica de rutas y API por módulo
│   ├── main.py            # Rutas de páginas estáticas
│   ├── alumnos.py         # Gestión de estudiantes y fotos
│   ├── asistencia.py      # Control de asistencia y faltas
│   ├── evaluacion.py      # Notas, rúbricas y SDAs
│   ├── informes.py        # Generación de PDF y exportación Excel
│   ├── reuniones.py       # Gestión de reuniones de padres y ciclo
│   ├── horario.py         # Gestión de horarios (Clase/Profesor)
│   ├── google_cal.py      # Integración con Google Calendar
│   └── ...
├── utils/                 # Utilidades compartidas
│   └── db.py              # Conexión y helpers de base de datos
├── static/                # Frontend
│   ├── index.html         # Dashboard (Punto de entrada)
│   ├── programacion.html  # Agenda y Calendario
│   ├── ...                # Resto de vistas HTML
│   ├── css/               # Estilos globales y específicos
│   └── js/                # Scripts de soporte (FullCalendar, etc.)
└── app_evaluar.db         # Base de datos SQLite
```

---

## 3. Módulos Clave y Características

### 📊 Informes y Estadísticas
Permite la generación de informes PDF detallados y exportaciones a Excel.
- **Informe Individual**: Resumen por alumno con notas y observaciones.
  - Generación de gráficas con `matplotlib` (barras horizontales por área)
  - Validación de parámetros (`alumno_id` requerido)
  - Corrección de encoding en headers (UTF-8)
- **Informe Grupal**: Visión global de la clase por área y trimestre.
  - **PDF**: Gráfico circular de promoción y gráfico de barras de asistencia
  - **Excel**: Múltiples hojas con gráficos embebidos usando `openpyxl.drawing.image`
- **Tecnologías**: `reportlab`, `matplotlib` (backend 'Agg'), `pandas`, `openpyxl`

### ✅ Gestión de Tareas
Sistema completo de tareas pendientes para el docente.
- **CRUD Completo**: Crear, leer, actualizar y eliminar tareas
- **Base de Datos**: Tabla `tareas` con campos: `id`, `texto`, `fecha`, `hecha`
- **Endpoints**:
  - `GET /api/tareas`: Listar todas las tareas
  - `POST /api/tareas`: Crear nueva tarea
  - `PUT /api/tareas/<id>`: Toggle completada o edición completa (soporta both modes)
  - `DELETE /api/tareas/<id>`: Borrar tarea individual
  - `POST /api/tareas/bulk_delete_completed`: Borrar todas las completadas
- **Frontend Features**:
  - Indicador visual de vencimiento (borde rojo, ⚠️ icon)
  - Alerta automática al cargar si hay tareas vencidas
  - Edición inline con prompts para texto y fecha
  - Sistema de notificaciones toast

### 📅 Programación y Google Calendar
Gestión de la agenda docente con sincronización bidireccional.
- **Sincronización**: Usa OAuth 2.0. Se ha implementado `prompt='consent'` para asegurar la obtención del `refresh_token`.
- **Importación/Exportación**: Permite volcar la programación diaria a Google Calendar y viceversa.

### 👥 Reuniones (Padres y Ciclo)
Sistema de registro para reuniones de tutoría y coordinación pedagógica.
- **Dualidad**: Soporta reuniones individuales (Padres) y colectivas (Ciclo).
- **PDF**: Genera actas de reunión con logos y firmas dinámicas.

### ⏰ Horario Dual
Permite gestionar dos horarios distintos de forma independiente.
- **Clase**: Horario del grupo de alumnos.
- **Profesor**: Horario personal del docente.
- **Implementación**: Almacenamiento de imágenes con prefijos específicos en el servidor.

---

## 4. Esquema de Base de Datos (Tablas Principales)

- **`alumnos`**: Registro de estudiantes, incluyendo ruta de la foto y estado en comedor.
- **`asistencia`**: Registro por fecha y estado (presente, falta, retraso, etc.).
- **`seguimiento_sda`**: Almacena las notas por alumno, criterio y situación de aprendizaje.
- **`reuniones`**: Actas de reuniones, diferenciadas por el campo `tipo`.
- **`informe_individual` / `informe_grupo`**: Observaciones específicas para los informes trimestrales.
- **`horario`**: Almacena las rutas de las imágenes de los horarios.
- **`tareas`**: Gestión de tareas del docente
  - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
  - `texto`: TEXT NOT NULL (descripción de la tarea)
  - `fecha`: TEXT (fecha límite en formato YYYY-MM-DD, opcional)
  - `hecha`: INTEGER DEFAULT 0 (0 = pendiente, 1 = completada)

---

## 5. Mantenimiento y Desarrollo

### Requisitos de Instalación
```bash
pip install -r requirements.txt
```

### Configuración de Entorno (.env)
Se requiere un archivo `.env` con:
- `SECRET_KEY`: Para la sesión de Flask.
- `FLASK_APP`: app.py
- `FLASK_ENV`: development/production

### Google Calendar setup
Es imperativo tener `credentials.json` en la raíz para habilitar la API. Los tokens de usuario se guardan en `token.json`.
