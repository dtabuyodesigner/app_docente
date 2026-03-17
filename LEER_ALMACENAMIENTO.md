# 📁 Guía de Almacenamiento y Compartición del Cuaderno del Docente

Esta guía te explica de forma muy sencilla dónde están tus datos ahora mismo y cómo debes compartir la aplicación con otras personas sin enviarles tus cosas.

## 1. El Archivo que debes compartir (El ZIP "Limpio")

Cuando quieras mandar el Cuaderno a Pilar o a cualquier otro compañero, **solo debes enviar este archivo**:

- **Nombre:** `APP_EVALUAR_Limpio_YYYYMMDD.zip` (por ejemplo, `APP_EVALUAR_Limpio_20260310.zip`)
- **Ruta:** `/home/danito73/Documentos/APP_EVALUAR/APP_EVALUAR_Limpio_20260310.zip`

**¿Qué contiene este archivo?**
Contiene todo el código necesario para que la aplicación funcione en su ordenador, pero está completamente vacío de datos. Cuando ellos lo abran, el programa creará una base de datos nueva y les pedirá configurar su propio usuario y contraseña de acceso.

---

## 2. Dónde están TUS datos personales (Seguros y Ocultos)

Tu base de datos (con todos tus alumnos, notas, programaciones y configuraciones) **sigue existiendo y funcionando exactamente igual**, pero ya no vive en la carpeta principal del código.

La hemos movido a una carpeta propia de tu sistema Linux, que está diseñada para guardar configuraciones de usuario de forma invisible y permanente:

- **Ruta Oculta:** `/home/danito73/.cuadernodeltutor/app_evaluar.db`

*(El punto `.` delante de `cuadernodeltutor` significa que es una carpeta oculta. Tu sistema operativo no la borra por accidente y no aparece a simple vista).*

### ¿Dónde se guardan los datos nuevos que metes ahora?
Todo lo que estás guardando ahora (nuevas faltas de asistencia, nuevas notas, etc.) **se guarda automáticamente en esta misma ubicación segura**:
`~/.cuadernodeltutor/app_evaluar.db`

### ¿Dónde se guardan tus Copias de Seguridad (Backups)?
Al igual que tu base de datos central, los backups diarios y manuales que hagas se guardan en esta carpeta secreta junto a la BD:
`/home/danito73/.cuadernodeltutor/backups/`

---

## 💡 Resumen
1. **Tu aplicación sigue intacta:** Entra desde el navegador como siempre.
2. **Tus datos están protegidos:** Están en `/home/danito73/.cuadernodeltutor/`.
3. **Compartir:** Pasa el archivo `APP_EVALUAR_Limpio...zip` (que está en tu carpeta de Documentos) a tus compañeros. ¡Tus datos NO viajan en ese ZIP!

---

## 🛠️ 3. Generación del Ejecutable y Paquete .deb (v1.1.0)

Para crear los instaladores de la nueva versión, sigue estos pasos:

### Para Linux (Generar archivo .deb)
Utiliza el script automatizado que se encuentra en la carpeta `scripts`:

```bash
# 1. Asegúrate de estar en la carpeta raíz del proyecto
# 2. Dale permisos (solo la primera vez)
chmod +x scripts/build_linux_deb.sh

# 3. Ejecuta la compilación
./scripts/build_linux_deb.sh
```
El instalador aparecerá en la carpeta `dist/` con el nombre `cuaderno-del-tutor_1.1-1_amd64.deb`.

### Para Windows (Generar archivo .exe)

Si quieres compilar la aplicación en un ordenador con Windows (por ejemplo, para pasársela a un compañero que no use Linux), sigue este **paso a paso detallado**:

#### Paso 1: Preparar el ordenador Windows
Antes de nada, el ordenador Windows necesita tener Python instalado:
1. Descarga **Python 3.11** (o superior) desde [python.org](https://www.python.org/downloads/).
2. **MUY IMPORTANTE**: Al instalarlo, marca la casilla que dice **"Add Python to PATH"**. Si no lo haces, nada de lo siguiente funcionará.

#### Paso 2: Extraer el ZIP "Limpio"
1. Lleva el archivo `APP_EVALUAR_Limpio_YYYYMMDD.zip` al Windows (con un pendrive).
2. Haz clic derecho sobre él y elige **"Extraer todo..."**.
3. Elige una carpeta sencilla, por ejemplo en el Escritorio.

#### Paso 3: Instalar las dependencias (Solo la primera vez)
1. Entra en la carpeta donde has extraído el código.
2. Haz clic en la barra de direcciones de la carpeta (donde pone la ruta), escribe **`cmd`** y pulsa Intro. Se abrirá una ventana negra.
3. Escribe este comando y pulsa Intro:
   ```batch
   pip install -r requirements.txt
   ```
   *(Esto descargará todas las piezas necesarias de internet. Tardará un par de minutos).*

#### Paso 4: Crear el ejecutable
1. Sin cerrar la ventana negra (o abriéndola de nuevo en esa carpeta), escribe:
   ```batch
   build_windows.bat
   ```
2. El ordenador trabajará durante un rato. Verás pasar muchas letras.
3. Cuando termine, te dirá "Build completado".

#### Paso 5: ¿Dónde está el programa?
1. Entra en la carpeta **`dist`** que habrá aparecido.
2. Dentro verás otra carpeta llamada **`CuadernoDelTutor`**.
3. El archivo **`CuadernoDelTutor.exe`** es el programa. ¡Ya puedes abrirlo!

> [!TIP]
> Si quieres compartirlo con otros, comprime esa carpeta `dist/CuadernoDelTutor` en un nuevo ZIP o pásala entera por pendrive.

---

> [!IMPORTANT]
> Antes de compilar, asegúrate de que el archivo `version.py` tiene la versión correcta (`v1.1.0`).
