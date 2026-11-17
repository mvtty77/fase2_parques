"""Conexión a MySQL con SQLAlchemy + PyMySQL.

Las credenciales NO se escriben en el código: se leen de variables de entorno
o, si no existen, del archivo .env en la raíz del repositorio (ver .env.example).
Funciona igual en GitHub Codespaces y en un PC con MySQL + Workbench.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, Engine

RAIZ = Path(__file__).resolve().parent.parent


def cargar_env(ruta: Path = RAIZ / ".env") -> None:
    """Lee líneas CLAVE=valor del archivo .env sin sobrescribir variables ya definidas."""
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    cargar_env()
    faltantes = [v for v in ("DB_USER", "DB_PASSWORD") if not os.getenv(v)]
    if faltantes:
        raise RuntimeError(
            f"Faltan datos de conexión: {', '.join(faltantes)}. Copie .env.example a .env y complételo.")
    url = URL.create(
        "mysql+pymysql",
        username=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME", "parques_db"),
        query={"charset": "utf8mb4"},
    )
    # pool_pre_ping evita errores por conexiones cerradas por el servidor
    return create_engine(url, pool_pre_ping=True, pool_recycle=1800)


def consultar(sql: str, params: dict | None = None) -> pd.DataFrame:
    """Ejecuta un SELECT parametrizado y devuelve un DataFrame de Pandas."""
    with get_engine().connect() as con:
        return pd.read_sql(text(sql), con, params=params or {})
