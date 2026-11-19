"""PMV · Red de Parques · Caso 1 · Grupo 1 · TDFI103 Fase 2

Ejecutar:  streamlit run app/main.py
Arquitectura: Usuario → Streamlit (main.py, interfaz) → negocio.py (reglas, permisos,
transacciones) → db.py (SQLAlchemy + PyMySQL) → MySQL 8 (parques_db)

Diseño: navegación superior (st.navigation), portada con indicadores, inscripción en
tres pasos, CRUD maestro-detalle (tabla seleccionable + panel lateral) y dashboard 2x2.
"""
from __future__ import annotations

from datetime import date

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

import negocio as ng
from seguridad import (CRUD_ESPECIE, CRUD_PARQUE, DASHBOARD, INSCRIPCION, USUARIOS,
                       PermisoDenegado, Sesion)

st.set_page_config(page_title="Red de Parques", page_icon=":material/landscape:", layout="wide",
                   initial_sidebar_state="collapsed")

# ---------------------------------------------------------------------
# Identidad visual
# ---------------------------------------------------------------------
OCRE = "#C2662D"
BOSQUE = "#2E4A3F"
ARENA = "#EFE6D6"
TINTA = "#22302A"
COLORES_TIPO = {"Vegetal": "#5E8C4A", "Animal": "#C2662D", "Mineral": "#7C8A99", "Sin clasificar": "#D9A441"}
COLORES_MODALIDAD = {"GUIADA": BOSQUE, "AUTOGUIADA": OCRE, "EDUCATIVA": "#4F7CAC", "NOCTURNA": "#7A5C8F"}

pio.templates["red_parques"] = go.layout.Template(layout=go.Layout(
    font={"family": "Source Sans 3, sans-serif", "color": TINTA, "size": 13},
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    colorway=[BOSQUE, OCRE, "#4F7CAC", "#D9A441", "#7A5C8F", "#5E8C4A", "#A0522D", "#7C8A99"],
    xaxis={"gridcolor": "#E3DACA", "zerolinecolor": "#E3DACA"},
    yaxis={"gridcolor": "#E3DACA", "zerolinecolor": "#E3DACA"},
    margin={"l": 10, "r": 10, "t": 30, "b": 10},
    legend={"orientation": "h", "y": -0.18, "x": 0},
))
pio.templates.default = "plotly+red_parques"

st.markdown(f"""
<style>
  .block-container {{ padding-top: 3.6rem; max-width: 1280px; }}
  h1, h2, h3 {{ letter-spacing: -0.01em; }}
  .rp-banda {{ background: {BOSQUE}; color: #F7F2E8; border-radius: 14px; padding: 1.1rem 1.4rem;
              display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }}
  .rp-banda .marca {{ font-family: Georgia, serif; font-size: 1.55rem; font-weight: 700; }}
  .rp-banda .marca span {{ color: #E9B17F; }}
  .rp-banda .quien {{ text-align: right; font-size: .9rem; opacity: .92; line-height: 1.35; }}
  .rp-chip {{ display: inline-block; background: {OCRE}; color: #fff; border-radius: 999px;
              padding: .05rem .6rem; font-size: .75rem; margin-left: .25rem; }}
  .rp-paso {{ display: inline-flex; align-items: center; justify-content: center; width: 1.7rem; height: 1.7rem;
              border-radius: 50%; background: {OCRE}; color: white; font-weight: 700; margin-right: .5rem; }}
  .rp-titulo-paso {{ font-weight: 700; font-size: 1.05rem; color: {TINTA}; }}
  .rp-hero {{ background: linear-gradient(160deg, {BOSQUE} 0%, #3F6253 100%); color: #F7F2E8;
              border-radius: 18px; padding: 2.2rem 2rem; min-height: 470px; }}
  .rp-hero h1 {{ color: #F7F2E8; font-family: Georgia, serif; font-size: 2.3rem; margin: 0 0 .4rem 0; }}
  .rp-hero p {{ opacity: .9; font-size: 1.02rem; }}
  .rp-dato {{ border-top: 1px solid rgba(247,242,232,.25); padding-top: .7rem; margin-top: .9rem; }}
  .rp-dato b {{ font-family: Georgia, serif; font-size: 1.6rem; color: #E9B17F; display: block; }}
  .rp-nota {{ color: #6B6457; font-size: .85rem; }}
  div[data-testid="stMetric"] {{ background: #FFFDF8; border: 1px solid #E3DACA; border-radius: 12px;
                                 padding: .7rem .9rem; }}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------
# Sesión, permisos y utilidades
# ---------------------------------------------------------------------
def sesion() -> Sesion | None:
    return st.session_state.get("sesion")


def requiere(permiso: str) -> Sesion:
    """Control de acceso efectivo: si el rol no autoriza, la página se detiene."""
    s = sesion()
    if s is None or not s.puede(permiso):
        st.error("Acceso denegado: su rol no tiene permiso para esta sección.")
        st.stop()
    return s


def mostrar_aviso() -> None:
    msg = st.session_state.pop("aviso", None)
    if msg:
        st.toast(msg, icon=":material/check_circle:")
        st.success(msg)


def ejecutar(accion, exito: str, recargar: bool = False):
    """Ejecuta una operación de negocio y muestra el resultado o el error."""
    try:
        r = accion()
        if recargar:
            st.session_state["aviso"] = exito.format(r=r)
            st.rerun()
        st.success(exito.format(r=r))
        return r
    except PermisoDenegado as e:
        st.error(f"Permiso denegado. {e}")
    except ng.ErrorNegocio as e:
        st.error(str(e))
    return None


def banda(titulo: str, s: Sesion) -> None:
    roles = "".join(f'<span class="rp-chip">{r.lower()}</span>' for r in s.roles)
    c1, c2 = st.columns([6, 1], vertical_alignment="center")
    c1.markdown(f"""<div class="rp-banda"><div class="marca">Red de <span>Parques</span>
                <div style="font-family:inherit;font-size:.95rem;font-weight:400;opacity:.85">{titulo}</div></div>
                <div class="quien">{s.nombre}<br>{roles}</div></div>""", unsafe_allow_html=True)
    if c2.button("Salir", icon=":material/logout:", width="stretch"):
        st.session_state.clear()
        st.rerun()


def entero(v) -> str:
    return "—" if v is None else f"{int(v):,}".replace(",", ".")


# ---------------------------------------------------------------------
# Ingreso
# ---------------------------------------------------------------------
def pantalla_login() -> None:
    try:
        r = ng.resumen_general()
    except Exception:  # noqa: BLE001 — la base puede no estar disponible todavía
        r = {}
    izq, der = st.columns([1.15, 1], gap="large")
    with izq:
        st.markdown(f"""
        <div class="rp-hero">
          <div style="letter-spacing:.18em;font-size:.8rem;opacity:.75">SISTEMA DE GESTIÓN</div>
          <h1>Red de Parques</h1>
          <p>Áreas protegidas, inventario de especies, excursiones y visitantes en un solo lugar.</p>
          <div class="rp-dato"><b>{entero(r.get('parques'))}</b>parques activos con {entero(r.get('areas'))} áreas</div>
          <div class="rp-dato"><b>{entero(r.get('especies'))}</b>especies y recursos inventariados</div>
          <div class="rp-dato"><b>{entero(r.get('excursiones_proximas'))}</b>excursiones programadas desde hoy</div>
        </div>""", unsafe_allow_html=True)
    with der:
        st.write("")
        st.write("")
        st.subheader("Ingreso del personal")
        st.markdown('<p class="rp-nota">Use la cuenta asignada por administración.</p>', unsafe_allow_html=True)
        with st.form("login", border=True):
            usuario = st.text_input("Usuario", placeholder="ej. admin")
            clave = st.text_input("Contraseña", type="password")
            entrar = st.form_submit_button("Ingresar", type="primary", width="stretch",
                                           icon=":material/login:")
        if entrar:
            try:
                s = ng.autenticar(usuario, clave)
            except Exception as e:  # noqa: BLE001
                st.error(f"No fue posible conectar con la base de datos: {e}")
                return
            if s is None:
                st.error("Usuario o contraseña incorrectos, o cuenta desactivada.")
            else:
                st.session_state["sesion"] = s
                st.rerun()


# ---------------------------------------------------------------------
# Portada
# ---------------------------------------------------------------------
def pagina_inicio() -> None:
    s = sesion()
    banda("Inicio", s)
    r = ng.resumen_general()
    c = st.columns(4)
    c[0].metric("Parques activos", entero(r["parques"]), help="Parques no desactivados")
    c[1].metric("Especies inventariadas", entero(r["especies"]))
    c[2].metric(f"Visitas {date.today().year}", entero(r["visitas_anio"]), help="Asistencias registradas en el año")
    c[3].metric("Evaluación promedio", "—" if r["nota_promedio"] is None else f"{r['nota_promedio']:.2f} / 5")

    st.markdown("#### Próximas excursiones")
    prox = ng.proximas_excursiones(6)
    if prox.empty:
        st.info("No hay excursiones programadas.")
    else:
        cols = st.columns(3)
        for i, e in enumerate(prox.itertuples()):
            with cols[i % 3].container(border=True):
                st.markdown(f"**{e.parque}** · {e.area}")
                st.caption(f"{e.fecha:%d-%m-%Y} · {str(e.horario)[-8:-3]} h · {e.modalidad.capitalize()} · {e.codigo_excursion}")
                st.progress(min(1.0, e.inscritos / e.capacidad), text=f"{e.inscritos} de {e.capacidad} cupos")

    st.markdown("#### Accesos")
    accesos = [("Inscribir visitantes", INSCRIPCION, "pages_inscripciones"),
               ("Parques y especies", None, "pages_maestros"),
               ("Indicadores", DASHBOARD, "pages_dashboard")]
    cols = st.columns(3)
    for i, (t, p, k) in enumerate(accesos):
        if p is None:
            ok = s.puede(CRUD_PARQUE) or s.puede(CRUD_ESPECIE)
        else:
            ok = s.puede(p)
        if ok and k in st.session_state.get("_paginas", {}):
            cols[i].page_link(st.session_state["_paginas"][k], label=t, icon=":material/arrow_forward:")


# ---------------------------------------------------------------------
# 1. Formulario transaccional: inscripción en tres pasos
# ---------------------------------------------------------------------
def paso(n: int, texto: str) -> None:
    st.markdown(f'<span class="rp-paso">{n}</span><span class="rp-titulo-paso">{texto}</span>', unsafe_allow_html=True)


def pagina_inscripcion() -> None:
    s = requiere(INSCRIPCION)
    banda("Inscripciones", s)
    mostrar_aviso()
    modo = st.segmented_control("Acción", ["Nueva inscripción", "Registrar asistencia"],
                                default="Nueva inscripción", label_visibility="collapsed") or "Nueva inscripción"

    if modo == "Nueva inscripción":
        exc = ng.excursiones_abiertas()
        if exc.empty:
            st.info("No hay excursiones abiertas desde hoy en adelante.")
            return
        exc["cupos"] = exc["capacidad"] - exc["inscritos"]
        izq, der = st.columns([1.1, 1], gap="large")
        with izq:
            with st.container(border=True):
                paso(1, "Elegir la excursión")
                parques = ["Todos"] + sorted(exc["parque"].unique().tolist())
                fp = st.selectbox("Parque", parques)
                vista = exc if fp == "Todos" else exc[exc["parque"] == fp]
                etiquetas = vista.apply(lambda r: f"{r.codigo_excursion} — {r.fecha:%d-%m-%Y} · {r.area} · "
                                                  f"{r.modalidad.capitalize()}", axis=1).tolist()
                sel = st.selectbox("Excursión", etiquetas)
                fila = vista.iloc[etiquetas.index(sel)]
                m1, m2, m3 = st.columns(3)
                m1.metric("Cupos libres", int(fila.cupos))
                m2.metric("Capacidad", int(fila.capacidad))
                m3.metric("Hora", str(fila.horario)[-8:-3])
                st.progress(min(1.0, fila.inscritos / fila.capacidad),
                            text=f"Ocupación {fila.inscritos}/{fila.capacidad} · {fila.parque}")
        with der:
            with st.container(border=True):
                paso(2, "Buscar al visitante")
                filtro = st.text_input("RUT, nombre o apellido", placeholder="ej. 16877015-4 o Torres")
                vis = ng.buscar_visitantes(filtro)
                if vis.empty:
                    st.warning("Sin coincidencias.")
                    return
                opcion = st.selectbox(f"Visitante ({len(vis)} resultados)",
                                      (vis["rut_persona"] + " · " + vis["nombre"]).tolist())
            with st.container(border=True):
                paso(3, "Confirmar")
                with st.form("form_inscripcion", clear_on_submit=True, border=False):
                    estados = ["INSCRITO"] if fila.fecha > date.today() else ["INSCRITO", "ASISTIO", "NO_ASISTIO"]
                    estado = st.radio("Estado de asistencia", estados, horizontal=True,
                                      help="La asistencia solo puede registrarse desde el día de la excursión.")
                    obs = st.text_input("Observaciones (opcional)", max_chars=200)
                    if st.form_submit_button("Inscribir visitante", type="primary", width="stretch",
                                             icon=":material/how_to_reg:"):
                        rut = opcion.split(" · ")[0]
                        ejecutar(lambda: ng.inscribir_visitante(s, rut, fila.codigo_excursion, estado, obs),
                                 "Inscripción {r} registrada.", recargar=True)
        with st.expander(f"Inscritos en {fila.codigo_excursion}"):
            st.dataframe(ng.inscripciones_de(fila.codigo_excursion), hide_index=True, width="stretch")
    else:
        realizadas = ng.excursiones_realizadas()
        if realizadas.empty:
            st.info("No hay excursiones realizadas con inscripciones.")
            return
        realizadas["etiqueta"] = realizadas.apply(
            lambda r: f"{r.codigo_excursion} — {r.fecha:%d-%m-%Y} · {r.parque} / {r.area} · pendientes: {int(r.pendientes)}",
            axis=1)
        with st.container(border=True):
            sel2 = st.selectbox("Excursión realizada", realizadas["etiqueta"].tolist())
            cod = sel2.split(" — ")[0]
            ins = ng.inscripciones_de(cod)
            editado = st.data_editor(
                ins, hide_index=True, width="stretch", key=f"asis_{cod}",
                disabled=["id_inscripcion", "rut_persona", "visitante", "fecha_inscripcion", "evaluada"],
                column_config={"estado_asistencia": st.column_config.SelectboxColumn(
                    "Asistencia", options=["INSCRITO", "ASISTIO", "NO_ASISTIO"], required=True)})
            if st.button("Guardar asistencia", type="primary", icon=":material/save:"):
                cambios = dict(zip(editado["id_inscripcion"], editado["estado_asistencia"]))
                ejecutar(lambda: ng.registrar_asistencia(s, cod, cambios), "{r} inscripciones actualizadas.",
                         recargar=True)


# ---------------------------------------------------------------------
# 2. CRUD maestro-detalle: Parque y Especie
# ---------------------------------------------------------------------
def _form_parque(prefijo: str, base: dict | None = None) -> dict:
    b = base or {}
    nombre = st.text_input("Nombre", b.get("nombre", ""), key=f"{prefijo}_n")
    c1, c2 = st.columns(2)
    fecha = c1.date_input("Fecha de declaración", b.get("fecha_declaracion", date(2000, 1, 1)),
                          min_value=date(1900, 1, 1), max_value=date.today(), key=f"{prefijo}_f")
    cat = c2.selectbox("Categoría SNASPE", ng.CATEGORIAS,
                       ng.CATEGORIAS.index(b.get("categoria_snap", "PARQUE NACIONAL")), key=f"{prefijo}_c")
    sup = c1.number_input("Superficie (ha)", 0.0, value=float(b.get("superficie_total", 1000.0)), key=f"{prefijo}_s")
    pres = c2.number_input("Presupuesto anual (CLP)", 0.0, value=float(b.get("presupuesto_anual", 1e8)),
                           step=1e6, key=f"{prefijo}_p")
    est = c1.selectbox("Estado de conservación", ng.ESTADOS_PARQUE,
                       ng.ESTADOS_PARQUE.index(b.get("estado_conservacion", "BUENO")), key=f"{prefijo}_e")
    org = c2.text_input("Organismo responsable", b.get("organismo_responsable", "CONAF"), key=f"{prefijo}_o")
    return {"nombre": nombre, "fecha_declaracion": fecha, "superficie_total": sup, "presupuesto_anual": pres,
            "estado_conservacion": est, "categoria_snap": cat, "organismo_responsable": org}


def fila_seleccionada(evento, df):
    filas = evento.selection.rows if evento and evento.selection else []
    return df.iloc[filas[0]] if filas else None


def crud_parques(s: Sesion) -> None:
    ver_todos = st.toggle("Incluir desactivados", key="tp")
    df = ng.listar_parques(solo_activos=not ver_todos)
    tabla, panel = st.columns([1.55, 1], gap="medium")
    with tabla:
        st.caption("Seleccione una fila para editarla o eliminarla.")
        ev = st.dataframe(
            df[["nombre", "categoria_snap", "region_principal", "areas", "estado_conservacion", "activo"]],
            hide_index=True, width="stretch", height=430, on_select="rerun", selection_mode="single-row",
            key="tabla_parques",
            column_config={"nombre": "Parque", "categoria_snap": "Categoría", "region_principal": "Región",
                           "areas": st.column_config.NumberColumn("Áreas", width="small"),
                           "estado_conservacion": "Conservación",
                           "activo": st.column_config.CheckboxColumn("Activo", width="small")})
    elegido = fila_seleccionada(ev, df)
    with panel:
        with st.container(border=True):
            if elegido is None:
                st.markdown("**Nuevo parque**")
                with st.form("crear_parque", border=False):
                    datos = _form_parque("cp")
                    reg = ng.listar_regiones()
                    region = st.selectbox("Región principal", reg["nombre"].tolist())
                    c1, c2 = st.columns(2)
                    area_n = c1.text_input("Primera área", "Sector Acceso")
                    area_e = c2.number_input("Extensión (ha)", 0.0, value=100.0)
                    if st.form_submit_button("Crear parque", type="primary", width="stretch", icon=":material/add:"):
                        id_reg = int(reg.loc[reg["nombre"] == region, "id_region"].iloc[0])
                        ejecutar(lambda: ng.crear_parque(s, datos, id_reg, {"nombre": area_n, "extension": area_e}),
                                 "Parque creado con clave {r}.", recargar=True)
            else:
                anio, cor = int(elegido.anio_declaracion), int(elegido.nro_correlativo)
                st.markdown(f"**{elegido.nombre}** · clave {anio}-{cor}")
                with st.form("editar_parque", border=False):
                    datos = _form_parque(f"ep{anio}{cor}", elegido.to_dict())
                    if st.form_submit_button("Guardar cambios", type="primary", width="stretch", icon=":material/save:"):
                        ejecutar(lambda: ng.actualizar_parque(s, anio, cor, datos), "Parque actualizado.", recargar=True)
                c1, c2 = st.columns(2)
                if c1.button("Eliminar", icon=":material/delete:", width="stretch"):
                    ejecutar(lambda: ng.eliminar_parque(s, anio, cor),
                             "Parque «" + elegido.nombre + "»: eliminación {r}.", recargar=True)
                if not elegido.activo and c2.button("Reactivar", icon=":material/restore:", width="stretch"):
                    ejecutar(lambda: ng.reactivar_parque(s, anio, cor), "Parque reactivado.", recargar=True)
                st.caption("Con excursiones, inventario, asignaciones o estudios asociados, el parque se "
                           "desactiva (eliminación lógica) para no romper la integridad referencial.")


def _form_especie(prefijo: str, tipo: str, b: dict | None = None) -> tuple[dict, dict]:
    b = b or {}
    estados = ["LC", "NT", "VU", "EN", "CR", "NO_APLICA"]
    origenes = ["NATIVO", "ENDEMICO", "INTRODUCIDO", "GEOLOGICO"]
    datos = {
        "nombre_comun": st.text_input("Nombre común", b.get("nombre_comun") or "", key=f"{prefijo}_nm"),
        "nombre_cientifico": st.text_input("Nombre científico", b.get("nombre_cientifico") or "", key=f"{prefijo}_nc"),
    }
    c1, c2 = st.columns(2)
    datos["estado_conservacion"] = c1.selectbox("Estado UICN", estados,
                                                estados.index(b.get("estado_conservacion") or "LC"), key=f"{prefijo}_es")
    datos["origen"] = c2.selectbox("Origen", origenes, origenes.index(b.get("origen") or "NATIVO"), key=f"{prefijo}_or")
    sub: dict = {}
    if tipo == "VEGETAL":
        tv = ["ARBOL", "ARBUSTO", "HIERBA", "HELECHO", "CACTACEA", "TREPADORA"]
        sub["tipo_vegetacion"] = c1.selectbox("Tipo de vegetación", tv, tv.index(b.get("tipo_vegetacion") or "ARBOL"),
                                              key=f"{prefijo}_tv")
        sub["periodo_floracion"] = c2.text_input("Floración", b.get("periodo_floracion") or "", key=f"{prefijo}_pf")
    elif tipo == "ANIMAL":
        ta = ["HERBIVORO", "CARNIVORO", "OMNIVORO", "INSECTIVORO", "CARRONERO", "PISCIVORO"]
        sub["tipo_alimentacion"] = c1.selectbox("Alimentación", ta, ta.index(b.get("tipo_alimentacion") or "HERBIVORO"),
                                                key=f"{prefijo}_ta")
        sub["periodo_celo"] = c2.text_input("Período de celo", b.get("periodo_celo") or "", key=f"{prefijo}_pc")
    elif tipo == "MINERAL":
        sub["tipo_material"] = c1.text_input("Tipo de material", b.get("tipo_material") or "", key=f"{prefijo}_tm")
        sub["composicion"] = c2.text_input("Composición", b.get("composicion") or "", key=f"{prefijo}_co")
        sub["dureza_mohs"] = c1.number_input("Dureza de Mohs", 1.0, 10.0, float(b.get("dureza_mohs") or 5.0), 0.5,
                                             key=f"{prefijo}_du")
    datos["descripcion"] = st.text_area("Descripción", b.get("descripcion") or "", max_chars=250, height=80,
                                        key=f"{prefijo}_de")
    return datos, sub


def crud_especies(s: Sesion) -> None:
    c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
    tipos = c1.pills("Tipo", ng.TIPOS_ESPECIE, selection_mode="multi", default=ng.TIPOS_ESPECIE)
    ver_todas = c2.toggle("Incluir desactivadas", key="te")
    df = ng.listar_especies(solo_activas=not ver_todas)
    df = df[df["tipo"].isin(tipos or [])].reset_index(drop=True)
    tabla, panel = st.columns([1.55, 1], gap="medium")
    with tabla:
        st.caption(f"{len(df)} especies. Seleccione una fila para editarla o eliminarla.")
        ev = st.dataframe(
            df[["nombre_comun", "nombre_cientifico", "tipo", "estado_conservacion", "origen", "registros_inventario",
                "activo"]],
            hide_index=True, width="stretch", height=430, on_select="rerun", selection_mode="single-row",
            key="tabla_especies",
            column_config={"nombre_comun": "Nombre común", "nombre_cientifico": "Nombre científico", "tipo": "Tipo",
                           "estado_conservacion": "UICN", "origen": "Origen",
                           "registros_inventario": st.column_config.NumberColumn("Inventarios", width="small"),
                           "activo": st.column_config.CheckboxColumn("Activa", width="small")})
    e = fila_seleccionada(ev, df)
    with panel:
        with st.container(border=True):
            if e is None:
                st.markdown("**Nueva especie**")
                tipo = st.radio("Tipo", ng.TIPOS_ESPECIE, horizontal=True, key="ct")
                with st.form("crear_especie", border=False):
                    datos, sub = _form_especie(f"ce_{tipo}", tipo)
                    if st.form_submit_button("Crear especie", type="primary", width="stretch", icon=":material/add:"):
                        ejecutar(lambda: ng.crear_especie(s, datos, tipo, sub), "Especie creada con id {r}.",
                                 recargar=True)
            else:
                st.markdown(f"**{e.nombre_comun}** · *{e.nombre_cientifico}* · {e.tipo.lower()}")
                with st.form("editar_especie", border=False):
                    datos, sub = _form_especie(f"ee{e.id_recurso}", e.tipo, e.to_dict())
                    if st.form_submit_button("Guardar cambios", type="primary", width="stretch", icon=":material/save:"):
                        ejecutar(lambda: ng.actualizar_especie(s, int(e.id_recurso), datos, e.tipo, sub),
                                 "Especie actualizada.", recargar=True)
                b1, b2 = st.columns(2)
                if b1.button("Eliminar", icon=":material/delete:", width="stretch"):
                    ejecutar(lambda: ng.eliminar_especie(s, int(e.id_recurso)),
                             "Especie «" + e.nombre_comun + "»: eliminación {r}.", recargar=True)
                if not e.activo and b2.button("Reactivar", icon=":material/restore:", width="stretch"):
                    ejecutar(lambda: ng.reactivar_especie(s, int(e.id_recurso)), "Especie reactivada.", recargar=True)
                st.caption(f"Registros de inventario: {int(e.registros_inventario)}. Con inventario o proyectos "
                           "asociados se aplica desactivación lógica. El subtipo no se cambia (especialización disjunta).")


def pagina_maestros() -> None:
    s = sesion()
    secciones = [n for n, p in (("Parques", CRUD_PARQUE), ("Especies", CRUD_ESPECIE)) if s and s.puede(p)]
    if not secciones:
        requiere(CRUD_PARQUE)
    banda("Parques y especies", s)
    mostrar_aviso()
    eleccion = st.segmented_control("Tabla", secciones, default=secciones[0],
                                    label_visibility="collapsed") or secciones[0]
    if eleccion == "Parques":
        crud_parques(requiere(CRUD_PARQUE))
    else:
        crud_especies(requiere(CRUD_ESPECIE))


# ---------------------------------------------------------------------
# 3. Control de usuarios
# ---------------------------------------------------------------------
def pagina_usuarios() -> None:
    s = requiere(USUARIOS)
    banda("Cuentas y roles", s)
    mostrar_aviso()
    df = ng.listar_cuentas(s)
    c = st.columns(3)
    c[0].metric("Cuentas", len(df))
    c[1].metric("Activas", int(df["activa"].sum()))
    c[2].metric("Administradores", int(df["roles"].fillna("").str.contains("ADMINISTRADOR").sum()))
    tabla, panel = st.columns([1.55, 1], gap="medium")
    with tabla:
        ev = st.dataframe(df[["usuario", "trabajador", "cargo", "roles", "activa"]], hide_index=True, width="stretch",
                          height=420, on_select="rerun", selection_mode="single-row", key="tabla_cuentas",
                          column_config={"usuario": "Usuario", "trabajador": "Trabajador", "cargo": "Cargo",
                                         "roles": "Roles", "activa": st.column_config.CheckboxColumn("Activa")})
    cuenta = fila_seleccionada(ev, df)
    with panel:
        with st.container(border=True):
            st.markdown("**Permisos por rol**")
            st.markdown("- **Administrador:** todo\n- **Operador:** inscripciones e indicadores\n"
                        "- **Analista:** especies e indicadores")
            if cuenta is None:
                st.caption("Seleccione una cuenta en la tabla para cambiar su estado o sus roles.")
            else:
                st.divider()
                st.markdown(f"**{cuenta.usuario}** · {cuenta.trabajador}")
                with st.form("cuenta", border=False):
                    activa = st.toggle("Cuenta activa", value=bool(cuenta.activa))
                    roles = st.multiselect("Roles", ng.ROLES,
                                           default=cuenta.roles.split(", ") if cuenta.roles else [])
                    if st.form_submit_button("Guardar", type="primary", width="stretch", icon=":material/save:"):
                        ejecutar(lambda: ng.actualizar_cuenta(s, int(cuenta.id_cuenta), activa, roles),
                                 "Cuenta actualizada.", recargar=True)


# ---------------------------------------------------------------------
# 4. Dashboard: cuatro preguntas en cuadrícula 2x2
# ---------------------------------------------------------------------
def pagina_dashboard() -> None:
    s = requiere(DASHBOARD)
    banda("Indicadores", s)
    parques = ng.listar_parques()["nombre"].tolist()
    with st.container(border=True):
        f1, f2, f3 = st.columns([1, 1, 2])
        inicio = f1.date_input("Desde", date(2025, 1, 1), format="DD/MM/YYYY")
        fin = f2.date_input("Hasta", date.today(), format="DD/MM/YYYY")
        parque_sel = f3.selectbox("Parque (preguntas 2 y 3)", ["Todos"] + parques)
    if inicio > fin:
        st.error("La fecha inicial debe ser anterior a la final.")
        st.stop()
    psel = None if parque_sel == "Todos" else parque_sel

    fila1 = st.columns(2, gap="medium")
    fila2 = st.columns(2, gap="medium")

    # P1 · Áreas con más visitantes ----------------------------------------
    with fila1[0].container(border=True):
        st.markdown("**1 · Áreas con más visitantes**")
        a, b = st.columns([3, 1])
        sel_parques = a.multiselect("Parques", parques, default=parques, key="p1", label_visibility="collapsed",
                                    placeholder="Parques")
        top = b.number_input("Top", 5, 30, 10, label_visibility="collapsed")
        d1 = ng.dash_areas_visitantes(s, inicio, fin, sel_parques)
        if d1.empty:
            st.info("Sin visitantes en el período y parques elegidos.")
        else:
            d1 = d1.head(int(top))
            fig = px.bar(d1, x="visitantes", y="area", orientation="h", text="visitantes",
                         hover_data=["parque", "excursiones"], labels={"visitantes": "Visitantes (asistencias)", "area": ""},
                         color_discrete_sequence=[BOSQUE])
            fig.update_yaxes(categoryorder="total ascending")
            fig.update_traces(textposition="outside", cliponaxis=False)
            fig.update_layout(height=390, showlegend=False)
            st.plotly_chart(fig, width="stretch")

    # P2 · Composición de especies -------------------------------------------
    with fila1[1].container(border=True):
        st.markdown("**2 · Composición de especies inventariadas**")
        todas_areas = ng.listar_areas()
        areas = [] if psel is None else todas_areas.loc[todas_areas["parque"] == psel, "nombre"].tolist()
        a, b = st.columns(2)
        area2 = a.selectbox("Área", ["Todas"] + areas, key="a2", label_visibility="collapsed")
        medida = b.segmented_control("Medida", ["Especies", "Cantidad"], default="Especies",
                                     label_visibility="collapsed") or "Especies"
        d2 = ng.dash_composicion_especies(s, psel, None if area2 == "Todas" else area2)
        if d2.empty:
            st.info("Sin inventario para el filtro.")
        else:
            col = "especies" if medida == "Especies" else "cantidad"
            eje = "parque" if psel is None else "area"
            g = d2.groupby([eje, "tipo"], as_index=False)[col].sum()
            fig = px.bar(g, y=eje, x=col, color="tipo", orientation="h", color_discrete_map=COLORES_TIPO,
                         barmode="stack", labels={col: "Especies distintas" if col == "especies" else "% de la cantidad",
                                                  eje: "", "tipo": ""})
            if col == "cantidad":
                fig.update_layout(barnorm="percent")
            fig.update_layout(height=390)
            st.plotly_chart(fig, width="stretch")

    # P3 · Participantes vs evaluación ---------------------------------------
    with fila2[0].container(border=True):
        st.markdown("**3 · Participantes por excursión vs. evaluación**")
        d3 = ng.dash_visitantes_vs_evaluacion(s, inicio, fin, psel)
        if len(d3) < 3:
            st.info("Se necesitan al menos 3 excursiones evaluadas para analizar la relación.")
        else:
            x, y = d3["participantes"].astype(float), d3["promedio"].astype(float)
            r = float(np.corrcoef(x, y)[0, 1]) if x.std() > 0 else float("nan")
            m, b0 = np.polyfit(x, y, 1) if x.std() > 0 else (0.0, y.mean())
            k1, k2 = st.columns(2)
            k1.metric("Correlación (r)", f"{r:.2f}")
            k2.metric("Cambio por participante", f"{m:+.3f}")
            vista = st.segmented_control("Ver", ["Gráfico", "Tabla"], default="Gráfico",
                                         label_visibility="collapsed") or "Gráfico"
            if vista == "Gráfico":
                fig = px.scatter(d3, x="participantes", y="promedio", color="modalidad", size="evaluaciones",
                                 color_discrete_map=COLORES_MODALIDAD, opacity=0.75,
                                 hover_data=["codigo_excursion", "parque", "area", "fecha"],
                                 labels={"participantes": "Participantes", "promedio": "Evaluación (1-5)",
                                         "modalidad": ""})
                xs = np.linspace(x.min(), x.max(), 20)
                fig.add_trace(go.Scatter(x=xs, y=m * xs + b0, mode="lines", name="Tendencia",
                                         line={"color": TINTA, "dash": "dash"}))
                fig.update_layout(height=330, legend={"orientation": "h", "y": 1.12, "x": 0})
                st.plotly_chart(fig, width="stretch")
            else:
                st.dataframe(d3, hide_index=True, width="stretch", height=330)

    # P4 · Ocupación de la capacidad (pregunta propuesta) --------------------
    with fila2[1].container(border=True):
        st.markdown("**4 · Aprovechamiento de la capacidad** (propuesta)")
        st.caption("¿Qué parques y modalidades usan menos los cupos que ofrecen? Orienta dónde reducir "
                   "frecuencia y dónde reasignar guías.")
        d4 = ng.dash_ocupacion_capacidad(s, inicio, fin)
        if d4.empty:
            st.info("Sin excursiones realizadas en el período.")
        else:
            piv = d4.pivot_table(index="parque", columns="modalidad", values="ocupacion_pct")
            fig = px.imshow(piv, text_auto=".0f", aspect="auto", zmin=0, zmax=100,
                            color_continuous_scale=[[0, "#B5452B"], [0.5, "#F1D9A7"], [1, "#3E7A5A"]],
                            labels={"color": "% ocupación", "x": "", "y": ""})
            fig.update_layout(height=330, coloraxis_colorbar={"thickness": 10})
            st.plotly_chart(fig, width="stretch")
            bajo = d4[d4["excursiones"] >= 2].nsmallest(3, "ocupacion_pct")
            if not bajo.empty:
                st.caption("Menor aprovechamiento (≥ 2 excursiones): " + "; ".join(
                    f"{r.parque} · {r.modalidad.lower()} ({r.ocupacion_pct:.0f} %)" for r in bajo.itertuples()))


# ---------------------------------------------------------------------
# Navegación superior según rol (solo se registran las páginas permitidas)
# ---------------------------------------------------------------------
def main() -> None:
    s = sesion()
    if s is None:
        st.navigation([st.Page(pantalla_login, title="Ingreso", icon=":material/login:")], position="hidden").run()
        return
    paginas = {"pages_inicio": st.Page(pagina_inicio, title="Inicio", icon=":material/home:", default=True)}
    if s.puede(INSCRIPCION):
        paginas["pages_inscripciones"] = st.Page(pagina_inscripcion, title="Inscripciones",
                                                 icon=":material/how_to_reg:", url_path="inscripciones")
    if s.puede(CRUD_PARQUE) or s.puede(CRUD_ESPECIE):
        paginas["pages_maestros"] = st.Page(pagina_maestros, title="Parques y especies",
                                            icon=":material/forest:", url_path="maestros")
    if s.puede(DASHBOARD):
        paginas["pages_dashboard"] = st.Page(pagina_dashboard, title="Indicadores",
                                             icon=":material/monitoring:", url_path="indicadores")
    if s.puede(USUARIOS):
        paginas["pages_usuarios"] = st.Page(pagina_usuarios, title="Usuarios",
                                            icon=":material/manage_accounts:", url_path="usuarios")
    st.session_state["_paginas"] = paginas
    st.navigation(list(paginas.values()), position="top").run()


main()
