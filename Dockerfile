FROM python:3.10-slim

WORKDIR /app

# System deps + debug tools
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    procps \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# ✅ Remove gevent install (not needed for gthread)
# RUN pip install --no-cache-dir gevent

# App code
COPY . /app/

# Collect static at build time
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Default command (compose will override with its command)
CMD ["gunicorn", "aas.wsgi:application", "--bind", "0.0.0.0:8000"]
