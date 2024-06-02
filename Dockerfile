# Используем базовый образ Python
FROM python:3.9-slim

# Устанавливаем зависимости
RUN apt-get update && apt-get install -y ffmpeg libavcodec-extra

# Создаем рабочую директорию
WORKDIR /app

# Копируем файлы requirements.txt и bot.py в контейнер
COPY requirements.txt requirements.txt
COPY bot.py bot.py

# Устанавливаем зависимости Python
RUN pip install --no-cache-dir -r requirements.txt

# Запуск бота
CMD ["python", "bot.py"]
