"""PMV · Sistema Integral de Gestión de Parques Naturales · Caso 1 · Grupo 1

Ejecutar:  streamlit run app/main.py
Arquitectura: Usuario → Streamlit (main.py) → negocio.py (reglas, permisos,
transacciones) → db.py (SQLAlchemy + PyMySQL) → MySQL 8 (parques_db)
"""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import negocio as ng
from seguridad import (CRUD_ESPECIE, CRUD_PARQUE, DASHBOARD, INSCRIPCION, USUARIOS,
                       PermisoDenegado, Sesion)

st.set_page_config(page_title="Parques Naturales · Gestión", page_icon="🌲", layout="wide")

COLORES_TIPO = {"Vegetal": "#4C8C4A", "Animal": "#B5651D", "Mineral": "#6B7A8F", "Sin clasificar": "#C9A227"}
COLORES_MODALIDAD = {"GUIADA": "#2F5D50", "AUTOGUIADA": "#E08E2B", "EDUCATIVA": "#3E7CB1", "NOCTURNA": "#7A4E9E"}


# ---------------------------------------------------------------------
# Sesión y control de acceso
# ---------------------------------------------------------------------
def sesion() -> Sesion | None:
    return st.session_state.get("sesion")


def requiere(permiso: str) -> Sesion:
    """Control de acceso efectivo en la interfaz: detiene la página si el rol no autoriza."""
    s = sesion()
    if s is None or not s.puede(permiso):
        st.error("Acceso denegado: su rol no tiene permiso para esta sección.")
        st.stop()
    return s


def pantalla_login() -> None:
    st.title("🌲 Gestión de Parques Naturales")
    st.caption("Ingrese con su cuenta de trabajador.")
    with st.form("login"):
        usuario = st.text_input("Usuario")
        clave = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Ingresar", type="primary"):
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


def mostrar_aviso() -> None:
    """Muestra el mensaje de éxito guardado antes de recargar la página."""
    msg = st.session_state.pop("aviso", None)
    if msg:
        st.success(msg)


def ejecutar(accion, exito: str, recargar: bool = False):
    """Ejecuta una operación de negocio mostrando errores de forma uniforme.
    Con recargar=True guarda el mensaje y recarga la página para mostrar datos actualizados."""
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


# ---------------------------------------------------------------------
# 1. Formulario transaccional: inscripción
# ---------------------------------------------------------------------
def pagina_inscripcion() -> None:
    s = requiere(INSCRIPCION)
    st.header("Inscripción de visitantes")
    mostrar_aviso()
    tab1, tab2 = st.tabs(["Nueva inscripción", "Registrar asistencia"])

    with tab1:
        exc = ng.excursiones_abiertas()
        if exc.empty:
            st.info("No hay excursiones abiertas desde hoy en adelante.")
            return
        exc["cupos"] = exc["capacidad"] - exc["inscritos"]
        exc["etiqueta"] = exc.apply(
            lambda r: f"{r.codigo_excursion} · {r.fecha:%d-%m-%Y} {str(r.horario)[-8:-3]} · {r.parque} / {r.area}"
                      f" · {r.modalidad} · {r.cupos} cupos libres de {r.capacidad}", axis=1)
        col1, col2 = st.columns([3, 2])
        with col1:
            sel = st.selectbox("Excursión", exc["etiqueta"].tolist())
            fila = exc[exc["etiqueta"] == sel].iloc[0]
            st.progress(min(1.0, fila.inscritos / fila.capacidad),
                        text=f"Ocupación: {fila.inscritos} de {fila.capacidad}")
        with col2:
            filtro = st.text_input("Buscar visitante (RUT, nombre o apellido)")
            vis = ng.buscar_visitantes(filtro)
            if vis.empty:
                st.warning("Sin coincidencias.")
                return
            opcion = st.selectbox("Visitante", (vis["rut_persona"] + " · " + vis["nombre"]).tolist())
        with st.form("form_inscripcion", clear_on_submit=True):
            estados = ["INSCRITO"] if fila.fecha > date.today() else ["INSCRITO", "ASISTIO", "NO_ASISTIO"]
            estado = st.radio("Estado de asistencia", estados, horizontal=True,
                              help="La asistencia solo puede registrarse desde el día de la excursión.")
            obs = st.text_input("Observaciones (opcional)", max_chars=200)
            if st.form_submit_button("Inscribir visitante", type="primary"):
                rut = opcion.split(" · ")[0]
                ejecutar(lambda: ng.inscribir_visitante(s, rut, fila.codigo_excursion, estado, obs),
                         "Inscripción {r} registrada.", recargar=True)
        with st.expander("Inscritos en esta excursión"):
            st.dataframe(ng.inscripciones_de(fila.codigo_excursion), hide_index=True, width="stretch")

    with tab2:
        realizadas = ng.excursiones_realizadas()
        if realizadas.empty:
            st.info("No hay excursiones realizadas con inscripciones.")
            return
        realizadas["etiqueta"] = realizadas.apply(
            lambda r: f"{r.codigo_excursion} · {r.fecha:%d-%m-%Y} · {r.parque} / {r.area} · pendientes: {int(r.pendientes)}",
            axis=1)
        sel2 = st.selectbox("Excursión realizada", realizadas["etiqueta"].tolist())
        cod = sel2.split(" · ")[0]
        ins = ng.inscripciones_de(cod)
        editado = st.data_editor(
            ins, hide_index=True, width="stretch", key=f"asis_{cod}",
            disabled=["id_inscripcion", "rut_persona", "visitante", "fecha_inscripcion", "evaluada"],
            column_config={"estado_asistencia": st.column_config.SelectboxColumn(
                "Asistencia", options=["INSCRITO", "ASISTIO", "NO_ASISTIO"], required=True)})
        if st.button("Guardar asistencia", type="primary"):
            cambios = dict(zip(editado["id_inscripcion"], editado["estado_asistencia"]))
            ejecutar(lambda: ng.registrar_asistencia(s, cod, cambios), "{r} inscripciones actualizadas.", recargar=True)


# ---------------------------------------------------------------------
# 2. CRUD de tablas maestras: Parque y Especie
# ---------------------------------------------------------------------
def _form_parque(prefijo: str, base: dict | None = None) -> dict:
    b = base or {}
    c1, c2 = st.columns(2)
    with c1:
        nombre = st.text_input("Nombre", b.get("nombre", ""), key=f"{prefijo}_n")
        fecha = st.date_input("Fecha de declaración", b.get("fecha_declaracion", date(2000, 1, 1)),
                              min_value=date(1900, 1, 1), max_value=date.today(), key=f"{prefijo}_f")
        sup = st.number_input("Superficie total (ha)", 0.0, value=float(b.get("superficie_total", 1000.0)),
                              key=f"{prefijo}_s")
        pres = st.number_input("Presupuesto anual (CLP)", 0.0, value=float(b.get("presupuesto_anual", 1e8)),
                               step=1e6, key=f"{prefijo}_p")
    with c2:
        est = st.selectbox("Estado de conservación", ng.ESTADOS_PARQUE,
                           ng.ESTADOS_PARQUE.index(b.get("estado_conservacion", "BUENO")), key=f"{prefijo}_e")
        cat = st.selectbox("Categoría SNASPE", ng.CATEGORIAS,
                           ng.CATEGORIAS.index(b.get("categoria_snap", "PARQUE NACIONAL")), key=f"{prefijo}_c")
        org = st.text_input("Organismo responsable", b.get("organismo_responsable", "CONAF"), key=f"{prefijo}_o")
    return {"nombre": nombre, "fecha_declaracion": fecha, "superficie_total": sup, "presupuesto_anual": pres,
            "estado_conservacion": est, "categoria_snap": cat, "organismo_responsable": org}


def crud_parques(s: Sesion) -> None:
    ver_todos = st.toggle("Mostrar también parques desactivados", key="tp")
    df = ng.listar_parques(solo_activos=not ver_todos)
    st.dataframe(df, hide_index=True, width="stretch")
    t_crear, t_editar, t_borrar = st.tabs(["Crear", "Modificar", "Eliminar / desactivar"])
    with t_crear:
        with st.form("crear_parque", clear_on_submit=False):
            datos = _form_parque("cp")
            st.markdown("**Región principal y primera área** (todo parque requiere ambas)")
            reg = ng.listar_regiones()
            c1, c2, c3 = st.columns(3)
            region = c1.selectbox("Región principal", reg["nombre"].tolist())
            area_n = c2.text_input("Nombre de la primera área", "Sector Acceso")
            area_e = c3.number_input("Extensión del área (ha)", 0.0, value=100.0)
            if st.form_submit_button("Crear parque", type="primary"):
                id_reg = int(reg.loc[reg["nombre"] == region, "id_region"].iloc[0])
                ejecutar(lambda: ng.crear_parque(s, datos, id_reg, {"nombre": area_n, "extension": area_e}),
                         "Parque creado con clave {r}.", recargar=True)
    opciones = {f"{r.nombre} ({r.anio_declaracion}-{r.nro_correlativo})": r for r in df.itertuples()}
    with t_editar:
        if opciones:
            elegido = opciones[st.selectbox("Parque a modificar", list(opciones), key="ep")]
            with st.form("editar_parque"):
                datos = _form_parque(f"ep{elegido.anio_declaracion}{elegido.nro_correlativo}", elegido._asdict())
                if st.form_submit_button("Guardar cambios", type="primary"):
                    ejecutar(lambda: ng.actualizar_parque(s, elegido.anio_declaracion, elegido.nro_correlativo, datos),
                             "Parque actualizado.", recargar=True)
    with t_borrar:
        if opciones:
            elegido = opciones[st.selectbox("Parque", list(opciones), key="bp")]
            st.caption("Si el parque tiene excursiones, inventarios, asignaciones o estudios, se desactiva "
                       "(eliminación lógica) para no romper la integridad referencial.")
            c1, c2 = st.columns(2)
            if c1.button("Eliminar parque", type="primary"):
                ejecutar(lambda: ng.eliminar_parque(s, elegido.anio_declaracion, elegido.nro_correlativo),
                         "Parque «" + elegido.nombre + "»: eliminación {r}.", recargar=True)
            if not elegido.activo and c2.button("Reactivar parque"):
                ejecutar(lambda: ng.reactivar_parque(s, elegido.anio_declaracion, elegido.nro_correlativo),
                         "Parque reactivado.", recargar=True)


def _form_especie(prefijo: str, tipo: str, b: dict | None = None) -> tuple[dict, dict]:
    b = b or {}
    estados = ["LC", "NT", "VU", "EN", "CR", "NO_APLICA"]
    origenes = ["NATIVO", "ENDEMICO", "INTRODUCIDO", "GEOLOGICO"]
    c1, c2 = st.columns(2)
    datos = {
        "nombre_cientifico": c1.text_input("Nombre científico", b.get("nombre_cientifico", ""), key=f"{prefijo}_nc"),
        "nombre_comun": c2.text_input("Nombre común", b.get("nombre_comun", ""), key=f"{prefijo}_nm"),
        "estado_conservacion": c1.selectbox("Estado de conservación (UICN)", estados,
                                            estados.index(b.get("estado_conservacion") or "LC"), key=f"{prefijo}_es"),
        "origen": c2.selectbox("Origen", origenes, origenes.index(b.get("origen") or "NATIVO"), key=f"{prefijo}_or"),
        "descripcion": st.text_area("Descripción", b.get("descripcion") or "", max_chars=250, key=f"{prefijo}_de"),
    }
    sub: dict = {}
    if tipo == "VEGETAL":
        tv = ["ARBOL", "ARBUSTO", "HIERBA", "HELECHO", "CACTACEA", "TREPADORA"]
        sub["periodo_floracion"] = c1.text_input("Período de floración", b.get("periodo_floracion") or "", key=f"{prefijo}_pf")
        sub["tipo_vegetacion"] = c2.selectbox("Tipo de vegetación", tv, tv.index(b.get("tipo_vegetacion") or "ARBOL"),
                                              key=f"{prefijo}_tv")
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
    return datos, sub


def crud_especies(s: Sesion) -> None:
    ver_todas = st.toggle("Mostrar también especies desactivadas", key="te")
    df = ng.listar_especies(solo_activas=not ver_todas)
    tipos = st.multiselect("Filtrar por tipo", ng.TIPOS_ESPECIE, default=ng.TIPOS_ESPECIE)
    st.dataframe(df[df["tipo"].isin(tipos)], hide_index=True, width="stretch")
    t_crear, t_editar, t_borrar = st.tabs(["Crear", "Modificar", "Eliminar / desactivar"])
    with t_crear:
        tipo = st.radio("Tipo de especie", ng.TIPOS_ESPECIE, horizontal=True, key="ct")
        with st.form("crear_especie"):
            datos, sub = _form_especie(f"ce_{tipo}", tipo)
            if st.form_submit_button("Crear especie", type="primary"):
                ejecutar(lambda: ng.crear_especie(s, datos, tipo, sub), "Especie creada con id {r}.", recargar=True)
    opciones = {f"{r.nombre_comun} · {r.nombre_cientifico} (id {r.id_recurso})": r for r in df.itertuples()}
    with t_editar:
        if opciones:
            e = opciones[st.selectbox("Especie a modificar", list(opciones), key="ee")]
            st.caption(f"Tipo: {e.tipo} (el subtipo no se cambia para mantener la especialización disjunta).")
            with st.form("editar_especie"):
                datos, sub = _form_especie(f"ee{e.id_recurso}", e.tipo, e._asdict())
                if st.form_submit_button("Guardar cambios", type="primary"):
                    ejecutar(lambda: ng.actualizar_especie(s, e.id_recurso, datos, e.tipo, sub), "Especie actualizada.",
                             recargar=True)
    with t_borrar:
        if opciones:
            e = opciones[st.selectbox("Especie", list(opciones), key="be")]
            st.caption(f"Registros de inventario: {e.registros_inventario}. Con inventario o proyectos asociados "
                       "se aplica desactivación lógica.")
            c1, c2 = st.columns(2)
            if c1.button("Eliminar especie", type="primary"):
                ejecutar(lambda: ng.eliminar_especie(s, e.id_recurso),
                         "Especie «" + e.nombre_comun + "»: eliminación {r}.", recargar=True)
            if not e.activo and c2.button("Reactivar especie"):
                ejecutar(lambda: ng.reactivar_especie(s, e.id_recurso), "Especie reactivada.", recargar=True)


def pagina_crud() -> None:
    s = sesion()
    st.header("Tablas maestras")
    mostrar_aviso()
    secciones = [n for n, p in (("Parques", CRUD_PARQUE), ("Especies", CRUD_ESPECIE)) if s and s.puede(p)]
    if not secciones:
        requiere(CRUD_PARQUE)
    eleccion = st.segmented_control("Tabla", secciones, default=secciones[0]) or secciones[0]
    if eleccion == "Parques":
        crud_parques(requiere(CRUD_PARQUE))
    else:
        crud_especies(requiere(CRUD_ESPECIE))


# ---------------------------------------------------------------------
# 3. Control de usuarios
# ---------------------------------------------------------------------
def pagina_usuarios() -> None:
    s = requiere(USUARIOS)
    st.header("Cuentas y roles")
    mostrar_aviso()
    st.caption("ADMINISTRADOR: todo · OPERADOR: inscripciones y dashboard · ANALISTA: especies y dashboard")
    df = ng.listar_cuentas(s)
    st.dataframe(df, hide_index=True, width="stretch")
    opciones = {f"{r.usuario} · {r.trabajador}": r for r in df.itertuples()}
    c = opciones[st.selectbox("Cuenta", list(opciones))]
    with st.form("cuenta"):
        activa = st.checkbox("Cuenta activa", value=bool(c.activa))
        roles = st.multiselect("Roles", ng.ROLES, default=(c.roles or "").split(", ") if c.roles else [])
        if st.form_submit_button("Guardar", type="primary"):
            ejecutar(lambda: ng.actualizar_cuenta(s, int(c.id_cuenta), activa, roles), "Cuenta actualizada.",
                     recargar=True)


# ---------------------------------------------------------------------
# 4. Dashboard
# ---------------------------------------------------------------------
def pagina_dashboard() -> None:
    s = requiere(DASHBOARD)
    st.header("Panel de información")
    parques = ng.listar_parques()["nombre"].tolist()
    c1, c2 = st.columns(2)
    inicio = c1.date_input("Desde", date(2025, 1, 1))
    fin = c2.date_input("Hasta", date.today())
    if inicio > fin:
        st.error("La fecha inicial debe ser anterior a la final.")
        st.stop()

    # P1 ---------------------------------------------------------------
    st.subheader("1 · Áreas con más visitantes en el período")
    sel_parques = st.multiselect("Parques", parques, default=parques, key="p1")
    top = st.slider("Mostrar las primeras", 5, 30, 10)
    d1 = ng.dash_areas_visitantes(s, inicio, fin, sel_parques)
    if d1.empty:
        st.info("Sin visitantes en el período y parques elegidos.")
    else:
        d1 = d1.head(top).iloc[::-1]
        fig = px.bar(d1, x="visitantes", y="area", orientation="h", color="parque",
                     hover_data=["excursiones"], labels={"visitantes": "Visitantes (asistencias)", "area": ""})
        fig.update_layout(height=max(320, 32 * len(d1)), legend_title_text="Parque")
        fig.update_yaxes(categoryorder="total ascending")   # ranking real aunque haya colores por parque
        st.plotly_chart(fig, width="stretch")

    # P2 ---------------------------------------------------------------
    st.subheader("2 · Composición de especies inventariadas")
    c1, c2, c3 = st.columns(3)
    parque2 = c1.selectbox("Parque", ["Todos"] + parques, key="p2")
    todas_areas = ng.listar_areas()
    areas = [] if parque2 == "Todos" else todas_areas.loc[todas_areas["parque"] == parque2, "nombre"].tolist()
    area2 = c2.selectbox("Área", ["Todas"] + areas, key="a2")
    medida = c3.radio("Medida", ["Especies distintas", "Cantidad inventariada"], horizontal=True)
    d2 = ng.dash_composicion_especies(s, None if parque2 == "Todos" else parque2, None if area2 == "Todas" else area2)
    if d2.empty:
        st.info("Sin inventario para el filtro.")
    else:
        col = "especies" if medida == "Especies distintas" else "cantidad"
        eje = "parque" if parque2 == "Todos" else "area"
        g = d2.groupby([eje, "tipo"], as_index=False)[col].sum()
        fig = px.bar(g, x=eje, y=col, color="tipo", color_discrete_map=COLORES_TIPO, barmode="stack",
                     labels={col: medida, eje: "", "tipo": "Tipo"})
        if col == "cantidad":
            fig.update_layout(barnorm="percent", yaxis_title="% de la cantidad inventariada")
        st.plotly_chart(fig, width="stretch")

    # P3 ---------------------------------------------------------------
    st.subheader("3 · Participantes por excursión y evaluación promedio")
    parque3 = st.selectbox("Parque", ["Todos"] + parques, key="p3")
    d3 = ng.dash_visitantes_vs_evaluacion(s, inicio, fin, None if parque3 == "Todos" else parque3)
    if len(d3) < 3:
        st.info("Se necesitan al menos 3 excursiones evaluadas para analizar la relación.")
    else:
        x, y = d3["participantes"].astype(float), d3["promedio"].astype(float)
        r = float(np.corrcoef(x, y)[0, 1]) if x.std() > 0 else float("nan")
        m, b = np.polyfit(x, y, 1) if x.std() > 0 else (0.0, y.mean())
        fig = px.scatter(d3, x="participantes", y="promedio", color="modalidad", size="evaluaciones",
                         color_discrete_map=COLORES_MODALIDAD, opacity=0.75,
                         hover_data=["codigo_excursion", "parque", "area", "fecha"],
                         labels={"participantes": "Participantes (asistentes)", "promedio": "Evaluación promedio (1-5)"})
        xs = np.linspace(x.min(), x.max(), 20)
        fig.add_trace(go.Scatter(x=xs, y=m * xs + b, mode="lines", name="Tendencia lineal",
                                 line={"color": "#1E2A26", "dash": "dash"}))
        st.plotly_chart(fig, width="stretch")
        st.caption(f"Correlación de Pearson r = {r:.2f} (n = {len(d3)} excursiones). "
                   f"Pendiente: {m:+.3f} puntos de evaluación por participante adicional.")
        st.dataframe(d3, hide_index=True, width="stretch")

    # P4 ---------------------------------------------------------------
    st.subheader("4 · Aprovechamiento de la capacidad por parque y modalidad")
    st.caption("Pregunta propuesta: ¿qué parques y modalidades usan menos la capacidad ofertada? "
               "Apoya decidir dónde reducir cupos o frecuencia y dónde ampliarlos, reasignando guías.")
    d4 = ng.dash_ocupacion_capacidad(s, inicio, fin)
    if d4.empty:
        st.info("Sin excursiones realizadas en el período.")
    else:
        piv = d4.pivot_table(index="parque", columns="modalidad", values="ocupacion_pct")
        fig = px.imshow(piv, text_auto=".0f", color_continuous_scale="RdYlGn", zmin=0, zmax=100, aspect="auto",
                        labels={"color": "% ocupación", "x": "Modalidad", "y": ""})
        fig.update_layout(height=max(360, 28 * len(piv)))
        st.plotly_chart(fig, width="stretch")
        bajo = d4[d4["excursiones"] >= 2].nsmallest(3, "ocupacion_pct")
        if not bajo.empty:
            st.markdown("**Menor aprovechamiento (≥ 2 excursiones):** " + "; ".join(
                f"{r.parque} · {r.modalidad.lower()} ({r.ocupacion_pct:.0f} %)" for r in bajo.itertuples()))
        st.dataframe(d4, hide_index=True, width="stretch")


# ---------------------------------------------------------------------
# Navegación
# ---------------------------------------------------------------------
PAGINAS = [
    ("Inscripciones", INSCRIPCION, pagina_inscripcion),
    ("Tablas maestras", None, pagina_crud),
    ("Dashboard", DASHBOARD, pagina_dashboard),
    ("Usuarios", USUARIOS, pagina_usuarios),
]


def main() -> None:
    s = sesion()
    if s is None:
        pantalla_login()
        return
    with st.sidebar:
        st.markdown(f"**{s.nombre}**  \n`{s.usuario}` · {', '.join(s.roles)}")
        visibles = [p for p in PAGINAS
                    if (p[1] and s.puede(p[1])) or (p[1] is None and (s.puede(CRUD_PARQUE) or s.puede(CRUD_ESPECIE)))]
        nombre = st.radio("Ir a", [p[0] for p in visibles])
        if st.button("Cerrar sesión"):
            st.session_state.clear()
            st.rerun()
    next(p[2] for p in visibles if p[0] == nombre)()


main()
