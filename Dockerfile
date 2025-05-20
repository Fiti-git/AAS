FROM python:3.10-slim

# set working directory inside container
WORKDIR /app

# copy requirements and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# copy entire project into container
COPY . /app

# expose port 8000 for django gunicorn
EXPOSE 8000

# start gunicorn server pointing to your django app module
CMD ["gunicorn", "aas.wsgi:application", "--bind", "0.0.0.0:8000"]
