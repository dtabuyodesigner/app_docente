#!/bin/bash
# Cuaderno del Tutor — abre la app en el navegador.
# Si el servidor ya está corriendo (autoarranque), solo abre el navegador.
# Si no está corriendo, lo arranca y abre el navegador.

PROJECT_DIR="$HOME/Documentos/APP_EVALUAR"
VENV="$PROJECT_DIR/venv/bin/python"

# Buscar el puerto en el que está escuchando el servidor
get_server_url() {
    local port
    port=$(ss -tlnp 2>/dev/null | grep "python" | grep -oP ':\K[0-9]+' | head -1)
    if [ -n "$port" ]; then
        echo "http://127.0.0.1:$port"
    fi
}

open_browser() {
    local url="$1"
    if command -v xdg-open > /dev/null; then
        xdg-open "$url"
    elif command -v open > /dev/null; then
        open "$url"
    else
        echo "Abre manualmente: $url"
    fi
}

URL=$(get_server_url)

if [ -n "$URL" ]; then
    echo "Servidor ya en marcha → abriendo $URL"
    open_browser "$URL"
else
    echo "Servidor no encontrado → arrancando..."
    export SECRET_KEY="032e62aa45336c139df941541738fd60f56e914a5a835eb9352466cb5161530a"
    cd "$PROJECT_DIR"
    exec "$VENV" desktop.py
fi
