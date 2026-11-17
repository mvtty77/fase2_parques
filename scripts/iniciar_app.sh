#!/usr/bin/env bash
# Abre (o reinicia) el PMV Streamlit en segundo plano, puerto 8501. Registro en /tmp/streamlit.log
source "$(dirname "$0")/_comun.sh"
cd "$RAIZ"
STREAMLIT="$HOME/.venv/bin/streamlit"; [ -x "$STREAMLIT" ] || STREAMLIT="streamlit"
pkill -f "streamlit run app/main.py" 2>/dev/null || true
nohup setsid "$STREAMLIT" run app/main.py --server.port 8501 --server.headless true > /tmp/streamlit.log 2>&1 &
for i in $(seq 1 30); do curl -s -m 2 http://localhost:8501/_stcore/health >/dev/null 2>&1 && { echo ">> PMV abierto en el puerto 8501"; exit 0; }; sleep 1; done
echo "!! La app no respondió. Revise: cat /tmp/streamlit.log"; exit 1
