"""Autenticación y permisos por rol del PMV.

Los permisos se verifican en DOS lugares:
  1. En la interfaz (main.py): una página no autorizada no se muestra y, si se
     fuerza, se detiene con st.stop().
  2. En la capa de negocio (negocio.py): cada operación de escritura recibe la
     sesión y llama a exigir_permiso(); si el rol no lo tiene, se lanza
     PermisoDenegado ANTES de tocar la base de datos.
"""
from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass, field

# Funcionalidades del PMV
INSCRIPCION = "inscripcion"
CRUD_PARQUE = "crud_parque"
CRUD_ESPECIE = "crud_especie"
DASHBOARD = "dashboard"
USUARIOS = "usuarios"

PERMISOS_POR_ROL: dict[str, set[str]] = {
    "ADMINISTRADOR": {INSCRIPCION, CRUD_PARQUE, CRUD_ESPECIE, DASHBOARD, USUARIOS},
    "OPERADOR": {INSCRIPCION, DASHBOARD},          # guías y guardaparques: atención de visitantes
    "ANALISTA": {CRUD_ESPECIE, DASHBOARD},         # investigación y conservación
}


class PermisoDenegado(Exception):
    """El rol de la sesión no autoriza la operación."""


@dataclass
class Sesion:
    id_cuenta: int
    usuario: str
    rut_persona: str
    nombre: str
    roles: list[str] = field(default_factory=list)

    @property
    def permisos(self) -> set[str]:
        p: set[str] = set()
        for r in self.roles:
            p |= PERMISOS_POR_ROL.get(r, set())
        return p

    def puede(self, permiso: str) -> bool:
        return permiso in self.permisos


def exigir_permiso(sesion: Sesion | None, permiso: str) -> None:
    if sesion is None or not sesion.puede(permiso):
        raise PermisoDenegado(f"Su rol no permite la operación «{permiso}».")


def hash_password(password: str, salt: str, iteraciones: int = 60000) -> str:
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iteraciones)
    return f"pbkdf2_sha256${iteraciones}${salt}${dk.hex()}"


def verificar_password(password: str, almacenado: str) -> bool:
    try:
        algoritmo, iteraciones, salt, _ = almacenado.split("$")
    except ValueError:
        return False
    if algoritmo != "pbkdf2_sha256":
        return False
    calculado = hash_password(password, salt, int(iteraciones))
    return hmac.compare_digest(calculado, almacenado)   # comparación en tiempo constante
