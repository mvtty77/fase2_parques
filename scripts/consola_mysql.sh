#!/usr/bin/env bash
# Consola MySQL con el usuario de la app, ya dentro de parques_db. Salir con: exit
source "$(dirname "$0")/_comun.sh"
MYSQL_PWD="$DB_PASSWORD" exec mysql -h 127.0.0.1 -u "$DB_USER" --default-character-set=utf8mb4 "$DB_NAME" "$@"
