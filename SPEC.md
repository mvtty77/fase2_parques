# SPEC · Caso 1 · Grupo 1 · Fase 2

Fuente normativa: `docs/enunciado_oficial.pdf`. Ante una contradicción, prevalece el PDF.

## Alcance

Implementar el modelo corregido de Fase 1 en MySQL 8, poblarlo, resolver R1-R12 (6 vistas y 6 procedimientos) y construir un PMV Streamlit integrado con 4 funcionalidades, ejecutado en GitHub Codespaces (MySQL 8 + Streamlit, sin Docker Compose) y en un PC con MySQL Workbench.

## Modelo

24 tablas (23 de Fase 1 + `ASIGNACION_TRABAJADOR`). Correcciones C1-C8 en `docs/mere/correcciones_mere.md`. Especializaciones: PERSONA total/solapada; RECURSO_NATURAL parcial/disjunta.

## Definiciones operativas

- **Visitantes** (R1, R4, R9, R11, R12, dashboard): inscripciones con `estado_asistencia = 'ASISTIO'`; se cuentan participaciones.
- **Período**: `EXCURSION.fecha BETWEEN inicio AND fin`.
- **Tipo de especie**: VEGETAL, ANIMAL, MINERAL según el subtipo; sin subtipo = SIN_CLASIFICAR.
- **Tasa de asistencia** (R5): ASISTIO / (ASISTIO + NO_ASISTIO); se excluyen las INSCRITO.
- **Promedio general de parques** (R12): promedio de los promedios por parque.

## Requisitos → objetos

| ID | Objeto | Nombre |
|---|---|---|
| R1 | PROCEDURE | `sp_r1_areas_mas_visitantes(inicio, fin)` |
| R2 | VIEW | `vw_r2_distribucion_especies` |
| R3 | VIEW | `vw_r3_visitantes_vs_evaluacion` |
| R4 | PROCEDURE | `sp_r4_parques_excursiones_visitantes(inicio, fin)` |
| R5 | VIEW | `vw_r5_tasa_asistencia_area` |
| R6 | VIEW | `vw_r6_especies_mayor_cantidad` |
| R7 | VIEW | `vw_r7_proyectos_participacion` |
| R8 | VIEW | `vw_r8_trabajadores_multifuncion` |
| R9 | PROCEDURE | `sp_r9_excursiones_sobre_promedio_parque(anio, correlativo, inicio, fin)` |
| R10 | PROCEDURE | `sp_r10_especies_sobre_promedio_tipo(tipo)` |
| R11 | PROCEDURE | `sp_r11_visitantes_destacados(inicio, fin)` |
| R12 | PROCEDURE | `sp_r12_parques_sobre_promedio_general(inicio, fin)` |

## PMV

| Funcionalidad | Implementación | Permiso |
|---|---|---|
| Formulario transaccional | Inscripción de visitante en excursión + registro de asistencia | `inscripcion` |
| CRUD | PARQUE y RECURSO_NATURAL (+subtipo); eliminación lógica si hay dependencias | `crud_parque`, `crud_especie` |
| Usuarios | Login PBKDF2; roles ADMINISTRADOR, OPERADOR y ANALISTA; administración de cuentas | `usuarios` |
| Dashboard | 3 preguntas de Fase 1 + ocupación de capacidad | `dashboard` |

Restricciones: el PMV no usa las vistas ni los procedimientos R1-R12; no hay credenciales en el código; toda escritura es transaccional.
