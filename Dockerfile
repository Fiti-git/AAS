# Use official python slim image
FROM python:3.10-slim

# Set workdir
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all code
COPY . /app/

# Collect static files (optional, skip if not used)
RUN python manage.py collectstatic --noinput

# Expose port 8000 for gunicorn
EXPOSE 8000

# Run migrations & start gunicorn server
CMD ["sh", "-c", "python manage.py migrate && gunicorn aas.wsgi:application --bind 0.0.0.0:8000"]
