"""
Construye sql/00_integral.sql concatenando, en el orden exigido por la
sección 8 del enunciado:
  1-3. 01_estructura.sql  (BD, tablas, restricciones, claves, triggers)
  4.   02_datos.sql       (inserción de los datos generados)
  5.   03_vistas.sql      (6 vistas)
  6.   04_procedimientos.sql (6 procedimientos)

Uso:  python scripts/generar_datos.py && python scripts/construir_integral.py
"""
from pathlib import Path

SQL = Path(__file__).resolve().parent.parent / "sql"
PARTES = ["01_estructura.sql", "02_datos.sql", "03_vistas.sql", "04_procedimientos.sql"]


def main() -> None:
    salida = SQL / "00_integral.sql"
    trozos = [
        "-- =====================================================================\n"
        "-- 00_integral.sql · SCRIPT INTEGRAL · Caso 1 · Grupo 1 · TDFI103 Fase 2\n"
        "-- Reconstruye la base parques_db desde cero: BD, tablas, restricciones,\n"
        "-- datos, 6 vistas y 6 procedimientos. Generado por scripts/construir_integral.py\n"
        "-- Ejecutar:  mysql -u root -p < sql/00_integral.sql   (o abrir en Workbench)\n"
        "-- =====================================================================\n"
        "SET NAMES utf8mb4;\n"
    ]
    for parte in PARTES:
        contenido = (SQL / parte).read_text(encoding="utf-8")
        trozos.append(f"\n-- >>>>>>>>>>>>>>>>>>>> INICIO {parte} >>>>>>>>>>>>>>>>>>>>\n")
        trozos.append(contenido)
        trozos.append(f"\n-- <<<<<<<<<<<<<<<<<<<< FIN {parte} <<<<<<<<<<<<<<<<<<<<\n")
    salida.write_text("".join(trozos), encoding="utf-8")
    print(f"Escrito {salida} ({salida.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
