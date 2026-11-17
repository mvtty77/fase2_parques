# Guion de defensa · 10 min de presentación + 5 min de preguntas

Presentación: `[PENDIENTE: docs/presentacion_defensa.pptx — diapositivas de la disertación]`. Todos los integrantes exponen; cada uno presenta lo que lideró según la matriz y debe poder responder sobre **cualquier** parte.

| Min | Diapositiva | Expone | Qué mostrar |
|---|---|---|---|
| 0:00 | Portada y alcance | Francisca | Caso, equipo, stack |
| 0:45 | MERE corregido | Carlos | Las 8 correcciones; énfasis en EJERCE_EN (R8) y especializaciones |
| 1:45 | Modelo relacional en Workbench | Gaspar | 24 tablas, claves compuestas, FK compuesta de EVALUACION, triggers |
| 2:45 | Poblamiento | Esteban | Faker con semilla, conteos frente a los rangos del PDF, validaciones |
| 3:30 | Vistas R2, R3, R5, R6, R7, R8 | Matias y Francisca | Una salida en Workbench; JOIN sin duplicar y HAVING |
| 4:45 | Procedimientos R1, R4, R9, R10, R11, R12 | Carlos y Esteban | CALL en vivo de R9 (subconsulta correlacionada) |
| 6:00 | PMV en vivo (Codespace o PC) | Matias → Gaspar → Esteban → Francisca | Inscripción (y rechazo por duplicado), CRUD con desactivación lógica, login con dos roles, dashboard |
| 8:30 | Despliegue | Matias | Codespace abierto: MySQL encendido, `bash scripts/reconstruir_base.sh` y puerto 8501 |
| 9:00 | Responsabilidades, IA y conclusiones | Todos | Matriz, bitácoras, validación de OpenCode, una conclusión por persona |

## Preguntas probables (practicar la respuesta en voz alta)

1. ¿Por qué AREA es entidad débil y cómo se refleja en su PK y en las FK que la referencian?
2. ¿Qué garantiza que una evaluación sea de la misma excursión que su inscripción?
3. ¿Por qué R3 calcula conteos y promedios en subconsultas separadas? ¿Qué pasaría con un JOIN directo?
4. ¿Qué es una subconsulta correlacionada? Señálela en R9.
5. ¿Qué hace `SELECT … FOR UPDATE` en el formulario y qué problema evita?
6. Si un analista llama a `inscribir_visitante()`, ¿dónde se le niega el acceso?
7. ¿Por qué un parque con excursiones se desactiva en vez de borrarse?
8. ¿Cómo se asegura que los datos generados sean reproducibles?
9. ¿Qué hace el Codespace la primera vez (`instalar.sh`) y cada vez que se abre (`iniciar.sh`)? ¿Qué hace `reconstruir_base.sh`?
10. ¿Cómo validaron lo que propuso la IA? Den un ejemplo de algo que corrigieron.

## Checklist del día

- [ ] Codespace abierto y app funcionando el día anterior; Workbench del PC con `parques_db` cargada como respaldo.
- [ ] Workbench conectado a `127.0.0.1:3307` con `05_pruebas.sql` abierto.
- [ ] Usuarios `admin`, `operador` y `analista` probados.
- [ ] Una excursión futura con cupo y otra llena identificadas para la demostración.
