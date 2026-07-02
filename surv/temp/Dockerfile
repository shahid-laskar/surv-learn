FROM python:3.12-slim

WORKDIR /code

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc curl && \
    rm -rf /var/lib/apt/lists/*

COPY app/requirements.txt /code/
RUN pip install --no-cache-dir -r /code/requirements.txt

COPY app/ /code/app/

ENV PYTHONPATH=/code

WORKDIR /code/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]