-- =====================================================================
-- 06_requerimientos_R1_R12.sql · UNA sentencia por requerimiento
-- Úselo para las CAPTURAS de MySQL Workbench (secciones 5 y 7 del PDF):
--   1) doble clic en parques_db (o ejecute la línea USE)
--   2) cursor sobre una sentencia + Ctrl+Enter
--   3) captura donde se vean la sentencia y la grilla de resultados
-- En el Codespace: SQLTools (clic en 'Run on active connection') o
--   bash scripts/consola_mysql.sh < sql/06_requerimientos_R1_R12.sql
-- =====================================================================
USE parques_db;

-- R1 · Áreas con más visitantes en un período (procedimiento, parámetros: fechas)
CALL sp_r1_areas_mas_visitantes('2025-01-01', '2025-12-31');

-- R2 · Distribución de especies vegetales/animales/minerales por parque y área (vista)
SELECT * FROM vw_r2_distribucion_especies ORDER BY parque, area, tipo_especie;

-- R3 · Visitantes por excursión vs. evaluación promedio (vista)
SELECT * FROM vw_r3_visitantes_vs_evaluacion ORDER BY cantidad_participantes DESC;

-- R4 · Parques con más excursiones y visitantes en un período (procedimiento)
CALL sp_r4_parques_excursiones_visitantes('2025-01-01', '2025-12-31');

-- R5 · Áreas con mayor tasa de asistencia (vista)
SELECT * FROM vw_r5_tasa_asistencia_area WHERE inscripciones >= 10 ORDER BY porcentaje_asistencia DESC;

-- R6 · Especies con mayor cantidad inventariada por parque y área (vista)
SELECT * FROM vw_r6_especies_mayor_cantidad WHERE ranking_en_area = 1 ORDER BY parque, area;

-- R7 · Proyectos con más investigadores y especies (vista)
SELECT * FROM vw_r7_proyectos_participacion ORDER BY investigadores DESC, especies_estudiadas DESC;

-- R8 · Trabajadores con más de una función y dónde la ejercen (vista)
SELECT * FROM vw_r8_trabajadores_multifuncion ORDER BY cantidad_funciones DESC, trabajador;

-- R9 · Excursiones sobre el promedio de su parque (procedimiento, subconsulta correlacionada)
CALL sp_r9_excursiones_sobre_promedio_parque(1959, 1, '2024-01-01', '2026-11-10');   -- 1959-1 = Torres del Paine

-- R10 · Especies sobre el promedio de su tipo (procedimiento, parámetro: tipo)
CALL sp_r10_especies_sobre_promedio_tipo('ANIMAL');

-- R11 · Visitantes destacados (procedimiento, parámetros: fechas)
CALL sp_r11_visitantes_destacados('2024-01-01', '2026-11-10');

-- R12 · Parques sobre el promedio general de visitantes por excursión (procedimiento)
CALL sp_r12_parques_sobre_promedio_general('2025-01-01', '2025-12-31');
