# Evidencias de respaldo

Todas se obtuvieron ejecutando el proyecto real (MySQL 8.0.46, Python 3.12, Streamlit 1.67) sobre la base construida con `sql/00_integral.sql`. Las operaciones de prueba (inscripción y desactivación de un parque) se revirtieron después de capturarlas.

> **No son capturas de MySQL Workbench.** El PDF exige capturas de Workbench (secciones 5 y 7): debe tomarlas el equipo en su PC (ver `docs/workbench/instrucciones_workbench.md`). Las de phpMyAdmin se tomaron solo como apoyo durante la validación; phpMyAdmin no forma parte de este repositorio.

## Terminal (texto)

| Archivo | Qué demuestra |
|---|---|
| `evidencia_01_script_integral.txt` | Reconstrucción desde cero: 24 tablas, 6 vistas, 6 procedimientos, 8 triggers, 28 FK, 12 UNIQUE, 35 CHECK |
| `evidencia_02_generacion_datos.txt` | Conteos del generador, validación previa y MD5 idéntico al regenerar (reproducible) |
| `evidencia_04_pruebas_sql.txt` | `05_pruebas.sql` completo: conteos, 11 pruebas negativas con su error, ROLLBACK y R1-R12 |
| `evidencia_05_pytest.txt` | 13/13 pruebas automáticas con el usuario limitado de la app |
| `salidas_referencia_R1_R12.md` | Salida completa de cada requerimiento, para comparar con las capturas de Workbench |

## PMV Streamlit (`pmv_*.png`)

01-02 login correcto e incorrecto · 03-06 formulario transaccional (inscripción, duplicado rechazado, asistencia) · 07-10 CRUD de parques y especies (incluida la desactivación lógica) · 11 administración de cuentas y roles · 12-15 las cuatro preguntas del dashboard · 16-17 menú efectivo de los roles OPERADOR y ANALISTA.

