FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY motion_consumer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY motion_consumer/motion_event_consumer.py .
CMD ["python", "-u", "motion_event_consumer.py"]