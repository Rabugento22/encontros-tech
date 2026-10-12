FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependências primeiro, para aproveitar o cache de camadas
COPY requirements.txt .
RUN pip install -r requirements.txt

# Usuário não-root
RUN useradd --system --create-home --uid 1000 appuser

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

# 1 worker + threads: a app cria as tabelas no import e as métricas Prometheus
# não estão configuradas para multiprocess, então múltiplos workers causariam
# corrida no create_all e métricas inconsistentes.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "main:app"]
