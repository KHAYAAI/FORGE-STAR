FROM python:3.12-slim
RUN pip install --no-cache-dir kafka-python==2.0.6
COPY simulate.py /app/simulate.py
CMD ["python", "-u", "/app/simulate.py"]
