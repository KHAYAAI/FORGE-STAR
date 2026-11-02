# Build context is the repo root (see docker-compose.yml) so the shared forgestar package is included.
FROM python:3.12-slim
RUN pip install --no-cache-dir kafka-python==2.0.6 numpy==2.1.3
COPY forgestar /app/forgestar
COPY ground/sandf/sandf.py /app/sandf.py
WORKDIR /app
CMD ["python", "-u", "sandf.py"]
