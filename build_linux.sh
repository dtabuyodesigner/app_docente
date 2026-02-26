#!/bin/bash
# Install dependencies from requirements if needed, then build using pyinstaller
# Assumes you are activating your virtualenv before running

echo "Construyendo Cuaderno del Tutor para Linux..."
pyinstaller --name "CuadernoDelTutor" \
            --windowed \
            --add-data "static:static" \
            --add-data "schema.sql:." \
            desktop.py

echo "Build completado. Revisa la carpeta dist/"
