FROM python:3.12-slim
RUN pip install --no-cache-dir "fastapi==0.115.6" "uvicorn==0.34.0" "psycopg[binary]==3.2.3"
COPY repo.py app.py /app/
WORKDIR /app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
