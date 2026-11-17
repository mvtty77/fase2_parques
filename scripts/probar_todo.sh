#!/usr/bin/env bash
# Ejecuta sql/05_pruebas.sql (conteos, pruebas negativas y R1-R12) y las 13 pruebas pytest.
# Deja la salida en docs/evidencias/. Las líneas ERROR del bloque B son ESPERADAS.
source "$(dirname "$0")/_comun.sh"
cd "$RAIZ"
mkdir -p docs/evidencias
bash scripts/mysql_root.sh -t -vv --force < sql/05_pruebas.sql > docs/evidencias/codespace_pruebas_sql.txt 2>&1 || true
echo ">> SQL: $(grep -c '^ERROR' docs/evidencias/codespace_pruebas_sql.txt) errores esperados (deben ser 13). Detalle en docs/evidencias/codespace_pruebas_sql.txt"
PY="$HOME/.venv/bin/python"; [ -x "$PY" ] || PY="python3"
"$PY" -m pytest -v tests/ 2>&1 | tee docs/evidencias/codespace_pytest.txt | tail -3
