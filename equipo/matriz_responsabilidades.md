# Matriz de responsabilidades · Grupo 1 · Caso 1

> **PROPUESTA PROVISIONAL — el equipo debe confirmarla antes de implementar** (sección 14 del PDF).
> Criterios: cada integrante es responsable principal en actividades de más de una etapa; carga equilibrada (3 responsabilidades principales cada uno); las cuatro funcionalidades del PMV tienen responsables distintos (Matias, Gaspar, Esteban, Francisca); nadie concentra la implementación técnica. Las asignaciones parten de los roles de Fase 1.

| Etapa / actividad | Responsable principal | Integrantes que colaboran | Evidencia esperada |
|---|---|---|---|
| Revisión y corrección del MERE | Carlos Vasconcellos | Matias Lagos, Gaspar Galaz | MERE corregido (ERDPlus) y `docs/mere/correcciones_mere.md` |
| Modelo relacional final | Gaspar Galaz | Carlos Vasconcellos | Modelo Workbench validado (`.mwb` y PNG) |
| Implementación DDL | Gaspar Galaz | Esteban Gonzales | `sql/01_estructura.sql` y pruebas negativas |
| Poblamiento y calidad de datos | Esteban Gonzales | Francisca Perez | `scripts/generar_datos.py`, `sql/02_datos.sql`, conteos |
| Requerimientos R1-R3 | Matias Lagos | Francisca Perez | SQL, capturas Workbench e interpretación |
| Requerimientos R4-R6 | Francisca Perez | Matias Lagos | SQL, capturas Workbench e interpretación |
| Requerimientos R7-R9 | Carlos Vasconcellos | Gaspar Galaz | SQL, capturas Workbench e interpretación |
| Requerimientos R10-R12 | Esteban Gonzales | Carlos Vasconcellos | SQL, capturas Workbench e interpretación |
| Formulario transaccional PMV | Matias Lagos | Esteban Gonzales | Funcionalidad integrada y prueba |
| CRUD PMV | Gaspar Galaz | Francisca Perez | Funcionalidad integrada y prueba |
| Usuarios y roles | Esteban Gonzales | Carlos Vasconcellos | Funcionalidad integrada y prueba |
| Dashboard | Francisca Perez | Matias Lagos | 4 visualizaciones integradas |
| Integración y pruebas del PMV | Carlos Vasconcellos | Todos | PMV completo funcionando; `pytest` |
| Codespace y despliegue | Matias Lagos | Gaspar Galaz | Codespace funcionando e instrucciones (README) |
| Integración del informe | Francisca Perez | Todos | Informe final y evidencias |

## Resumen por integrante

| Integrante | Responsabilidades principales | Etapas |
|---|---|---|
| Carlos Vasconcellos | MERE · R7-R9 · Integración y pruebas PMV | Modelamiento, SQL, PMV |
| Matias Lagos | R1-R3 · Formulario transaccional · Codespace | SQL, PMV, Despliegue |
| Esteban Gonzales | Poblamiento · R10-R12 · Usuarios y roles | Datos, SQL, PMV |
| Gaspar Galaz | Modelo relacional · DDL · CRUD | Modelamiento, Implementación, PMV |
| Francisca Perez | R4-R6 · Dashboard · Informe | SQL, PMV, Documentación |

> Si el equipo ya no tiene cinco integrantes, la regla «cada funcionalidad del PMV con un responsable distinto» no podría cumplirse: hay que consultarlo al docente antes de reasignar, sin inventar una excepción.
