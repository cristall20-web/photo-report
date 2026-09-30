# Python 3.12 — та же версия, что у вас локально
FROM python:3.12-slim

# Устанавливаем LibreOffice (для конвертации Word → PDF в Linux)
# и шрифты (для корректного отображения кириллицы)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-writer \
    fonts-liberation \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория внутри контейнера
WORKDIR /app

# Копируем список зависимостей и устанавливаем
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаём папки для данных
RUN mkdir -p uploads reports

# Открываем порт
EXPOSE 8000

# Команда запуска
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]