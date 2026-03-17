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

## 3. Frontend (HTML/JS)
Se han actualizado todas las referencias a imágenes de alumnos y menús que antes apuntaban a `/static/uploads/...` para que ahora apunten al nuevo endpoint `/uploads/...`:
*   `static/alumnos.html`
*   `static/perfil.html`
*   `static/diario.html`
*   `static/asistencia.html`
*   `static/horario.html`
