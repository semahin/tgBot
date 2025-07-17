FROM python:3.13.5

WORKDIR /pythonBOT1

# Копируем зависимости
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код проекта и данные (CSV)
COPY . .

# Указываем команду запуска
CMD ["python", "botik.py"]
