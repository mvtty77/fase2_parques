# 🌳 Sistema Integral de Gestión de Parques Naturales y Conservación Ambiental

**UNAB · TDFI103 Bases de Datos · Proyecto Semestral 2026 · Fase 2 · Caso 1 · Grupo 1 · NRC 12142**

Base de datos **MySQL 8** (24 tablas, 6 vistas, 6 procedimientos, 8 triggers, datos sintéticos) y PMV en **Python 3.12 + Streamlit** con inscripción de visitantes, CRUD de parques y especies, inicio de sesión con roles y dashboard.

Se trabaja en dos etapas, **sin Docker**:

| Etapa | Dónde | Para qué |
|---|---|---|
| 1 | **GitHub Codespaces** (en el navegador, sin instalar nada) | Desarrollar, ejecutar el SQL, usar la aplicación y correr las pruebas |
| 2 | **MySQL Workbench** en el PC | Modelo relacional (EER) y capturas oficiales R1–R12 — ver [`docs/workbench/instrucciones_workbench.md`](docs/workbench/instrucciones_workbench.md) |

```text
Usuario (navegador)
   │
   ▼
Streamlit · app/main.py ............ interfaz (puerto 8501)
   │
   ▼
app/negocio.py + app/seguridad.py .. reglas, permisos por rol, transacciones
   │
   ▼
app/db.py (SQLAlchemy + PyMySQL) ... credenciales desde .env
   │
   ▼
MySQL 8 · parques_db ............... FK, UNIQUE, CHECK, triggers, vistas, procedimientos
   ▲
   │  mismo script sql/00_integral.sql
MySQL Workbench (PC) ............... diagrama EER y capturas
```

---

## Etapa 1 · Abrir el proyecto en GitHub Codespaces

### Primera vez

1. En la página del repositorio en GitHub: botón verde **Code** → pestaña **Codespaces** → **Create codespace on main**.
2. Espere a que termine (la primera vez, **3-5 minutos**): GitHub instala MySQL 8, Python y las librerías, crea la base `parques_db` y abre la aplicación. En la terminal verá:

   ```text
   Listo. MySQL 8 con parques_db y el PMV en la pestaña PUERTOS (8501)
   ```

3. Pestaña **PUERTOS** (*PORTS*) → puerto **8501** → ícono del globo 🌐 → se abre la aplicación.

| Usuario | Contraseña | Rol | Puede |
|---|---|---|---|
| `admin` | `Parques2026!` | ADMINISTRADOR | todo |
| `operador` | `Parques2026!` | OPERADOR | inscripciones, asistencia y dashboard |
| `analista` | `Parques2026!` | ANALISTA | CRUD de especies y dashboard |

Son cuentas de datos sintéticos, no credenciales reales.

### Las veces siguientes

Abra el Codespace desde **Code → Codespaces** (aparece en la lista). Al iniciarse enciende MySQL y la aplicación solos. Un Codespace sin uso se detiene a los 30 minutos y no pierde nada.

### Ejecutar SQL dentro del Codespace

**Opción A · SQLTools** (ya viene instalado):
1. Barra izquierda → ícono del cilindro (**SQLTools**) → conexión **parques_db (Codespace)** → conectar. Contraseña: la de `DB_PASSWORD` en `.env` (por defecto `AppDemo2026`).
2. Abra `sql/06_requerimientos_R1_R12.sql`, ponga el cursor en una sentencia y pulse **Ctrl+E Ctrl+E** (o *Run on active connection*). El resultado aparece en una pestaña.

**Opción B · Terminal:**

```bash
bash scripts/consola_mysql.sh                               # consola MySQL dentro de parques_db (salir: exit)
bash scripts/consola_mysql.sh -t < sql/06_requerimientos_R1_R12.sql   # ejecuta R1-R12 de una vez
```

### Tareas rápidas

Menú **Terminal → Run Task…** (o en la terminal):

| Tarea | Comando |
|---|---|
| Abrir / reiniciar la aplicación | `bash scripts/iniciar_app.sh` |
| Consola MySQL | `bash scripts/consola_mysql.sh` |
| Pruebas SQL + pytest (deja evidencias en `docs/evidencias/`) | `bash scripts/probar_todo.sh` |
| **Reconstruir la base desde cero** (borra cambios hechos en la app) | `bash scripts/reconstruir_base.sh` |
| Encender MySQL | `bash scripts/encender_mysql.sh` |
| Regenerar datos (semilla 2026) y el script integral | `python scripts/generar_datos.py && python scripts/construir_integral.py` |

---

## Etapa 2 · MySQL Workbench en el PC

Resumen (detalle en [`docs/workbench/instrucciones_workbench.md`](docs/workbench/instrucciones_workbench.md)):

1. Instalar **MySQL Server 8** y **MySQL Workbench** (MySQL Installer).
2. En GitHub: **Code → Download ZIP** y descomprimir.
3. Workbench → conexión local → abrir `sql/00_integral.sql` → rayo ⚡.
4. `Database > Reverse Engineer` → diagrama EER → exportar PNG.
5. Abrir `sql/06_requerimientos_R1_R12.sql` → Ctrl+Enter en cada sentencia → captura.

---

## Estructura

```text
.devcontainer/          Codespace: devcontainer.json, instalar.sh (1.ª vez), iniciar.sh (cada inicio)
.vscode/tasks.json      Tareas rápidas del menú Terminal
app/                    PMV Streamlit: main.py, negocio.py, seguridad.py, db.py
sql/00_integral.sql     Script integral: BD + tablas + restricciones + datos + 6 vistas + 6 procedimientos
sql/01_estructura.sql   Tablas, PK, FK, UNIQUE, CHECK, triggers
sql/02_datos.sql        Inserción de datos (generada)
sql/03_vistas.sql       R2, R3, R5, R6, R7, R8
sql/04_procedimientos.sql  R1, R4, R9, R10, R11, R12
sql/05_pruebas.sql      Conteos, 11 pruebas negativas y R1-R12
sql/06_requerimientos_R1_R12.sql  Una sentencia por requerimiento (capturas Workbench)
sql/07_usuario_app_local.sql      Usuario de la app para el PC (Workbench)
scripts/                generar_datos.py (Faker), construir_integral.py y scripts .sh del Codespace
tests/                  13 pruebas pytest
docs/                   informe_final.md, mere/, workbench/, evidencias/, fase1/, defensa.md, uso_ia_validacion.md
equipo/                 matriz_responsabilidades.md, bitacoras/
```

## Entregables de Canvas

| Entregable | Archivo |
|---|---|
| Informe final | `docs/informe_final.md` (completar los PENDIENTE y exportar a Word/PDF) |
| Script integral SQL | `sql/00_integral.sql` |
| Script de generación de datos | `scripts/generar_datos.py` (+ `sql/02_datos.sql`) |
| Código fuente PMV | `app/`, `requirements.txt`, `.streamlit/` |
| Docker | `[PENDIENTE: el PDF lo pide; este repositorio no usa Docker. Consultar al docente]` |
| Documento disertación | `[PENDIENTE]` diapositivas según `docs/defensa.md` |

## Problemas frecuentes

| Síntoma | Solución |
|---|---|
| El puerto 8501 no abre o la app muestra error de conexión | `bash scripts/encender_mysql.sh` y luego `bash scripts/iniciar_app.sh` |
| Cambié `DB_PASSWORD` en `.env` y ahora no conecta | `bash scripts/crear_usuario_app.sh` (actualiza la contraseña en MySQL) |
| Quiero volver a los datos originales | `bash scripts/reconstruir_base.sh` |
| El formulario dice que no hay excursiones abiertas | Las excursiones futuras llegan hasta el 20-12-2026; después, cambiar `HOY` y `FIN_EXC` en `scripts/generar_datos.py`, regenerar y reconstruir |
| Ver el registro de la app | `cat /tmp/streamlit.log` |

## Uso de IA

Se uso un asistente de IA (Claude, de Anthropic) para generar el **borrador inicial** del codigo y la documentacion. El equipo revisa, ejecuta, valida y completa ese borrador. Detalle en [docs/uso_ia_validacion.md](docs/uso_ia_validacion.md).
