@echo off
SETLOCAL EnableDelayedExpansion

echo ==========================================
echo   Cuaderno del Tutor - MODO DESARROLLADOR
echo ==========================================
echo.

:: 1. Verificar si existe Python
echo [+] Verificando instalacion de Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] No se encuentra el comando 'python'. 
    echo Intentando con el comando 'py'
    py --version >nul 2>&1
    if !errorlevel! equ 0 (
        SET PY_CMD=py
        echo [OK] Usando comando 'py'
    ) else (
        echo [CRITICO] No se encuentra Python en el sistema.
        echo Por favor, instalalo desde https://www.python.org/
        echo IMPORTANTE: Marca la casilla "Add Python to PATH" en la instalacion.
        pause
        exit /b
    )
) else (
    SET PY_CMD=python
    echo [OK] Usando comando 'python'
)

:: 2. Crear entorno virtual si no existe
if not exist venv (
    echo [+] Creando entorno virtual - esto solo ocurre la primera vez
    !PY_CMD! -m venv venv
    if !errorlevel! neq 0 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b
    )
    echo [OK] Entorno virtual creado.
)

:: 3. Activar venv e instalar dependencias
echo [+] Activando entorno virtual
if not exist venv\Scripts\activate.bat (
    echo [ERROR] No se encuentra el script de activacion.
    echo Borra la carpeta 'venv' e intenta de nuevo.
    pause
    exit /b
)
call venv\Scripts\activate.bat

echo [+] Actualizando pip...
python -m pip install --upgrade pip

echo [+] Verificando librerias (esto puede tardar la primera vez)
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] No se han podido instalar las librerias.
    echo Esto suele pasar si falta algun componente de Windows.
    echo Probando instalacion ligera (Safe Mode - Solo binarios)...
    pip install --only-binary :all: Flask Flask-WTF matplotlib numpy pandas pillow reportlab requests python-dotenv flasgger openpyxl
)

:: 4. Lanzar la aplicacion
echo.
echo ==========================================
echo   PREPARANDO SERVIDOR...
echo ==========================================
echo.

:: Abrir el navegador automaticamente tras un pequeno retardo
echo [+] Abriendo navegador en http://127.0.0.1:5000
timeout /t 3 /nobreak >nul
start http://127.0.0.1:5000

echo [+] Iniciando servidor Flask...
python app.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] La aplicacion se ha detenido inesperadamente.
    echo Codigo de error: %errorlevel%
    echo Revisa los mensajes de arriba antes de cerrar.
    pause
) else (
    echo.
    echo [OK] El servidor se ha cerrado normalmente.
    pause
)

echo.
echo Presiona una tecla para cerrar esta ventana...
pause >nul
