#!/usr/bin/env bash
# Funciones comunes: raíz del repo, sudo y lectura de .env
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
[ -f "$RAIZ/.env" ] || cp "$RAIZ/.env.example" "$RAIZ/.env"
leer_env() { grep -E "^$1=" "$RAIZ/.env" | tail -1 | cut -d= -f2- | tr -d '\r"'"'"; }
DB_USER="$(leer_env DB_USER)"; DB_PASSWORD="$(leer_env DB_PASSWORD)"; DB_NAME="$(leer_env DB_NAME)"
DB_NAME="${DB_NAME:-parques_db}"
