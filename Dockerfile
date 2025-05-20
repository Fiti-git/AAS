# Use official Python slim image
FROM python:3.10-slim

# Set working dir inside container
WORKDIR /app

# Copy requirements and install deps
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . /app/

# Expose port 8000 (default for Django)
EXPOSE 8000

# Run migrations (optional but good)
#RUN python manage.py migrate

# Start gunicorn server with your project name (aas)
CMD ["gunicorn", "aas.wsgi:application", "--bind", "0.0.0.0:8000"]
