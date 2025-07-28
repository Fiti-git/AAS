from django.urls import path
from . import views  # Import views from the current app

urlpatterns = [
    path('', views.attendance_page),
    path('download-images/', views.download_employee_images, name='download_employee_images'),
    path('download-folder/<int:employee_id>/', views.download_employee_folder, name='download_employee_folder'),
]