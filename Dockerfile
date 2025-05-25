# Use official python slim image
FROM python:3.10-slim

# Set workdir
WORKDIR /app

# Install system dependencies for OpenCV (libGL)
RUN apt-get update && apt-get install -y libgl1 && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt /app/

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all code
COPY . /app/

# Collect static files (optional)
RUN python manage.py collectstatic --noinput

# Expose port 8000 for gunicorn
EXPOSE 8000

# Run migrations & start gunicorn server
CMD ["sh", "-c", "python manage.py migrate && gunicorn aas.wsgi:application --bind 0.0.0.0:8000"]
