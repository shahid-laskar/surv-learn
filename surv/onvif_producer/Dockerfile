FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY onvif_producer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY onvif_producer/onvif_motion_producer.py .
CMD ["python", "-u", "onvif_motion_producer.py"]