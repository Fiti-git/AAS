from django.urls import path
from .views import (
    DashboardOverviewAPIView,
    LeavePresenceTrendAPIView,
    OutletSummaryAPIView,
    EmployeeAttendanceSummaryAPIView,
    EmployeeReportAPIView,
    # New outlet-filtered views
    DashboardOverviewByOutletAPIView,
    LeavePresenceTrendByOutletAPIView,
    EmployeeAttendanceSummaryByOutletAPIView,
    EmployeesByManagerAPIView,
    OutletLeaveListAPIView,
    LeaveStatusUpdateAPIView,
    LeaveBulkCreateAPIView,
    OutletDataAPIView,
    EmployeeListCreateView,
    EmployeeDetailView,
)

urlpatterns = [
    # -------------------------------------------------------------------------
    # Dashboard (all outlets)
    # -------------------------------------------------------------------------
    path('dashboard/overview/', DashboardOverviewAPIView.as_view(), name='dashboard_overview'),
    path('dashboard/leave-presence-trend/', LeavePresenceTrendAPIView.as_view(), name='leave_presence_trend'),
    path('dashboard/outlet-summary/', OutletSummaryAPIView.as_view(), name='outlet_summary'),
    path('dashboard/employee-attendance-summary/', EmployeeAttendanceSummaryAPIView.as_view(), name='employee_attendance_summary'),

    # No-slash aliases (frontend sometimes calls without trailing slash)
    path('dashboard/overview', DashboardOverviewAPIView.as_view()),
    path('dashboard/leave-presence-trend', LeavePresenceTrendAPIView.as_view()),
    path('dashboard/outlet-summary', OutletSummaryAPIView.as_view()),
    path('dashboard/employee-attendance-summary', EmployeeAttendanceSummaryAPIView.as_view()),

    # -------------------------------------------------------------------------
    # Dashboard (outlet filtered)
    # -------------------------------------------------------------------------
    # Option 1: Using URL param
    path('dashboard/overview/outlet/<int:outlet_id>/', DashboardOverviewByOutletAPIView.as_view(), name='dashboard_overview_by_outlet'),
    path('dashboard/leave-presence-trend/outlet/<int:outlet_id>/', LeavePresenceTrendByOutletAPIView.as_view(), name='leave_presence_trend_by_outlet'),
    path('dashboard/employee-attendance-summary/outlet/<int:outlet_id>/', EmployeeAttendanceSummaryByOutletAPIView.as_view(), name='employee_attendance_summary_by_outlet'),

    # No-slash aliases
    path('dashboard/overview/outlet/<int:outlet_id>', DashboardOverviewByOutletAPIView.as_view()),
    path('dashboard/leave-presence-trend/outlet/<int:outlet_id>', LeavePresenceTrendByOutletAPIView.as_view()),
    path('dashboard/employee-attendance-summary/outlet/<int:outlet_id>', EmployeeAttendanceSummaryByOutletAPIView.as_view()),

    # Option 2: Using query params
    path('dashboard/overview/filter/', DashboardOverviewByOutletAPIView.as_view(), name='dashboard_overview_filter'),
    path('dashboard/leave-presence-trend/filter/', LeavePresenceTrendByOutletAPIView.as_view(), name='leave_presence_trend_filter'),
    path('dashboard/employee-attendance-summary/filter/', EmployeeAttendanceSummaryByOutletAPIView.as_view(), name='employee_attendance_summary_filter'),

    # No-slash aliases
    path('dashboard/overview/filter', DashboardOverviewByOutletAPIView.as_view()),
    path('dashboard/leave-presence-trend/filter', LeavePresenceTrendByOutletAPIView.as_view()),
    path('dashboard/employee-attendance-summary/filter', EmployeeAttendanceSummaryByOutletAPIView.as_view()),

    # -------------------------------------------------------------------------
    # Employee endpoints
    # -------------------------------------------------------------------------
    path('employee/<int:employee_id>/', EmployeeReportAPIView.as_view(), name='employee_report'),
    path('employees/user/<int:user_id>/', EmployeesByManagerAPIView.as_view(), name='employees_by_user'),

    # No-slash aliases (this one fixes your issue)
    path('employee/<int:employee_id>', EmployeeReportAPIView.as_view()),
    path('employees/user/<int:user_id>', EmployeesByManagerAPIView.as_view()),

    # -------------------------------------------------------------------------
    # Leave report
    # -------------------------------------------------------------------------
    path('leaves/outlet/', OutletLeaveListAPIView.as_view(), name='outlet-leave-list'),
    path('leaves/<int:leave_refno>/status/', LeaveStatusUpdateAPIView.as_view(), name='leave-status-update'),
    path('leaves/bulk_create/', LeaveBulkCreateAPIView.as_view(), name='leave-bulk-create'),
    path('leaves/outlet-data/', OutletDataAPIView.as_view(), name='leave-outlet-data'),

    # No-slash aliases
    path('leaves/outlet', OutletLeaveListAPIView.as_view()),
    path('leaves/<int:leave_refno>/status', LeaveStatusUpdateAPIView.as_view()),
    path('leaves/bulk_create', LeaveBulkCreateAPIView.as_view()),
    path('leaves/outlet-data', OutletDataAPIView.as_view()),

    # -------------------------------------------------------------------------
    # Employee CRUD
    # -------------------------------------------------------------------------
    path('employees/', EmployeeListCreateView.as_view()),
    path('employees/<int:pk>/', EmployeeDetailView.as_view()),

    # No-slash aliases
    path('employees', EmployeeListCreateView.as_view()),
    path('employees/<int:pk>', EmployeeDetailView.as_view()),
]
