#!/usr/bin/env bash
# BORRA y vuelve a crear parques_db desde cero con sql/00_integral.sql (sección 8 del PDF).
source "$(dirname "$0")/_comun.sh"
bash "$RAIZ/scripts/encender_mysql.sh"
echo ">> Ejecutando sql/00_integral.sql ..."
bash "$RAIZ/scripts/mysql_root.sh" < "$RAIZ/sql/00_integral.sql"
bash "$RAIZ/scripts/crear_usuario_app.sh"
bash "$RAIZ/scripts/mysql_root.sh" -t -e "
SELECT 'Tablas' objeto, COUNT(*) n FROM information_schema.tables WHERE table_schema='$DB_NAME' AND table_type='BASE TABLE'
UNION ALL SELECT 'Vistas', COUNT(*) FROM information_schema.views WHERE table_schema='$DB_NAME'
UNION ALL SELECT 'Procedimientos', COUNT(*) FROM information_schema.routines WHERE routine_schema='$DB_NAME'
UNION ALL SELECT 'Triggers', COUNT(*) FROM information_schema.triggers WHERE trigger_schema='$DB_NAME';"
echo ">> Base reconstruida. Esperado: 24 tablas, 6 vistas, 6 procedimientos, 8 triggers."
