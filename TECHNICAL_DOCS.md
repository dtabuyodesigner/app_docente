# Documentación Técnica: Cuaderno del Tutor

## 1. Visión General
**Cuaderno del Tutor** es una aplicación web diseñada para la gestión docente de un grupo de alumnos. Permite el control de asistencia, evaluación continua basada en criterios y competencias (SDA), generación de informes y planificación diaria.

### Stack Tecnológico
*   **Backend**: Python 3 con Flask.
*   **Base de Datos**: SQLite (`app_evaluar.db`).
*   **Frontend**: HTML5, JavaScript (Vanilla), CSS3.
*   **Librerías Clave**:
    *   `Flask`: Servidor web.
    *   `google-api-python-client`: Integración con Google Calendar.
    *   `xhtml2pdf`: Generación de informes en PDF.
    *   `pandas`: Procesamiento de datos (importación/exportación).
    *   `matplotlib`: Generación de gráficas para informes.

---

## 2. Diario de Clase
El módulo de diario (`/diario`) permite registrar observaciones diarias de los alumnos.

### Características
- **Filtrado por Asignatura**: Se pueden registrar observaciones generales o específicas por área (Lengua, Matemáticas, etc.).
- **Persistencia**: Las observaciones se guardan automáticamente al perder el foco (evento `blur`) o cambiar de alumno.
- **Exportación PDF**: Generación de informes en PDF por alumno, agrupando observaciones por fecha y asignatura.
- **Interfaz**: Diseño en tarjetas con indicadores visuales de guardado.

### Base de Datos
- Tabla `observaciones`:
    - `id`: PK
    - `alumno_id`: FK -> alumnos
    - `area_id`: FK -> areas (Nullable)
    - `fecha`: TEXT (ISO 8601)
    - `texto`: TEXT

### API Endpoints
- `POST /api/observaciones`: Crea o actualiza una observación (Upsert).
- `GET /api/observaciones/dia`: Obtiene observaciones de un día, opcionalmente filtradas por `area_id`.
- `GET /api/informe/pdf_diario/<id>`: Genera y descarga el PDF del diario del alumno.

---

## 3. Estructura del Proyecto

```
/
├── app.py                 # Punto de entrada de la aplicación y lógica del backend
├── app_evaluar.db         # Base de datos SQLite
├── schema.sql             # Esquema inicial de base de datos
├── requirements.txt       # Dependencias del proyecto
├── static/                # Archivos estáticos
│   ├── css/               # Hojas de estilo
│   ├── js/                # Scripts del frontend
│   │   ├── alumnos.js     # Lógica de gestión de alumnos
│   │   ├── asistencia.js  # Lógica de asistencia
│   │   ├── evaluacion.js  # Lógica de evaluación y notas
│   │   └── ...
│   ├── *.html             # Vistas de la aplicación (SPA enrutada por backend)
│   └── img/               # Imágenes y recursos
└── templates/             # Plantillas Jinja2 (si se usan, mayormente estáticos servidos)
```

---

## 3. Esquema de Base de Datos

El sistema utiliza una base de datos relacional SQLite con las siguientes tablas principales:

### Alumnos y Asistencia
*   **`alumnos`**: Datos básicos (`id`, `nombre`, `no_comedor`).
*   **`asistencia`**: Registro diario (`alumno_id`, `fecha`, `estado`, `observacion`). Estados: `presente`, `retraso`, `falta_justificada`, `falta_no_justificada`.
*   **`observaciones`**: Notas generales por alumno y fecha.

### Currículo y Evaluación
*   **`areas`**: Asignaturas (Matemáticas, Lengua, etc.).
*   **`sda`**: Situaciones de Aprendizaje asociadas a un área y trimestre.
*   **`criterios`**: Criterios de evaluación oficiales.
*   **`evaluaciones`**: Notas registradas (`alumno_id`, `criterio_id`, `sda_id`, `nota`, `nivel`).
*   **`rubricas`**: Definiciones de niveles de logro (1-4) para cada criterio.

### Programación
*   **`programacion_diaria`**: Eventos del calendario (`fecha`, `actividad`, `tipo`, `observaciones`).
*   **`tareas`**: Lista de tareas pendientes (ToDo).

---

## 4. API Reference (Principales Endpoints)

### Alumnos
*   `GET /api/alumnos`: Devuelve lista de alumnos.
*   `POST /api/alumnos/nuevo`: Crea un nuevo alumno.
*   `PUT /api/alumnos/<id>`: Actualiza datos.
*   `DELETE /api/alumnos/<id>`: Elimina un alumno.

### Asistencia
*   `GET /api/asistencia/hoy`: Asistencia del día actual.
*   `POST /api/asistencia`: Guarda la asistencia del día.
*   `GET /api/asistencia/mes`: Histórico mensual.

### Evaluación
*   `GET /api/evaluacion/areas`: Lista de áreas.
*   `GET /api/evaluacion/sda/<area_id>`: SDAs de un área.
*   `GET /api/evaluacion/criterios/<sda_id>`: Criterios de una SDA.
*   `GET /api/evaluacion/alumno`: Notas de un alumno.
*   `POST /api/evaluacion`: Guardar una nota.

### Programación
*   `GET /api/programacion`: Obtiene eventos del calendario.
*   `POST /api/programacion`: Crea un evento.
*   `POST /api/calendar/sync`: Sincroniza hacia Google Calendar.
*   `POST /api/calendar/import`: Importa desde Google Calendar.

### Informes
*   `GET /api/informe/pdf_individual`: Genera PDF del alumno.
*   `GET /api/informe/pdf_grupo`: Genera resumen de la clase.

---

## 5. Instalación y Despliegue

### Requisitos previos
*   Python 3.8+
*   pip (gestor de paquetes)

### Pasos
1.  **Clonar el repositorio** o copiar los archivos.
2.  **Crear entorno virtual**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # En Linux/Mac
    ```
3.  **Instalar dependencias**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Inicializar Base de Datos** (si es la primera vez):
    ```bash
    # Ejecutar script schema.sql manualmente o dejar que app.py lo cree si está configurado
    python init_db.py  # (Si existe script de inicialización)
    ```
5.  **Ejecutar la aplicación**:
    ```bash
    python app.py
    ```
6.  Acceder a `http://localhost:5000` en el navegador.

### Google Calendar Setup
Para que funcione la sincronización, el archivo `credentials.json` (OAuth 2.0 Client ID) debe estar presente en la raíz del proyecto.
