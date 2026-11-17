"""
Generador de datos sintéticos · Caso 1 · Grupo 1 · TDFI103 Fase 2
-----------------------------------------------------------------
Genera datos coherentes y reproducibles (semilla fija) respetando las
claves foráneas, reglas de negocio y volúmenes orientativos de la sección 6
del enunciado.

Uso:
    python scripts/generar_datos.py                 # escribe sql/02_datos.sql
    python scripts/generar_datos.py --cargar        # además inserta vía SQLAlchemy
    python scripts/generar_datos.py --semilla 7     # otra semilla

La conexión para --cargar se toma de variables de entorno (ver .env.example):
DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME.

Todos los RUT, correos y teléfonos son FICTICIOS (dominio correo.example).
"""
from __future__ import annotations

import argparse
import hashlib
import os
import random
import secrets
from collections import defaultdict
from datetime import date, time, timedelta
from pathlib import Path

from faker import Faker

RAIZ = Path(__file__).resolve().parent.parent
SALIDA_SQL = RAIZ / "sql" / "02_datos.sql"

HOY = date(2026, 11, 10)          # fecha de referencia fija → datos reproducibles
INICIO_EXC = date(2024, 1, 8)
FIN_EXC = date(2026, 12, 20)
PASSWORD_DEMO = "Parques2026!"    # contraseña de PRUEBA común a las cuentas sintéticas

# ---------------------------------------------------------------------
# Catálogos base (dominio chileno, adaptación de Fase 1)
# ---------------------------------------------------------------------
REGIONES = [  # (nombre, macrozona)  → "comunidades administradoras"
    ("Arica y Parinacota", "NORTE"), ("Atacama", "NORTE"), ("Coquimbo", "NORTE"),
    ("Valparaíso", "CENTRO"), ("Maule", "CENTRO"), ("Biobío", "SUR"),
    ("La Araucanía", "SUR"), ("Los Lagos", "SUR"), ("Aysén", "AUSTRAL"),
    ("Magallanes", "AUSTRAL"),
]

# (nombre, año, categoría, regiones [principal primero], popularidad relativa)
PARQUES = [
    ("Torres del Paine", 1959, "PARQUE NACIONAL", ["Magallanes"], 3.0),
    ("Conguillío", 1950, "PARQUE NACIONAL", ["La Araucanía"], 1.6),
    ("Vicente Pérez Rosales", 1926, "PARQUE NACIONAL", ["Los Lagos"], 2.2),
    ("Puyehue", 1941, "PARQUE NACIONAL", ["Los Lagos"], 1.3),
    ("Villarrica", 1940, "PARQUE NACIONAL", ["La Araucanía", "Los Lagos"], 2.0),
    ("Lauca", 1970, "PARQUE NACIONAL", ["Arica y Parinacota"], 0.9),
    ("La Campana", 1967, "PARQUE NACIONAL", ["Valparaíso"], 1.8),
    ("Nahuelbuta", 1939, "PARQUE NACIONAL", ["La Araucanía", "Biobío"], 0.8),
    ("Pan de Azúcar", 1985, "PARQUE NACIONAL", ["Atacama"], 1.1),
    ("Chiloé", 1982, "PARQUE NACIONAL", ["Los Lagos"], 1.0),
    ("Alerce Andino", 1982, "PARQUE NACIONAL", ["Los Lagos"], 0.7),
    ("Queulat", 1983, "PARQUE NACIONAL", ["Aysén"], 0.9),
    ("Radal Siete Tazas", 1996, "RESERVA NACIONAL", ["Maule"], 1.2),
    ("Bosque Fray Jorge", 1941, "PARQUE NACIONAL", ["Coquimbo"], 0.6),
    ("Huerquehue", 1967, "PARQUE NACIONAL", ["La Araucanía"], 1.0),
    ("Pichasca", 1985, "MONUMENTO NATURAL", ["Coquimbo"], 0.4),
]
ORGANISMOS = ["CONAF", "SBAP", "CONAF - Comunidad Mapuche asociada", "CONAF - Municipalidad local"]

NOMBRES_AREA = ["Sector Lago", "Sendero del Bosque", "Mirador Norte", "Valle Central",
                "Cascadas", "Sector Volcán", "Humedal", "Quebrada Alta", "Costa",
                "Bosque Antiguo", "Glaciar", "Pampa", "Laguna Verde", "Cordón Sur"]

VEGETALES = [  # (científico, común, estado, origen, floración, tipo)
    ("Araucaria araucana", "Araucaria", "EN", "ENDEMICO", "Diciembre-Enero", "ARBOL"),
    ("Nothofagus pumilio", "Lenga", "LC", "NATIVO", "Octubre-Noviembre", "ARBOL"),
    ("Nothofagus dombeyi", "Coigüe", "LC", "NATIVO", "Septiembre-Octubre", "ARBOL"),
    ("Nothofagus antarctica", "Ñirre", "LC", "NATIVO", "Octubre-Noviembre", "ARBOL"),
    ("Fitzroya cupressoides", "Alerce", "EN", "NATIVO", "Septiembre-Octubre", "ARBOL"),
    ("Jubaea chilensis", "Palma chilena", "VU", "ENDEMICO", "Noviembre-Diciembre", "ARBOL"),
    ("Drimys winteri", "Canelo", "LC", "NATIVO", "Agosto-Octubre", "ARBOL"),
    ("Luma apiculata", "Arrayán", "LC", "NATIVO", "Enero-Marzo", "ARBOL"),
    ("Aextoxicon punctatum", "Olivillo", "LC", "ENDEMICO", "Septiembre-Noviembre", "ARBOL"),
    ("Cryptocarya alba", "Peumo", "LC", "ENDEMICO", "Noviembre-Enero", "ARBOL"),
    ("Quillaja saponaria", "Quillay", "LC", "ENDEMICO", "Octubre-Enero", "ARBOL"),
    ("Lithraea caustica", "Litre", "LC", "ENDEMICO", "Septiembre-Diciembre", "ARBOL"),
    ("Embothrium coccineum", "Notro", "LC", "NATIVO", "Octubre-Enero", "ARBUSTO"),
    ("Berberis microphylla", "Calafate", "LC", "NATIVO", "Septiembre-Noviembre", "ARBUSTO"),
    ("Fuchsia magellanica", "Chilco", "LC", "NATIVO", "Noviembre-Marzo", "ARBUSTO"),
    ("Chusquea quila", "Quila", "LC", "NATIVO", "Irregular", "ARBUSTO"),
    ("Escallonia rubra", "Siete camisas", "LC", "NATIVO", "Diciembre-Febrero", "ARBUSTO"),
    ("Azorella compacta", "Llareta", "VU", "NATIVO", "Diciembre-Febrero", "ARBUSTO"),
    ("Polylepis tarapacana", "Queñoa", "NT", "NATIVO", "Enero-Marzo", "ARBUSTO"),
    ("Gunnera tinctoria", "Nalca", "LC", "NATIVO", "Octubre-Diciembre", "HIERBA"),
    ("Alstroemeria aurea", "Amancay", "LC", "NATIVO", "Diciembre-Febrero", "HIERBA"),
    ("Chloraea magellanica", "Orquídea porcelana", "NT", "NATIVO", "Noviembre-Enero", "HIERBA"),
    ("Rhodophiala phycelloides", "Añañuca", "VU", "ENDEMICO", "Septiembre-Octubre", "HIERBA"),
    ("Leucocoryne ixioides", "Huilli", "LC", "ENDEMICO", "Septiembre-Noviembre", "HIERBA"),
    ("Lophosoria quadripinnata", "Ampe", "LC", "NATIVO", "No florece", "HELECHO"),
    ("Blechnum chilense", "Costilla de vaca", "LC", "NATIVO", "No florece", "HELECHO"),
    ("Hymenophyllum pectinatum", "Helecho película", "LC", "NATIVO", "No florece", "HELECHO"),
    ("Copiapoa cinerea", "Copiapoa", "LC", "ENDEMICO", "Noviembre-Febrero", "CACTACEA"),
    ("Echinopsis chiloensis", "Quisco", "LC", "ENDEMICO", "Octubre-Diciembre", "CACTACEA"),
    ("Eulychnia breviflora", "Copao", "NT", "ENDEMICO", "Agosto-Octubre", "CACTACEA"),
    ("Lapageria rosea", "Copihue", "LC", "ENDEMICO", "Marzo-Julio", "TREPADORA"),
    ("Mitraria coccinea", "Botellita", "LC", "NATIVO", "Noviembre-Marzo", "TREPADORA"),
    ("Pinus radiata", "Pino insigne", "LC", "INTRODUCIDO", "Agosto-Septiembre", "ARBOL"),
    ("Rubus ulmifolius", "Zarzamora", "LC", "INTRODUCIDO", "Noviembre-Enero", "ARBUSTO"),
]
ANIMALES = [  # (científico, común, estado, origen, alimentación, celo)
    ("Puma concolor", "Puma", "NT", "NATIVO", "CARNIVORO", "Todo el año"),
    ("Lama guanicoe", "Guanaco", "LC", "NATIVO", "HERBIVORO", "Noviembre-Febrero"),
    ("Vicugna vicugna", "Vicuña", "LC", "NATIVO", "HERBIVORO", "Marzo-Abril"),
    ("Hippocamelus bisulcus", "Huemul", "EN", "NATIVO", "HERBIVORO", "Marzo-Mayo"),
    ("Pudu puda", "Pudú", "VU", "NATIVO", "HERBIVORO", "Abril-Mayo"),
    ("Vultur gryphus", "Cóndor andino", "VU", "NATIVO", "CARRONERO", "Agosto-Octubre"),
    ("Lycalopex culpaeus", "Zorro culpeo", "LC", "NATIVO", "CARNIVORO", "Julio-Agosto"),
    ("Lycalopex griseus", "Zorro chilla", "LC", "NATIVO", "OMNIVORO", "Julio-Agosto"),
    ("Leopardus guigna", "Güiña", "VU", "NATIVO", "CARNIVORO", "Enero-Marzo"),
    ("Dromiciops gliroides", "Monito del monte", "NT", "ENDEMICO", "INSECTIVORO", "Septiembre-Diciembre"),
    ("Campephilus magellanicus", "Carpintero negro", "LC", "NATIVO", "INSECTIVORO", "Octubre-Diciembre"),
    ("Rhea pennata", "Ñandú", "NT", "NATIVO", "OMNIVORO", "Julio-Septiembre"),
    ("Phoenicopterus chilensis", "Flamenco chileno", "NT", "NATIVO", "OMNIVORO", "Diciembre-Febrero"),
    ("Cygnus melancoryphus", "Cisne de cuello negro", "LC", "NATIVO", "HERBIVORO", "Julio-Septiembre"),
    ("Spheniscus humboldti", "Pingüino de Humboldt", "VU", "NATIVO", "PISCIVORO", "Abril-Diciembre"),
    ("Lontra provocax", "Huillín", "EN", "NATIVO", "PISCIVORO", "Todo el año"),
    ("Chloephaga picta", "Caiquén", "LC", "NATIVO", "HERBIVORO", "Septiembre-Noviembre"),
    ("Sephanoides sephaniodes", "Picaflor chico", "LC", "NATIVO", "OMNIVORO", "Agosto-Diciembre"),
    ("Pteroptochos tarnii", "Hued-hued", "LC", "ENDEMICO", "INSECTIVORO", "Octubre-Diciembre"),
    ("Strix rufipes", "Concón", "LC", "NATIVO", "CARNIVORO", "Septiembre-Noviembre"),
    ("Rhinoderma darwinii", "Ranita de Darwin", "EN", "NATIVO", "INSECTIVORO", "Octubre-Marzo"),
    ("Liolaemus tenuis", "Lagartija esbelta", "LC", "ENDEMICO", "INSECTIVORO", "Septiembre-Noviembre"),
    ("Philodryas chamissonis", "Culebra de cola larga", "LC", "ENDEMICO", "CARNIVORO", "Septiembre-Noviembre"),
    ("Octodon degus", "Degú", "LC", "ENDEMICO", "HERBIVORO", "Septiembre-Octubre"),
    ("Abrocoma bennettii", "Ratón chinchilla", "LC", "ENDEMICO", "HERBIVORO", "Agosto-Octubre"),
    ("Lagidium viscacia", "Vizcacha", "LC", "NATIVO", "HERBIVORO", "Octubre-Diciembre"),
    ("Galictis cuja", "Quique", "LC", "NATIVO", "CARNIVORO", "Julio-Septiembre"),
    ("Theristicus melanopis", "Bandurria", "LC", "NATIVO", "INSECTIVORO", "Septiembre-Diciembre"),
    ("Enicognathus ferrugineus", "Cachaña", "LC", "NATIVO", "HERBIVORO", "Noviembre-Enero"),
    ("Castor canadensis", "Castor", "LC", "INTRODUCIDO", "HERBIVORO", "Enero-Febrero"),
    ("Neovison vison", "Visón", "LC", "INTRODUCIDO", "CARNIVORO", "Febrero-Marzo"),
    ("Oncorhynchus mykiss", "Trucha arcoíris", "LC", "INTRODUCIDO", "CARNIVORO", "Junio-Septiembre"),
]
MINERALES = [  # (científico/nombre, común, tipo_material, composición, dureza)
    ("Cuarzo", "Cuarzo", "SILICATO", "SiO2", 7.0),
    ("Calcita", "Calcita", "CARBONATO", "CaCO3", 3.0),
    ("Obsidiana", "Vidrio volcánico", "ROCA IGNEA", "SiO2 amorfo", 5.5),
    ("Basalto", "Basalto", "ROCA IGNEA", "Plagioclasa + piroxeno", 6.0),
    ("Andesita", "Andesita", "ROCA IGNEA", "Plagioclasa + anfíbol", 6.0),
    ("Pumicita", "Piedra pómez", "ROCA IGNEA", "Vidrio volcánico poroso", 6.0),
    ("Azufre nativo", "Azufre", "ELEMENTO NATIVO", "S", 2.0),
    ("Halita", "Sal gema", "HALURO", "NaCl", 2.5),
    ("Yeso", "Yeso", "SULFATO", "CaSO4·2H2O", 2.0),
    ("Atacamita", "Atacamita", "HALURO", "Cu2Cl(OH)3", 3.5),
    ("Crisocola", "Crisocola", "SILICATO", "(Cu,Al)2H2Si2O5(OH)4", 2.5),
    ("Lapislázuli", "Lapislázuli", "ROCA METAMORFICA", "Lazurita + calcita + pirita", 5.5),
    ("Magnetita", "Magnetita", "OXIDO", "Fe3O4", 6.0),
    ("Pirita", "Oro de los tontos", "SULFURO", "FeS2", 6.5),
    ("Feldespato ortoclasa", "Ortoclasa", "SILICATO", "KAlSi3O8", 6.0),
    ("Granito", "Granito", "ROCA IGNEA", "Cuarzo + feldespato + mica", 6.5),
    ("Pizarra", "Pizarra", "ROCA METAMORFICA", "Arcillas metamorfizadas", 3.0),
    ("Turba", "Turba", "SEDIMENTO", "Materia orgánica", 1.0),
    ("Arenisca", "Arenisca", "ROCA SEDIMENTARIA", "Granos de cuarzo cementados", 6.0),
    ("Caliza fosilífera", "Caliza con fósiles", "ROCA SEDIMENTARIA", "CaCO3 + fósiles", 3.0),
]
SIN_CLASIFICAR = [  # hongos, líquenes y algas: no son vegetal/animal/mineral (especialización parcial)
    ("Cyttaria darwinii", "Digüeñe", "LC", "NATIVO"),
    ("Cyttaria espinosae", "Lihuén", "LC", "ENDEMICO"),
    ("Fistulina antarctica", "Lengua de vaca", "LC", "NATIVO"),
    ("Usnea barbata", "Barba de viejo", "LC", "NATIVO"),
    ("Cladonia rangiferina", "Liquen de reno", "LC", "NATIVO"),
    ("Durvillaea antarctica", "Cochayuyo", "LC", "NATIVO"),
    ("Macrocystis pyrifera", "Huiro", "LC", "NATIVO"),
    ("Morchella esculenta", "Morilla", "LC", "NATIVO"),
    ("Grifola gargal", "Gargal", "NT", "NATIVO"),
    ("Ramaria flava", "Changle", "LC", "NATIVO"),
    ("Xanthoria parietina", "Liquen amarillo", "LC", "NATIVO"),
    ("Lessonia spicata", "Huiro negro", "LC", "NATIVO"),
]

FUNCIONES = ["GESTION", "VIGILANCIA", "CONSERVACION", "INVESTIGACION", "GUIA"]
CARGOS = {"GESTION": "Administrador de parque", "VIGILANCIA": "Guardaparque",
          "CONSERVACION": "Técnico en conservación", "INVESTIGACION": "Investigador",
          "GUIA": "Guía de turismo"}
NACIONALIDADES = ["Chilena"] * 16 + ["Argentina", "Peruana", "Alemana", "Francesa",
                                     "Estadounidense", "Brasileña", "Española", "Colombiana"]
COMENTARIOS_BUENOS = ["Excelente guía y paisajes", "Muy recomendable", "Bien organizada",
                      "Aprendí mucho de la flora nativa", "Vimos fauna nativa", None, None]
COMENTARIOS_MALOS = ["Grupo demasiado grande", "Poca información del recorrido",
                     "Retraso en el inicio", "Sendero en mal estado", None]


# ---------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------
def dv_rut(numero: int) -> str:
    """Dígito verificador módulo 11 (formato chileno; RUT FICTICIO)."""
    suma, factor = 0, 2
    for d in reversed(str(numero)):
        suma += int(d) * factor
        factor = 2 if factor == 7 else factor + 1
    r = 11 - (suma % 11)
    return "0" if r == 11 else "K" if r == 10 else str(r)


def hash_password(password: str, salt: str | None = None, iteraciones: int = 60000) -> str:
    """PBKDF2-SHA256 (biblioteca estándar). Formato: pbkdf2_sha256$iter$salt$hash"""
    salt = salt or secrets.token_hex(8)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iteraciones)
    return f"pbkdf2_sha256${iteraciones}${salt}${dk.hex()}"


def fecha_aleatoria(rnd: random.Random, desde: date, hasta: date) -> date:
    return desde + timedelta(days=rnd.randint(0, (hasta - desde).days))


def sql_lit(v) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, (date, time)):
        return f"'{v.isoformat()}'"
    s = str(v).replace("\\", "\\\\").replace("'", "''")
    return f"'{s}'"


# ---------------------------------------------------------------------
# Generación
# ---------------------------------------------------------------------
def generar(semilla: int = 2026) -> dict[str, list[dict]]:
    rnd = random.Random(semilla)
    fake = Faker("es_CL")
    Faker.seed(semilla)
    D: dict[str, list[dict]] = defaultdict(list)

    # REGION ----------------------------------------------------------
    id_region = {}
    for i, (nom, macro) in enumerate(REGIONES, start=1):
        D["REGION"].append({"id_region": i, "nombre": nom, "macrozona": macro})
        id_region[nom] = i

    # PARQUE y PARQUE_REGION -----------------------------------------
    correl_por_anio: dict[int, int] = defaultdict(int)
    parques = []
    for nom, anio, cat, regs, pop in PARQUES:
        correl_por_anio[anio] += 1
        clave = (anio, correl_por_anio[anio])
        estado = rnd.choices(["BUENO", "REGULAR", "CRITICO"], [0.55, 0.35, 0.10])[0]
        D["PARQUE"].append({
            "anio_declaracion": anio, "nro_correlativo": clave[1], "nombre": nom,
            "fecha_declaracion": fecha_aleatoria(rnd, date(anio, 1, 1), date(anio, 12, 28)),
            "superficie_total": round(rnd.uniform(800, 240000), 2),
            "presupuesto_anual": round(rnd.uniform(80, 1500) * 1_000_000, 2),
            "estado_conservacion": estado, "categoria_snap": cat,
            "organismo_responsable": rnd.choice(ORGANISMOS), "activo": True})
        parques.append({"clave": clave, "nombre": nom, "pop": pop})
        if len(regs) == 1:
            D["PARQUE_REGION"].append({"anio_declaracion": anio, "nro_correlativo": clave[1],
                                       "id_region": id_region[regs[0]],
                                       "porcentaje_territorial": 100.00, "es_principal": True})
        else:
            p1 = round(rnd.uniform(55, 80), 2)
            D["PARQUE_REGION"].append({"anio_declaracion": anio, "nro_correlativo": clave[1],
                                       "id_region": id_region[regs[0]],
                                       "porcentaje_territorial": p1, "es_principal": True})
            D["PARQUE_REGION"].append({"anio_declaracion": anio, "nro_correlativo": clave[1],
                                       "id_region": id_region[regs[1]],
                                       "porcentaje_territorial": round(100 - p1, 2),
                                       "es_principal": False})

    # AREA -------------------------------------------------------------
    areas = []  # dicts con clave, parque, acceso, estado, pop, asistencia
    for p in parques:
        n_areas = rnd.choices([2, 3, 4], [0.3, 0.45, 0.25])[0]
        nombres = rnd.sample(NOMBRES_AREA, n_areas)
        for k, nom_a in enumerate(nombres, start=1):
            acceso = "PUBLICO" if k == 1 else rnd.choices(
                ["PUBLICO", "RESTRINGIDO", "PROTEGIDO"], [0.55, 0.28, 0.17])[0]
            estado = "OPERATIVA" if k == 1 else rnd.choices(
                ["OPERATIVA", "MANTENCION", "CERRADA"], [0.75, 0.15, 0.10])[0]
            clave = (*p["clave"], k)
            D["AREA"].append({"anio_declaracion": clave[0], "nro_correlativo": clave[1],
                              "nro_area": k, "nombre": nom_a,
                              "extension": round(rnd.uniform(50, 25000), 2),
                              "nivel_acceso": acceso, "estado_operativo": estado})
            areas.append({"clave": clave, "parque": p, "acceso": acceso, "estado": estado,
                          "pop": p["pop"] * rnd.uniform(0.4, 1.6),
                          "asistencia": rnd.uniform(0.62, 0.96)})

    # RECURSO_NATURAL + subtipos ---------------------------------------
    recursos = []  # (id, tipo)
    rid = 0

    def nuevo_recurso(cient, comun, estado, origen, desc):
        nonlocal rid
        rid += 1
        D["RECURSO_NATURAL"].append({
            "id_recurso": rid, "nombre_cientifico": cient, "nombre_comun": comun,
            "estado_conservacion": estado,
            "fecha_incorporacion": fecha_aleatoria(rnd, date(2010, 1, 1), date(2023, 12, 31)),
            "origen": origen, "descripcion": desc, "activo": True})
        return rid

    for c, n, e, o, flor, tipo in VEGETALES:
        i = nuevo_recurso(c, n, e, o, f"Especie vegetal ({tipo.lower()}) registrada en inventarios.")
        D["VEGETAL"].append({"id_recurso": i, "periodo_floracion": flor, "tipo_vegetacion": tipo})
        recursos.append((i, "VEGETAL"))
    for c, n, e, o, alim, celo in ANIMALES:
        i = nuevo_recurso(c, n, e, o, f"Especie animal de dieta {alim.lower()}.")
        D["ANIMAL"].append({"id_recurso": i, "tipo_alimentacion": alim, "periodo_celo": celo})
        recursos.append((i, "ANIMAL"))
    for c, n, tmat, comp, dur in MINERALES:
        i = nuevo_recurso(c, n, "NO_APLICA", "GEOLOGICO", f"Ocurrencia mineral: {tmat.lower()}.")
        D["MINERAL"].append({"id_recurso": i, "tipo_material": tmat, "composicion": comp,
                             "dureza_mohs": dur})
        recursos.append((i, "MINERAL"))
    for c, n, e, o in SIN_CLASIFICAR:
        i = nuevo_recurso(c, n, e, o, "Organismo sin clasificar en subtipo (hongo, liquen o alga).")
        recursos.append((i, "SIN_CLASIFICAR"))

    # INVENTARIO_RECURSO ----------------------------------------------
    rangos_cant = {"VEGETAL": (40, 6000), "ANIMAL": (2, 350), "MINERAL": (1, 90),
                   "SIN_CLASIFICAR": (10, 700)}
    inventario_area = defaultdict(set)
    for a in areas:
        n = rnd.randint(6, 11)
        for r_id, tipo in rnd.sample(recursos, n):
            lo, hi = rangos_cant[tipo]
            # distribución sesgada: pocas áreas con cantidades muy altas
            cant = int(lo + (hi - lo) * (rnd.random() ** 2.2))
            mon = None if rnd.random() < 0.05 else fecha_aleatoria(rnd, date(2024, 1, 1), date(2026, 10, 31))
            obs = rnd.choice([None, None, None, "Conteo por transecto", "Estimación por parcela",
                              "Requiere nuevo monitoreo", "Registro con cámara trampa"])
            D["INVENTARIO_RECURSO"].append({
                "anio_declaracion": a["clave"][0], "nro_correlativo": a["clave"][1],
                "nro_area": a["clave"][2], "id_recurso": r_id, "cantidad_inventariada": cant,
                "fecha_ultimo_monitoreo": mon, "observaciones": obs})
            inventario_area[a["clave"]].add(r_id)

    # PERSONAS ---------------------------------------------------------
    ruts_usados, correos_usados = set(), set()

    def nueva_persona(rango):
        while True:
            num = rnd.randint(*rango)
            rut = f"{num}-{dv_rut(num)}"
            if rut not in ruts_usados:
                ruts_usados.add(rut)
                break
        gen = fake.first_name_female if rnd.random() < 0.5 else fake.first_name_male
        nombres = gen() + (f" {gen()}" if rnd.random() < 0.45 else "")
        if len(set(nombres.split())) < len(nombres.split()):
            nombres = nombres.split()[0]
        ap_p, ap_m = fake.last_name(), (fake.last_name() if rnd.random() < 0.93 else None)
        correo = None
        if rnd.random() < 0.9:
            base = f"{nombres.split()[0]}.{ap_p}".lower()
            for a_, b_ in zip("áéíóúñü ", "aeiounu_"):
                base = base.replace(a_, b_)
            correo, k = f"{base}@correo.example", 1
            while correo in correos_usados:
                k += 1
                correo = f"{base}{k}@correo.example"
            correos_usados.add(correo)
        D["PERSONA"].append({"rut_persona": rut, "nombres": nombres, "apellido_paterno": ap_p,
                             "apellido_materno": ap_m, "correo": correo,
                             "nacionalidad": rnd.choice(NACIONALIDADES)})
        for _ in range(rnd.choices([0, 1, 2], [0.08, 0.72, 0.20])[0]):
            tel = f"+569{rnd.randint(10000000, 99999999)}"
            if not any(t["rut_persona"] == rut and t["telefono"] == tel for t in D["PERSONA_TELEFONO"]):
                D["PERSONA_TELEFONO"].append({"rut_persona": rut, "telefono": tel})
        return rut, nombres, ap_p

    # TRABAJADOR, TRABAJADOR_FUNCION, ASIGNACION ----------------------
    N_TRAB = 60
    trabajadores = []
    for t in range(N_TRAB):
        rut, nom, ap = nueva_persona((8_000_000, 19_999_999))
        if t < 6:
            principal = "GESTION"
        elif t < 26:
            principal = "INVESTIGACION" if t < 22 else "CONSERVACION"
        else:
            principal = rnd.choice(["VIGILANCIA", "GUIA", "CONSERVACION", "VIGILANCIA", "GUIA"])
        funcs = [principal]
        n_extra = rnd.choices([0, 1, 2], [0.55, 0.35, 0.10])[0]
        funcs += rnd.sample([f for f in FUNCIONES if f != principal], n_extra)
        trabajadores.append({"rut": rut, "nombres": nom, "ap": ap, "funcs": funcs,
                             "parque_base": rnd.choice(parques)})
    jefes = trabajadores[:6]
    for i, t in enumerate(trabajadores):
        D["TRABAJADOR"].append({
            "rut_persona": t["rut"],
            "fecha_ingreso": fecha_aleatoria(rnd, date(2005, 1, 1), date(2025, 12, 31)),
            "cargo": CARGOS[t["funcs"][0]],
            "rut_supervisor": None if i < 6 else rnd.choice(jefes)["rut"]})
        for f in t["funcs"]:
            D["TRABAJADOR_FUNCION"].append({"rut_persona": t["rut"], "funcion": f})
            areas_parque = [a for a in areas if a["parque"] is t["parque_base"]]
            elegidas = rnd.sample(areas_parque, min(len(areas_parque), rnd.randint(1, 2)))
            if rnd.random() < 0.25:  # algunos ejercen también en otro parque
                elegidas.append(rnd.choice(areas))
            for a in {e["clave"]: e for e in elegidas}.values():
                D["ASIGNACION_TRABAJADOR"].append({
                    "rut_persona": t["rut"], "funcion": f, "anio_declaracion": a["clave"][0],
                    "nro_correlativo": a["clave"][1], "nro_area": a["clave"][2],
                    "fecha_inicio": fecha_aleatoria(rnd, date(2018, 1, 1), date(2026, 6, 30))})

    # CUENTA y CUENTA_ROL (usuarios/roles 40-80) ------------------------
    N_CUENTAS = 50
    usuarios_usados = set()
    demo = {0: "admin", 30: "operador", 6: "analista"}  # índices de trabajadores demo
    orden = [0, 6, 30] + [i for i in range(N_TRAB) if i not in (0, 6, 30)]
    for cid, idx in enumerate(orden[:N_CUENTAS], start=1):
        t = trabajadores[idx]
        if idx in demo:
            usuario = demo[idx]
        else:
            base = (t["nombres"][0] + t["ap"]).lower()
            for a_, b_ in zip("áéíóúñü ", "aeiounu_"):
                base = base.replace(a_, b_)
            usuario, k = base, 1
            while usuario in usuarios_usados:
                k += 1
                usuario = f"{base}{k}"
        usuarios_usados.add(usuario)
        activa = not (idx not in demo and rnd.random() < 0.06)
        D["CUENTA"].append({"id_cuenta": cid, "rut_persona": t["rut"], "usuario": usuario,
                            "password_hash": hash_password(PASSWORD_DEMO, salt=f"s{semilla}{cid:04d}"),
                            "activa": activa,
                            "fecha_creacion": fecha_aleatoria(rnd, date(2024, 1, 1), date(2026, 9, 30))})
        if idx == 0:
            roles = ["ADMINISTRADOR"]
        elif idx == 6:
            roles = ["ANALISTA"]
        elif idx == 30:
            roles = ["OPERADOR"]
        else:
            f0 = t["funcs"][0]
            roles = ["ADMINISTRADOR"] if f0 == "GESTION" else \
                    ["ANALISTA"] if f0 in ("INVESTIGACION", "CONSERVACION") else ["OPERADOR"]
            if rnd.random() < 0.2:  # cuentas con dos roles
                roles.append(rnd.choice([r for r in ("OPERADOR", "ANALISTA") if r not in roles]))
        for r in roles:
            D["CUENTA_ROL"].append({"id_cuenta": cid, "rol": r})

    # PROYECTO_CIENTIFICO, PARTICIPA, ESTUDIA, INVESTIGA ----------------
    temas = ["Monitoreo de", "Dinámica poblacional de", "Conservación de", "Restauración del hábitat de",
             "Genética de", "Impacto del turismo sobre", "Fenología de"]
    temas_geo = ["Caracterización geológica de", "Erosión y conservación de", "Cartografía de afloramientos de"]
    investigadores = [t for t in trabajadores if "INVESTIGACION" in t["funcs"]]
    conservadores = [t for t in trabajadores if "CONSERVACION" in t["funcs"]]
    nombres_proy = set()
    for pid in range(1, 31):
        area0 = rnd.choice(areas)
        candidatos = list(inventario_area[area0["clave"]])
        r_obj = rnd.choice(candidatos)
        comun = next(r["nombre_comun"] for r in D["RECURSO_NATURAL"] if r["id_recurso"] == r_obj)
        tipo_obj = dict(recursos)[r_obj]
        tema = rnd.choice(temas_geo if tipo_obj == "MINERAL" else temas)
        nombre = f"{tema} {comun.lower()} en {area0['parque']['nombre']}"
        while nombre in nombres_proy:
            nombre += " (fase II)"
        nombres_proy.add(nombre)
        ini = fecha_aleatoria(rnd, date(2019, 1, 1), date(2026, 8, 31))
        if ini > date(2026, 6, 1):
            estado, fin = "PLANIFICADO", None
        else:
            estado = rnd.choices(["EN_CURSO", "FINALIZADO", "SUSPENDIDO"], [0.5, 0.4, 0.1])[0]
            fin = None if estado == "EN_CURSO" else min(ini + timedelta(days=rnd.randint(180, 1100)), HOY)
        D["PROYECTO_CIENTIFICO"].append({
            "id_proyecto": pid, "nombre": nombre[:120],
            "objetivo": f"Evaluar el estado y las amenazas de {comun.lower()} para orientar acciones de manejo.",
            "fecha_inicio": ini, "fecha_fin": fin, "estado": estado})
        equipo = rnd.sample(investigadores, min(len(investigadores), rnd.choices([1, 2, 3, 4, 5, 6], [0.15, 0.25, 0.25, 0.15, 0.12, 0.08])[0]))
        if rnd.random() < 0.4:
            equipo.append(rnd.choice(conservadores))
        for t in {e["rut"]: e for e in equipo}.values():
            D["PARTICIPA_PROYECTO"].append({"rut_persona": t["rut"], "id_proyecto": pid})
        areas_est = [area0] + rnd.sample([a for a in areas if a["parque"] is area0["parque"] and a is not area0],
                                         k=min(rnd.randint(0, 2), len([a for a in areas if a["parque"] is area0["parque"]]) - 1))
        for a in areas_est:
            D["ESTUDIA"].append({"id_proyecto": pid, "anio_declaracion": a["clave"][0],
                                 "nro_correlativo": a["clave"][1], "nro_area": a["clave"][2]})
        pool = set()
        for a in areas_est:
            pool |= inventario_area[a["clave"]]
        especies = {r_obj} | set(rnd.sample(sorted(pool), min(len(pool), rnd.randint(0, 6))))
        for r in sorted(especies):
            D["INVESTIGA"].append({"id_proyecto": pid, "id_recurso": r})

    # VISITANTE (incluye trabajadores que también visitan: especialización solapada)
    visitantes = []
    for t in rnd.sample(trabajadores, 12):
        visitantes.append({"rut": t["rut"], "registro": fecha_aleatoria(rnd, date(2023, 1, 1), date(2025, 6, 30))})
    while len(visitantes) < 240:
        rut, _, _ = nueva_persona((5_000_000, 27_999_999))
        visitantes.append({"rut": rut, "registro": fecha_aleatoria(rnd, date(2023, 1, 1), date(2025, 12, 31))})
    for v in visitantes:
        v["peso"] = rnd.paretovariate(2.6)  # recurrencia: algunos visitantes muy frecuentes
        D["VISITANTE"].append({"rut_persona": v["rut"], "fecha_registro": v["registro"]})

    # EXCURSION --------------------------------------------------------
    areas_exc = [a for a in areas if a["acceso"] != "PROTEGIDO"]
    cap_rango = {"GUIADA": (8, 20), "AUTOGUIADA": (12, 30), "EDUCATIVA": (10, 25), "NOCTURNA": (6, 12)}
    fechas = []
    for _ in range(200):
        f = fecha_aleatoria(rnd, INICIO_EXC, FIN_EXC)
        if f.month in (6, 7, 8) and rnd.random() < 0.45:      # menos excursiones en invierno
            f = fecha_aleatoria(rnd, INICIO_EXC, FIN_EXC)
        fechas.append(f)
    # asegurar ~20 excursiones futuras para el formulario del PMV
    futuras = [f for f in fechas if f > HOY]
    while len(futuras) < 18:
        fechas[rnd.randrange(len(fechas))] = fecha_aleatoria(rnd, HOY + timedelta(days=3), FIN_EXC)
        futuras = [f for f in fechas if f > HOY]
    fechas.sort()
    excursiones = []
    for n, f in enumerate(fechas, start=1):
        a = rnd.choices(areas_exc, [x["pop"] for x in areas_exc])[0]
        if f > HOY and a["estado"] != "OPERATIVA":
            a = rnd.choice([x for x in areas_exc if x["estado"] == "OPERATIVA"])
        mod = rnd.choices(["GUIADA", "AUTOGUIADA", "EDUCATIVA", "NOCTURNA"], [0.42, 0.25, 0.2, 0.13])[0]
        cap = rnd.randint(*cap_rango[mod])
        hora = time(rnd.choice([20, 21]), 0) if mod == "NOCTURNA" else time(rnd.choice([8, 9, 10, 11, 14, 15, 16]), rnd.choice([0, 30]))
        cod = f"EXC{n:04d}"
        D["EXCURSION"].append({"codigo_excursion": cod, "fecha": f, "horario": hora, "modalidad": mod,
                               "capacidad": cap, "anio_declaracion": a["clave"][0],
                               "nro_correlativo": a["clave"][1], "nro_area": a["clave"][2]})
        excursiones.append({"cod": cod, "fecha": f, "area": a, "mod": mod, "cap": cap,
                            "calidad": rnd.uniform(2.6, 4.7)})

    # INSCRIPCION y EVALUACION ---------------------------------------
    nins = 0
    for ex in excursiones:
        temporada = 1.25 if ex["fecha"].month in (12, 1, 2) else 0.8 if ex["fecha"].month in (6, 7, 8) else 1.0
        llenado = min(1.0, 0.76 * rnd.betavariate(2.0, 2.6) * temporada * min(1.4, 0.55 + ex["area"]["pop"] / 3))
        if rnd.random() < 0.06:
            llenado = 1.0                            # algunas excursiones completas
        n = max(1, round(ex["cap"] * llenado))
        candidatos = [v for v in visitantes if v["registro"] <= ex["fecha"]]
        elegidos: list[dict] = []
        pesos = [v["peso"] for v in candidatos]
        while len(elegidos) < n and len(elegidos) < len(candidatos):
            v = rnd.choices(candidatos, pesos)[0]
            if v not in elegidos:
                elegidos.append(v)
        pasada = ex["fecha"] <= HOY
        p_asis = ex["area"]["asistencia"] * (0.85 if ex["mod"] == "NOCTURNA" else 1.0)
        asistentes = []
        filas = []
        for v in elegidos:
            nins += 1
            fi = max(v["registro"], ex["fecha"] - timedelta(days=rnd.randint(0, 45)))
            fi = min(fi, HOY)
            if pasada:
                estado = "ASISTIO" if rnd.random() < p_asis else "NO_ASISTIO"
            else:
                estado = "INSCRITO"
            obs = rnd.choice([None] * 8 + ["Requiere accesibilidad", "Viaja con menores", "Grupo familiar"])
            fila = {"id_inscripcion": f"INS{nins:06d}", "rut_persona": v["rut"],
                    "codigo_excursion": ex["cod"], "fecha_inscripcion": fi,
                    "estado_asistencia": estado, "observaciones": obs}
            filas.append(fila)
            if estado == "ASISTIO":
                asistentes.append(fila)
        D["INSCRIPCION"].extend(filas)
        # evaluación promedio: calidad propia de la excursión, castigo por grupos grandes
        nro = 0
        for fila in asistentes:
            if rnd.random() < 0.62:
                nro += 1
                media = ex["calidad"] - 0.045 * (len(asistentes) - 10)
                nota = int(min(5, max(1, round(rnd.gauss(media, 0.75)))))
                com = rnd.choice(COMENTARIOS_BUENOS if nota >= 4 else COMENTARIOS_MALOS)
                D["EVALUACION"].append({
                    "codigo_excursion": ex["cod"], "nro_evaluacion": nro,
                    "id_inscripcion": fila["id_inscripcion"],
                    "fecha_evaluacion": min(HOY, ex["fecha"] + timedelta(days=rnd.randint(0, 7))),
                    "calificacion": nota, "comentario": com})
    return D


ORDEN_TABLAS = ["REGION", "PARQUE", "PARQUE_REGION", "AREA", "PERSONA", "PERSONA_TELEFONO",
                "TRABAJADOR", "TRABAJADOR_FUNCION", "ASIGNACION_TRABAJADOR", "VISITANTE",
                "CUENTA", "CUENTA_ROL", "RECURSO_NATURAL", "VEGETAL", "ANIMAL", "MINERAL",
                "INVENTARIO_RECURSO", "PROYECTO_CIENTIFICO", "PARTICIPA_PROYECTO", "ESTUDIA",
                "INVESTIGA", "EXCURSION", "INSCRIPCION", "EVALUACION"]


def validar(D: dict[str, list[dict]]) -> list[str]:
    """Validaciones previas a la carga (FK, duplicados, cupos, reglas)."""
    errores = []
    pk = lambda t, cols: [tuple(r[c] for c in cols) for r in D[t]]
    for t, cols in [("PERSONA", ["rut_persona"]), ("INSCRIPCION", ["id_inscripcion"]),
                    ("INSCRIPCION", ["rut_persona", "codigo_excursion"]),
                    ("EVALUACION", ["codigo_excursion", "nro_evaluacion"]),
                    ("EVALUACION", ["id_inscripcion"]), ("RECURSO_NATURAL", ["nombre_cientifico"]),
                    ("INVENTARIO_RECURSO", ["anio_declaracion", "nro_correlativo", "nro_area", "id_recurso"])]:
        claves = pk(t, cols)
        if len(claves) != len(set(claves)):
            errores.append(f"Duplicados en {t}{cols}")
    areas = set(pk("AREA", ["anio_declaracion", "nro_correlativo", "nro_area"]))
    for t in ("EXCURSION", "INVENTARIO_RECURSO", "ESTUDIA", "ASIGNACION_TRABAJADOR"):
        if not set(pk(t, ["anio_declaracion", "nro_correlativo", "nro_area"])) <= areas:
            errores.append(f"FK de {t} a AREA inválida")
    vis = {r["rut_persona"] for r in D["VISITANTE"]}
    if not {r["rut_persona"] for r in D["INSCRIPCION"]} <= vis:
        errores.append("INSCRIPCION referencia visitantes inexistentes")
    cap = {e["codigo_excursion"]: e["capacidad"] for e in D["EXCURSION"]}
    cnt = defaultdict(int)
    for i in D["INSCRIPCION"]:
        cnt[i["codigo_excursion"]] += 1
    if any(cnt[c] > cap[c] for c in cnt):
        errores.append("Excursiones sobre su capacidad")
    estado = {i["id_inscripcion"]: i["estado_asistencia"] for i in D["INSCRIPCION"]}
    if any(estado[e["id_inscripcion"]] != "ASISTIO" for e in D["EVALUACION"]):
        errores.append("Evaluación de inscripción sin asistencia")
    principales = defaultdict(int)
    for r in D["PARQUE_REGION"]:
        principales[(r["anio_declaracion"], r["nro_correlativo"])] += r["es_principal"]
    if any(v != 1 for v in principales.values()):
        errores.append("Parque sin exactamente una región principal")
    sub = [r["id_recurso"] for t in ("VEGETAL", "ANIMAL", "MINERAL") for r in D[t]]
    if len(sub) != len(set(sub)):
        errores.append("Especialización no disjunta")
    return errores


def escribir_sql(D: dict[str, list[dict]], ruta: Path, semilla: int) -> None:
    lineas = ["-- =====================================================================",
              "-- 02_datos.sql · Inserción masiva de datos sintéticos (Faker, semilla "
              f"{semilla})",
              "-- Generado por scripts/generar_datos.py. NO editar a mano: regenerar.",
              "-- Todos los RUT, correos y teléfonos son ficticios.",
              "-- =====================================================================",
              "USE parques_db;", "SET NAMES utf8mb4;", "START TRANSACTION;", ""]
    for t in ORDEN_TABLAS:
        filas = D[t]
        if not filas:
            continue
        cols = list(filas[0].keys())
        lineas.append(f"-- {t}: {len(filas)} filas")
        for i in range(0, len(filas), 200):
            bloque = filas[i:i + 200]
            valores = ",\n".join("(" + ", ".join(sql_lit(r[c]) for c in cols) + ")" for r in bloque)
            lineas.append(f"INSERT INTO {t} ({', '.join(cols)}) VALUES\n{valores};")
        lineas.append("")
    lineas.append("COMMIT;")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8")


def cargar_mysql(D: dict[str, list[dict]]) -> None:
    """Inserta los datos con SQLAlchemy + PyMySQL en una única transacción."""
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import URL
    url = URL.create("mysql+pymysql", username=os.getenv("DB_USER", "root"),
                     password=os.getenv("DB_PASSWORD", ""), host=os.getenv("DB_HOST", "localhost"),
                     port=int(os.getenv("DB_PORT", "3306")), database=os.getenv("DB_NAME", "parques_db"),
                     query={"charset": "utf8mb4"})
    engine = create_engine(url)
    with engine.begin() as con:                       # COMMIT al final o ROLLBACK ante error
        for t in reversed(ORDEN_TABLAS):
            con.execute(text(f"DELETE FROM {t}"))
        for t in ORDEN_TABLAS:
            if D[t]:
                cols = list(D[t][0].keys())
                sql = text(f"INSERT INTO {t} ({', '.join(cols)}) VALUES ({', '.join(':' + c for c in cols)})")
                con.execute(sql, D[t])
    print("Carga en MySQL completada.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--semilla", type=int, default=2026)
    ap.add_argument("--salida", type=Path, default=SALIDA_SQL)
    ap.add_argument("--cargar", action="store_true", help="insertar directamente en MySQL")
    args = ap.parse_args()

    D = generar(args.semilla)
    errores = validar(D)
    print(f"{'Tabla':<24}{'Filas':>7}")
    for t in ORDEN_TABLAS:
        print(f"{t:<24}{len(D[t]):>7}")
    if errores:
        raise SystemExit("Validación fallida:\n - " + "\n - ".join(errores))
    print("Validaciones previas: OK")
    escribir_sql(D, args.salida, args.semilla)
    print(f"SQL escrito en {args.salida}")
    if args.cargar:
        cargar_mysql(D)


if __name__ == "__main__":
    main()
