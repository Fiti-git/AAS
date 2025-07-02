FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files into the container
COPY . /app/

# Run collectstatic to gather static files for Django
RUN python manage.py collectstatic --noinput

# Expose the required port for Django
EXPOSE 8000

# Start the application with Gunicorn, migrating the database first
CMD ["sh", "-c", "python manage.py migrate && gunicorn aas.wsgi:application --bind 0.0.0.0:8000"]
