# Instalación 1 clic — Cuaderno del Tutor (Windows)

## Para Pilar (instrucciones cortas)

1. Copiar `instalar_todo_1click.bat` al Escritorio.
2. Clic derecho → **Ejecutar como administrador**.
3. Esperar a que termine (puede tardar 5-10 min la primera vez).
4. La app se abre sola al acabar y aparece el icono **"Cuaderno del Tutor"** en el Escritorio.
5. A partir de ahora: doble clic en ese icono para abrir la app.

Para actualizar la app en el futuro: volver a ejecutar `instalar_todo_1click.bat`.

---

## Qué hace el instalador por dentro

1. Comprueba que `winget` está disponible (Windows 10/11 moderno).
2. Instala **Git** con `winget` si no está.
3. Instala **Python 3.12** con `winget` si no está.
4. Clona el repo en `C:\CuadernoDelTutor` (o hace `git pull` si ya existe).
5. Establece `SECRET_KEY` de entorno para que PyInstaller pueda analizar el código.
6. Ejecuta `build_windows.bat` → genera `dist\CuadernoDelTutor\CuadernoDelTutor.exe`.
7. Crea el **acceso directo** "Cuaderno del Tutor" en el Escritorio.
8. Abre la app.

---

## Requisitos

- Windows 10 (con App Installer) o Windows 11.
- Conexión a internet la primera vez.
- Aceptar el aviso UAC si Windows lo pide.

---

## Distribución

El archivo a entregar a Pilar es `instalar_todo_1click.zip` (contiene solo el `.bat`).  
No hace falta entregar nada más — el instalador descarga todo desde GitHub.

**Importante:** cualquier cambio en el código debe haberse subido a GitHub con `git push`
antes de que Pilar ejecute el instalador. El `.bat` clona/actualiza desde el repo remoto.

---

## Errores conocidos y solución

### `winget` no disponible
El sistema tiene Windows antiguo o sin App Installer.  
Solución: actualizar Windows o instalar "App Installer" desde Microsoft Store.

### SECRET_KEY error al arrancar el EXE
Ver sección correspondiente en `INSTRUCCIONES.md` y `GUIA_GENERAR_EXE_WINDOWS.md`.  
Causa más frecuente: el código con el fix no se ha hecho `push` a GitHub.

### Acceso directo no se crea
Mensaje `[AVISO]` en pantalla con la ruta exacta del `.exe`.  
Solución manual: clic derecho sobre `C:\CuadernoDelTutor\dist\CuadernoDelTutor\CuadernoDelTutor.exe`
→ "Enviar a" → "Escritorio (crear acceso directo)".

### Antivirus bloquea el EXE
Añadir excepción a la carpeta `C:\CuadernoDelTutor\dist\`.

---

## Rutas relevantes en el equipo de Pilar

| Qué | Dónde |
|-----|-------|
| Repo clonado | `C:\CuadernoDelTutor\` |
| Ejecutable | `C:\CuadernoDelTutor\dist\CuadernoDelTutor\CuadernoDelTutor.exe` |
| Base de datos | `C:\Users\<usuario>\AppData\Roaming\CuadernoDelTutor\app_evaluar.db` |
| SECRET_KEY persistida | `C:\Users\<usuario>\AppData\Roaming\CuadernoDelTutor\secret_key.txt` |
| Backups automáticos | `C:\Users\<usuario>\AppData\Roaming\CuadernoDelTutor\backups\` |
