-- =====================================================================
-- 05_pruebas.sql · Verificación de restricciones, conteos y objetos SQL
-- Ejecutar con:  mysql --force -u root -p < sql/05_pruebas.sql
-- (--force continúa tras los errores ESPERADOS de las pruebas negativas)
-- En Workbench: ejecutar sentencia por sentencia (Ctrl+Enter) y capturar.
-- =====================================================================
USE parques_db;
SET NAMES utf8mb4;

-- ---------------------------------------------------------------------
-- A. Conteo por tabla (comparar con los rangos de la sección 6 del PDF)
-- ---------------------------------------------------------------------
SELECT 'REGION (comunidades)' AS tabla, COUNT(*) AS filas, '5-10' AS rango_pdf FROM REGION
UNION ALL SELECT 'PARQUE', COUNT(*), '12-20' FROM PARQUE
UNION ALL SELECT 'AREA', COUNT(*), '35-60' FROM AREA
UNION ALL SELECT 'RECURSO_NATURAL (especies)', COUNT(*), '60-120' FROM RECURSO_NATURAL
UNION ALL SELECT 'INVENTARIO_RECURSO', COUNT(*), '250-500' FROM INVENTARIO_RECURSO
UNION ALL SELECT 'TRABAJADOR (personal)', COUNT(*), '40-80' FROM TRABAJADOR
UNION ALL SELECT 'PROYECTO_CIENTIFICO', COUNT(*), '20-40' FROM PROYECTO_CIENTIFICO
UNION ALL SELECT 'VISITANTE', COUNT(*), '150-300' FROM VISITANTE
UNION ALL SELECT 'EXCURSION', COUNT(*), '120-250' FROM EXCURSION
UNION ALL SELECT 'INSCRIPCION', COUNT(*), '800-1500' FROM INSCRIPCION
UNION ALL SELECT 'EVALUACION', COUNT(*), '400-900' FROM EVALUACION
UNION ALL SELECT 'CUENTA (usuarios)', COUNT(*), '40-80' FROM CUENTA;

-- Distribuciones relevantes
SELECT estado_asistencia, COUNT(*) AS n FROM INSCRIPCION GROUP BY estado_asistencia;
SELECT CASE WHEN v.id_recurso IS NOT NULL THEN 'VEGETAL' WHEN a.id_recurso IS NOT NULL THEN 'ANIMAL'
            WHEN m.id_recurso IS NOT NULL THEN 'MINERAL' ELSE 'SIN_CLASIFICAR' END AS tipo, COUNT(*) AS especies
FROM RECURSO_NATURAL r LEFT JOIN VEGETAL v USING (id_recurso) LEFT JOIN ANIMAL a USING (id_recurso)
LEFT JOIN MINERAL m USING (id_recurso) GROUP BY tipo;
SELECT rol, COUNT(*) AS cuentas FROM CUENTA_ROL GROUP BY rol;
SELECT calificacion, COUNT(*) AS n FROM EVALUACION GROUP BY calificacion ORDER BY calificacion;

-- Integridad: personas sin subtipo (especialización total → debe ser 0)
SELECT COUNT(*) AS personas_sin_subtipo FROM PERSONA p
WHERE NOT EXISTS (SELECT 1 FROM TRABAJADOR t WHERE t.rut_persona = p.rut_persona)
  AND NOT EXISTS (SELECT 1 FROM VISITANTE v WHERE v.rut_persona = p.rut_persona);
-- Personas en ambos subtipos (especialización solapada → > 0)
SELECT COUNT(*) AS trabajadores_que_visitan FROM TRABAJADOR t JOIN VISITANTE v USING (rut_persona);
-- Parques sin área o sin región principal (debe ser 0)
SELECT COUNT(*) AS parques_sin_area FROM PARQUE p WHERE NOT EXISTS
  (SELECT 1 FROM AREA a WHERE a.anio_declaracion = p.anio_declaracion AND a.nro_correlativo = p.nro_correlativo);
SELECT COUNT(*) AS parques_sin_region_principal FROM PARQUE p WHERE NOT EXISTS
  (SELECT 1 FROM PARQUE_REGION r WHERE r.anio_declaracion = p.anio_declaracion
     AND r.nro_correlativo = p.nro_correlativo AND r.es_principal);
-- Cuentas sin rol (debe ser 0)
SELECT COUNT(*) AS cuentas_sin_rol FROM CUENTA c WHERE NOT EXISTS (SELECT 1 FROM CUENTA_ROL r WHERE r.id_cuenta = c.id_cuenta);

-- ---------------------------------------------------------------------
-- B. Pruebas NEGATIVAS: cada sentencia DEBE fallar con el error indicado
-- ---------------------------------------------------------------------
-- B1. CHECK calificación 1-5 → ERROR 3819
INSERT INTO EVALUACION VALUES ('EXC0001', 99, (SELECT id_inscripcion FROM INSCRIPCION WHERE codigo_excursion='EXC0001' LIMIT 1), '2026-01-01', 7, NULL);
-- B2. FK: inscripción a excursión inexistente → ERROR 1452
INSERT INTO INSCRIPCION VALUES ('INS999999', (SELECT rut_persona FROM VISITANTE LIMIT 1), 'EXC9999', '2026-01-01', 'INSCRITO', NULL);
-- B3. UNIQUE (visitante, excursión): inscripción duplicada → ERROR 1062
INSERT INTO INSCRIPCION
SELECT 'INS999998', rut_persona, codigo_excursion, fecha_inscripcion, 'INSCRITO', NULL FROM INSCRIPCION LIMIT 1;
-- B4. Trigger de cupo: excursión llena → ERROR 1644 'Excursión sin cupo disponible'
INSERT INTO INSCRIPCION
SELECT 'INS999997', v.rut_persona, x.codigo_excursion, '2024-01-01', 'INSCRITO', NULL
FROM (SELECT e.codigo_excursion FROM EXCURSION e JOIN INSCRIPCION i USING (codigo_excursion)
      GROUP BY e.codigo_excursion, e.capacidad HAVING COUNT(*) >= e.capacidad LIMIT 1) x
JOIN VISITANTE v
WHERE NOT EXISTS (SELECT 1 FROM INSCRIPCION i2 WHERE i2.rut_persona = v.rut_persona AND i2.codigo_excursion = x.codigo_excursion)
LIMIT 1;
-- B5. Trigger: evaluar una inscripción con NO_ASISTIO → ERROR 1644
INSERT INTO EVALUACION
SELECT codigo_excursion, 98, id_inscripcion, CURDATE(), 4, 'prueba'
FROM INSCRIPCION WHERE estado_asistencia = 'NO_ASISTIO' LIMIT 1;
-- B6. Evaluación de otra excursión (FK compuesta C4) → ERROR 1452
INSERT INTO EVALUACION
SELECT 'EXC0002', 97, id_inscripcion, CURDATE(), 4, NULL
FROM INSCRIPCION WHERE codigo_excursion = 'EXC0001' AND estado_asistencia = 'ASISTIO'
  AND id_inscripcion NOT IN (SELECT id_inscripcion FROM EVALUACION) LIMIT 1;
-- B7. Dos regiones principales para un parque → ERROR 1062 (C5)
INSERT INTO PARQUE_REGION (anio_declaracion, nro_correlativo, id_region, porcentaje_territorial, es_principal)
SELECT p.anio_declaracion, p.nro_correlativo, r.id_region, 10, TRUE
FROM PARQUE p JOIN REGION r
WHERE NOT EXISTS (SELECT 1 FROM PARQUE_REGION x WHERE x.anio_declaracion = p.anio_declaracion
                    AND x.nro_correlativo = p.nro_correlativo AND x.id_region = r.id_region)
LIMIT 1;
-- B8. Especialización disjunta: vegetal registrado también como animal → ERROR 1644
INSERT INTO ANIMAL VALUES ((SELECT MIN(id_recurso) FROM VEGETAL), 'HERBIVORO', 'Marzo');
-- B9. Borrar un parque con áreas (ON DELETE RESTRICT) → ERROR 1451
DELETE FROM PARQUE WHERE nombre = 'Torres del Paine';
-- B10. CHECK nivel de acceso → ERROR 3819
UPDATE AREA SET nivel_acceso = 'LIBRE' WHERE nro_area = 1 LIMIT 1;
-- B11. Supervisarse a sí mismo → ERROR 1644
UPDATE TRABAJADOR SET rut_supervisor = rut_persona LIMIT 1;

-- ---------------------------------------------------------------------
-- C. Prueba POSITIVA con reversión (no deja rastro)
-- ---------------------------------------------------------------------
START TRANSACTION;
INSERT INTO INSCRIPCION
SELECT 'INS900000', v.rut_persona, e.codigo_excursion, CURDATE(), 'INSCRITO', 'prueba'
FROM EXCURSION e JOIN VISITANTE v
WHERE e.fecha > CURDATE()
  AND (SELECT COUNT(*) FROM INSCRIPCION i WHERE i.codigo_excursion = e.codigo_excursion) < e.capacidad
  AND NOT EXISTS (SELECT 1 FROM INSCRIPCION i WHERE i.codigo_excursion = e.codigo_excursion AND i.rut_persona = v.rut_persona)
LIMIT 1;
SELECT id_inscripcion, codigo_excursion, estado_asistencia FROM INSCRIPCION WHERE id_inscripcion = 'INS900000';
ROLLBACK;
SELECT COUNT(*) AS debe_ser_0 FROM INSCRIPCION WHERE id_inscripcion = 'INS900000';

-- ---------------------------------------------------------------------
-- D. Sentencias de consulta/ejecución de los 12 requerimientos (evidencia)
-- ---------------------------------------------------------------------
CALL sp_r1_areas_mas_visitantes('2025-01-01', '2025-12-31');
SELECT * FROM vw_r2_distribucion_especies ORDER BY parque, area, tipo_especie;
SELECT * FROM vw_r3_visitantes_vs_evaluacion ORDER BY cantidad_participantes DESC;
CALL sp_r4_parques_excursiones_visitantes('2025-01-01', '2025-12-31');
SELECT * FROM vw_r5_tasa_asistencia_area WHERE inscripciones >= 10 ORDER BY porcentaje_asistencia DESC;
SELECT * FROM vw_r6_especies_mayor_cantidad WHERE ranking_en_area = 1 ORDER BY parque, area;
SELECT * FROM vw_r7_proyectos_participacion ORDER BY investigadores DESC, especies_estudiadas DESC;
SELECT * FROM vw_r8_trabajadores_multifuncion ORDER BY cantidad_funciones DESC, trabajador;
CALL sp_r9_excursiones_sobre_promedio_parque(1959, 1, '2024-01-01', '2026-11-10');   -- Torres del Paine
CALL sp_r9_excursiones_sobre_promedio_parque(NULL, NULL, '2025-01-01', '2025-12-31'); -- todos los parques
CALL sp_r10_especies_sobre_promedio_tipo('ANIMAL');
CALL sp_r10_especies_sobre_promedio_tipo('VEGETAL');
CALL sp_r11_visitantes_destacados('2024-01-01', '2026-11-10');
CALL sp_r12_parques_sobre_promedio_general('2025-01-01', '2025-12-31');
-- Validación de parámetros (debe fallar con mensaje claro)
CALL sp_r1_areas_mas_visitantes('2025-12-31', '2025-01-01');
CALL sp_r10_especies_sobre_promedio_tipo('HONGO');
