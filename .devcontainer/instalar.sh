#!/usr/bin/env bash
# Se ejecuta UNA vez, al crear el Codespace: instala MySQL 8, Python y las librerías.
set -euo pipefail
cd "$(dirname "$0")/.."
SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"

echo ">> Instalando MySQL Server 8 y Python 3.12..."
$SUDO apt-get update -qq
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y -qq mysql-server mysql-client python3 python3-venv python3-pip

echo ">> Creando entorno virtual de Python e instalando requirements.txt..."
python3 -m venv "$HOME/.venv"
"$HOME/.venv/bin/pip" install -q --upgrade pip
"$HOME/.venv/bin/pip" install -q -r requirements.txt
grep -q '.venv/bin/activate' "$HOME/.bashrc" || echo 'source "$HOME/.venv/bin/activate"' >> "$HOME/.bashrc"

[ -f .env ] || { cp .env.example .env; echo ">> Se creó .env a partir de .env.example"; }
echo ">> Instalación terminada."
