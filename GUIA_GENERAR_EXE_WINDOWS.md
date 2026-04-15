# Guia Windows: generar EXE y permitir actualizaciones desde la app

Fecha: 2026-04-15

## Resumen rapido
1. Para generar EXE: ejecutar `build_windows.bat` en la raiz del proyecto.
2. Para que el boton "Actualizar" funcione: la app debe ejecutarse desde un clon Git (carpeta con `.git`).
3. No entregar solo el `.exe`: entregar la carpeta completa `dist\CuadernoDelTutor\`.

## Opcion A (portable, sin actualizacion desde la app)
Usa esta opcion si solo quieres entregar una version fija.

1. Descomprimir proyecto.
2. Abrir `cmd` en la raiz del proyecto.
3. Ejecutar:
```bat
build_windows.bat
```
4. Resultado:
- `dist\CuadernoDelTutor\CuadernoDelTutor.exe`
5. Entrega:
- Comprimir `dist\CuadernoDelTutor\` completa y compartir ese ZIP.

Nota: en esta opcion el boton "Actualizar" puede fallar con "not a git repository" si no hay `.git`.

## Opcion B (recomendada para Pilar: con actualizacion desde la app)
Usa esta opcion si quieres poder hacer `git pull` desde la app.

### Requisitos (primera vez)
1. Instalar Git.
2. Instalar Python 3.10+ (marcando "Add Python to PATH").

### Preparacion inicial
1. Abrir `cmd`.
2. Clonar repo:
```bat
cd /d C:\
git clone <URL_DEL_REPO> CuadernoDelTutor
```
3. Entrar y generar EXE:
```bat
cd /d C:\CuadernoDelTutor
build_windows.bat
```
4. Ejecutar siempre desde:
- `C:\CuadernoDelTutor\dist\CuadernoDelTutor\CuadernoDelTutor.exe`

Importante:
- No mover `dist\CuadernoDelTutor\` fuera del repo clonado.
- Si mueves solo el EXE a otra carpeta, perderas la actualizacion por Git.

## Comando manual alternativo (sin .bat)
Si prefieres hacerlo a mano:
```bat
python -m PyInstaller --clean CuadernoDelTutor.spec
```

## Errores comunes
### 1) `python` no se reconoce
- Reinstalar Python con PATH y reabrir `cmd`.

### 2) Error `not a git repository`
- Git esta instalado, pero la carpeta actual no tiene `.git`.
- Solucion: ejecutar la app desde un clon del repo.

### 3) Error `SECRET_KEY environment variable is required`

Este error tiene tres causas posibles, en orden de frecuencia:

**a) El código con el fix no está en GitHub**
El instalador `instalar_todo_1click.bat` clona desde GitHub. Si el arreglo está solo
en local y no se ha hecho `git push`, el EXE construido tendrá el código viejo.
Solución: `git push origin master` antes de que Pilar ejecute el instalador.

**b) `build_windows.bat` no pone el placeholder de SECRET_KEY**
PyInstaller importa `app.py` durante el análisis y necesita SECRET_KEY en el entorno.
Sin el placeholder, el build falla silenciosamente o el EXE generado es incorrecto.
Solución: verificar que `build_windows.bat` tiene el bloque `if not defined SECRET_KEY`.

**c) `desktop.py` importa `app` antes de llamar a `ensure_secret_key()`**
El orden correcto es: `ensure_secret_key()` → `from app import app`.
Si se invierte (por ejemplo, importando `app` a nivel de módulo), la clave no está
en el entorno cuando `app.py` la necesita.
Solución: `from app import app` debe estar **dentro** de `main()`, después de `ensure_secret_key()`.

**Arquitectura actual (correcta):**
```
build_windows.bat        → pone SECRET_KEY=placeholder (para el build)
desktop.py:main()        → ensure_secret_key() lee/genera AppData/secret_key.txt
                         → from app import app  (ya tiene la clave en os.environ)
app.py                   → os.getenv("SECRET_KEY") → funciona
                         → si falla (red de seguridad): lee AppData/secret_key.txt
```

### 4) Antivirus bloquea el EXE
- Anadir excepcion a la carpeta del proyecto o `dist\`.

## Script 1 clic (setup + update + build)
Archivo sugerido: `actualizar_y_build_windows.bat`.

Que hace:
1. Comprueba Git (y lo instala con `winget` si falta).
2. Clona repo si no existe en `C:\CuadernoDelTutor`.
3. Si ya existe, hace `git pull`.
4. Ejecuta `build_windows.bat`.

Notas:
- Puede pedir permisos de administrador para instalar Git.
- Requiere internet para instalar Git y clonar/actualizar.
