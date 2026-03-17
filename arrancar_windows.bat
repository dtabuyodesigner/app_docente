@echo off
echo ==============================================
echo  Iniciando Cuaderno del Tutor (Modo Developer)
echo ==============================================

if exist venv\Scripts\activate.bat (
    echo [OK] Entorno virtual encontrado. Activando...
    call venv\Scripts\activate.bat
) else (
    echo [INFO] No se encontro entorno virtual. Creando uno...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual. Asegurate de tener Python instalado.
        pause
        exit /b %errorlevel%
    )
    echo [OK] venv creado. Instalando dependencias...
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Hubo un problema instalando los requisitos.
        pause
        exit /b %errorlevel%
    )
)

echo [OK] Iniciando la aplicacin...
python desktop.py

if errorlevel 1 (
    echo [ERROR] La aplicacion se cerro con errores.
    pause
)
