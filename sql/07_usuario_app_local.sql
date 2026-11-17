-- =====================================================================
-- 07_usuario_app_local.sql · SOLO para el PC con MySQL + Workbench
-- Ejecutar como root DESPUÉS de 00_integral.sql. Crea el usuario que usa
-- la aplicación (mismos datos que .env.example). Si cambia la contraseña
-- aquí, cámbiela también en el archivo .env de su PC.
-- (En el Codespace esto lo hace solo scripts/crear_usuario_app.sh)
-- =====================================================================
CREATE USER IF NOT EXISTS 'parques_app'@'localhost' IDENTIFIED BY 'AppDemo2026';
GRANT ALL PRIVILEGES ON parques_db.* TO 'parques_app'@'localhost';
FLUSH PRIVILEGES;
SHOW GRANTS FOR 'parques_app'@'localhost';
