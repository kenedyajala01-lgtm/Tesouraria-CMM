#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# run.sh — Inicialização da Tesouraria Grêmio Naval
# Uso: bash run.sh
# ─────────────────────────────────────────────────────────────────

set -e

# Vai para o diretório do script independente de onde for chamado
cd "$(dirname "$0")"

echo "⚓ Tesouraria Grêmio Naval"
echo "──────────────────────────"

# Instala dependências se necessário
if ! python -c "import streamlit" 2>/dev/null; then
    echo "📦 Instalando dependências..."
    pip install -r requirements.txt --quiet
else
    echo "✅ Dependências OK"
fi

echo "🚀 Iniciando aplicação em http://localhost:8501"
echo ""

streamlit run app.py \
    --server.port 8501 \
    --server.headless false \
    --browser.gatherUsageStats false
