# Imagen de la aplicación Streamlit (PMV) · Caso 1 · Grupo 1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 1) Dependencias primero: Docker reutiliza esta capa si solo cambia el código
COPY requirements.txt .
RUN pip install -r requirements.txt

# 2) Código de la aplicación, configuración y generador de datos
COPY app/ ./app/
COPY .streamlit/ ./.streamlit/
COPY scripts/ ./scripts/
COPY tests/ ./tests/

# Usuario sin privilegios
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
