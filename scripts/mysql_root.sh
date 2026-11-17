#!/usr/bin/env bash
# Abre MySQL como root (Ubuntu: autenticación por socket, sin contraseña). Acepta argumentos de mysql.
source "$(dirname "$0")/_comun.sh"
exec $SUDO mysql --default-character-set=utf8mb4 "$@"
