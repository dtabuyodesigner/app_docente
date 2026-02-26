#!/bin/bash
# Builds the .app bundle for macOS
echo "Construyendo Cuaderno del Tutor para macOS..."

pyinstaller --name "CuadernoDelTutor" \
            --windowed \
            --add-data "static:static" \
            --add-data "schema.sql:." \
            desktop.py

echo "Build completado. Revisa la carpeta dist/"
