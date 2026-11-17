#!/usr/bin/env bash
# Se ejecuta CADA vez que el Codespace se inicia:
#   1) enciende MySQL  2) crea parques_db si no existe  3) asegura el usuario de la app
#   4) abre el PMV Streamlit en el puerto 8501
set -euo pipefail
cd "$(dirname "$0")/.."
bash scripts/encender_mysql.sh

if ! bash scripts/mysql_root.sh -N -e "SHOW DATABASES LIKE 'parques_db'" | grep -q parques_db; then
  echo ">> La base no existe: ejecutando sql/00_integral.sql (unos segundos)..."
  bash scripts/mysql_root.sh < sql/00_integral.sql
fi
bash scripts/crear_usuario_app.sh
bash scripts/iniciar_app.sh

echo ""
echo "=================================================================="
echo " Listo. MySQL 8 con parques_db y el PMV en la pestaña PUERTOS (8501)"
echo " App: usuario admin / contraseña Parques2026!"
echo " SQL: abra sql/06_requerimientos_R1_R12.sql y ejecútelo con SQLTools"
echo "      o en la terminal:  bash scripts/consola_mysql.sh"
echo "=================================================================="
