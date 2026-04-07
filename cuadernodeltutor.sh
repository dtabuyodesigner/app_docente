#!/bin/bash
# Cuaderno del Tutor - Script de arranque para Linux
# Coloca este archivo en la raíz del proyecto: ~/Documentos/APP_EVALUAR/

PROJECT_DIR="$HOME/Documentos/APP_EVALUAR"
VENV="$PROJECT_DIR/venv/bin/python"

cd "$PROJECT_DIR"
exec "$VENV" desktop.py
