from django.urls import path
from .views import EmployeeReportAPIView, EmployeeDetailsByUserAPIView

urlpatterns = [
    path('employee/<int:employee_id>/', EmployeeReportAPIView.as_view(), name='employee_report'),
    path('employees/user/<int:user_id>/', EmployeeDetailsByUserAPIView.as_view(), name='employees_by_user'),
]
