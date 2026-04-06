#!/usr/bin/env bash
# setup.sh — Bootstrap complet : venv Poetry + pre-commit + Ruff
# Usage : bash setup.sh

set -euo pipefail

# ─── Couleurs ─────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()    { echo -e "${CYAN}▶ $*${NC}"; }
success() { echo -e "${GREEN}✅ $*${NC}"; }
warn()    { echo -e "${YELLOW}⚠️  $*${NC}"; }
error()   { echo -e "${RED}❌ $*${NC}"; exit 1; }

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════╗"
echo "║   🕷️  AI Scraper — Setup de l'environnement ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# ─── 1. Vérification Poetry ───────────────────────────────────────────────────
info "Vérification de Poetry..."
if ! command -v poetry &>/dev/null; then
    warn "Poetry non trouvé — installation en cours..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi
success "Poetry $(poetry --version | cut -d' ' -f3)"

# ─── 2. venv dans le projet (.venv/) ─────────────────────────────────────────
info "Configuration du venv local (.venv/)..."
poetry config virtualenvs.in-project true

# ─── 3. Installation des dépendances ─────────────────────────────────────────
info "Installation des dépendances (prod + dev)..."
poetry install --with dev
success "Dépendances installées"

# ─── 4. pre-commit ───────────────────────────────────────────────────────────
info "Installation des hooks pre-commit..."
poetry run pre-commit install
success "Hooks pre-commit activés"

# ─── 5. Ruff : vérification initiale ─────────────────────────────────────────
info "Vérification Ruff initiale..."
if poetry run ruff check . --quiet; then
    success "Ruff : aucune erreur"
else
    warn "Ruff a détecté des problèmes — lancez 'poetry run ruff check . --fix'"
fi

# ─── 6. Rappel clé API ───────────────────────────────────────────────────────
echo ""
if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
    warn "Variable ANTHROPIC_API_KEY non définie."
    echo "    Ajoutez dans ~/.bashrc (ou ~/.zshrc) :"
    echo "    export ANTHROPIC_API_KEY=\"sk-ant-...\""
else
    success "ANTHROPIC_API_KEY détectée"
fi

# ─── Résumé ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  Setup terminé ! Commandes utiles :${NC}"
echo ""
echo "  poetry run python main.py          # Mode interactif"
echo "  poetry run python main.py --help   # Aide CLI"
echo "  poetry run pytest                  # Tests"
echo "  poetry run ruff check .            # Lint"
echo "  poetry run ruff format .           # Format"
echo "  pre-commit run --all-files         # Vérif complète"
echo -e "${GREEN}════════════════════════════════════════${NC}"
