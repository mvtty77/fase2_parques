# Etapa 2 · MySQL Workbench en el PC (modelo relacional y capturas)

El Codespace sirve para trabajar desde GitHub. Las capturas **oficiales** del PDF (modelo relacional, sección 5, y R1–R12, sección 7) se toman en **MySQL Workbench** en un PC. Todo lo necesario ya está en este repositorio.

## 1. Instalar (una vez)

1. Descargar **MySQL Installer** desde <https://dev.mysql.com/downloads/installer/> (Windows).
2. Elegir *Custom* e instalar **MySQL Server 8.x** y **MySQL Workbench 8.x**.
3. Al configurar el servidor: puerto **3306**, autenticación recomendada, y crear la contraseña de **root**. Anotarla.

## 2. Bajar el repositorio al PC

En GitHub: botón verde **Code → Download ZIP** y descomprimir (por ejemplo en el Escritorio).

## 3. Crear la base en Workbench

1. Abrir Workbench y entrar a la conexión **Local instance MySQL80** (127.0.0.1, puerto 3306, usuario root).
2. `File > Open SQL Script…` → `sql/00_integral.sql` → botón del rayo ⚡ (ejecutar todo).
3. En el panel *Schemas* pulsar el botón de refrescar: debe aparecer **parques_db** con 24 tablas, 6 vistas y 6 procedimientos (*Stored Procedures*).
4. (Solo si va a correr la app en el PC) abrir y ejecutar `sql/07_usuario_app_local.sql`: crea el usuario `parques_app` con la contraseña de `.env.example`.

## 4. Modelo relacional (diagrama EER)

1. `Database > Reverse Engineer…` → conexión local → `Next`.
2. Marcar el esquema **parques_db** → `Next` hasta *Select Objects*: dejar marcadas las tablas (24). Las vistas y rutinas se pueden desmarcar para que el diagrama sea legible.
3. `Execute` → `Finish`. Ordenar con `Arrange > Auto-Layout` y ajustar a mano por zonas (personas/cuentas · territorio · excursiones · recursos · proyectos).
4. Guardar: `File > Save Model As…` → `docs/workbench/modelo_parques.mwb`.
5. Exportar: `File > Export > Export as PNG…` → `docs/workbench/modelo_relacional_final.png`.

## 5. Capturas R1–R12

1. Doble clic en **parques_db** (queda en negrita).
2. Abrir `sql/06_requerimientos_R1_R12.sql`: tiene una sentencia por requerimiento, en orden.
3. Cursor sobre la sentencia → **Ctrl+Enter** (ejecuta solo esa) → captura con **Windows+Shift+S** donde se vean la sentencia y la grilla *Result Grid*.
4. Guardar como `docs/evidencias/wb_R01.png` … `wb_R12.png`.
5. Comparar con `docs/evidencias/salidas_referencia_R1_R12.md`: deben coincidir.

Capturas adicionales de la sección 6 del informe, desde `sql/05_pruebas.sql`:

| Captura | Qué ejecutar | Archivo |
|---|---|---|
| Conteo por tabla | Bloque A, primer `SELECT` | `wb_conteos.png` |
| Restricciones activas | Bloque B, pruebas B1 y B3 (deben dar error; se ve en *Output*) | `wb_prueba_B1.png`, `wb_prueba_B3.png` |

## 6. Correr la aplicación en el PC (opcional)

Requiere Python 3.12 (marcar *Add python.exe to PATH* al instalar). En la carpeta del repositorio, con PowerShell:

```powershell
copy .env.example .env
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app/main.py
```

La app lee `.env` sola. Si en el paso 3.4 no creó `parques_app`, edite `.env` y ponga `DB_USER=root` y su contraseña de root.

## Errores típicos

| Mensaje | Causa y solución |
|---|---|
| `No database selected` | Falta el doble clic en parques_db o `USE parques_db;` |
| `Access denied` | Contraseña o puerto equivocados (en el PC es 3306) |
| `Error Code: 1644 Período inválido` | Fecha inicio posterior a fecha término: el procedimiento lo valida a propósito |
| Resultado vacío | No hay excursiones en ese rango; los datos van de enero 2024 a diciembre 2026 |
| `Error Code: 2013 Lost connection` al ejecutar 00_integral | `Edit > Preferences > SQL Editor` → subir *DBMS connection read timeout* a 600 y repetir |
