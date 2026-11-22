# Imagen única para la demo en línea (Render): MySQL 8 + PMV Streamlit en un solo contenedor.
# El despliegue oficial del proyecto sigue siendo docker-compose.yml; esta imagen solo
# existe porque el hosting gratuito ejecuta un contenedor por servicio.
FROM mysql:8.0

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=America/Santiago \
    DB_HOST=127.0.0.1 \
    DB_PORT=3306 \
    DB_NAME=parques_db

RUN microdnf install -y python3.11 python3.11-pip && microdnf clean all

WORKDIR /app
COPY requirements.txt .
RUN grep -v -E "^(pytest|Faker)" requirements.txt > req_demo.txt \
 && python3.11 -m pip install -r req_demo.txt

COPY app/ ./app/
COPY .streamlit/ ./.streamlit/
COPY sql/00_integral.sql ./sql/00_integral.sql
COPY deploy/render/iniciar.sh /usr/local/bin/iniciar.sh
RUN chmod +x /usr/local/bin/iniciar.sh

EXPOSE 10000
ENTRYPOINT ["/usr/local/bin/iniciar.sh"]
