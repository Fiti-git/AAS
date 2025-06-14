from django.urls import path
from . import api  # Import views from the current app

urlpatterns = [
    path('punch-in/', api.punch_in, name='punch_in'),
    path('punch-out/', api.punch_out, name='punch_out'),
    path('me/', api.get_my_attendance, name='get_my_attendance'),
    path('outlet/', api.get_outlet_attendance, name='get_outlet_attendance'),
    path('get_attall/', api.get_all_attendance, name='get_all_attendance'),
    path('get_att/<int:id>/', api.get_attendance, name='get_attendance'),
    path('status/<int:id>/', api.update_attendance_status, name='update_attendance_status'),
    path('applyleave/', api.LeaveRequestAPIView.as_view(), name='leave-request'),
    path('myleaverequests/', api.my_leave_requests, name='my_leave_requests'),
    path('allleaverequests/', api.all_leave_requests, name='all_leave_requests'),
    path('outletleaverequests/', api.leave_requests_by_outlet, name='outlet_leave_requests'),
    path('pendingleave/', api.pending_leave_requests, name='pending_leave_requests'),
    path('updateleavestatus/<int:id>/', api.update_leave_status, name='update_leave_status'),
    path('report/', api.generate_report, name='generate-report'),
]