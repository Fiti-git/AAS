from django.urls import path
from .views import EmployeeReportAPIView, EmployeesByOutletAPIView

urlpatterns = [
    path('employee/<int:employee_id>/', EmployeeReportAPIView.as_view(), name='employee_report'),
    path('employees/outlets/', EmployeesByOutletAPIView.as_view(), name='employees_by_outlet'),
]
