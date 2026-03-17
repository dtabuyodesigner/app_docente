#!/bin/bash
# Script para compilar y empaquetar APP_EVALUAR como .deb para Linux

set -e

APP_NAME="cuaderno-del-tutor"
BUILD_VER="1.1-1"
BIN_NAME="CuadernoDelTutor"
SRC_DIR="$(pwd)"
DIST_DIR="${SRC_DIR}/dist"
PKG_DIR="${DIST_DIR}/${APP_NAME}_${BUILD_VER}_amd64"
OPT_DIR="${PKG_DIR}/opt/${APP_NAME}"

echo "=========================================="
echo "    Empaquetando Cuaderno del Tutor (.deb) "
echo "=========================================="

echo "[1/4] Limpiando builds anteriores..."
rm -rf build/
rm -rf "${PKG_DIR}"
rm -f "${DIST_DIR}/${APP_NAME}_${BUILD_VER}_amd64.deb"

echo "[2/4] Compilando con PyInstaller..."
# Intentar usar pyinstaller del venv si existe, si no, el global
PYINSTALLER_BIN="pyinstaller"
if [ -f "${SRC_DIR}/venv/bin/pyinstaller" ]; then
    PYINSTALLER_BIN="${SRC_DIR}/venv/bin/pyinstaller"
fi

# Usamos --onedir porque es más rápido al iniciar en Linux
# y empaquetamos la base de datos vacía y static
$PYINSTALLER_BIN --name "${BIN_NAME}" \
            --windowed \
            --onedir \
            --add-data "static:static" \
            --add-data "schema.sql:." \
            desktop.py

echo "[3/4] Preparando estructura del paquete Debian..."
mkdir -p "${PKG_DIR}/DEBIAN"
mkdir -p "${OPT_DIR}"
mkdir -p "${PKG_DIR}/usr/share/applications"
mkdir -p "${PKG_DIR}/usr/share/pixmaps"

# Mover el binario compilado (onedir) a /opt/
cp -r ${DIST_DIR}/${BIN_NAME}/* "${OPT_DIR}/"

# Icono
cp static/icon-512.png "${PKG_DIR}/usr/share/pixmaps/${APP_NAME}.png"

# Archivo Desktop
cp AppEvaluar.desktop "${PKG_DIR}/usr/share/applications/"

# Permisos requeridos
chmod 755 "${OPT_DIR}/${BIN_NAME}"
find "${PKG_DIR}" -type d -exec chmod 755 {} +

# Crear archivo de control Debian
cat <<EOF > "${PKG_DIR}/DEBIAN/control"
Package: ${APP_NAME}
Version: ${BUILD_VER}
Section: education
Priority: optional
Architecture: amd64
Depends: gir1.2-webkit2-4.1, python3-gi, gir1.2-gtk-3.0
Maintainer: Tutor <soporte@ejemplo.com>
Description: Cuaderno del Tutor
 Aplicacion offline para el profesorado: programacion, diario 
 y evaluacion por rubricas, SDA y LOMLOE.
EOF

# Permisos del directorio DEBIAN
chmod 755 "${PKG_DIR}/DEBIAN"
chmod 644 "${PKG_DIR}/DEBIAN/control"

echo "[4/4] Construyendo el archivo .deb..."
dpkg-deb --build "${PKG_DIR}"

echo "=========================================="
echo " ✅ Paquete creado exitosamente en: "
echo " ${DIST_DIR}/${APP_NAME}_${BUILD_VER}_amd64.deb"
echo "=========================================="
