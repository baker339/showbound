FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Alembic migrations will be run via entrypoint script
COPY ./alembic.ini ./

# Entrypoint script
COPY ./scripts/docker_backend_entrypoint.sh /docker_backend_entrypoint.sh
RUN chmod +x /docker_backend_entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/docker_backend_entrypoint.sh"] 