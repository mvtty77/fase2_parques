-- =====================================================================
-- 03_vistas.sql · Requerimientos R2, R3, R5, R6, R7 y R8 (VIEW)
-- Caso 1 · Grupo 1 · TDFI103 Fase 2
-- =====================================================================
USE parques_db;

-- ---------------------------------------------------------------------
-- R2. ¿Cómo se distribuyen las especies inventariadas entre vegetales,
--     animales y minerales, considerando parque y área?
-- Integra: RECURSO_NATURAL + subtipos (especialización), INVENTARIO_RECURSO,
--          AREA y PARQUE. Recursos sin subtipo → 'SIN_CLASIFICAR'.
-- Mide: especies distintas y cantidad total inventariada por tipo.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_r2_distribucion_especies AS
SELECT p.anio_declaracion,
       p.nro_correlativo,
       p.nombre                         AS parque,
       a.nro_area,
       a.nombre                         AS area,
       CASE
         WHEN v.id_recurso IS NOT NULL THEN 'VEGETAL'
         WHEN an.id_recurso IS NOT NULL THEN 'ANIMAL'
         WHEN m.id_recurso IS NOT NULL THEN 'MINERAL'
         ELSE 'SIN_CLASIFICAR'
       END                              AS tipo_especie,
       COUNT(DISTINCT ir.id_recurso)    AS especies_distintas,
       SUM(ir.cantidad_inventariada)    AS cantidad_total
FROM INVENTARIO_RECURSO ir
JOIN RECURSO_NATURAL rn ON rn.id_recurso = ir.id_recurso
JOIN AREA a   ON a.anio_declaracion = ir.anio_declaracion
             AND a.nro_correlativo  = ir.nro_correlativo
             AND a.nro_area         = ir.nro_area
JOIN PARQUE p ON p.anio_declaracion = a.anio_declaracion
             AND p.nro_correlativo  = a.nro_correlativo
LEFT JOIN VEGETAL v  ON v.id_recurso  = rn.id_recurso
LEFT JOIN ANIMAL  an ON an.id_recurso = rn.id_recurso
LEFT JOIN MINERAL m  ON m.id_recurso  = rn.id_recurso
GROUP BY p.anio_declaracion, p.nro_correlativo, p.nombre,
         a.nro_area, a.nombre, tipo_especie;

-- ---------------------------------------------------------------------
-- R3. ¿Existe relación entre la cantidad de visitantes de una excursión y
--     su evaluación promedio?
-- Integra: EXCURSION, INSCRIPCION, EVALUACION. Los conteos y promedios se
-- calculan en tablas derivadas separadas para evitar duplicar filas en el
-- JOIN. Una excursión sin evaluaciones queda con promedio NULL (no 0).
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_r3_visitantes_vs_evaluacion AS
SELECT e.codigo_excursion,
       e.fecha,
       e.modalidad,
       e.capacidad,
       COALESCE(ins.participantes, 0)   AS cantidad_participantes,
       COALESCE(ins.inscritos, 0)       AS cantidad_inscritos,
       COALESCE(ev.n_evaluaciones, 0)   AS cantidad_evaluaciones,
       ev.promedio_evaluacion
FROM EXCURSION e
LEFT JOIN (SELECT codigo_excursion,
                  COUNT(*)                                  AS inscritos,
                  SUM(estado_asistencia = 'ASISTIO')        AS participantes
             FROM INSCRIPCION
            GROUP BY codigo_excursion) ins
       ON ins.codigo_excursion = e.codigo_excursion
LEFT JOIN (SELECT codigo_excursion,
                  COUNT(*)                                  AS n_evaluaciones,
                  ROUND(AVG(calificacion), 2)               AS promedio_evaluacion
             FROM EVALUACION
            GROUP BY codigo_excursion) ev
       ON ev.codigo_excursion = e.codigo_excursion
WHERE e.fecha <= CURDATE();

-- ---------------------------------------------------------------------
-- R5. ¿Qué áreas presentan mayor tasa de asistencia respecto de las
--     inscripciones realizadas?
-- Integra: PARQUE, AREA, EXCURSION, INSCRIPCION. Solo cuentan inscripciones
-- de excursiones ya realizadas (estado ASISTIO o NO_ASISTIO); las de estado
-- INSCRITO (excursiones futuras) no tienen asistencia definida.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_r5_tasa_asistencia_area AS
SELECT p.nombre                                     AS parque,
       a.nro_area,
       a.nombre                                     AS area,
       COUNT(DISTINCT e.codigo_excursion)           AS excursiones,
       COUNT(i.id_inscripcion)                      AS inscripciones,
       SUM(i.estado_asistencia = 'ASISTIO')         AS asistencias,
       ROUND(100 * SUM(i.estado_asistencia = 'ASISTIO') / COUNT(i.id_inscripcion), 2)
                                                    AS porcentaje_asistencia
FROM PARQUE p
JOIN AREA a        ON a.anio_declaracion = p.anio_declaracion
                  AND a.nro_correlativo  = p.nro_correlativo
JOIN EXCURSION e   ON e.anio_declaracion = a.anio_declaracion
                  AND e.nro_correlativo  = a.nro_correlativo
                  AND e.nro_area         = a.nro_area
JOIN INSCRIPCION i ON i.codigo_excursion = e.codigo_excursion
WHERE i.estado_asistencia IN ('ASISTIO', 'NO_ASISTIO')
GROUP BY p.anio_declaracion, p.nro_correlativo, p.nombre, a.nro_area, a.nombre;

-- ---------------------------------------------------------------------
-- R6. ¿Qué especies presentan mayor cantidad inventariada por parque y área?
-- Integra: PARQUE, AREA, INVENTARIO_RECURSO, RECURSO_NATURAL.
-- ranking_en_area = 1 identifica la especie con mayor cantidad de cada área.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_r6_especies_mayor_cantidad AS
SELECT p.nombre                     AS parque,
       a.nro_area,
       a.nombre                     AS area,
       rn.id_recurso,
       rn.nombre_comun,
       rn.nombre_cientifico,
       ir.cantidad_inventariada,
       ir.fecha_ultimo_monitoreo,
       RANK() OVER (PARTITION BY ir.anio_declaracion, ir.nro_correlativo, ir.nro_area
                    ORDER BY ir.cantidad_inventariada DESC) AS ranking_en_area
FROM INVENTARIO_RECURSO ir
JOIN RECURSO_NATURAL rn ON rn.id_recurso = ir.id_recurso
JOIN AREA a   ON a.anio_declaracion = ir.anio_declaracion
             AND a.nro_correlativo  = ir.nro_correlativo
             AND a.nro_area         = ir.nro_area
JOIN PARQUE p ON p.anio_declaracion = a.anio_declaracion
             AND p.nro_correlativo  = a.nro_correlativo
WHERE rn.activo = TRUE;

-- ---------------------------------------------------------------------
-- R7. ¿Qué proyectos de investigación concentran mayor participación de
--     investigadores y especies estudiadas?
-- Integra: PROYECTO_CIENTIFICO, PARTICIPA_PROYECTO (personal), INVESTIGA
-- (especies) y ESTUDIA (áreas). COUNT(DISTINCT) evita el producto cartesiano
-- entre participantes y especies. HAVING: al menos 2 investigadores y 2 especies.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_r7_proyectos_participacion AS
SELECT pc.id_proyecto,
       pc.nombre                        AS proyecto,
       pc.estado,
       COUNT(DISTINCT pp.rut_persona)   AS investigadores,
       COUNT(DISTINCT inv.id_recurso)   AS especies_estudiadas,
       COUNT(DISTINCT CONCAT_WS('-', es.anio_declaracion, es.nro_correlativo, es.nro_area))
                                        AS areas_estudiadas
FROM PROYECTO_CIENTIFICO pc
JOIN PARTICIPA_PROYECTO pp ON pp.id_proyecto = pc.id_proyecto
JOIN TRABAJADOR t          ON t.rut_persona  = pp.rut_persona
JOIN INVESTIGA inv         ON inv.id_proyecto = pc.id_proyecto
LEFT JOIN ESTUDIA es       ON es.id_proyecto = pc.id_proyecto
GROUP BY pc.id_proyecto, pc.nombre, pc.estado
HAVING COUNT(DISTINCT pp.rut_persona) >= 2
   AND COUNT(DISTINCT inv.id_recurso) >= 2;

-- ---------------------------------------------------------------------
-- R8. ¿Qué trabajadores desempeñan más de una función y en qué parques o
--     áreas desarrollan sus actividades?
-- Integra: PERSONA, TRABAJADOR, TRABAJADOR_FUNCION, ASIGNACION_TRABAJADOR,
-- AREA y PARQUE. Funciones de grupo: COUNT(DISTINCT) y GROUP_CONCAT.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_r8_trabajadores_multifuncion AS
SELECT t.rut_persona,
       CONCAT(pe.nombres, ' ', pe.apellido_paterno)                 AS trabajador,
       t.cargo,
       COUNT(DISTINCT tf.funcion)                                   AS cantidad_funciones,
       GROUP_CONCAT(DISTINCT tf.funcion ORDER BY tf.funcion SEPARATOR ', ')       AS funciones,
       COUNT(DISTINCT p.nombre)                                     AS cantidad_parques,
       GROUP_CONCAT(DISTINCT p.nombre ORDER BY p.nombre SEPARATOR ', ')          AS parques,
       GROUP_CONCAT(DISTINCT CONCAT(p.nombre, ' / ', a.nombre)
                    ORDER BY p.nombre, a.nombre SEPARATOR '; ')     AS areas
FROM TRABAJADOR t
JOIN PERSONA pe            ON pe.rut_persona = t.rut_persona
JOIN TRABAJADOR_FUNCION tf ON tf.rut_persona = t.rut_persona
LEFT JOIN ASIGNACION_TRABAJADOR asg ON asg.rut_persona = tf.rut_persona
                                   AND asg.funcion     = tf.funcion
LEFT JOIN AREA a   ON a.anio_declaracion = asg.anio_declaracion
                  AND a.nro_correlativo  = asg.nro_correlativo
                  AND a.nro_area         = asg.nro_area
LEFT JOIN PARQUE p ON p.anio_declaracion = a.anio_declaracion
                  AND p.nro_correlativo  = a.nro_correlativo
GROUP BY t.rut_persona, pe.nombres, pe.apellido_paterno, t.cargo
HAVING COUNT(DISTINCT tf.funcion) > 1;
