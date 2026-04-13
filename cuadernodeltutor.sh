#!/bin/bash
# Cuaderno del Tutor - Script de arranque para Linux
# Coloca este archivo en la raíz del proyecto: ~/Documentos/APP_EVALUAR/

PROJECT_DIR="$HOME/Documentos/APP_EVALUAR"
VENV="$PROJECT_DIR/venv/bin/python"

cd "$PROJECT_DIR"

# SECRET_KEY para sesiones — generada una vez, no cambiar en producción
export SECRET_KEY="032e62aa45336c139df941541738fd60f56e914a5a835eb9352466cb5161530a"

exec "$VENV" desktop.py
