import os
from django.http import FileResponse
from django.shortcuts import render
from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import subprocess
from datetime import datetime
from django.http import HttpResponse
import psycopg2



# Create your views here.
def attendance_page(request):
    return render(request, 'attendance.html')  # Path to the HTML file



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def db_health_check(request):
    try:
        db_conn = connections['default']
        db_conn.cursor()  # try connection
        return Response({
            "status": "ok",
            "database": "connected"
        })
    except OperationalError as e:
        return Response({
            "status": "error",
            "database": "not connected",
            "message": str(e)
        }, status=500)
    


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_db_backup(request):
    # Permission check
    if not request.user.groups.filter(name__in=["Manager", "Admin"]).exists() and not request.user.is_staff:
        return HttpResponse("Permission denied", status=403)

    # CSV filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"db_backup_{timestamp}.csv"

    # HTTP response setup
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Database connection from environment variables
    db_name = os.environ.get("DATABASE_NAME", "aas_db")
    db_user = os.environ.get("DATABASE_USER", "aas_user")
    db_password = os.environ.get("DATABASE_PASSWORD", "your-db-password-here")
    db_host = os.environ.get("DATABASE_HOST", "db")
    db_port = os.environ.get("DATABASE_PORT", 5432)

    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        cur = conn.cursor()

        # Replace 'myapp_mymodel' with the table you want to export
        cur.copy_expert("COPY myapp_mymodel TO STDOUT WITH CSV HEADER", response)

        cur.close()
        conn.close()

    except Exception as e:
        return HttpResponse(f"Error generating backup: {str(e)}", status=500)

    return response