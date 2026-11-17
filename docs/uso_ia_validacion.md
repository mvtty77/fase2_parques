# Uso de inteligencia artificial y validación

El PDF (sección 11) exige **OpenCode** como asistente de IA del curso y evidencia resumida del uso y, sobre todo, de la validación. Este archivo distingue lo que ya se hizo de lo que debe hacer y registrar el equipo.

## 1. Origen del borrador

El borrador inicial del repositorio (SQL, generador, PMV, Codespace y documentación) se produjo con **Claude (Anthropic)**, a partir del PDF oficial, el informe de Fase 1 y el prompt del grupo. Declararlo es obligatorio para un uso honesto de IA. **Este borrador no sustituye el uso de OpenCode:** el equipo debe usarlo para revisar, corregir o ampliar el código y registrarlo abajo.

## 2. Validación técnica ya ejecutada sobre el borrador

Ejecutada en MySQL 8.0.46 y Python 3.12; salidas en `docs/evidencias/`.

| Actividad | Validación realizada | Resultado | Evidencia |
|---|---|---|---|
| DDL | Script integral ejecutado desde cero | 24 tablas, 28 FK, 12 UNIQUE, 35 CHECK, 8 triggers | `evidencia_04_pruebas_sql.txt` |
| Restricciones | 11 pruebas negativas (CHECK, FK, UNIQUE, triggers) | Las 11 fallan con el error esperado | `evidencia_04_pruebas_sql.txt` |
| Poblamiento | Validación previa en Python + carga con triggers activos + conteos | Volúmenes dentro de los rangos del PDF | `evidencia_02_generacion_datos.txt` |
| R1-R12 | Ejecución de las 6 vistas y 6 procedimientos; revisión de cada interpretación contra los datos | Resultados no triviales; se corrigió una interpretación de R1 que no coincidía con la salida | `salidas_referencia_R1_R12.md` |
| PMV | 13 pruebas pytest + prueba de la app por rol + capturas en navegador | 13/13; cada rol ve solo sus páginas | `evidencia_05_pytest.txt`, `pmv_*.png` |
| Codespace | Se simuló el Codespace (Ubuntu 24.04, usuario `vscode` con sudo): instalación, primer arranque, reapertura con MySQL apagado y reconstrucción | MySQL 8.0.46 + base + app en 8501; 13/13 pruebas | `codespace_pruebas_sql.txt`, `codespace_pytest.txt` |

Errores de la IA detectados y corregidos durante la validación (ejemplos útiles para la defensa):

1. Un CHECK sobre `rut_supervisor` falló con el error 3823 de MySQL (columna con acción referencial): se reemplazó por trigger.
2. El primer poblamiento generó 1.652 inscripciones, sobre el rango del PDF: se ajustó la tasa de llenado (1.363).
3. Nombres con género mezclado («Byron Alejandra») y un visitante con 38 excursiones: se corrigió el uso de Faker y la distribución de recurrencia.
4. Proyectos con títulos sin sentido («Fenología de vidrio volcánico»): se separaron temas biológicos y geológicos.
5. Una prueba automática elegía una excursión ya llena: se corrigió la prueba, no el código.
6. La interpretación de R1 afirmaba algo que la salida no mostraba: se reescribió con la cifra real (163 de 369).

## 3. Registro de uso de OpenCode (completar por el equipo)

| Fecha | Integrante | Actividad (Modelamiento/SQL, Poblamiento, Python/Streamlit, Despliegue) | Qué se pidió a OpenCode | Qué se aceptó, modificó o rechazó | Cómo se validó (ejecución, prueba, comparación con el modelo) |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |
| | | | | | |

Validación mínima que exige el PDF por actividad:

- **Modelamiento/SQL:** comparar con el modelo, ejecutar y comprobar resultados.
- **Poblamiento:** verificar FK, distribuciones, fechas y coherencia del negocio.
- **Python/Streamlit:** ejecutar, probar casos y explicar el código.
- **Despliegue (el PDF pide Docker):** demostrar que la solución se instala y ejecuta; ver nota en el informe, sección 12.
