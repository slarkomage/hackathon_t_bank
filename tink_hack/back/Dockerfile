FROM python:3.9-slim

WORKDIR /app

COPY req.txt req.txt
RUN pip install --no-cache-dir -r req.txt
RUN pip install psycopg2-binary sqlalchemy-utils

COPY . .

# Создаем директорию shared
RUN mkdir -p /app/shared

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
