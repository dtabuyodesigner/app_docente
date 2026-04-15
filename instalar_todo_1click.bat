@echo off
setlocal EnableDelayedExpansion

REM =====================================================
REM instalar_todo_1click.bat
REM Instalacion completa para Pilar:
REM 1) Instala Git si falta
REM 2) Instala Python si falta
REM 3) Clona/actualiza repo
REM 4) Build del EXE
REM 5) Abre la app
REM =====================================================

set "REPO_URL=https://github.com/dtabuyodesigner/app_docente.git"
set "TARGET_DIR=C:\CuadernoDelTutor"

echo ====================================================
echo   Cuaderno del Tutor - Instalacion 1 clic
echo ====================================================
echo.
echo Este proceso puede tardar varios minutos la primera vez.
echo.

where winget >nul 2>&1
if errorlevel 1 (
    echo [ERROR] winget no esta disponible en este Windows.
    echo         Solucion: actualizar Windows o instalar App Installer desde Microsoft Store.
    pause
    exit /b 1
)

where git >nul 2>&1
if errorlevel 1 (
    echo [INFO] Git no detectado. Instalando...
    winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo [ERROR] No se pudo instalar Git automaticamente.
        pause
        exit /b 1
    )
)

echo [OK] Git:
git --version

echo.
python --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Python no detectado. Instalando...
    winget install --id Python.Python.3.12 -e --source winget --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo [ERROR] No se pudo instalar Python automaticamente.
        pause
        exit /b 1
    )
)

echo [OK] Python:
python --version

echo.
if exist "%TARGET_DIR%\.git" (
    echo [INFO] Repo ya existe. Actualizando con git pull...
    cd /d "%TARGET_DIR%"
    git pull
    if errorlevel 1 (
        echo [ERROR] Fallo en git pull.
        pause
        exit /b 1
    )
) else (
    echo [INFO] Clonando repo en %TARGET_DIR% ...
    cd /d C:\
    git clone "%REPO_URL%" "%TARGET_DIR%"
    if errorlevel 1 (
        echo [ERROR] Fallo en git clone.
        pause
        exit /b 1
    )
)

echo.
cd /d "%TARGET_DIR%"
if not exist "build_windows.bat" (
    echo [ERROR] No existe build_windows.bat en %TARGET_DIR%
    pause
    exit /b 1
)

echo [INFO] Generando EXE...
REM SECRET_KEY necesaria para que PyInstaller pueda importar app.py en el analisis
if not defined SECRET_KEY set "SECRET_KEY=pyinstaller-build-placeholder-not-used-at-runtime"
call build_windows.bat
if errorlevel 1 (
    echo [ERROR] Build fallido.
    pause
    exit /b 1
)

set "EXE_PATH=%TARGET_DIR%\dist\CuadernoDelTutor\CuadernoDelTutor.exe"
echo.
if exist "%EXE_PATH%" (
    echo [OK] Instalacion completada.

    REM ── Crear acceso directo en el Escritorio ────────────────────────────
    REM    Join-Path en PowerShell maneja el espacio en "Cuaderno del Tutor.lnk"
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$wsh = New-Object -ComObject WScript.Shell; $sc = $wsh.CreateShortcut((Join-Path $env:USERPROFILE 'Desktop\Cuaderno del Tutor.lnk')); $sc.TargetPath = '%EXE_PATH%'; $sc.WorkingDirectory = '%TARGET_DIR%\dist\CuadernoDelTutor'; $sc.Description = 'Cuaderno del Tutor'; $sc.Save()"
    if errorlevel 1 (
        echo [AVISO] No se pudo crear el acceso directo automaticamente.
        echo         Crea uno manualmente desde: %EXE_PATH%
    ) else (
        echo [OK] Acceso directo "Cuaderno del Tutor" creado en el Escritorio.
    )

    echo [OK] Abriendo la app...
    start "" "%EXE_PATH%"
) else (
    echo [ERROR] No se encontro el EXE final en:
    echo         %EXE_PATH%
)

echo.
echo Para volver a abrir la app: usa el acceso directo del Escritorio
echo                              o ejecuta: %EXE_PATH%
echo.
echo Para actualizar en el futuro: vuelve a ejecutar este mismo archivo.
pause
