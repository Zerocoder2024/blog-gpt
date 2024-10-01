# Используем официальный образ Python
FROM python:3.9-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt /app/

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы в контейнер
COPY . /app/

# Открываем порт 8000 для приложения
EXPOSE 8000

# Команда для запуска приложения
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
