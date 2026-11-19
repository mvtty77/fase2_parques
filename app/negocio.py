"""Capa de negocio del PMV: reglas, validaciones y transacciones.

Todas las escrituras usan `engine.begin()`: si cualquier sentencia falla, el
bloque hace ROLLBACK automático; si todo sale bien, hace COMMIT al salir.
Las consultas del dashboard son SELECT propios e independientes de las 6
vistas y 6 procedimientos de los requerimientos R1-R12 (sección 9 del PDF).
"""
from __future__ import annotations

import re
from datetime import date

import pandas as pd
from sqlalchemy import bindparam, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from db import consultar, get_engine
from seguridad import (CRUD_ESPECIE, CRUD_PARQUE, DASHBOARD, INSCRIPCION, USUARIOS,
                       Sesion, exigir_permiso, verificar_password)

TIPOS_ESPECIE = ["VEGETAL", "ANIMAL", "MINERAL", "SIN_CLASIFICAR"]
ROLES = ["ADMINISTRADOR", "OPERADOR", "ANALISTA"]


class ErrorNegocio(Exception):
    """Error de validación o regla de negocio, con mensaje para el usuario."""


def _mensaje_bd(e: DBAPIError) -> str:
    """Traduce errores de MySQL (FK, UNIQUE, CHECK, SIGNAL de triggers)."""
    try:
        codigo, msg = e.orig.args[0], e.orig.args[1]
    except Exception:  # noqa: BLE001
        return str(e)
    traducciones = {1062: "Registro duplicado", 1451: "Existen registros que dependen de este",
                    1452: "Referencia a un registro inexistente", 3819: "Valor fuera de las reglas permitidas"}
    if codigo == 1644:          # SIGNAL desde un trigger o procedimiento
        return msg
    return f"{traducciones.get(codigo, 'Error de base de datos')} ({codigo}): {msg}"


# ---------------------------------------------------------------------
# Validaciones
# ---------------------------------------------------------------------
def validar_rut(rut: str) -> str:
    rut = (rut or "").strip().upper().replace(".", "")
    if not re.fullmatch(r"\d{7,8}-[\dK]", rut):
        raise ErrorNegocio("RUT con formato inválido (use 12345678-9).")
    numero, dv = rut.split("-")
    suma, factor = 0, 2
    for d in reversed(numero):
        suma += int(d) * factor
        factor = 2 if factor == 7 else factor + 1
    r = 11 - suma % 11
    esperado = "0" if r == 11 else "K" if r == 10 else str(r)
    if dv != esperado:
        raise ErrorNegocio("El dígito verificador del RUT no es válido.")
    return rut


def _texto(valor: str, campo: str, minimo: int = 2, maximo: int = 120, obligatorio: bool = True) -> str | None:
    v = (valor or "").strip()
    if not v:
        if obligatorio:
            raise ErrorNegocio(f"El campo «{campo}» es obligatorio.")
        return None
    if not (minimo <= len(v) <= maximo):
        raise ErrorNegocio(f"«{campo}» debe tener entre {minimo} y {maximo} caracteres.")
    return v


# ---------------------------------------------------------------------
# Autenticación
# ---------------------------------------------------------------------
def autenticar(usuario: str, password: str) -> Sesion | None:
    df = consultar("""
        SELECT c.id_cuenta, c.usuario, c.password_hash, c.rut_persona,
               CONCAT(p.nombres, ' ', p.apellido_paterno) AS nombre
          FROM CUENTA c JOIN PERSONA p ON p.rut_persona = c.rut_persona
         WHERE c.usuario = :u AND c.activa = TRUE""", {"u": (usuario or "").strip().lower()})
    if df.empty or not verificar_password(password or "", df.at[0, "password_hash"]):
        return None
    roles = consultar("SELECT rol FROM CUENTA_ROL WHERE id_cuenta = :c ORDER BY rol",
                      {"c": int(df.at[0, "id_cuenta"])})["rol"].tolist()
    if not roles:
        return None
    return Sesion(int(df.at[0, "id_cuenta"]), df.at[0, "usuario"], df.at[0, "rut_persona"],
                  df.at[0, "nombre"], roles)


# ---------------------------------------------------------------------
# Catálogos
# ---------------------------------------------------------------------
def listar_parques(solo_activos: bool = True) -> pd.DataFrame:
    return consultar(f"""
        SELECT p.anio_declaracion, p.nro_correlativo, p.nombre, p.fecha_declaracion,
               p.superficie_total, p.presupuesto_anual, p.estado_conservacion, p.categoria_snap,
               p.organismo_responsable, p.activo,
               (SELECT r.nombre FROM PARQUE_REGION pr JOIN REGION r ON r.id_region = pr.id_region
                 WHERE pr.anio_declaracion = p.anio_declaracion AND pr.nro_correlativo = p.nro_correlativo
                   AND pr.es_principal) AS region_principal,
               (SELECT COUNT(*) FROM AREA a WHERE a.anio_declaracion = p.anio_declaracion
                   AND a.nro_correlativo = p.nro_correlativo) AS areas
          FROM PARQUE p {'WHERE p.activo' if solo_activos else ''}
         ORDER BY p.nombre""")


def listar_regiones() -> pd.DataFrame:
    return consultar("SELECT id_region, nombre FROM REGION ORDER BY nombre")


def listar_areas(anio: int | None = None, correl: int | None = None) -> pd.DataFrame:
    return consultar("""
        SELECT a.anio_declaracion, a.nro_correlativo, a.nro_area, a.nombre, p.nombre AS parque
          FROM AREA a JOIN PARQUE p USING (anio_declaracion, nro_correlativo)
         WHERE (:anio IS NULL OR (a.anio_declaracion = :anio AND a.nro_correlativo = :cor))
         ORDER BY p.nombre, a.nro_area""", {"anio": anio, "cor": correl})


def buscar_visitantes(filtro: str = "") -> pd.DataFrame:
    f = f"%{(filtro or '').strip()}%"
    return consultar("""
        SELECT v.rut_persona, CONCAT(p.nombres, ' ', p.apellido_paterno,
               IFNULL(CONCAT(' ', p.apellido_materno), '')) AS nombre, p.nacionalidad
          FROM VISITANTE v JOIN PERSONA p ON p.rut_persona = v.rut_persona
         WHERE v.rut_persona LIKE :f OR p.nombres LIKE :f OR p.apellido_paterno LIKE :f
         ORDER BY p.apellido_paterno, p.nombres LIMIT 200""", {"f": f})


def excursiones_abiertas() -> pd.DataFrame:
    """Excursiones de hoy en adelante, en áreas operativas de parques activos, con cupo."""
    return consultar("""
        SELECT e.codigo_excursion, e.fecha, e.horario, e.modalidad, e.capacidad,
               p.nombre AS parque, a.nombre AS area,
               (SELECT COUNT(*) FROM INSCRIPCION i WHERE i.codigo_excursion = e.codigo_excursion) AS inscritos
          FROM EXCURSION e
          JOIN AREA a   ON a.anio_declaracion = e.anio_declaracion AND a.nro_correlativo = e.nro_correlativo
                       AND a.nro_area = e.nro_area
          JOIN PARQUE p ON p.anio_declaracion = a.anio_declaracion AND p.nro_correlativo = a.nro_correlativo
         WHERE e.fecha >= CURDATE() AND a.estado_operativo = 'OPERATIVA' AND p.activo
         ORDER BY e.fecha, e.horario""")


def excursiones_realizadas(limite: int = 60) -> pd.DataFrame:
    return consultar("""
        SELECT e.codigo_excursion, e.fecha, p.nombre AS parque, a.nombre AS area, e.modalidad,
               SUM(i.estado_asistencia = 'INSCRITO') AS pendientes
          FROM EXCURSION e
          JOIN AREA a   ON a.anio_declaracion = e.anio_declaracion AND a.nro_correlativo = e.nro_correlativo
                       AND a.nro_area = e.nro_area
          JOIN PARQUE p ON p.anio_declaracion = a.anio_declaracion AND p.nro_correlativo = a.nro_correlativo
          JOIN INSCRIPCION i ON i.codigo_excursion = e.codigo_excursion
         WHERE e.fecha <= CURDATE()
         GROUP BY e.codigo_excursion, e.fecha, p.nombre, a.nombre, e.modalidad
         ORDER BY e.fecha DESC LIMIT :lim""", {"lim": limite})


def inscripciones_de(codigo: str) -> pd.DataFrame:
    return consultar("""
        SELECT i.id_inscripcion, i.rut_persona, CONCAT(p.nombres, ' ', p.apellido_paterno) AS visitante,
               i.fecha_inscripcion, i.estado_asistencia,
               EXISTS (SELECT 1 FROM EVALUACION ev WHERE ev.id_inscripcion = i.id_inscripcion) AS evaluada
          FROM INSCRIPCION i JOIN PERSONA p ON p.rut_persona = i.rut_persona
         WHERE i.codigo_excursion = :c ORDER BY p.apellido_paterno""", {"c": codigo})


# ---------------------------------------------------------------------
# 1. FORMULARIO TRANSACCIONAL: inscripción de un visitante en una excursión
# ---------------------------------------------------------------------
def inscribir_visitante(sesion: Sesion, rut: str, codigo_excursion: str,
                        estado: str = "INSCRITO", observaciones: str = "") -> str:
    exigir_permiso(sesion, INSCRIPCION)
    rut = validar_rut(rut)
    if estado not in ("INSCRITO", "ASISTIO", "NO_ASISTIO"):
        raise ErrorNegocio("Estado de asistencia inválido.")
    obs = _texto(observaciones, "Observaciones", 0, 200, obligatorio=False)
    try:
        with get_engine().begin() as con:                        # BEGIN … COMMIT / ROLLBACK
            # Bloquea la fila de la excursión: dos operadores no pueden ocupar el último cupo a la vez
            exc = con.execute(text("""
                SELECT e.fecha, e.capacidad, a.estado_operativo, p.activo
                  FROM EXCURSION e
                  JOIN AREA a   ON a.anio_declaracion = e.anio_declaracion AND a.nro_correlativo = e.nro_correlativo
                               AND a.nro_area = e.nro_area
                  JOIN PARQUE p ON p.anio_declaracion = a.anio_declaracion AND p.nro_correlativo = a.nro_correlativo
                 WHERE e.codigo_excursion = :c FOR UPDATE"""), {"c": codigo_excursion}).mappings().first()
            if exc is None:
                raise ErrorNegocio("La excursión seleccionada no existe.")
            hoy = date.today()
            if exc["fecha"] < hoy:
                raise ErrorNegocio("La excursión ya se realizó: no admite nuevas inscripciones.")
            if exc["estado_operativo"] != "OPERATIVA" or not exc["activo"]:
                raise ErrorNegocio("El área o el parque de la excursión no está operativo.")
            if estado != "INSCRITO" and exc["fecha"] > hoy:
                raise ErrorNegocio("Solo se registra asistencia el día de la excursión o después.")
            if con.execute(text("SELECT 1 FROM VISITANTE WHERE rut_persona = :r"), {"r": rut}).first() is None:
                raise ErrorNegocio("El RUT no corresponde a un visitante registrado.")
            if con.execute(text("""SELECT 1 FROM INSCRIPCION
                                    WHERE rut_persona = :r AND codigo_excursion = :c"""),
                           {"r": rut, "c": codigo_excursion}).first():
                raise ErrorNegocio("El visitante ya está inscrito en esta excursión.")
            ocupados = con.execute(text("SELECT COUNT(*) FROM INSCRIPCION WHERE codigo_excursion = :c"),
                                   {"c": codigo_excursion}).scalar_one()
            if ocupados >= exc["capacidad"]:
                raise ErrorNegocio(f"Excursión sin cupo ({ocupados}/{exc['capacidad']}).")
            ultimo = con.execute(text("SELECT MAX(id_inscripcion) FROM INSCRIPCION FOR UPDATE")).scalar()
            nuevo_id = f"INS{(int(ultimo[3:]) if ultimo else 0) + 1:06d}"
            con.execute(text("""
                INSERT INTO INSCRIPCION (id_inscripcion, rut_persona, codigo_excursion,
                                         fecha_inscripcion, estado_asistencia, observaciones)
                VALUES (:id, :r, :c, CURDATE(), :e, :o)"""),
                        {"id": nuevo_id, "r": rut, "c": codigo_excursion, "e": estado, "o": obs})
        return nuevo_id
    except DBAPIError as e:      # el trigger o una restricción rechazó la operación → ya hubo ROLLBACK
        raise ErrorNegocio(_mensaje_bd(e)) from e


def registrar_asistencia(sesion: Sesion, codigo_excursion: str, estados: dict[str, str]) -> int:
    """Actualiza el estado de asistencia de varias inscripciones en UNA transacción."""
    exigir_permiso(sesion, INSCRIPCION)
    if any(v not in ("INSCRITO", "ASISTIO", "NO_ASISTIO") for v in estados.values()):
        raise ErrorNegocio("Estado de asistencia inválido.")
    try:
        with get_engine().begin() as con:
            n = 0
            for id_ins, est in estados.items():
                n += con.execute(text("""UPDATE INSCRIPCION SET estado_asistencia = :e
                                          WHERE id_inscripcion = :i AND codigo_excursion = :c
                                            AND estado_asistencia <> :e"""),
                                 {"e": est, "i": id_ins, "c": codigo_excursion}).rowcount
        return n
    except DBAPIError as e:
        raise ErrorNegocio(_mensaje_bd(e)) from e


# ---------------------------------------------------------------------
# 2. CRUD: PARQUE
# ---------------------------------------------------------------------
ESTADOS_PARQUE = ["BUENO", "REGULAR", "CRITICO"]
CATEGORIAS = ["PARQUE NACIONAL", "RESERVA NACIONAL", "MONUMENTO NATURAL", "SANTUARIO DE LA NATURALEZA"]


def _validar_parque(d: dict) -> dict:
    d = dict(d)
    d["nombre"] = _texto(d.get("nombre"), "Nombre", 3, 80)
    d["organismo_responsable"] = _texto(d.get("organismo_responsable"), "Organismo responsable", 3, 80)
    if d["estado_conservacion"] not in ESTADOS_PARQUE or d["categoria_snap"] not in CATEGORIAS:
        raise ErrorNegocio("Estado de conservación o categoría inválidos.")
    if float(d["superficie_total"]) <= 0:
        raise ErrorNegocio("La superficie debe ser mayor que 0.")
    if float(d["presupuesto_anual"]) < 0:
        raise ErrorNegocio("El presupuesto no puede ser negativo.")
    if d["fecha_declaracion"] > date.today():
        raise ErrorNegocio("La fecha de declaración no puede ser futura.")
    return d


def crear_parque(sesion: Sesion, datos: dict, id_region: int, area: dict) -> tuple[int, int]:
    """Crea parque + región principal + primera área (reglas: ≥1 área y 1 región principal)."""
    exigir_permiso(sesion, CRUD_PARQUE)
    d = _validar_parque(datos)
    nombre_area = _texto(area.get("nombre"), "Nombre del área", 3, 80)
    if float(area.get("extension", 0)) <= 0:
        raise ErrorNegocio("La extensión del área debe ser mayor que 0.")
    anio = d["fecha_declaracion"].year
    try:
        with get_engine().begin() as con:
            correl = con.execute(text("""SELECT COALESCE(MAX(nro_correlativo), 0) + 1 FROM PARQUE
                                          WHERE anio_declaracion = :a FOR UPDATE"""), {"a": anio}).scalar_one()
            con.execute(text("""
                INSERT INTO PARQUE (anio_declaracion, nro_correlativo, nombre, fecha_declaracion, superficie_total,
                                    presupuesto_anual, estado_conservacion, categoria_snap, organismo_responsable)
                VALUES (:a, :c, :nombre, :fecha_declaracion, :superficie_total, :presupuesto_anual,
                        :estado_conservacion, :categoria_snap, :organismo_responsable)"""),
                        {**d, "a": anio, "c": correl})
            con.execute(text("""INSERT INTO PARQUE_REGION (anio_declaracion, nro_correlativo, id_region,
                                    porcentaje_territorial, es_principal) VALUES (:a, :c, :r, 100, TRUE)"""),
                        {"a": anio, "c": correl, "r": id_region})
            con.execute(text("""INSERT INTO AREA VALUES (:a, :c, 1, :n, :ext, :acc, 'OPERATIVA')"""),
                        {"a": anio, "c": correl, "n": nombre_area, "ext": area["extension"],
                         "acc": area.get("nivel_acceso", "PUBLICO")})
        return anio, correl
    except DBAPIError as e:
        raise ErrorNegocio(_mensaje_bd(e)) from e


def actualizar_parque(sesion: Sesion, anio: int, correl: int, datos: dict) -> None:
    exigir_permiso(sesion, CRUD_PARQUE)
    d = _validar_parque(datos)
    if d["fecha_declaracion"].year != anio:
        raise ErrorNegocio("La fecha de declaración debe mantener el año de la clave del parque.")
    try:
        with get_engine().begin() as con:
            filas = con.execute(text("""
                UPDATE PARQUE SET nombre = :nombre, fecha_declaracion = :fecha_declaracion,
                       superficie_total = :superficie_total, presupuesto_anual = :presupuesto_anual,
                       estado_conservacion = :estado_conservacion, categoria_snap = :categoria_snap,
                       organismo_responsable = :organismo_responsable
                 WHERE anio_declaracion = :a AND nro_correlativo = :c"""), {**d, "a": anio, "c": correl}).rowcount
        if filas == 0:
            raise ErrorNegocio("No se encontró el parque o no hubo cambios.")
    except DBAPIError as e:
        raise ErrorNegocio(_mensaje_bd(e)) from e


def eliminar_parque(sesion: Sesion, anio: int, correl: int) -> str:
    """Eliminación física si el parque no tiene historial; si lo tiene, desactivación lógica."""
    exigir_permiso(sesion, CRUD_PARQUE)
    k = {"a": anio, "c": correl}
    with get_engine().begin() as con:
        dependencias = con.execute(text("""
            SELECT (SELECT COUNT(*) FROM EXCURSION WHERE anio_declaracion = :a AND nro_correlativo = :c)
                 + (SELECT COUNT(*) FROM INVENTARIO_RECURSO WHERE anio_declaracion = :a AND nro_correlativo = :c)
                 + (SELECT COUNT(*) FROM ASIGNACION_TRABAJADOR WHERE anio_declaracion = :a AND nro_correlativo = :c)
                 + (SELECT COUNT(*) FROM ESTUDIA WHERE anio_declaracion = :a AND nro_correlativo = :c)"""),
                                   k).scalar_one()
        if dependencias:
            con.execute(text("UPDATE PARQUE SET activo = FALSE WHERE anio_declaracion = :a AND nro_correlativo = :c"), k)
            return "lógica (registro desactivado)"
        con.execute(text("DELETE FROM AREA WHERE anio_declaracion = :a AND nro_correlativo = :c"), k)
        con.execute(text("DELETE FROM PARQUE WHERE anio_declaracion = :a AND nro_correlativo = :c"), k)  # PARQUE_REGION en cascada
        return "física"


def reactivar_parque(sesion: Sesion, anio: int, correl: int) -> None:
    exigir_permiso(sesion, CRUD_PARQUE)
    with get_engine().begin() as con:
        con.execute(text("UPDATE PARQUE SET activo = TRUE WHERE anio_declaracion = :a AND nro_correlativo = :c"),
                    {"a": anio, "c": correl})


# ---------------------------------------------------------------------
# 2. CRUD: ESPECIE (RECURSO_NATURAL + subtipo VEGETAL / ANIMAL / MINERAL)
# ---------------------------------------------------------------------
SQL_ESPECIES = """
    SELECT r.id_recurso, r.nombre_cientifico, r.nombre_comun, r.estado_conservacion, r.origen,
           r.fecha_incorporacion, r.descripcion, r.activo,
           CASE WHEN v.id_recurso IS NOT NULL THEN 'VEGETAL' WHEN a.id_recurso IS NOT NULL THEN 'ANIMAL'
                WHEN m.id_recurso IS NOT NULL THEN 'MINERAL' ELSE 'SIN_CLASIFICAR' END AS tipo,
           v.periodo_floracion, v.tipo_vegetacion, a.tipo_alimentacion, a.periodo_celo,
           m.tipo_material, m.composicion, m.dureza_mohs,
           (SELECT COUNT(*) FROM INVENTARIO_RECURSO ir WHERE ir.id_recurso = r.id_recurso) AS registros_inventario
      FROM RECURSO_NATURAL r
      LEFT JOIN VEGETAL v ON v.id_recurso = r.id_recurso
      LEFT JOIN ANIMAL  a ON a.id_recurso = r.id_recurso
      LEFT JOIN MINERAL m ON m.id_recurso = r.id_recurso"""


def listar_especies(solo_activas: bool = True) -> pd.DataFrame:
    return consultar(SQL_ESPECIES + (" WHERE r.activo" if solo_activas else "") + " ORDER BY r.nombre_comun")


def _validar_especie(d: dict) -> dict:
    d = dict(d)
    d["nombre_cientifico"] = _texto(d.get("nombre_cientifico"), "Nombre científico", 3, 100)
    d["nombre_comun"] = _texto(d.get("nombre_comun"), "Nombre común", 2, 80)
    d["descripcion"] = _texto(d.get("descripcion"), "Descripción", 0, 250, obligatorio=False)
    if d["estado_conservacion"] not in ("LC", "NT", "VU", "EN", "CR", "NO_APLICA"):
        raise ErrorNegocio("Estado de conservación inválido.")
    if d["origen"] not in ("NATIVO", "ENDEMICO", "INTRODUCIDO", "GEOLOGICO"):
        raise ErrorNegocio("Origen inválido.")
    return d


def _validar_subtipo(tipo: str, s: dict) -> dict:
    if tipo == "VEGETAL":
        return {"periodo_floracion": _texto(s.get("periodo_floracion"), "Período de floración", 3, 30),
                "tipo_vegetacion": s.get("tipo_vegetacion")}
    if tipo == "ANIMAL":
        return {"tipo_alimentacion": s.get("tipo_alimentacion"),
                "periodo_celo": _texto(s.get("periodo_celo"), "Período de celo", 3, 30)}
    if tipo == "MINERAL":
        dureza = float(s.get("dureza_mohs") or 0)
        if not 1 <= dureza <= 10:
            raise ErrorNegocio("La dureza de Mohs debe estar entre 1 y 10.")
        return {"tipo_material": _texto(s.get("tipo_material"), "Tipo de material", 3, 20),
                "composicion": _texto(s.get("composicion"), "Composición", 1, 60), "dureza_mohs": dureza}
    return {}


SQL_SUBTIPO = {
    "VEGETAL": "INSERT INTO VEGETAL VALUES (:id, :periodo_floracion, :tipo_vegetacion)",
    "ANIMAL": "INSERT INTO ANIMAL VALUES (:id, :tipo_alimentacion, :periodo_celo)",
    "MINERAL": "INSERT INTO MINERAL VALUES (:id, :tipo_material, :composicion, :dureza_mohs)",
}


def crear_especie(sesion: Sesion, datos: dict, tipo: str, sub: dict) -> int:
    exigir_permiso(sesion, CRUD_ESPECIE)
    if tipo not in TIPOS_ESPECIE:
        raise ErrorNegocio("Tipo de especie inválido.")
    d, s = _validar_especie(datos), _validar_subtipo(tipo, sub)
    try:
        with get_engine().begin() as con:          # recurso + subtipo: todo o nada
            res = con.execute(text("""
                INSERT INTO RECURSO_NATURAL (nombre_cientifico, nombre_comun, estado_conservacion,
                                             fecha_incorporacion, origen, descripcion)
                VALUES (:nombre_cientifico, :nombre_comun, :estado_conservacion, CURDATE(), :origen, :descripcion)"""), d)
            nuevo = res.lastrowid
            if tipo in SQL_SUBTIPO:
                con.execute(text(SQL_SUBTIPO[tipo]), {**s, "id": nuevo})
        return nuevo
    except DBAPIError as e:
        raise ErrorNegocio(_mensaje_bd(e)) from e


def actualizar_especie(sesion: Sesion, id_recurso: int, datos: dict, tipo: str, sub: dict) -> None:
    """El tipo (subtipo) no se cambia: preservaría la especialización disjunta sin perder historial."""
    exigir_permiso(sesion, CRUD_ESPECIE)
    d, s = _validar_especie(datos), _validar_subtipo(tipo, sub)
    try:
        with get_engine().begin() as con:
            con.execute(text("""
                UPDATE RECURSO_NATURAL SET nombre_cientifico = :nombre_cientifico, nombre_comun = :nombre_comun,
                       estado_conservacion = :estado_conservacion, origen = :origen, descripcion = :descripcion
                 WHERE id_recurso = :id"""), {**d, "id": id_recurso})
            if tipo == "VEGETAL":
                con.execute(text("UPDATE VEGETAL SET periodo_floracion = :periodo_floracion, "
                                 "tipo_vegetacion = :tipo_vegetacion WHERE id_recurso = :id"), {**s, "id": id_recurso})
            elif tipo == "ANIMAL":
                con.execute(text("UPDATE ANIMAL SET tipo_alimentacion = :tipo_alimentacion, "
                                 "periodo_celo = :periodo_celo WHERE id_recurso = :id"), {**s, "id": id_recurso})
            elif tipo == "MINERAL":
                con.execute(text("UPDATE MINERAL SET tipo_material = :tipo_material, composicion = :composicion, "
                                 "dureza_mohs = :dureza_mohs WHERE id_recurso = :id"), {**s, "id": id_recurso})
    except DBAPIError as e:
        raise ErrorNegocio(_mensaje_bd(e)) from e


def eliminar_especie(sesion: Sesion, id_recurso: int) -> str:
    exigir_permiso(sesion, CRUD_ESPECIE)
    with get_engine().begin() as con:
        usos = con.execute(text("""
            SELECT (SELECT COUNT(*) FROM INVENTARIO_RECURSO WHERE id_recurso = :i)
                 + (SELECT COUNT(*) FROM INVESTIGA WHERE id_recurso = :i)"""), {"i": id_recurso}).scalar_one()
        if usos:
            con.execute(text("UPDATE RECURSO_NATURAL SET activo = FALSE WHERE id_recurso = :i"), {"i": id_recurso})
            return "lógica (registro desactivado)"
        con.execute(text("DELETE FROM RECURSO_NATURAL WHERE id_recurso = :i"), {"i": id_recurso})  # subtipo en cascada
        return "física"


def reactivar_especie(sesion: Sesion, id_recurso: int) -> None:
    exigir_permiso(sesion, CRUD_ESPECIE)
    with get_engine().begin() as con:
        con.execute(text("UPDATE RECURSO_NATURAL SET activo = TRUE WHERE id_recurso = :i"), {"i": id_recurso})


# ---------------------------------------------------------------------
# 3. CONTROL DE USUARIOS (administración de cuentas y roles)
# ---------------------------------------------------------------------
def listar_cuentas(sesion: Sesion) -> pd.DataFrame:
    exigir_permiso(sesion, USUARIOS)
    return consultar("""
        SELECT c.id_cuenta, c.usuario, CONCAT(p.nombres, ' ', p.apellido_paterno) AS trabajador,
               t.cargo, c.activa, GROUP_CONCAT(cr.rol ORDER BY cr.rol SEPARATOR ', ') AS roles
          FROM CUENTA c
          JOIN TRABAJADOR t ON t.rut_persona = c.rut_persona
          JOIN PERSONA p    ON p.rut_persona = c.rut_persona
          LEFT JOIN CUENTA_ROL cr ON cr.id_cuenta = c.id_cuenta
         GROUP BY c.id_cuenta, c.usuario, p.nombres, p.apellido_paterno, t.cargo, c.activa
         ORDER BY c.usuario""")


def actualizar_cuenta(sesion: Sesion, id_cuenta: int, activa: bool, roles: list[str]) -> None:
    exigir_permiso(sesion, USUARIOS)
    if not roles or any(r not in ROLES for r in roles):
        raise ErrorNegocio("Cada cuenta debe tener al menos un rol válido.")
    if id_cuenta == sesion.id_cuenta and (not activa or "ADMINISTRADOR" not in roles):
        raise ErrorNegocio("No puede desactivar su propia cuenta ni quitarse el rol de administrador.")
    with get_engine().begin() as con:
        con.execute(text("UPDATE CUENTA SET activa = :a WHERE id_cuenta = :i"), {"a": activa, "i": id_cuenta})
        con.execute(text("DELETE FROM CUENTA_ROL WHERE id_cuenta = :i"), {"i": id_cuenta})
        con.execute(text("INSERT INTO CUENTA_ROL (id_cuenta, rol) VALUES (:i, :r)"),
                    [{"i": id_cuenta, "r": r} for r in roles])


# ---------------------------------------------------------------------
# 4. DASHBOARD (consultas propias, independientes de R1-R12)
# ---------------------------------------------------------------------
def dash_areas_visitantes(sesion: Sesion, inicio: date, fin: date, parques: list[str]) -> pd.DataFrame:
    """P1 Fase 1: áreas con mayor cantidad de visitantes mediante excursiones en un período."""
    exigir_permiso(sesion, DASHBOARD)
    sql = text("""
        SELECT CONCAT(a.nombre, ' (', p.nombre, ')') AS area, p.nombre AS parque,
               COUNT(DISTINCT e.codigo_excursion) AS excursiones,
               SUM(i.estado_asistencia = 'ASISTIO') AS visitantes
          FROM EXCURSION e
          JOIN AREA a   ON a.anio_declaracion = e.anio_declaracion AND a.nro_correlativo = e.nro_correlativo
                       AND a.nro_area = e.nro_area
          JOIN PARQUE p ON p.anio_declaracion = a.anio_declaracion AND p.nro_correlativo = a.nro_correlativo
          JOIN INSCRIPCION i ON i.codigo_excursion = e.codigo_excursion
         WHERE e.fecha BETWEEN :ini AND :fin AND p.nombre IN :parques
         GROUP BY a.anio_declaracion, a.nro_correlativo, a.nro_area, a.nombre, p.nombre
        HAVING visitantes > 0
         ORDER BY visitantes DESC""").bindparams(bindparam("parques", expanding=True))
    with get_engine().connect() as con:
        return pd.read_sql(sql, con, params={"ini": inicio, "fin": fin, "parques": parques or ["__ninguno__"]})


def dash_composicion_especies(sesion: Sesion, parque: str | None, area: str | None) -> pd.DataFrame:
    """P2 Fase 1: especies inventariadas vegetales/animales/minerales por parque/área."""
    exigir_permiso(sesion, DASHBOARD)
    return consultar("""
        SELECT p.nombre AS parque, a.nombre AS area,
               CASE WHEN v.id_recurso IS NOT NULL THEN 'Vegetal' WHEN an.id_recurso IS NOT NULL THEN 'Animal'
                    WHEN m.id_recurso IS NOT NULL THEN 'Mineral' ELSE 'Sin clasificar' END AS tipo,
               COUNT(DISTINCT ir.id_recurso) AS especies,
               SUM(ir.cantidad_inventariada) AS cantidad
          FROM INVENTARIO_RECURSO ir
          JOIN AREA a   ON a.anio_declaracion = ir.anio_declaracion AND a.nro_correlativo = ir.nro_correlativo
                       AND a.nro_area = ir.nro_area
          JOIN PARQUE p ON p.anio_declaracion = a.anio_declaracion AND p.nro_correlativo = a.nro_correlativo
          LEFT JOIN VEGETAL v  ON v.id_recurso = ir.id_recurso
          LEFT JOIN ANIMAL an  ON an.id_recurso = ir.id_recurso
          LEFT JOIN MINERAL m  ON m.id_recurso = ir.id_recurso
         WHERE p.activo AND (:parque IS NULL OR p.nombre = :parque) AND (:area IS NULL OR a.nombre = :area)
         GROUP BY p.nombre, a.nombre, tipo""", {"parque": parque, "area": area})


def dash_visitantes_vs_evaluacion(sesion: Sesion, inicio: date, fin: date, parque: str | None) -> pd.DataFrame:
    """P3 Fase 1: participantes por excursión vs evaluación promedio (conteos separados, sin duplicar)."""
    exigir_permiso(sesion, DASHBOARD)
    return consultar("""
        SELECT e.codigo_excursion, e.fecha, e.modalidad, p.nombre AS parque, a.nombre AS area,
               ins.participantes, ev.evaluaciones, ev.promedio
          FROM EXCURSION e
          JOIN AREA a   ON a.anio_declaracion = e.anio_declaracion AND a.nro_correlativo = e.nro_correlativo
                       AND a.nro_area = e.nro_area
          JOIN PARQUE p ON p.anio_declaracion = a.anio_declaracion AND p.nro_correlativo = a.nro_correlativo
          JOIN (SELECT codigo_excursion, SUM(estado_asistencia = 'ASISTIO') AS participantes
                  FROM INSCRIPCION GROUP BY codigo_excursion) ins ON ins.codigo_excursion = e.codigo_excursion
          JOIN (SELECT codigo_excursion, COUNT(*) AS evaluaciones, ROUND(AVG(calificacion), 2) AS promedio
                  FROM EVALUACION GROUP BY codigo_excursion) ev ON ev.codigo_excursion = e.codigo_excursion
         WHERE e.fecha BETWEEN :ini AND :fin AND (:parque IS NULL OR p.nombre = :parque)
         ORDER BY ins.participantes""", {"ini": inicio, "fin": fin, "parque": parque})


def dash_ocupacion_capacidad(sesion: Sesion, inicio: date, fin: date) -> pd.DataFrame:
    """P4 propuesta: ¿qué parques y modalidades aprovechan peor la capacidad ofrecida?
    Ocupación = asistentes / capacidad ofertada. Apoya decidir dónde reducir cupos o
    frecuencia y dónde ampliarlos (reasignación de guías y guardaparques)."""
    exigir_permiso(sesion, DASHBOARD)
    return consultar("""
        SELECT p.nombre AS parque, e.modalidad,
               COUNT(*)                                  AS excursiones,
               SUM(e.capacidad)                          AS capacidad_ofertada,
               SUM(COALESCE(x.inscritos, 0))             AS inscritos,
               SUM(COALESCE(x.asistentes, 0))            AS asistentes,
               ROUND(100 * SUM(COALESCE(x.asistentes, 0)) / SUM(e.capacidad), 1) AS ocupacion_pct
          FROM EXCURSION e
          JOIN PARQUE p ON p.anio_declaracion = e.anio_declaracion AND p.nro_correlativo = e.nro_correlativo
          LEFT JOIN (SELECT codigo_excursion, COUNT(*) AS inscritos,
                            SUM(estado_asistencia = 'ASISTIO') AS asistentes
                       FROM INSCRIPCION GROUP BY codigo_excursion) x ON x.codigo_excursion = e.codigo_excursion
         WHERE e.fecha BETWEEN :ini AND :fin AND e.fecha <= CURDATE()
         GROUP BY p.nombre, e.modalidad
         ORDER BY ocupacion_pct""", {"ini": inicio, "fin": fin})


# ---------------------------------------------------------------------
# Resumen para la portada (indicadores generales, sin permisos especiales)
# ---------------------------------------------------------------------
def resumen_general() -> dict:
    """Totales simples para la portada y la pantalla de ingreso."""
    df = consultar("""
        SELECT (SELECT COUNT(*) FROM PARQUE WHERE activo)                                  AS parques,
               (SELECT COUNT(*) FROM AREA a JOIN PARQUE p USING (anio_declaracion, nro_correlativo)
                 WHERE p.activo)                                                          AS areas,
               (SELECT COUNT(*) FROM RECURSO_NATURAL WHERE activo)                         AS especies,
               (SELECT COUNT(*) FROM EXCURSION WHERE fecha >= CURDATE())                   AS excursiones_proximas,
               (SELECT COUNT(*) FROM INSCRIPCION i JOIN EXCURSION e USING (codigo_excursion)
                 WHERE i.estado_asistencia = 'ASISTIO' AND YEAR(e.fecha) = YEAR(CURDATE())) AS visitas_anio,
               (SELECT ROUND(AVG(calificacion), 2) FROM EVALUACION)                        AS nota_promedio""")
    return {k: (None if pd.isna(v) else v) for k, v in df.iloc[0].to_dict().items()}


def proximas_excursiones(limite: int = 6) -> pd.DataFrame:
    """Próximas excursiones con su ocupación, para la portada."""
    return consultar("""
        SELECT e.codigo_excursion, e.fecha, e.horario, e.modalidad, p.nombre AS parque, a.nombre AS area,
               e.capacidad,
               (SELECT COUNT(*) FROM INSCRIPCION i WHERE i.codigo_excursion = e.codigo_excursion) AS inscritos
          FROM EXCURSION e
          JOIN AREA a   ON a.anio_declaracion = e.anio_declaracion AND a.nro_correlativo = e.nro_correlativo
                       AND a.nro_area = e.nro_area
          JOIN PARQUE p ON p.anio_declaracion = a.anio_declaracion AND p.nro_correlativo = a.nro_correlativo
         WHERE e.fecha >= CURDATE()
         ORDER BY e.fecha, e.horario
         LIMIT :lim""", {"lim": limite})
