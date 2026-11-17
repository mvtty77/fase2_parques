"""Pruebas automáticas del PMV (pytest).

- Pruebas unitarias: no requieren base de datos.
- Pruebas de integración: requieren la base parques_db cargada con el script
  integral y las variables DB_* configuradas. Se omiten si no hay conexión.
  Cada prueba limpia lo que crea.

Ejecutar:  pytest -v tests/
"""
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

import negocio as ng  # noqa: E402
from seguridad import (CRUD_PARQUE, INSCRIPCION, PermisoDenegado, Sesion,  # noqa: E402
                       hash_password, verificar_password)

PASSWORD_DEMO = "Parques2026!"


# ------------------------- unitarias ---------------------------------
def test_hash_y_verificacion():
    h = hash_password("secreta", "sal123")
    assert verificar_password("secreta", h)
    assert not verificar_password("otra", h)
    assert not verificar_password("secreta", "formato-invalido")


@pytest.mark.parametrize("rut", ["11111111-1", "12345678-5", "7654321-6"])
def test_rut_valido(rut):
    assert ng.validar_rut(rut) == rut


@pytest.mark.parametrize("rut", ["12345678-9", "1234-5", "abc", ""])
def test_rut_invalido(rut):
    with pytest.raises(ng.ErrorNegocio):
        ng.validar_rut(rut)


def test_permisos_por_rol():
    operador = Sesion(1, "op", "1-9", "Op", ["OPERADOR"])
    analista = Sesion(2, "an", "1-9", "An", ["ANALISTA"])
    assert operador.puede(INSCRIPCION) and not operador.puede(CRUD_PARQUE)
    assert not analista.puede(INSCRIPCION)


def test_permiso_denegado_antes_de_tocar_bd():
    analista = Sesion(2, "an", "1-9", "An", ["ANALISTA"])
    with pytest.raises(PermisoDenegado):
        ng.inscribir_visitante(analista, "11111111-1", "EXC0001")
    with pytest.raises(PermisoDenegado):
        ng.eliminar_parque(analista, 1959, 1)


# ----------------------- integración ---------------------------------
def _hay_bd() -> bool:
    try:
        ng.consultar("SELECT 1")
        return True
    except Exception:  # noqa: BLE001
        return False


bd = pytest.mark.skipif(not _hay_bd(), reason="Sin conexión a MySQL (configure DB_*)")


@bd
def test_login_roles():
    s = ng.autenticar("admin", PASSWORD_DEMO)
    assert s is not None and "ADMINISTRADOR" in s.roles
    assert ng.autenticar("admin", "incorrecta") is None
    assert ng.autenticar("noexiste", PASSWORD_DEMO) is None
    op = ng.autenticar("operador", PASSWORD_DEMO)
    assert op is not None and op.roles == ["OPERADOR"]


@bd
def test_inscripcion_completa_duplicado_y_cupo():
    s = ng.autenticar("operador", PASSWORD_DEMO)
    exc = ng.excursiones_abiertas()
    exc = exc[exc["fecha"] > date.today()]
    exc = exc.assign(libres=exc["capacidad"] - exc["inscritos"])
    fila = exc[exc["libres"] >= 2].sort_values("libres").iloc[0]   # excursión casi llena
    ya = set(ng.inscripciones_de(fila.codigo_excursion)["rut_persona"])
    candidatos = [r for r in ng.buscar_visitantes("")["rut_persona"] if r not in ya]
    creados = []
    try:
        # llenar los cupos libres
        for rut in candidatos[: int(fila.capacidad - fila.inscritos)]:
            creados.append(ng.inscribir_visitante(s, rut, fila.codigo_excursion))
        # duplicado
        with pytest.raises(ng.ErrorNegocio, match="ya está inscrito"):
            ng.inscribir_visitante(s, candidatos[0], fila.codigo_excursion)
        # sin cupo
        with pytest.raises(ng.ErrorNegocio, match="sin cupo"):
            ng.inscribir_visitante(s, candidatos[len(creados)], fila.codigo_excursion)
        # asistencia en excursión futura
        with pytest.raises(ng.ErrorNegocio):
            ng.registrar_asistencia(s, fila.codigo_excursion, {creados[0]: "ASISTIO"})
    finally:
        from sqlalchemy import bindparam, text
        with ng.get_engine().begin() as con:
            if creados:
                con.execute(text("DELETE FROM INSCRIPCION WHERE id_inscripcion IN :ids")
                            .bindparams(bindparam("ids", expanding=True)), {"ids": creados})


@bd
def test_crud_parque_y_especie():
    s = ng.autenticar("admin", PASSWORD_DEMO)
    datos = {"nombre": "Parque de Prueba Pytest", "fecha_declaracion": date(2024, 5, 1),
             "superficie_total": 1500, "presupuesto_anual": 1e8, "estado_conservacion": "BUENO",
             "categoria_snap": "PARQUE NACIONAL", "organismo_responsable": "CONAF"}
    anio, cor = ng.crear_parque(s, datos, 1, {"nombre": "Sector Prueba", "extension": 50})
    datos["presupuesto_anual"] = 2e8
    ng.actualizar_parque(s, anio, cor, datos)
    assert ng.eliminar_parque(s, anio, cor) == "física"        # sin historial → física
    # parque con historial → lógica
    tp = ng.listar_parques().query("nombre == 'Torres del Paine'").iloc[0]
    assert ng.eliminar_parque(s, int(tp.anio_declaracion), int(tp.nro_correlativo)).startswith("lógica")
    ng.reactivar_parque(s, int(tp.anio_declaracion), int(tp.nro_correlativo))
    # especie mineral con subtipo
    idr = ng.crear_especie(s, {"nombre_cientifico": "Mineralis pytestensis", "nombre_comun": "Prueba",
                               "estado_conservacion": "NO_APLICA", "origen": "GEOLOGICO", "descripcion": ""},
                           "MINERAL", {"tipo_material": "SILICATO", "composicion": "SiO2", "dureza_mohs": 7})
    with pytest.raises(ng.ErrorNegocio, match="duplicado|Duplicate"):
        ng.crear_especie(s, {"nombre_cientifico": "Mineralis pytestensis", "nombre_comun": "Otra",
                             "estado_conservacion": "NO_APLICA", "origen": "GEOLOGICO", "descripcion": ""},
                         "MINERAL", {"tipo_material": "SILICATO", "composicion": "SiO2", "dureza_mohs": 7})
    assert ng.eliminar_especie(s, idr) == "física"
