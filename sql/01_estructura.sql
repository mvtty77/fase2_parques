-- =====================================================================
-- TDFI103 · Proyecto Semestral 2026 · Fase 2 · Caso 1 · Grupo 1
-- Sistema Integral de Gestión de Parques Naturales y Conservación Ambiental
-- 01_estructura.sql : base de datos, tablas, PK, FK, NOT NULL, UNIQUE,
--                     CHECK y triggers de reglas de negocio (MySQL 8.x)
-- =====================================================================
-- Modelo de Fase 1 (23 tablas) + correcciones de Fase 2 (ver docs/mere):
--   C1. ASIGNACION_TRABAJADOR: vincula cada función del trabajador con
--       el área (y por ende el parque) donde la ejerce. Necesaria para R8.
--   C2. CUENTA: se agregan usuario (UNIQUE), password_hash y fecha_creacion
--       para el inicio de sesión del PMV.
--   C3. PARQUE.activo y RECURSO_NATURAL.activo: desactivación lógica en el CRUD.
--   C4. EVALUACION referencia (id_inscripcion, codigo_excursion) de INSCRIPCION:
--       garantiza que la evaluación corresponde a la misma excursión.
--   C5. PARQUE_REGION.principal_unica: columna generada + UNIQUE que impide
--       más de una región principal por parque (regla 5).
--   C6. Triggers: cupo de excursión, evaluación solo con asistencia, fechas
--       coherentes y especialización disjunta de RECURSO_NATURAL (regla 16).
-- =====================================================================

DROP DATABASE IF EXISTS parques_db;
CREATE DATABASE parques_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_spanish_ci;
USE parques_db;

SET NAMES utf8mb4;

-- ---------------------------------------------------------------------
-- PERSONAS, TRABAJADORES, VISITANTES Y CUENTAS
-- ---------------------------------------------------------------------
CREATE TABLE PERSONA (
  rut_persona       VARCHAR(12)  NOT NULL,
  nombres           VARCHAR(80)  NOT NULL,
  apellido_paterno  VARCHAR(50)  NOT NULL,
  apellido_materno  VARCHAR(50)  NULL,
  correo            VARCHAR(120) NULL,
  nacionalidad      VARCHAR(40)  NOT NULL,
  CONSTRAINT pk_persona PRIMARY KEY (rut_persona),
  CONSTRAINT uq_persona_correo UNIQUE (correo),
  CONSTRAINT ck_persona_rut CHECK (rut_persona REGEXP '^[0-9]{7,8}-[0-9K]$'),
  CONSTRAINT ck_persona_correo CHECK (correo IS NULL OR correo LIKE '%_@_%._%')
) ENGINE=InnoDB;

CREATE TABLE PERSONA_TELEFONO (
  rut_persona VARCHAR(12) NOT NULL,
  telefono    VARCHAR(15) NOT NULL,
  CONSTRAINT pk_persona_telefono PRIMARY KEY (rut_persona, telefono),
  CONSTRAINT fk_tel_persona FOREIGN KEY (rut_persona)
    REFERENCES PERSONA (rut_persona) ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT ck_telefono CHECK (telefono REGEXP '^\\+?[0-9]{8,14}$')
) ENGINE=InnoDB;

CREATE TABLE TRABAJADOR (
  rut_persona    VARCHAR(12) NOT NULL,
  fecha_ingreso  DATE        NOT NULL,
  cargo          VARCHAR(60) NOT NULL,
  rut_supervisor VARCHAR(12) NULL,
  CONSTRAINT pk_trabajador PRIMARY KEY (rut_persona),
  CONSTRAINT fk_trab_persona FOREIGN KEY (rut_persona)
    REFERENCES PERSONA (rut_persona) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_trab_supervisor FOREIGN KEY (rut_supervisor)
    REFERENCES TRABAJADOR (rut_persona) ON UPDATE CASCADE ON DELETE SET NULL
  -- La regla "nadie se supervisa a sí mismo" se valida en trg_trab_supervisor_bi/bu:
  -- MySQL no admite CHECK sobre columnas con acciones referenciales (error 3823).
) ENGINE=InnoDB;

CREATE TABLE TRABAJADOR_FUNCION (
  rut_persona VARCHAR(12) NOT NULL,
  funcion     VARCHAR(20) NOT NULL,
  CONSTRAINT pk_trabajador_funcion PRIMARY KEY (rut_persona, funcion),
  CONSTRAINT fk_tf_trabajador FOREIGN KEY (rut_persona)
    REFERENCES TRABAJADOR (rut_persona) ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT ck_tf_funcion CHECK (funcion IN ('GESTION','VIGILANCIA','CONSERVACION','INVESTIGACION','GUIA'))
) ENGINE=InnoDB;

CREATE TABLE VISITANTE (
  rut_persona    VARCHAR(12) NOT NULL,
  fecha_registro DATE        NOT NULL,
  CONSTRAINT pk_visitante PRIMARY KEY (rut_persona),
  CONSTRAINT fk_vis_persona FOREIGN KEY (rut_persona)
    REFERENCES PERSONA (rut_persona) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE CUENTA (
  id_cuenta      INT          NOT NULL AUTO_INCREMENT,
  rut_persona    VARCHAR(12)  NOT NULL,
  usuario        VARCHAR(40)  NOT NULL,
  password_hash  VARCHAR(200) NOT NULL,
  activa         BOOLEAN      NOT NULL DEFAULT TRUE,
  fecha_creacion DATE         NOT NULL,
  CONSTRAINT pk_cuenta PRIMARY KEY (id_cuenta),
  CONSTRAINT uq_cuenta_rut UNIQUE (rut_persona),
  CONSTRAINT uq_cuenta_usuario UNIQUE (usuario),
  CONSTRAINT fk_cuenta_trabajador FOREIGN KEY (rut_persona)
    REFERENCES TRABAJADOR (rut_persona) ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT ck_cuenta_usuario CHECK (CHAR_LENGTH(usuario) >= 4)
) ENGINE=InnoDB;

CREATE TABLE CUENTA_ROL (
  id_cuenta INT         NOT NULL,
  rol       VARCHAR(20) NOT NULL,
  CONSTRAINT pk_cuenta_rol PRIMARY KEY (id_cuenta, rol),
  CONSTRAINT fk_cr_cuenta FOREIGN KEY (id_cuenta)
    REFERENCES CUENTA (id_cuenta) ON DELETE CASCADE,
  CONSTRAINT ck_cr_rol CHECK (rol IN ('ADMINISTRADOR','OPERADOR','ANALISTA'))
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- TERRITORIO: REGION (comunidad administradora), PARQUE, AREA
-- ---------------------------------------------------------------------
CREATE TABLE REGION (
  id_region INT         NOT NULL AUTO_INCREMENT,
  nombre    VARCHAR(60) NOT NULL,
  macrozona VARCHAR(20) NULL,
  CONSTRAINT pk_region PRIMARY KEY (id_region),
  CONSTRAINT uq_region_nombre UNIQUE (nombre),
  CONSTRAINT ck_region_macrozona CHECK (macrozona IS NULL OR macrozona IN ('NORTE','CENTRO','SUR','AUSTRAL'))
) ENGINE=InnoDB;

CREATE TABLE PARQUE (
  anio_declaracion      SMALLINT      NOT NULL,
  nro_correlativo       SMALLINT      NOT NULL,
  nombre                VARCHAR(80)   NOT NULL,
  fecha_declaracion     DATE          NOT NULL,
  superficie_total      DECIMAL(12,2) NOT NULL,
  presupuesto_anual     DECIMAL(14,2) NOT NULL,
  estado_conservacion   VARCHAR(15)   NOT NULL,
  categoria_snap        VARCHAR(40)   NOT NULL,
  organismo_responsable VARCHAR(80)   NOT NULL,
  activo                BOOLEAN       NOT NULL DEFAULT TRUE,
  CONSTRAINT pk_parque PRIMARY KEY (anio_declaracion, nro_correlativo),
  CONSTRAINT uq_parque_nombre UNIQUE (nombre),
  CONSTRAINT ck_parque_anio CHECK (anio_declaracion BETWEEN 1900 AND 2100),
  CONSTRAINT ck_parque_correlativo CHECK (nro_correlativo > 0),
  CONSTRAINT ck_parque_anio_fecha CHECK (YEAR(fecha_declaracion) = anio_declaracion),
  CONSTRAINT ck_parque_superficie CHECK (superficie_total > 0),
  CONSTRAINT ck_parque_presupuesto CHECK (presupuesto_anual >= 0),
  CONSTRAINT ck_parque_estado CHECK (estado_conservacion IN ('BUENO','REGULAR','CRITICO')),
  CONSTRAINT ck_parque_categoria CHECK (categoria_snap IN ('PARQUE NACIONAL','RESERVA NACIONAL','MONUMENTO NATURAL','SANTUARIO DE LA NATURALEZA'))
) ENGINE=InnoDB;

CREATE TABLE PARQUE_REGION (
  anio_declaracion       SMALLINT     NOT NULL,
  nro_correlativo        SMALLINT     NOT NULL,
  id_region              INT          NOT NULL,
  porcentaje_territorial DECIMAL(5,2) NOT NULL,
  es_principal           BOOLEAN      NOT NULL DEFAULT FALSE,
  -- C5: vale 1 solo para la fila principal; NULL en las demás (UNIQUE admite varios NULL)
  principal_unica        TINYINT AS (IF(es_principal, 1, NULL)) STORED,
  CONSTRAINT pk_parque_region PRIMARY KEY (anio_declaracion, nro_correlativo, id_region),
  CONSTRAINT uq_parque_region_principal UNIQUE (anio_declaracion, nro_correlativo, principal_unica),
  CONSTRAINT fk_pr_parque FOREIGN KEY (anio_declaracion, nro_correlativo)
    REFERENCES PARQUE (anio_declaracion, nro_correlativo) ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_pr_region FOREIGN KEY (id_region)
    REFERENCES REGION (id_region) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT ck_pr_porcentaje CHECK (porcentaje_territorial > 0 AND porcentaje_territorial <= 100)
) ENGINE=InnoDB;

CREATE TABLE AREA (
  anio_declaracion SMALLINT      NOT NULL,
  nro_correlativo  SMALLINT      NOT NULL,
  nro_area         SMALLINT      NOT NULL,
  nombre           VARCHAR(80)   NOT NULL,
  extension        DECIMAL(10,2) NOT NULL,
  nivel_acceso     VARCHAR(15)   NOT NULL,
  estado_operativo VARCHAR(15)   NOT NULL,
  CONSTRAINT pk_area PRIMARY KEY (anio_declaracion, nro_correlativo, nro_area),
  CONSTRAINT uq_area_nombre_parque UNIQUE (anio_declaracion, nro_correlativo, nombre),
  CONSTRAINT fk_area_parque FOREIGN KEY (anio_declaracion, nro_correlativo)
    REFERENCES PARQUE (anio_declaracion, nro_correlativo) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT ck_area_nro CHECK (nro_area > 0),
  CONSTRAINT ck_area_extension CHECK (extension > 0),
  CONSTRAINT ck_area_acceso CHECK (nivel_acceso IN ('PUBLICO','RESTRINGIDO','PROTEGIDO')),
  CONSTRAINT ck_area_estado CHECK (estado_operativo IN ('OPERATIVA','MANTENCION','CERRADA'))
) ENGINE=InnoDB;

CREATE TABLE ASIGNACION_TRABAJADOR (            -- C1 (corrección Fase 2)
  rut_persona      VARCHAR(12) NOT NULL,
  funcion          VARCHAR(20) NOT NULL,
  anio_declaracion SMALLINT    NOT NULL,
  nro_correlativo  SMALLINT    NOT NULL,
  nro_area         SMALLINT    NOT NULL,
  fecha_inicio     DATE        NOT NULL,
  CONSTRAINT pk_asignacion PRIMARY KEY (rut_persona, funcion, anio_declaracion, nro_correlativo, nro_area),
  CONSTRAINT fk_asig_funcion FOREIGN KEY (rut_persona, funcion)
    REFERENCES TRABAJADOR_FUNCION (rut_persona, funcion) ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_asig_area FOREIGN KEY (anio_declaracion, nro_correlativo, nro_area)
    REFERENCES AREA (anio_declaracion, nro_correlativo, nro_area) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- EXCURSIONES, INSCRIPCIONES Y EVALUACIONES
-- ---------------------------------------------------------------------
CREATE TABLE EXCURSION (
  codigo_excursion VARCHAR(10) NOT NULL,
  fecha            DATE        NOT NULL,
  horario          TIME        NOT NULL,
  modalidad        VARCHAR(15) NOT NULL,
  capacidad        SMALLINT    NOT NULL,
  anio_declaracion SMALLINT    NOT NULL,
  nro_correlativo  SMALLINT    NOT NULL,
  nro_area         SMALLINT    NOT NULL,
  CONSTRAINT pk_excursion PRIMARY KEY (codigo_excursion),
  CONSTRAINT fk_exc_area FOREIGN KEY (anio_declaracion, nro_correlativo, nro_area)
    REFERENCES AREA (anio_declaracion, nro_correlativo, nro_area) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT ck_exc_codigo CHECK (codigo_excursion REGEXP '^EXC[0-9]{4}$'),
  CONSTRAINT ck_exc_modalidad CHECK (modalidad IN ('GUIADA','AUTOGUIADA','EDUCATIVA','NOCTURNA')),
  CONSTRAINT ck_exc_capacidad CHECK (capacidad BETWEEN 1 AND 60),
  CONSTRAINT ck_exc_horario CHECK (horario BETWEEN '06:00:00' AND '22:00:00')
) ENGINE=InnoDB;

CREATE INDEX ix_exc_fecha ON EXCURSION (fecha);

CREATE TABLE INSCRIPCION (
  id_inscripcion    VARCHAR(10)  NOT NULL,
  rut_persona       VARCHAR(12)  NOT NULL,
  codigo_excursion  VARCHAR(10)  NOT NULL,
  fecha_inscripcion DATE         NOT NULL,
  estado_asistencia VARCHAR(12)  NOT NULL DEFAULT 'INSCRITO',
  observaciones     VARCHAR(200) NULL,
  CONSTRAINT pk_inscripcion PRIMARY KEY (id_inscripcion),
  CONSTRAINT uq_insc_visitante_excursion UNIQUE (rut_persona, codigo_excursion),   -- regla 7
  CONSTRAINT uq_insc_id_excursion UNIQUE (id_inscripcion, codigo_excursion),        -- soporta C4
  CONSTRAINT fk_insc_visitante FOREIGN KEY (rut_persona)
    REFERENCES VISITANTE (rut_persona) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_insc_excursion FOREIGN KEY (codigo_excursion)
    REFERENCES EXCURSION (codigo_excursion) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT ck_insc_id CHECK (id_inscripcion REGEXP '^INS[0-9]{6}$'),
  CONSTRAINT ck_insc_estado CHECK (estado_asistencia IN ('INSCRITO','ASISTIO','NO_ASISTIO'))
) ENGINE=InnoDB;

CREATE TABLE EVALUACION (
  codigo_excursion VARCHAR(10)  NOT NULL,
  nro_evaluacion   SMALLINT     NOT NULL,
  id_inscripcion   VARCHAR(10)  NOT NULL,
  fecha_evaluacion DATE         NOT NULL,
  calificacion     TINYINT      NOT NULL,
  comentario       VARCHAR(250) NULL,
  CONSTRAINT pk_evaluacion PRIMARY KEY (codigo_excursion, nro_evaluacion),
  CONSTRAINT uq_eval_inscripcion UNIQUE (id_inscripcion),                          -- regla 9
  CONSTRAINT fk_eval_excursion FOREIGN KEY (codigo_excursion)
    REFERENCES EXCURSION (codigo_excursion) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_eval_inscripcion FOREIGN KEY (id_inscripcion, codigo_excursion)    -- C4
    REFERENCES INSCRIPCION (id_inscripcion, codigo_excursion) ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT ck_eval_nro CHECK (nro_evaluacion > 0),
  CONSTRAINT ck_eval_calificacion CHECK (calificacion BETWEEN 1 AND 5)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- RECURSOS NATURALES (especies) Y ESPECIALIZACIÓN PARCIAL/DISJUNTA
-- ---------------------------------------------------------------------
CREATE TABLE RECURSO_NATURAL (
  id_recurso          INT          NOT NULL AUTO_INCREMENT,
  nombre_cientifico   VARCHAR(100) NOT NULL,
  nombre_comun        VARCHAR(80)  NOT NULL,
  estado_conservacion VARCHAR(10)  NOT NULL,
  fecha_incorporacion DATE         NOT NULL,
  origen              VARCHAR(15)  NOT NULL,
  descripcion         VARCHAR(250) NULL,
  activo              BOOLEAN      NOT NULL DEFAULT TRUE,
  CONSTRAINT pk_recurso PRIMARY KEY (id_recurso),
  CONSTRAINT uq_recurso_cientifico UNIQUE (nombre_cientifico),
  CONSTRAINT ck_rec_estado CHECK (estado_conservacion IN ('LC','NT','VU','EN','CR','NO_APLICA')),
  CONSTRAINT ck_rec_origen CHECK (origen IN ('NATIVO','ENDEMICO','INTRODUCIDO','GEOLOGICO'))
) ENGINE=InnoDB;

CREATE TABLE VEGETAL (
  id_recurso        INT         NOT NULL,
  periodo_floracion VARCHAR(30) NOT NULL,
  tipo_vegetacion   VARCHAR(20) NOT NULL,
  CONSTRAINT pk_vegetal PRIMARY KEY (id_recurso),
  CONSTRAINT fk_veg_recurso FOREIGN KEY (id_recurso)
    REFERENCES RECURSO_NATURAL (id_recurso) ON DELETE CASCADE,
  CONSTRAINT ck_veg_tipo CHECK (tipo_vegetacion IN ('ARBOL','ARBUSTO','HIERBA','HELECHO','CACTACEA','TREPADORA'))
) ENGINE=InnoDB;

CREATE TABLE ANIMAL (
  id_recurso        INT         NOT NULL,
  tipo_alimentacion VARCHAR(15) NOT NULL,
  periodo_celo      VARCHAR(30) NOT NULL,
  CONSTRAINT pk_animal PRIMARY KEY (id_recurso),
  CONSTRAINT fk_ani_recurso FOREIGN KEY (id_recurso)
    REFERENCES RECURSO_NATURAL (id_recurso) ON DELETE CASCADE,
  CONSTRAINT ck_ani_alim CHECK (tipo_alimentacion IN ('HERBIVORO','CARNIVORO','OMNIVORO','INSECTIVORO','CARRONERO','PISCIVORO'))
) ENGINE=InnoDB;

CREATE TABLE MINERAL (
  id_recurso    INT          NOT NULL,
  tipo_material VARCHAR(20)  NOT NULL,
  composicion   VARCHAR(60)  NOT NULL,
  dureza_mohs   DECIMAL(3,1) NOT NULL,
  CONSTRAINT pk_mineral PRIMARY KEY (id_recurso),
  CONSTRAINT fk_min_recurso FOREIGN KEY (id_recurso)
    REFERENCES RECURSO_NATURAL (id_recurso) ON DELETE CASCADE,
  CONSTRAINT ck_min_dureza CHECK (dureza_mohs BETWEEN 1 AND 10)
) ENGINE=InnoDB;

CREATE TABLE INVENTARIO_RECURSO (
  anio_declaracion       SMALLINT     NOT NULL,
  nro_correlativo        SMALLINT     NOT NULL,
  nro_area               SMALLINT     NOT NULL,
  id_recurso             INT          NOT NULL,
  cantidad_inventariada  INT          NOT NULL,
  fecha_ultimo_monitoreo DATE         NULL,
  observaciones          VARCHAR(200) NULL,
  CONSTRAINT pk_inventario PRIMARY KEY (anio_declaracion, nro_correlativo, nro_area, id_recurso),
  CONSTRAINT fk_inv_area FOREIGN KEY (anio_declaracion, nro_correlativo, nro_area)
    REFERENCES AREA (anio_declaracion, nro_correlativo, nro_area) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_inv_recurso FOREIGN KEY (id_recurso)
    REFERENCES RECURSO_NATURAL (id_recurso) ON DELETE RESTRICT,
  CONSTRAINT ck_inv_cantidad CHECK (cantidad_inventariada >= 0)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- PROYECTOS CIENTÍFICOS
-- ---------------------------------------------------------------------
CREATE TABLE PROYECTO_CIENTIFICO (
  id_proyecto  INT          NOT NULL AUTO_INCREMENT,
  nombre       VARCHAR(120) NOT NULL,
  objetivo     VARCHAR(250) NOT NULL,
  fecha_inicio DATE         NOT NULL,
  fecha_fin    DATE         NULL,
  estado       VARCHAR(15)  NOT NULL,
  CONSTRAINT pk_proyecto PRIMARY KEY (id_proyecto),
  CONSTRAINT uq_proyecto_nombre UNIQUE (nombre),
  CONSTRAINT ck_proy_estado CHECK (estado IN ('PLANIFICADO','EN_CURSO','FINALIZADO','SUSPENDIDO')),
  CONSTRAINT ck_proy_fechas CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_inicio)
) ENGINE=InnoDB;

CREATE TABLE PARTICIPA_PROYECTO (
  rut_persona VARCHAR(12) NOT NULL,
  id_proyecto INT         NOT NULL,
  CONSTRAINT pk_participa PRIMARY KEY (rut_persona, id_proyecto),
  CONSTRAINT fk_part_trabajador FOREIGN KEY (rut_persona)
    REFERENCES TRABAJADOR (rut_persona) ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_part_proyecto FOREIGN KEY (id_proyecto)
    REFERENCES PROYECTO_CIENTIFICO (id_proyecto) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE ESTUDIA (
  id_proyecto      INT      NOT NULL,
  anio_declaracion SMALLINT NOT NULL,
  nro_correlativo  SMALLINT NOT NULL,
  nro_area         SMALLINT NOT NULL,
  CONSTRAINT pk_estudia PRIMARY KEY (id_proyecto, anio_declaracion, nro_correlativo, nro_area),
  CONSTRAINT fk_est_proyecto FOREIGN KEY (id_proyecto)
    REFERENCES PROYECTO_CIENTIFICO (id_proyecto) ON DELETE CASCADE,
  CONSTRAINT fk_est_area FOREIGN KEY (anio_declaracion, nro_correlativo, nro_area)
    REFERENCES AREA (anio_declaracion, nro_correlativo, nro_area) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE INVESTIGA (
  id_proyecto INT NOT NULL,
  id_recurso  INT NOT NULL,
  CONSTRAINT pk_investiga PRIMARY KEY (id_proyecto, id_recurso),
  CONSTRAINT fk_inv_proyecto FOREIGN KEY (id_proyecto)
    REFERENCES PROYECTO_CIENTIFICO (id_proyecto) ON DELETE CASCADE,
  CONSTRAINT fk_investiga_recurso FOREIGN KEY (id_recurso)
    REFERENCES RECURSO_NATURAL (id_recurso) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- TRIGGERS DE REGLAS DE NEGOCIO (C6)
-- ---------------------------------------------------------------------
DELIMITER $$

-- Cupo: no se aceptan más inscripciones que la capacidad de la excursión
CREATE TRIGGER trg_insc_cupo_bi BEFORE INSERT ON INSCRIPCION
FOR EACH ROW
BEGIN
  DECLARE v_cap INT;
  DECLARE v_ocupados INT;
  DECLARE v_fecha DATE;
  SELECT capacidad, fecha INTO v_cap, v_fecha
    FROM EXCURSION WHERE codigo_excursion = NEW.codigo_excursion;
  SELECT COUNT(*) INTO v_ocupados
    FROM INSCRIPCION WHERE codigo_excursion = NEW.codigo_excursion;
  IF v_ocupados >= v_cap THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Excursión sin cupo disponible';
  END IF;
  IF NEW.fecha_inscripcion > v_fecha THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La inscripción debe ser anterior o igual a la fecha de la excursión';
  END IF;
  IF NEW.estado_asistencia <> 'INSCRITO' AND v_fecha > CURDATE() THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No se puede registrar asistencia de una excursión futura';
  END IF;
END$$

CREATE TRIGGER trg_insc_estado_bu BEFORE UPDATE ON INSCRIPCION
FOR EACH ROW
BEGIN
  DECLARE v_fecha DATE;
  SELECT fecha INTO v_fecha FROM EXCURSION WHERE codigo_excursion = NEW.codigo_excursion;
  IF NEW.estado_asistencia <> 'INSCRITO' AND v_fecha > CURDATE() THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No se puede registrar asistencia de una excursión futura';
  END IF;
  IF NEW.estado_asistencia <> 'ASISTIO'
     AND EXISTS (SELECT 1 FROM EVALUACION WHERE id_inscripcion = NEW.id_inscripcion) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La inscripción tiene evaluación: debe mantener estado ASISTIO';
  END IF;
END$$

-- Evaluación: solo de inscripciones con asistencia y con fecha >= excursión
CREATE TRIGGER trg_eval_bi BEFORE INSERT ON EVALUACION
FOR EACH ROW
BEGIN
  DECLARE v_estado VARCHAR(12);
  DECLARE v_fecha DATE;
  SELECT i.estado_asistencia, e.fecha INTO v_estado, v_fecha
    FROM INSCRIPCION i JOIN EXCURSION e ON e.codigo_excursion = i.codigo_excursion
   WHERE i.id_inscripcion = NEW.id_inscripcion;
  IF v_estado IS NULL OR v_estado <> 'ASISTIO' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Solo se evalúan inscripciones con asistencia (ASISTIO)';
  END IF;
  IF NEW.fecha_evaluacion < v_fecha THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La evaluación no puede ser anterior a la excursión';
  END IF;
END$$

-- Especialización disjunta de RECURSO_NATURAL (regla 16)
CREATE TRIGGER trg_vegetal_disjunto BEFORE INSERT ON VEGETAL
FOR EACH ROW
BEGIN
  IF EXISTS (SELECT 1 FROM ANIMAL WHERE id_recurso = NEW.id_recurso)
     OR EXISTS (SELECT 1 FROM MINERAL WHERE id_recurso = NEW.id_recurso) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Especialización disjunta: el recurso ya pertenece a otro subtipo';
  END IF;
END$$

CREATE TRIGGER trg_animal_disjunto BEFORE INSERT ON ANIMAL
FOR EACH ROW
BEGIN
  IF EXISTS (SELECT 1 FROM VEGETAL WHERE id_recurso = NEW.id_recurso)
     OR EXISTS (SELECT 1 FROM MINERAL WHERE id_recurso = NEW.id_recurso) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Especialización disjunta: el recurso ya pertenece a otro subtipo';
  END IF;
END$$

CREATE TRIGGER trg_mineral_disjunto BEFORE INSERT ON MINERAL
FOR EACH ROW
BEGIN
  IF EXISTS (SELECT 1 FROM VEGETAL WHERE id_recurso = NEW.id_recurso)
     OR EXISTS (SELECT 1 FROM ANIMAL WHERE id_recurso = NEW.id_recurso) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Especialización disjunta: el recurso ya pertenece a otro subtipo';
  END IF;
END$$

-- Supervisión: nadie se supervisa a sí mismo ni hay ciclo directo (A↔B)
CREATE TRIGGER trg_trab_supervisor_bi BEFORE INSERT ON TRABAJADOR
FOR EACH ROW
BEGIN
  IF NEW.rut_supervisor = NEW.rut_persona THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Un trabajador no puede supervisarse a sí mismo';
  END IF;
  IF NEW.rut_supervisor IS NOT NULL AND EXISTS (
       SELECT 1 FROM TRABAJADOR WHERE rut_persona = NEW.rut_supervisor
                                  AND rut_supervisor = NEW.rut_persona) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ciclo de supervisión no permitido';
  END IF;
END$$

CREATE TRIGGER trg_trab_supervisor_bu BEFORE UPDATE ON TRABAJADOR
FOR EACH ROW
BEGIN
  IF NEW.rut_supervisor = NEW.rut_persona THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Un trabajador no puede supervisarse a sí mismo';
  END IF;
END$$

DELIMITER ;
