#!/usr/bin/env bash
# =============================================================================
# release.sh — Gestor de versiones y releases para APP_EVALUAR
#
# Uso:
#   ./release.sh           → bump patch  (1.1.22 → 1.1.23)
#   ./release.sh minor     → bump minor  (1.1.22 → 1.2.0)
#   ./release.sh major     → bump major  (1.1.22 → 2.0.0)
#   ./release.sh preview   → muestra cambios pendientes sin commitear
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION_FILE="$SCRIPT_DIR/VERSION"
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

cd "$SCRIPT_DIR"

# ─── helpers ──────────────────────────────────────────────────────────────────
read_version() { cat "$VERSION_FILE" | tr -d '[:space:]'; }

bump_version() {
    local ver="$1" type="$2"
    IFS='.' read -r major minor patch <<< "$ver"
    case "$type" in
        major) echo "$((major+1)).0.0" ;;
        minor) echo "${major}.$((minor+1)).0" ;;
        *)     echo "${major}.${minor}.$((patch+1))" ;;  # patch (default)
    esac
}

show_pending_changes() {
    echo ""
    echo -e "${CYAN}══════════════════════════════════════════${NC}"
    echo -e "${CYAN}  CAMBIOS PENDIENTES DE SUBIR A GIT${NC}"
    echo -e "${CYAN}══════════════════════════════════════════${NC}"

    # Ficheros modificados/nuevos no staged
    local unstaged
    unstaged=$(git diff --name-only 2>/dev/null)
    if [[ -n "$unstaged" ]]; then
        echo -e "${YELLOW}📝 Ficheros modificados (no staged):${NC}"
        echo "$unstaged" | sed 's/^/   • /'
        echo ""
    fi

    # Ficheros staged
    local staged
    staged=$(git diff --cached --name-only 2>/dev/null)
    if [[ -n "$staged" ]]; then
        echo -e "${GREEN}✅ Ficheros staged:${NC}"
        echo "$staged" | sed 's/^/   • /'
        echo ""
    fi

    # Ficheros nuevos untracked
    local untracked
    untracked=$(git ls-files --others --exclude-standard 2>/dev/null)
    if [[ -n "$untracked" ]]; then
        echo -e "${BLUE}🆕 Ficheros nuevos (untracked):${NC}"
        echo "$untracked" | sed 's/^/   • /'
        echo ""
    fi

    # Resumen de líneas cambiadas
    local diffstat
    diffstat=$(git diff --stat HEAD 2>/dev/null)
    if [[ -n "$diffstat" ]]; then
        echo -e "${CYAN}📊 Resumen de cambios:${NC}"
        echo "$diffstat" | sed 's/^/   /'
        echo ""
    fi

    if [[ -z "$unstaged" && -z "$staged" && -z "$untracked" ]]; then
        echo -e "${YELLOW}⚠️  No hay cambios pendientes en el árbol de trabajo.${NC}"
        echo ""
    fi
}

# ─── modo preview ─────────────────────────────────────────────────────────────
if [[ "$1" == "preview" ]]; then
    CURRENT=$(read_version)
    echo -e "${BLUE}📦 Versión actual: ${GREEN}v${CURRENT}${NC}"
    show_pending_changes
    exit 0
fi

# ─── bump type ────────────────────────────────────────────────────────────────
BUMP_TYPE="${1:-patch}"
if [[ "$BUMP_TYPE" != "patch" && "$BUMP_TYPE" != "minor" && "$BUMP_TYPE" != "major" ]]; then
    echo -e "${RED}❌ Tipo de bump inválido: '$BUMP_TYPE'. Usa: patch | minor | major | preview${NC}"
    exit 1
fi

# ─── mostrar estado ───────────────────────────────────────────────────────────
CURRENT=$(read_version)
NEW_VERSION=$(bump_version "$CURRENT" "$BUMP_TYPE")

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        APP_EVALUAR — Release Tool        ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════╝${NC}"
echo -e "  Versión actual : ${YELLOW}v${CURRENT}${NC}"
echo -e "  Nueva versión  : ${GREEN}v${NEW_VERSION}${NC}  (bump: ${BUMP_TYPE})"

show_pending_changes

# ─── pedir descripción ────────────────────────────────────────────────────────
echo -e "${CYAN}✏️  Describe brevemente los cambios de esta release:${NC}"
read -r DESCRIPTION

if [[ -z "$DESCRIPTION" ]]; then
    echo -e "${RED}❌ La descripción no puede estar vacía. Release cancelada.${NC}"
    exit 1
fi

# ─── confirmar ────────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}¿Confirmas el release?${NC}"
echo -e "  Commit: ${GREEN}v${NEW_VERSION}: ${DESCRIPTION}${NC}"
echo -e "  Branch: ${CYAN}$(git branch --show-current)${NC}"
echo -n "  [s/N] → "
read -r CONFIRM
CONFIRM="${CONFIRM,,}"  # lowercase

if [[ "$CONFIRM" != "s" && "$CONFIRM" != "si" && "$CONFIRM" != "y" && "$CONFIRM" != "yes" ]]; then
    echo -e "${YELLOW}⚠️  Release cancelada por el usuario.${NC}"
    exit 0
fi

# ─── actualizar VERSION ───────────────────────────────────────────────────────
echo "$NEW_VERSION" > "$VERSION_FILE"
echo -e "${GREEN}✅ VERSION actualizado: v${CURRENT} → v${NEW_VERSION}${NC}"

# ─── git add + commit + push ──────────────────────────────────────────────────
git add -A
git commit -m "v${NEW_VERSION}: ${DESCRIPTION}"
echo -e "${GREEN}✅ Commit creado: v${NEW_VERSION}: ${DESCRIPTION}${NC}"

BRANCH=$(git branch --show-current)
git push origin "$BRANCH"
echo -e "${GREEN}✅ Push a origin/${BRANCH} completado.${NC}"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   🚀 Release v${NEW_VERSION} publicada!   ${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
