#!/bin/bash
# Script para arrancar la aplicación Cuaderno del Tutor automáticamente

PROJECT_DIR="/home/danito73/Documentos/APP_EVALUAR"

echo "------------------------------------------"
echo "Iniciando Cuaderno del Tutor..."
echo "------------------------------------------"

cd "$PROJECT_DIR" || exit

# Activar el entorno virtual
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Error: No se encontró el entorno virtual 'venv'."
    exit 1
fi

# Cerrar instancias previas para evitar conflictos
echo "Limpiando procesos anteriores en puerto 5000..."
fuser -k 5000/tcp > /dev/null 2>&1
pkill -f "python3 app.py" > /dev/null 2>&1
sleep 1

# Iniciar la aplicación en segundo plano
echo "Arrancando el servidor Flask..."
nohup python3 app.py > app.log 2>&1 &
APP_PID=$!

# Esperar a que el servidor esté listo (máximo 20 segundos)
echo "Esperando a que el servidor responda..."
SERVER_READY=0
for i in {1..20}; do
    if curl -s "http://127.0.0.1:5000/login" > /dev/null; then
        echo "Servidor listo en el puerto 5000."
        SERVER_READY=1
        break
    fi
    echo -n "."
    sleep 1
done
echo ""

if [ $SERVER_READY -eq 0 ]; then
    echo "Error: El servidor no arrancó correctamente. Revisa app.log"
    exit 1
fi

# Abrir el navegador con un pequeño retardo adicional para asegurar que el motor de plantillas esté listo
echo "Abriendo el navegador..."
( 
    sleep 2
    if command -v xdg-open > /dev/null; then
        xdg-open "http://127.0.0.1:5000"
    elif command -v open > /dev/null; then
        open "http://127.0.0.1:5000"
    else
        echo "Abre http://127.0.0.1:5000 manualmente"
    fi
) &

echo "Aplicación iniciada con PID $APP_PID."
echo "Puedes ver los logs en tiempo real con: tail -f app.log"
echo "------------------------------------------"
sleep 1
