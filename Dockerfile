FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    METERLINK_DB=/app/data/meterlink.db

WORKDIR /app

COPY requirements.txt pyproject.toml ./
COPY config ./config
COPY src ./src
COPY web ./web

RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["uvicorn", "web.main:app", "--host", "0.0.0.0", "--port", "8000"]
