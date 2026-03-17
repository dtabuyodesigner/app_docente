# 🚀 Plan de Acción: Camino B (Simulación del Autoupdater)

Este documento guarda el estado exacto en el que lo hemos dejado y los pasos a seguir para cuando vuelvas a encender el ordenador o inicies una nueva sesión con otra IA.

## Estado Actual (v1.0.0)
Hemos empaquetado exitosamente la versión **1.0.0** de "Cuaderno del Tutor" para Linux (`dist/cuaderno-del-tutor_1.0-1_amd64.deb`). Esta versión **ya contiene** el código del *Autoupdater* que busca nuevas versiones en GitHub (`danito73/APP_EVALUAR`), pero **aún no tiene** el botón mágico de "Subir Backup .db" (lo dejaremos para la v1.1).

## Próximos Pasos (Lo que vas a hacer tú)

### 1. Instalar y Migrar (La "prueba de fuego")
Para simular el caso de uso real de un usuario que estrena la app:
1. Instala el archivo `.deb` que tienes en tu carpeta `dist/`.
2. Ábrelo una vez desde el menú de aplicaciones de tu Linux para que se cree la estructura base y ciérralo.
3. Coge tu archivo con datos reales `app_evaluar.db` (el que está en la carpeta de tu código fuente).
4. Cópialo y pégalo "a lo bruto" dentro de la ruta del sistema: `/opt/cuaderno-del-tutor/` (te pedirá contraseña de sudo/administrador).
5. Abre la aplicación de nuevo. ¡Deberías tener todos tus alumnos, notas y configuraciones allí!

### 2. Preparar el Terreno en GitHub
- Ve a tu repositorio de GitHub (`danito73/APP_EVALUAR`).
- Crea un nuevo "Release" y etiquétalo exactamente como `v1.0.0`. Sube ahí si quieres los instaladores `.exe` y `.deb` actuales (opcional).

### 3. Programar la Actualización (La futura v1.1)
Cuando inicies una nueva sesión conmigo o con otra instancia, dile:
> *"Lee el documento `PLAN_ACTUALIZACION_V1.1.md` (este documento). Vamos a programar la versión v1.1: Necesitamos añadir el botón de 'Restaurar Backup Externo' en el panel de Backups."*

1. Modificaremos el código (`configuracion.html`, `admin.py`, etc.) para implementar la subida de backups.
2. Cambiaremos el archivo `version.py` de `v1.0.0` a **`v1.1.0`**.
3. Volveremos a compilar el `.deb` y el `.exe` (ejecutando los scripts de build).
4. Subiremos esos nuevos compilados a un nuevo Release en GitHub etiquetado como **`v1.1`** o **`v1.1.0`**.

### 4. La Magia del Autoupdater
Una vez subida la `v1.1.0` a GitHub:
1. Abrirás tu aplicación instalada en Linux (la que está en la v1.0.0 y ya tiene tus datos).
2. Irás a Configuración -> Buscar Actualizaciones.
3. La aplicación detectará que en GitHub existe la `v1.1.0`, mostrará el mensaje verde de alerta y te invitará a descargar la nueva versión.

De esta manera, validaremos que el sistema de actualizaciones funciona perfectamente en un entorno real. ¡Que vaya muy bien y nos vemos en la próxima sesión!
