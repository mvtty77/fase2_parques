-- =====================================================================
-- 04_procedimientos.sql · Requerimientos R1, R4, R9, R10, R11 y R12 (PROCEDURE)
-- Caso 1 · Grupo 1 · TDFI103 Fase 2
-- Convención: "visitantes" = inscripciones con estado_asistencia = 'ASISTIO'
-- (participaciones; un visitante que asiste a dos excursiones cuenta dos veces,
-- criterio definido en el informe de Fase 1). Período filtrado por EXCURSION.fecha.
-- =====================================================================
USE parques_db;

DROP PROCEDURE IF EXISTS sp_r1_areas_mas_visitantes;
DROP PROCEDURE IF EXISTS sp_r4_parques_excursiones_visitantes;
DROP PROCEDURE IF EXISTS sp_r9_excursiones_sobre_promedio_parque;
DROP PROCEDURE IF EXISTS sp_r10_especies_sobre_promedio_tipo;
DROP PROCEDURE IF EXISTS sp_r11_visitantes_destacados;
DROP PROCEDURE IF EXISTS sp_r12_parques_sobre_promedio_general;

DELIMITER $$

-- ---------------------------------------------------------------------
-- R1. ¿Cuáles son las áreas con mayor cantidad de visitantes mediante
--     excursiones durante un período determinado?
-- Parámetros: fecha inicio y fecha término.
-- Integra: PARQUE, AREA, EXCURSION, INSCRIPCION.
-- ---------------------------------------------------------------------
CREATE PROCEDURE sp_r1_areas_mas_visitantes(IN p_inicio DATE, IN p_fin DATE)
BEGIN
  IF p_inicio IS NULL OR p_fin IS NULL OR p_inicio > p_fin THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Período inválido: fecha inicio debe ser <= fecha término';
  END IF;

  SELECT p.nombre                                AS parque,
         a.nro_area,
         a.nombre                                AS area,
         COUNT(DISTINCT e.codigo_excursion)      AS excursiones,
         COUNT(i.id_inscripcion)                 AS inscripciones,
         SUM(i.estado_asistencia = 'ASISTIO')    AS visitantes
  FROM PARQUE p
  JOIN AREA a        ON a.anio_declaracion = p.anio_declaracion
                    AND a.nro_correlativo  = p.nro_correlativo
  JOIN EXCURSION e   ON e.anio_declaracion = a.anio_declaracion
                    AND e.nro_correlativo  = a.nro_correlativo
                    AND e.nro_area         = a.nro_area
  JOIN INSCRIPCION i ON i.codigo_excursion = e.codigo_excursion
  WHERE e.fecha BETWEEN p_inicio AND p_fin
  GROUP BY p.anio_declaracion, p.nro_correlativo, p.nombre, a.nro_area, a.nombre
  ORDER BY visitantes DESC, excursiones DESC, parque, area;
END$$

-- ---------------------------------------------------------------------
-- R4. ¿Qué parques concentran la mayor cantidad de excursiones y visitantes
--     en un período determinado?
-- Parámetros: fechas. Integra: PARQUE, AREA, EXCURSION, INSCRIPCION.
-- LEFT JOIN a INSCRIPCION para contar también excursiones sin inscritos.
-- ---------------------------------------------------------------------
CREATE PROCEDURE sp_r4_parques_excursiones_visitantes(IN p_inicio DATE, IN p_fin DATE)
BEGIN
  IF p_inicio IS NULL OR p_fin IS NULL OR p_inicio > p_fin THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Período inválido: fecha inicio debe ser <= fecha término';
  END IF;

  SELECT p.nombre                                              AS parque,
         COUNT(DISTINCT a.nro_area)                            AS areas_con_excursiones,
         COUNT(DISTINCT e.codigo_excursion)                    AS excursiones,
         COALESCE(SUM(i.estado_asistencia = 'ASISTIO'), 0)     AS visitantes,
         COUNT(i.id_inscripcion)                               AS inscripciones
  FROM PARQUE p
  JOIN AREA a          ON a.anio_declaracion = p.anio_declaracion
                      AND a.nro_correlativo  = p.nro_correlativo
  JOIN EXCURSION e     ON e.anio_declaracion = a.anio_declaracion
                      AND e.nro_correlativo  = a.nro_correlativo
                      AND e.nro_area         = a.nro_area
  LEFT JOIN INSCRIPCION i ON i.codigo_excursion = e.codigo_excursion
  WHERE e.fecha BETWEEN p_inicio AND p_fin
  GROUP BY p.anio_declaracion, p.nro_correlativo, p.nombre
  ORDER BY excursiones DESC, visitantes DESC;
END$$

-- ---------------------------------------------------------------------
-- R9. ¿Qué excursiones superan el promedio de visitantes de las excursiones
--     realizadas en el mismo parque?
-- Parámetros: parque (año_declaracion, nro_correlativo; NULL = todos) y período.
-- Subconsulta CORRELACIONADA: el promedio se calcula para el parque de la fila
-- externa (x.anio_declaracion, x.nro_correlativo) dentro del mismo período.
-- ---------------------------------------------------------------------
CREATE PROCEDURE sp_r9_excursiones_sobre_promedio_parque(
  IN p_anio SMALLINT, IN p_correlativo SMALLINT, IN p_inicio DATE, IN p_fin DATE)
BEGIN
  IF p_inicio IS NULL OR p_fin IS NULL OR p_inicio > p_fin THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Período inválido: fecha inicio debe ser <= fecha término';
  END IF;

  SELECT x.parque, x.area, x.codigo_excursion, x.fecha, x.modalidad, x.visitantes,
         (SELECT ROUND(AVG(y.visitantes), 2)
            FROM (SELECT e2.codigo_excursion, e2.anio_declaracion, e2.nro_correlativo,
                         SUM(i2.estado_asistencia = 'ASISTIO') AS visitantes
                    FROM EXCURSION e2
                    JOIN INSCRIPCION i2 ON i2.codigo_excursion = e2.codigo_excursion
                   WHERE e2.fecha BETWEEN p_inicio AND p_fin
                   GROUP BY e2.codigo_excursion, e2.anio_declaracion, e2.nro_correlativo) y
           WHERE y.anio_declaracion = x.anio_declaracion
             AND y.nro_correlativo  = x.nro_correlativo)        AS promedio_parque
  FROM (SELECT p.anio_declaracion, p.nro_correlativo, p.nombre AS parque,
               a.nombre AS area, e.codigo_excursion, e.fecha, e.modalidad,
               SUM(i.estado_asistencia = 'ASISTIO') AS visitantes
          FROM PARQUE p
          JOIN AREA a        ON a.anio_declaracion = p.anio_declaracion
                            AND a.nro_correlativo  = p.nro_correlativo
          JOIN EXCURSION e   ON e.anio_declaracion = a.anio_declaracion
                            AND e.nro_correlativo  = a.nro_correlativo
                            AND e.nro_area         = a.nro_area
          JOIN INSCRIPCION i ON i.codigo_excursion = e.codigo_excursion
         WHERE e.fecha BETWEEN p_inicio AND p_fin
           AND (p_anio IS NULL OR (p.anio_declaracion = p_anio AND p.nro_correlativo = p_correlativo))
         GROUP BY p.anio_declaracion, p.nro_correlativo, p.nombre, a.nombre,
                  e.codigo_excursion, e.fecha, e.modalidad) x
  WHERE x.visitantes > (SELECT AVG(y.visitantes)
                          FROM (SELECT e2.anio_declaracion, e2.nro_correlativo,
                                       SUM(i2.estado_asistencia = 'ASISTIO') AS visitantes
                                  FROM EXCURSION e2
                                  JOIN INSCRIPCION i2 ON i2.codigo_excursion = e2.codigo_excursion
                                 WHERE e2.fecha BETWEEN p_inicio AND p_fin
                                 GROUP BY e2.codigo_excursion, e2.anio_declaracion, e2.nro_correlativo) y
                         WHERE y.anio_declaracion = x.anio_declaracion      -- correlación
                           AND y.nro_correlativo  = x.nro_correlativo)
  ORDER BY x.parque, x.visitantes DESC;
END$$

-- ---------------------------------------------------------------------
-- R10. ¿Qué especies poseen una cantidad inventariada superior al promedio
--      de las especies de su mismo tipo?
-- Parámetro: tipo de especie ('VEGETAL','ANIMAL','MINERAL','SIN_CLASIFICAR').
-- Integra: RECURSO_NATURAL/subtipo, INVENTARIO_RECURSO, AREA, PARQUE.
-- Subconsulta: promedio de la cantidad total por especie dentro del tipo.
-- ---------------------------------------------------------------------
CREATE PROCEDURE sp_r10_especies_sobre_promedio_tipo(IN p_tipo VARCHAR(20))
BEGIN
  IF p_tipo NOT IN ('VEGETAL','ANIMAL','MINERAL','SIN_CLASIFICAR') OR p_tipo IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Tipo inválido: use VEGETAL, ANIMAL, MINERAL o SIN_CLASIFICAR';
  END IF;

  SELECT rn.id_recurso,
         rn.nombre_comun,
         rn.nombre_cientifico,
         p_tipo                                    AS tipo_especie,
         SUM(ir.cantidad_inventariada)             AS cantidad_total,
         COUNT(DISTINCT CONCAT_WS('-', a.anio_declaracion, a.nro_correlativo, a.nro_area)) AS areas,
         COUNT(DISTINCT p.nombre)                  AS parques,
         GROUP_CONCAT(DISTINCT p.nombre ORDER BY p.nombre SEPARATOR ', ') AS presente_en
  FROM RECURSO_NATURAL rn
  JOIN INVENTARIO_RECURSO ir ON ir.id_recurso = rn.id_recurso
  JOIN AREA a   ON a.anio_declaracion = ir.anio_declaracion
               AND a.nro_correlativo  = ir.nro_correlativo
               AND a.nro_area         = ir.nro_area
  JOIN PARQUE p ON p.anio_declaracion = a.anio_declaracion
               AND p.nro_correlativo  = a.nro_correlativo
  WHERE (CASE WHEN EXISTS (SELECT 1 FROM VEGETAL v WHERE v.id_recurso = rn.id_recurso) THEN 'VEGETAL'
              WHEN EXISTS (SELECT 1 FROM ANIMAL  x WHERE x.id_recurso = rn.id_recurso) THEN 'ANIMAL'
              WHEN EXISTS (SELECT 1 FROM MINERAL m WHERE m.id_recurso = rn.id_recurso) THEN 'MINERAL'
              ELSE 'SIN_CLASIFICAR' END) = p_tipo
  GROUP BY rn.id_recurso, rn.nombre_comun, rn.nombre_cientifico
  HAVING SUM(ir.cantidad_inventariada) >
         (SELECT AVG(t.total)
            FROM (SELECT ir2.id_recurso, SUM(ir2.cantidad_inventariada) AS total
                    FROM INVENTARIO_RECURSO ir2
                    JOIN RECURSO_NATURAL rn2 ON rn2.id_recurso = ir2.id_recurso
                   WHERE (CASE WHEN EXISTS (SELECT 1 FROM VEGETAL v WHERE v.id_recurso = rn2.id_recurso) THEN 'VEGETAL'
                               WHEN EXISTS (SELECT 1 FROM ANIMAL  x WHERE x.id_recurso = rn2.id_recurso) THEN 'ANIMAL'
                               WHEN EXISTS (SELECT 1 FROM MINERAL m WHERE m.id_recurso = rn2.id_recurso) THEN 'MINERAL'
                               ELSE 'SIN_CLASIFICAR' END) = p_tipo
                   GROUP BY ir2.id_recurso) t)
  ORDER BY cantidad_total DESC;
END$$

-- ---------------------------------------------------------------------
-- R11. ¿Qué visitantes han participado en más excursiones que el promedio y
--      además poseen una evaluación promedio superior al promedio general?
-- Parámetros: rango de fechas. Integra: VISITANTE, PERSONA, INSCRIPCION,
-- EXCURSION, EVALUACION. "Participar" = asistir (ASISTIO).
-- Promedio de excursiones: entre visitantes con al menos una participación
-- en el período. Promedio general: todas las calificaciones del período.
-- ---------------------------------------------------------------------
CREATE PROCEDURE sp_r11_visitantes_destacados(IN p_inicio DATE, IN p_fin DATE)
BEGIN
  IF p_inicio IS NULL OR p_fin IS NULL OR p_inicio > p_fin THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Período inválido: fecha inicio debe ser <= fecha término';
  END IF;

  SELECT v.rut_persona,
         CONCAT(pe.nombres, ' ', pe.apellido_paterno)  AS visitante,
         COUNT(DISTINCT i.codigo_excursion)            AS excursiones,
         ROUND(AVG(ev.calificacion), 2)                AS evaluacion_promedio,
         (SELECT ROUND(AVG(c.n), 2)
            FROM (SELECT i2.rut_persona, COUNT(*) AS n
                    FROM INSCRIPCION i2
                    JOIN EXCURSION e2 ON e2.codigo_excursion = i2.codigo_excursion
                   WHERE i2.estado_asistencia = 'ASISTIO'
                     AND e2.fecha BETWEEN p_inicio AND p_fin
                   GROUP BY i2.rut_persona) c)         AS promedio_excursiones,
         (SELECT ROUND(AVG(ev3.calificacion), 2)
            FROM EVALUACION ev3
            JOIN EXCURSION e3 ON e3.codigo_excursion = ev3.codigo_excursion
           WHERE e3.fecha BETWEEN p_inicio AND p_fin)  AS promedio_general
  FROM VISITANTE v
  JOIN PERSONA pe     ON pe.rut_persona = v.rut_persona
  JOIN INSCRIPCION i  ON i.rut_persona = v.rut_persona AND i.estado_asistencia = 'ASISTIO'
  JOIN EXCURSION e    ON e.codigo_excursion = i.codigo_excursion
  LEFT JOIN EVALUACION ev ON ev.id_inscripcion = i.id_inscripcion
  WHERE e.fecha BETWEEN p_inicio AND p_fin
  GROUP BY v.rut_persona, pe.nombres, pe.apellido_paterno
  HAVING COUNT(DISTINCT i.codigo_excursion) >
           (SELECT AVG(c.n)
              FROM (SELECT i2.rut_persona, COUNT(*) AS n
                      FROM INSCRIPCION i2
                      JOIN EXCURSION e2 ON e2.codigo_excursion = i2.codigo_excursion
                     WHERE i2.estado_asistencia = 'ASISTIO'
                       AND e2.fecha BETWEEN p_inicio AND p_fin
                     GROUP BY i2.rut_persona) c)
     AND AVG(ev.calificacion) >
           (SELECT AVG(ev3.calificacion)
              FROM EVALUACION ev3
              JOIN EXCURSION e3 ON e3.codigo_excursion = ev3.codigo_excursion
             WHERE e3.fecha BETWEEN p_inicio AND p_fin)
  ORDER BY excursiones DESC, evaluacion_promedio DESC;
END$$

-- ---------------------------------------------------------------------
-- R12. ¿Qué parques presentan un promedio de visitantes por excursión
--      superior al promedio general de los parques durante un período?
-- Parámetros: fecha inicio y término. Integra: PARQUE, AREA, EXCURSION,
-- INSCRIPCION. Agrupación en dos niveles: excursión → parque.
-- Promedio general = promedio de los promedios de cada parque (subconsulta).
-- ---------------------------------------------------------------------
CREATE PROCEDURE sp_r12_parques_sobre_promedio_general(IN p_inicio DATE, IN p_fin DATE)
BEGIN
  IF p_inicio IS NULL OR p_fin IS NULL OR p_inicio > p_fin THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Período inválido: fecha inicio debe ser <= fecha término';
  END IF;

  SELECT pq.parque,
         pq.excursiones,
         pq.visitantes,
         ROUND(pq.promedio_visitantes, 2)                   AS promedio_visitantes_excursion,
         ROUND((SELECT AVG(g.prom)
                  FROM (SELECT AVG(ex.visitantes) AS prom
                          FROM (SELECT e.anio_declaracion, e.nro_correlativo, e.codigo_excursion,
                                       SUM(i.estado_asistencia = 'ASISTIO') AS visitantes
                                  FROM EXCURSION e
                                  JOIN INSCRIPCION i ON i.codigo_excursion = e.codigo_excursion
                                 WHERE e.fecha BETWEEN p_inicio AND p_fin
                                 GROUP BY e.anio_declaracion, e.nro_correlativo, e.codigo_excursion) ex
                         GROUP BY ex.anio_declaracion, ex.nro_correlativo) g), 2)
                                                            AS promedio_general_parques
  FROM (SELECT p.nombre AS parque,
               COUNT(*)              AS excursiones,
               SUM(ex.visitantes)    AS visitantes,
               AVG(ex.visitantes)    AS promedio_visitantes
          FROM PARQUE p
          JOIN (SELECT e.anio_declaracion, e.nro_correlativo, e.codigo_excursion,
                       SUM(i.estado_asistencia = 'ASISTIO') AS visitantes
                  FROM AREA a
                  JOIN EXCURSION e   ON e.anio_declaracion = a.anio_declaracion
                                    AND e.nro_correlativo  = a.nro_correlativo
                                    AND e.nro_area         = a.nro_area
                  JOIN INSCRIPCION i ON i.codigo_excursion = e.codigo_excursion
                 WHERE e.fecha BETWEEN p_inicio AND p_fin
                 GROUP BY e.anio_declaracion, e.nro_correlativo, e.codigo_excursion) ex
            ON ex.anio_declaracion = p.anio_declaracion
           AND ex.nro_correlativo  = p.nro_correlativo
         GROUP BY p.anio_declaracion, p.nro_correlativo, p.nombre) pq
  WHERE pq.promedio_visitantes >
        (SELECT AVG(g.prom)
           FROM (SELECT AVG(ex.visitantes) AS prom
                   FROM (SELECT e.anio_declaracion, e.nro_correlativo, e.codigo_excursion,
                                SUM(i.estado_asistencia = 'ASISTIO') AS visitantes
                           FROM EXCURSION e
                           JOIN INSCRIPCION i ON i.codigo_excursion = e.codigo_excursion
                          WHERE e.fecha BETWEEN p_inicio AND p_fin
                          GROUP BY e.anio_declaracion, e.nro_correlativo, e.codigo_excursion) ex
                  GROUP BY ex.anio_declaracion, ex.nro_correlativo) g)
  ORDER BY promedio_visitantes_excursion DESC;
END$$

DELIMITER ;
