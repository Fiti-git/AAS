from django.urls import path
from .views import EmployeeReportAPIView

urlpatterns = [
    path('employee/<int:employee_id>/', EmployeeReportAPIView.as_view(), name='employee_report'),
]
