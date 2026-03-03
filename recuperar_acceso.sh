#!/bin/bash
echo "==================================================="
echo "  INICIANDO RECUPERACION DE ACCESO A CUADERNO"
echo "==================================================="
echo ""
cd "$(dirname "$0")"
source venv/bin/activate
python scripts/recover_admin.py
echo ""
read -p "Presiona enter para continuar..."
