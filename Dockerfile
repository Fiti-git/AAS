FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt /app/

# Install build deps needed for psycopg2, then install python deps##
RUN apt-get update && apt-get install -y \
    libpq-dev gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && gunicorn aas.wsgi:application --bind 0.0.0.0:8000"]
