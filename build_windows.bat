@echo off
REM Construye el ejecutable para Windows usando PyInstaller
echo Construyendo Cuaderno del Tutor para Windows...

pyinstaller --name "CuadernoDelTutor" ^
            --windowed ^
            --add-data "static;static" ^
            --add-data "schema.sql;." ^
            desktop.py

echo Build completado. Revisa la carpeta dist/
pause
