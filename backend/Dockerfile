FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    API_HOST=0.0.0.0 \
    API_PORT=5001

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY config.py db.py app.py migrate_sqlite_to_mysql.py ./

EXPOSE 5001

CMD ["python", "app.py"]
