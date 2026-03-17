@echo off
setlocal EnableDelayedExpansion
title Cuaderno del Tutor - Build Windows

echo ============================================
echo   Cuaderno del Tutor - Build para Windows
echo ============================================
echo.

REM ── Comprobar que Python está disponible ──────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado. Instala Python 3.10+ y asegurate de que
    echo         este en el PATH del sistema.
    pause
    exit /b 1
)
echo [OK] Python encontrado:
python --version

REM ── Activar entorno virtual si existe ────────────────────────────────────
if exist venv\Scripts\activate.bat (
    echo [INFO] Activando entorno virtual...
    call venv\Scripts\activate.bat
) else (
    echo [INFO] No se encontro entorno virtual. Usando Python del sistema.
    echo [INFO] Recomendado: crea uno con  python -m venv venv
)
echo.

REM ── Comprobar PyInstaller ─────────────────────────────────────────────────
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] PyInstaller no encontrado. Instalando dependencias...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Fallo al instalar dependencias. Revisa requirements.txt
        pause
        exit /b 1
    )
) else (
    echo [OK] PyInstaller encontrado:
    python -m PyInstaller --version
)
echo.

REM ── Limpiar builds anteriores ─────────────────────────────────────────────
echo Limpiando builds anteriores...
if exist build\ (
    rmdir /s /q build\
    echo [OK] Carpeta build\ eliminada.
)
if exist dist\ (
    rmdir /s /q dist\
    echo [OK] Carpeta dist\ eliminada.
)
echo.

REM ── Ejecutar PyInstaller ──────────────────────────────────────────────────
echo Ejecutando PyInstaller...
python -m PyInstaller --clean CuadernoDelTutor.spec

if errorlevel 1 (
    echo.
    echo [ERROR] El build ha fallado. Revisa los mensajes anteriores.
    echo         Busca lineas que empiecen por ERROR o WARNING critico.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Build completado con exito!
echo ============================================
echo.
echo El ejecutable esta en:
echo   dist\CuadernoDelTutor\CuadernoDelTutor.exe
echo.
echo SIGUIENTE PASO:
echo   - Ejecuta el .exe y comprueba que abre el navegador
echo   - Si el antivirus lo bloquea, agrega excepcion a la carpeta dist\
echo   - Si el Firewall de Windows pregunta, haz clic en "Permitir acceso"
echo   - Primera vez: te pedira crear un usuario administrador
echo.
echo Para version final de Pilar:
echo   - Cambia console=True a console=False en CuadernoDelTutor.spec
echo   - Vuelve a ejecutar este script
echo.
pause
