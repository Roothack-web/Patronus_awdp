# ============================================================
# 砺剑AWDp — Platform Dockerfile
# ============================================================
FROM python:3.11-slim

WORKDIR /app

# Install Docker CLI (for managing challenge containers via host socket)
RUN apt-get update && apt-get install -y \
    curl \
    docker.io \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source (exclude large/unnecessary dirs via .dockerignore)
COPY app/ app/
COPY templates/ templates/
COPY static/ static/
COPY challenges/ challenges/
COPY config.py run.py seed.py evaluate_defense.py ./
COPY instance/ instance/

# Ensure uploads directory exists
RUN mkdir -p instance/uploads

EXPOSE 5000

CMD ["sh", "-c", "python run.py init-db && python run.py run"]
