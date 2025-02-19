# Указываем базовый образ, например, Python 3.9
FROM python:3.9-slim

# Устанавливаем зависимости (предположим, что у нас есть requirements.txt)
WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    libasound2-dev \
    portaudio19-dev \
    python3-dev
  
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект в контейнер
COPY . .

# Открываем порт, если потребуется прямой доступ (например, через Flask/FastAPI)
EXPOSE 8000

# Запускаем файл модели (например, app.py)
CMD ["python", "main.py"]

