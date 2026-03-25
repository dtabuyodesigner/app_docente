# Archivos modificados para compatibilidad con Windows y esquema de BD

Esta es la lista de los archivos que han sido modificados para asegurar que la base de datos coincida con el código Python y para que las rutas de subida de archivos (imágenes, menús) y logs funcionen correctamente al empaquetar la aplicación con PyInstaller en Windows.

## 1. Base de datos y configuración principal
*   `schema.sql`: Añadidas columnas `deleted_at`, `tiene_ayuda_material` a `alumnos`. Añadidos datos iniciales a `config` y `etapas`.
*   `utils/db.py`: Añadida la instrucción `PRAGMA foreign_keys = ON;` al conectar para asegurar la integridad referencial.
*   `app.py`: Añadido un nuevo endpoint `@app.route('/uploads/<filename>')` para servir archivos dinámicamente desde la carpeta de datos del usuario (`AppData`), evitando el uso de la carpeta estática del ejecutable.

## 2. Rutas del Backend (Uso de rutas persistentes)
*   `utils/security.py`: Actualizadas las rutas de los archivos de registro (`audit.log` y `security.log`) para que usen `get_app_data_dir()`.
*   `routes/alumnos.py`: Actualizada la ruta de subida de fotos de los alumnos para que se guarden en `get_app_data_dir() + "/uploads"`.
*   `routes/comedor.py`: Actualizada la ruta de subida de los menús del comedor para que se guarden en `get_app_data_dir() + "/uploads"`.

## 4. Refinamientos de Evaluación, Informes y UI (Última Fase)
Se han realizado los siguientes ajustes para mejorar la experiencia de usuario y la consistencia visual:
*   `static/evaluacion.html`: Implementada lógica de ciclo de notas para Infantil (`NI/PA` -> `EP/A` -> `CO/MA`).
*   `static/programacion.html`: Convertidos campos de descripción de sesiones en `textarea` para soportar textos largos sin recortes.
*   `static/progreso_clase.html`: Añadida preselección automática de etapa basada en el grupo activo y ajuste dinámico de escalas en gráficos (1-3 o 1-4).
*   `static/informes.html` y `static/diario.html`: Eliminados estilos inline de inputs de fecha y otros elementos para delegar en `theme.css`.
*   `static/css/theme.css`: Estandarizada la altura mínima (`min-height: 42px`) para todos los inputs y selects del sistema, asegurando una estética premium y consistente.
*   `routes/curricular.py`: Mejorada la robustez en la importación de SDAs (conteo de sesiones y gestión de descripciones).
*   `app.py`: Correcciones en el enrutamiento y registro de blueprints (eliminado registro duplicado que causaba ValueError en Windows).
