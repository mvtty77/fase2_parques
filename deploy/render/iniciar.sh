#!/bin/bash
# Arranque de la demo en línea: inicia MySQL, carga parques_db y abre el PMV.
# La base se carga desde sql/00_integral.sql en cada arranque, así que la demo
# siempre vuelve a los datos originales.
set -e
PORT="${PORT:-10000}"
DB_USER="${DB_USER:-parques_app}"
DB_PASSWORD="${DB_PASSWORD:-AppDemo2026}"
SOCK=/var/run/mysqld/mysqld.sock
OPTS=(--user=mysql --datadir=/var/lib/mysql --socket="$SOCK" --bind-address=127.0.0.1
      --skip-mysqlx --skip-log-bin --performance-schema=OFF
      --innodb-buffer-pool-size=48M --innodb-log-buffer-size=8M --key-buffer-size=8M
      --max-connections=30 --table-open-cache=256
      --character-set-server=utf8mb4 --collation-server=utf8mb4_spanish_ci)

mkdir -p /var/run/mysqld && chown mysql:mysql /var/run/mysqld
if [ ! -d /var/lib/mysql/mysql ]; then
  echo "[demo] Inicializando MySQL..."
  mysqld "${OPTS[@]}" --initialize-insecure
fi
mysqld "${OPTS[@]}" &
for i in $(seq 90); do
  mysqladmin --socket="$SOCK" -uroot ping --silent 2>/dev/null && break
  sleep 1
done

echo "[demo] Cargando parques_db..."
mysql --socket="$SOCK" -uroot < /app/sql/00_integral.sql
mysql --socket="$SOCK" -uroot <<SQL
CREATE USER IF NOT EXISTS '${DB_USER}'@'%' IDENTIFIED BY '${DB_PASSWORD}';
ALTER USER '${DB_USER}'@'%' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON parques_db.* TO '${DB_USER}'@'%';
FLUSH PRIVILEGES;
SQL
echo "[demo] Base lista. Iniciando la aplicación en el puerto ${PORT}..."
export DB_USER DB_PASSWORD
exec python3.11 -m streamlit run app/main.py \
  --server.port="$PORT" --server.address=0.0.0.0 --server.headless=true
