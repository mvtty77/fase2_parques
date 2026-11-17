#!/usr/bin/env bash
# Enciende MySQL si está apagado y espera a que responda.
source "$(dirname "$0")/_comun.sh"
if $SUDO mysqladmin ping --silent 2>/dev/null; then echo ">> MySQL ya está encendido."; exit 0; fi
echo ">> Encendiendo MySQL..."
$SUDO mkdir -p /var/run/mysqld && $SUDO chown mysql:mysql /var/run/mysqld
$SUDO service mysql start >/dev/null 2>&1 || ($SUDO setsid mysqld_safe --user=mysql >/dev/null 2>&1 &)
for i in $(seq 1 40); do $SUDO mysqladmin ping --silent 2>/dev/null && { echo ">> MySQL encendido."; exit 0; }; sleep 1; done
echo "!! MySQL no respondió. Revise: sudo tail -50 /var/log/mysql/error.log"; exit 1
