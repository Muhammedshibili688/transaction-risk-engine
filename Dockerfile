# syntax=docker/dockerfile:1

FROM python:3.10-slim

# ----------------------------------------------------
# Python Settings
# ----------------------------------------------------

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ----------------------------------------------------
# Working Directory
# ----------------------------------------------------

WORKDIR /app

# ----------------------------------------------------
# System Dependencies
# ----------------------------------------------------

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ----------------------------------------------------
# Python Dependencies
# ----------------------------------------------------

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ----------------------------------------------------
# Copy Project
# ----------------------------------------------------

COPY src ./src
COPY config ./config
COPY models ./models

COPY .env .
COPY simulator.py .
COPY setup.py .
# COPY README.md .

# Optional (only if your project actually uses them at runtime)
COPY dvc.yaml .
COPY dvc.lock .
COPY models.dvc .

# ----------------------------------------------------
# Default Model Path
# ----------------------------------------------------

ENV MODEL_PATH=/app/models/xgboost_baseline.joblib

# ----------------------------------------------------
# Python Module Path
# ----------------------------------------------------

ENV PYTHONPATH=/app

# ----------------------------------------------------
# API Port
# ----------------------------------------------------

EXPOSE 8000

# ----------------------------------------------------
# Default Command
# (Docker Compose will override this for each service)
# ----------------------------------------------------

CMD ["python", "simulator.py"]