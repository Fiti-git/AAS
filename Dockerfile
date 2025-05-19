# Step 2: Dockerfile for Django backend

FROM python:3.10-slim

# set working directory inside container
WORKDIR /app

# copy requirements first for caching
COPY requirements.txt /app/

# install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# copy all django project files
COPY . /app/

# expose port 8000 for django dev server
EXPOSE 8000

# run migrations and start django dev server on all interfaces
CMD bash -c "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"
