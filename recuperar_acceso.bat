@echo off
echo ===================================================
echo   INICIANDO RECUPERACION DE ACCESO A CUADERNO
echo ===================================================
echo.
cd /d "%~dp0"
call venv\Scripts\activate.bat
python scripts\recover_admin.py
echo.
pause
