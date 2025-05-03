from django.urls import path
from . import views  # Import views from the current app

urlpatterns = [
    path('', views.attendance_page)
]