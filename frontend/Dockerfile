FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FRONTEND_HOST=0.0.0.0 \
    FRONTEND_PORT=5000

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py api_client.py ./
COPY templates/ ./templates/

EXPOSE 5000

CMD ["python", "app.py"]
