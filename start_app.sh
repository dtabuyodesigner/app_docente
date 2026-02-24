#!/bin/bash
# Script para arrancar la aplicación Cuaderno del Tutor automáticamente

PROJECT_DIR="/home/danito73/Documentos/APP_EVALUAR"

echo "Iniciando Cuaderno del Tutor..."

cd "$PROJECT_DIR" || exit

# Activar el entorno virtual
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Error: No se encontró el entorno virtual 'venv'."
    exit 1
fi

# Cerrar instancias previas para evitar conflictos
echo "Limpiando procesos anteriores..."
fuser -k 5000/tcp > /dev/null 2>&1
pkill -f "python3 app.py" > /dev/null 2>&1

# Iniciar la aplicación en segundo plano
echo "Arrancando el servidor Flask..."
nohup python3 app.py > app.log 2>&1 &
APP_PID=$!

# Esperar a que el servidor esté listo (máximo 10 segundos)
echo "Esperando a que el servidor responda..."
for i in {1..10}; do
    if curl -s "http://127.0.0.1:5000" > /dev/null; then
        echo "Servidor listo."
        break
    fi
    sleep 1
done

# Abrir el navegador predeterminado
echo "Abriendo el navegador..."
( xdg-open "http://127.0.0.1:5000" || open "http://127.0.0.1:5000" || echo "Abre http://127.0.0.1:5000 manualmente" ) &

echo "Aplicación iniciada con PID $APP_PID. Los logs se guardan en app.log"
sleep 2
