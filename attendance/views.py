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

    # SQL filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"/tmp/aas_backup_{timestamp}.sql"

    # Database connection from environment variables
    db_name = os.environ.get("DATABASE_NAME", "aas_db")
    db_user = os.environ.get("DATABASE_USER", "aas_user")
    db_password = os.environ.get("DATABASE_PASSWORD", "your-db-password-here")
    db_host = os.environ.get("DATABASE_HOST", "db")
    db_port = os.environ.get("DATABASE_PORT", 5432)

    env = os.environ.copy()
    env["PGPASSWORD"] = db_password

    command = [
        "pg_dump",
        "-h", db_host,
        "-U", db_user,
        "-F", "c",        # custom format (compressed)
        "-b",             # include large objects
        "-v",             # verbose
        "-f", backup_file,
        db_name
    ]

    try:
        subprocess.run(command, env=env, check=True)
        return FileResponse(
            open(backup_file, 'rb'),
            as_attachment=True,
            filename=os.path.basename(backup_file)
        )

    except subprocess.CalledProcessError as e:
        return HttpResponse(f"Error during backup: {str(e)}", status=500)