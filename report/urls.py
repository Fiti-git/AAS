from django.urls import path
from .views import (
    DashboardOverviewAPIView,
    LeavePresenceTrendAPIView,
    OutletSummaryAPIView,
    EmployeeAttendanceSummaryAPIView,
    EmployeeReportAPIView,
    EmployeeDetailsByUserAPIView,
    # New outlet-filtered views
    DashboardOverviewByOutletAPIView,
    LeavePresenceTrendByOutletAPIView,
    EmployeeAttendanceSummaryByOutletAPIView,
    EmployeesByManagerAPIView,
    OutletLeaveListAPIView,
    LeaveStatusUpdateAPIView,
)

urlpatterns = [
    # Original endpoints (all outlets)
    path('dashboard/overview/', DashboardOverviewAPIView.as_view(), name='dashboard_overview'),
    path('dashboard/leave-presence-trend/', LeavePresenceTrendAPIView.as_view(), name='leave_presence_trend'),
    path('dashboard/outlet-summary/', OutletSummaryAPIView.as_view(), name='outlet_summary'),
    path('dashboard/employee-attendance-summary/', EmployeeAttendanceSummaryAPIView.as_view(), name='employee_attendance_summary'),

    # New outlet-filtered endpoints
    # Option 1: Using URL parameter
    path('dashboard/overview/outlet/<int:outlet_id>/', DashboardOverviewByOutletAPIView.as_view(), name='dashboard_overview_by_outlet'),
    path('dashboard/leave-presence-trend/outlet/<int:outlet_id>/', LeavePresenceTrendByOutletAPIView.as_view(), name='leave_presence_trend_by_outlet'),
    path('dashboard/employee-attendance-summary/outlet/<int:outlet_id>/', EmployeeAttendanceSummaryByOutletAPIView.as_view(), name='employee_attendance_summary_by_outlet'),
    
    # Option 2: Using query parameters (same view, no outlet_id in URL)
    # Example usage: /dashboard/overview/filter/?outlet_id=15
    path('dashboard/overview/filter/', DashboardOverviewByOutletAPIView.as_view(), name='dashboard_overview_filter'),
    path('dashboard/leave-presence-trend/filter/', LeavePresenceTrendByOutletAPIView.as_view(), name='leave_presence_trend_filter'),
    path('dashboard/employee-attendance-summary/filter/', EmployeeAttendanceSummaryByOutletAPIView.as_view(), name='employee_attendance_summary_filter'),

    # Existing employee endpoints
    path('employee/<int:employee_id>/', EmployeeReportAPIView.as_view(), name='employee_report'),
    path('employees/user/<int:user_id>/', EmployeesByManagerAPIView.as_view(), name='employees_by_user'),

    #leave report
    path('leaves/outlet/', OutletLeaveListAPIView.as_view(), name='outlet-leave-list'),
    path('leaves/<int:leave_refno>/status/', LeaveStatusUpdateAPIView.as_view(), name='leave-status-update'),
]