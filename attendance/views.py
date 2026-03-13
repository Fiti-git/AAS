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
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"/tmp/aas_backup_{timestamp}.sql"

    command = [
        "pg_dump",
        "-h", settings.DATABASES['default']['HOST'],
        "-U", settings.DATABASES['default']['USER'],
        settings.DATABASES['default']['NAME'],
    ]

    env = os.environ.copy()
    env["PGPASSWORD"] = settings.DATABASES['default']['PASSWORD']

    with open(backup_file, "w") as f:
        subprocess.run(command, stdout=f, env=env, check=True)

    return FileResponse(
        open(backup_file, 'rb'),
        as_attachment=True,
        filename=os.path.basename(backup_file)
    )