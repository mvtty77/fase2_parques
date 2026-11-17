#!/usr/bin/env bash
# Crea (o actualiza) el usuario de la aplicación con los datos de .env.
# Solo tiene permisos sobre parques_db. mysql_native_password: compatible con SQLTools y Workbench.
source "$(dirname "$0")/_comun.sh"
case "$DB_PASSWORD" in *"'"*|"") echo "!! DB_PASSWORD en .env no puede estar vacía ni tener comillas simples"; exit 1;; esac
bash "$RAIZ/scripts/mysql_root.sh" <<SQL
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED WITH mysql_native_password BY '$DB_PASSWORD';
CREATE USER IF NOT EXISTS '$DB_USER'@'%' IDENTIFIED WITH mysql_native_password BY '$DB_PASSWORD';
ALTER USER '$DB_USER'@'localhost' IDENTIFIED WITH mysql_native_password BY '$DB_PASSWORD';
ALTER USER '$DB_USER'@'%' IDENTIFIED WITH mysql_native_password BY '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON \`$DB_NAME\`.* TO '$DB_USER'@'localhost';
GRANT ALL PRIVILEGES ON \`$DB_NAME\`.* TO '$DB_USER'@'%';
FLUSH PRIVILEGES;
SQL
echo ">> Usuario de la app listo: $DB_USER (contraseña en .env)"
