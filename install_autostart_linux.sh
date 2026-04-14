#!/bin/bash
# Instala el autoarranque de Cuaderno del Tutor como servicio systemd de usuario.
# Ejecutar una sola vez tras instalar la app.

set -e

SERVICE_NAME="cuadernodeltutor"
PROJECT_DIR="$HOME/Documentos/APP_EVALUAR"
SYSTEMD_DIR="$HOME/.config/systemd/user"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Instalando autoarranque — Cuaderno del Tutor"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Crear directorio systemd del usuario si no existe
mkdir -p "$SYSTEMD_DIR"

# Copiar el archivo .service
cp "$PROJECT_DIR/$SERVICE_NAME.service" "$SYSTEMD_DIR/$SERVICE_NAME.service"
echo "✓ Servicio copiado en $SYSTEMD_DIR"

# Recargar systemd y habilitar el servicio
systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME"
systemctl --user start "$SERVICE_NAME"
echo "✓ Servicio habilitado y arrancado"

# Habilitar lingering para que el servicio arranque aunque el usuario no haya iniciado sesión en terminal
loginctl enable-linger "$USER" 2>/dev/null || true

echo ""
echo "Estado del servicio:"
systemctl --user status "$SERVICE_NAME" --no-pager

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Listo. El servidor arrancará automáticamente"
echo "  al iniciar sesión en el portátil."
echo ""
echo "  Comandos útiles:"
echo "  · Ver logs:    journalctl --user -u $SERVICE_NAME -f"
echo "  · Parar:       systemctl --user stop $SERVICE_NAME"
echo "  · Reiniciar:   systemctl --user restart $SERVICE_NAME"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
