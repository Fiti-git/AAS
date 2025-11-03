from django.urls import path
from .views import (
    DashboardOverviewAPIView,
    LeavePresenceTrendAPIView,
    OutletSummaryAPIView,
    EmployeeAttendanceSummaryAPIView,
    EmployeeReportAPIView,
    EmployeeDetailsByUserAPIView,
)

urlpatterns = [
    path('dashboard/overview/', DashboardOverviewAPIView.as_view(), name='dashboard_overview'),
    path('dashboard/leave-presence-trend/', LeavePresenceTrendAPIView.as_view(), name='leave_presence_trend'),
    path('dashboard/outlet-summary/', OutletSummaryAPIView.as_view(), name='outlet_summary'),
    path('dashboard/employee-attendance-summary/', EmployeeAttendanceSummaryAPIView.as_view(), name='employee_attendance_summary'),

    # Existing:
    path('employee/<int:employee_id>/', EmployeeReportAPIView.as_view(), name='employee_report'),
    path('employees/user/<int:user_id>/', EmployeeDetailsByUserAPIView.as_view(), name='employees_by_user'),
]
