#!/bin/bash
# Cuaderno del Tutor — abre la app en el navegador.
# Si el servidor ya está corriendo en el puerto 5000, solo abre el navegador.
# Si no, lo arranca (y abre el navegador automáticamente).

PROJECT_DIR="$HOME/Documentos/APP_EVALUAR"
VENV="$PROJECT_DIR/venv/bin/python"
URL="http://127.0.0.1:5000"

open_browser() {
    if command -v xdg-open > /dev/null; then
        xdg-open "$URL"
    elif command -v open > /dev/null; then
        open "$URL"
    else
        echo "Abre manualmente: $URL"
    fi
}

if nc -z 127.0.0.1 5000 2>/dev/null; then
    echo "Servidor ya en marcha → abriendo $URL"
    open_browser
else
    echo "Servidor no encontrado → arrancando..."
    export SECRET_KEY="032e62aa45336c139df941541738fd60f56e914a5a835eb9352466cb5161530a"
    cd "$PROJECT_DIR"
    exec "$VENV" desktop.py
fi
