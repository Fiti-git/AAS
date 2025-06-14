from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from main.models import Attendance, Employee, LeaveType, EmpLeave, Holiday
from django.utils import timezone
from main.serializers import EmpLeaveSerializer, HolidaySerializer, AttendanceSerializer
from django.db.models import Q
from datetime import datetime, timedelta, date
from rest_framework import status
from main.utils import verify_location
from face_recognition.views import verify_selfie
import logging
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


# POST /attendance/punch-in
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def punch_in(request):
    try:
        employee = request.user.employee
        data = request.data

        required_fields = ['check_in_lat', 'check_in_long', 'photo_check_in']
        if not all(field in data or field in request.FILES for field in required_fields):
            return Response(
                {"error": "Missing required fields: check_in_lat, check_in_long, photo_check_in"},
                status=status.HTTP_400_BAD_REQUEST
            )

        check_in_lat = float(data.get('check_in_lat'))
        check_in_long = float(data.get('check_in_long'))

        if Attendance.objects.filter(employee=employee, date=timezone.now().date()).exists():
            return Response(
                {"error": "You have already punched in today"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not verify_location(employee, check_in_lat, check_in_long):
            return Response(
                {"error": "You're not at an allowed location for punch-in"},
                status=status.HTTP_400_BAD_REQUEST
            )

        photo_file = request.FILES.get('photo_check_in')
        verification_result = verify_selfie(photo_file, employee)
        if not verification_result['success']:
            return Response(
                {"error": f"Selfie verification failed: {verification_result['message']}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        attendance = Attendance.objects.create(
            employee=employee,
            date=timezone.now().date(),
            check_in_time=timezone.now(),
            check_in_lat=check_in_lat,
            check_in_long=check_in_long,
            photo_check_in='sample',
            verified='Verified'
        )

        return Response(
            {
                "message": "Punch-in recorded successfully!",
                "data": AttendanceSerializer(attendance).data
            },
            status=status.HTTP_201_CREATED
        )

    except Exception as e:
        logger.error(f"Punch-in error: {str(e)}", exc_info=True)
        return Response(
            {"error": "An error occurred during punch-in"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def punch_out(request):
    try:
        employee = request.user.employee
        data = request.data
        
        # Validate required fields
        required_fields = ['check_out_lat', 'check_out_long', 'photo_check_out']
        if not all(field in data for field in required_fields):
            return Response(
                {"error": "Missing required fields (lat, long, selfie_url)"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        check_out_lat = float(request.POST.get('check_out_lat'))  # Convert to float
        check_out_long = float(request.POST.get('check_out_long'))  # Convert to float

        # Get today's attendance record
        attendance = Attendance.objects.filter(
            employee=employee,
            date=timezone.now().date()
        ).first()
        
        if not attendance:
            return Response(
                {"error": "No punch-in record found for today"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if attendance.check_out_time:
            return Response(
                {"error": "You have already punched out today"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify location and selfie
        if not verify_location(employee, check_out_lat, check_out_long):
            return Response(
                {"error": "You're not at an allowed location for punch-out"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        verification_result = verify_selfie(data['photo_check_out'], employee)
        if not verification_result['success']:
            return Response(
                {"error": f"Selfie verification failed: {verification_result['message']}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update attendance
        attendance.check_out_time = timezone.now()
        attendance.check_out_lat = check_out_lat
        attendance.check_out_long = check_out_long
        attendance.photo_check_out = 'sample2'
        attendance.verified = 'Pending' if verification_result['success'] else 'Requires Review'
        attendance.save()  # This will trigger the auto-calculation in save()
        
        return Response(
            {
                "message": "Punch-out recorded successfully!",
                "data": AttendanceSerializer(attendance).data
            },
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Punch-out error: {str(e)}", exc_info=True)
        return Response(
            {"error": "An error occurred during punch-out"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

# GET /attendance/me - Get logged-in user's attendance
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_attendance(request):
    employee = request.user.employee
    attendance = Attendance.objects.filter(employee=employee).order_by('-date')
    
    data = [{
        'date': att.date,
        'check_in_time': att.check_in_time,
        'check_out_time': att.check_out_time,
        'status': att.status,
        'worked_hours': att.worked_hours,
        'ot_hours': att.ot_hours,
    } for att in attendance]

    return Response(data)


# GET /attendance/outlet - Get attendance for outlet staff (Manager)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_outlet_attendance(request):
    employee = request.user.employee
    if not request.user.groups.filter(name="Manager").exists(): 
        return Response({"message": "You are not authorized to view this information."}, status=403)
    
    outlet_staff = Employee.objects.filter(outlets__in=employee.outlets.all()).distinct()
    attendance = Attendance.objects.filter(employee__in=outlet_staff).order_by('-date')

    data = [{
        'employee': att.employee.fullname,
        'date': att.date,
        'check_in_time': att.check_in_time,
        'check_out_time': att.check_out_time,
        'status': att.status,
        'worked_hours': att.worked_hours,
    } for att in attendance]

    return Response(data)


# GET /attendance/all - Get all attendance records (Admin)
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_all_attendance(request):
    attendance = Attendance.objects.all().order_by('-date')

    data = [{
        'employee': att.employee.fullname,
        'date': att.date,
        'check_in_time': att.check_in_time,
        'check_out_time': att.check_out_time,
        'status': att.status,
        'worked_hours': att.worked_hours,
    } for att in attendance]

    return Response(data)


# GET /attendance/{id} - View specific attendance record
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_attendance(request, id):
    try:
        attendance = Attendance.objects.get(attendance_id=id)
    except Attendance.DoesNotExist:
        return Response({"message": "Attendance record not found."}, status=404)

    data = {
        'employee': attendance.employee.fullname,
        'date': attendance.date,
        'check_in_time': attendance.check_in_time,
        'check_out_time': attendance.check_out_time,
        'status': attendance.status,
        'worked_hours': attendance.worked_hours,
        'ot_hours': attendance.ot_hours,
    }

    return Response(data)


# PUT /attendance/{id}/status - Mark or update attendance status (Manager/Admin)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_attendance_status(request, id):
    try:
        attendance = Attendance.objects.get(attendance_id=id)
    except Attendance.DoesNotExist:
        return Response({"message": "Attendance record not found."}, status=404)

    if not (request.user.groups.filter(name="Manager").exists()):
        return Response({"message": "You are not authorized to update the status."}, status=403)

    status = request.data.get('status')
    if status not in ['Present', 'Late', 'Absent']:
        return Response({"message": "Invalid status."}, status=400)

    attendance.status = status
    attendance.save()

    return Response({"message": "Attendance status updated."}, status=200)

class LeaveRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        employee = user.employee  # assuming one-to-one relation

        leave_type_id = request.data.get('leave_type')
        leave_dates = request.data.get('leave_dates')
        remarks = request.data.get('remarks', '')

        if not leave_type_id or not leave_dates:
            return Response({'error': 'leave_type and leave_dates are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            leave_type = LeaveType.objects.get(id=leave_type_id)
        except LeaveType.DoesNotExist:
            return Response({'error': 'Invalid leave_type.'}, status=status.HTTP_400_BAD_REQUEST)

        created = []
        for date_str in leave_dates:
            try:
                leave_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                obj = EmpLeave.objects.create(
                    employee=employee,
                    leave_date=leave_date,
                    leave_type=leave_type,
                    remarks=remarks,
                    status='pending'
                )
                created.append(obj.leave_refno)
            except ValueError:
                return Response({'error': f'Invalid date format: {date_str}'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'Leave requests submitted.', 'created_ids': created}, status=status.HTTP_201_CREATED)
    
@api_view(['GET'])
def my_leave_requests(request):
    if request.method == 'GET':
        leave_requests = EmpLeave.objects.filter(employee=request.user.employee)
        serializer = EmpLeaveSerializer(leave_requests, many=True)
        return Response(serializer.data)
    
@api_view(['GET'])
def all_leave_requests(request):
    leave_requests = EmpLeave.objects.all()
    serializer = EmpLeaveSerializer(leave_requests, many=True)
    return Response(serializer.data)

def leave_requests_by_outlet(request):
    user = request.user

    # Check if user is a manager
    if not user.groups.filter(name="Manager").exists():
        return Response({"detail": "Access denied. User is not a manager."}, status=403)

    outlet_id = request.query_params.get('outlet_id')
    if not outlet_id:
        return Response({"detail": "Missing outlet_id parameter."}, status=400)

    try:
        outlet_id = int(outlet_id)
    except ValueError:
        return Response({"detail": "Invalid outlet_id."}, status=400)

    # Check user has an employee profile
    employee = getattr(user, 'employee', None)
    if not employee:
        return Response({"detail": "Employee profile not found."}, status=404)

    # Check outlet access
    if not employee.outlets.filter(id=outlet_id).exists():
        return Response({"detail": "You are not assigned to this outlet."}, status=403)

    # Filter leave requests for employees in that outlet
    leave_requests = EmpLeave.objects.filter(employee__outlets__id=outlet_id).distinct()
    serializer = EmpLeaveSerializer(leave_requests, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pending_leave_requests(request):
    user = request.user
    employee = user.employee

    today = date.today()
    result = []

    # Fetch all active leave types
    leave_types = LeaveType.objects.filter(active=True)

    for leave_type in leave_types:
        # Get the year range from leave type
        start_date = leave_type.year_start_date
        end_date = leave_type.year_end_date

        # Get count of used leaves (pending + approved) in the year range
        used_count = EmpLeave.objects.filter(
            employee=employee,
            leave_type=leave_type,
            status__in=['pending', 'approved'],
            leave_date__range=(start_date, end_date)
        ).count()

        allowed = leave_type.att_type_no_of_days_in_year
        remaining = max(allowed - used_count, 0)

        result.append({
            'leave_type': leave_type.att_type_name,
            'leave_code': leave_type.att_type,
            'allowed': allowed,
            'used': used_count,
            'remaining': remaining
        })

    return Response(result)

@api_view(['PUT'])
def update_leave_status(request, id):
    try:
        leave_request = EmpLeave.objects.select_related('employee__user').prefetch_related('employee__outlets').get(leave_refno=id)
    except EmpLeave.DoesNotExist:
        return Response({"message": "Leave request not found."}, status=404)

    user = request.user

    is_admin = user.is_staff or user.is_superuser
    is_manager = user.groups.filter(name="Manager").exists()
    same_outlet = (
        hasattr(user, 'employee') and
        leave_request.employee.outlets.filter(id__in=user.employee.outlets.values_list('id', flat=True)).exists()
    )


    if not (is_admin or (is_manager and same_outlet)):
        return Response({"message": "You are not authorized to update this leave request."}, status=403)

    new_status = request.data.get('status')

    if new_status not in ['approved', 'rejected']:
        return Response({"message": "Invalid status. Must be 'approved' or 'rejected'."}, status=400)

    leave_request.status = new_status
    leave_request.action_date = timezone.now().date()
    leave_request.action_user = user
    leave_request.save()

    return Response({"message": f"Leave request {new_status}."}, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_holidays(request):
    holidays = Holiday.objects.all()
    serializer = HolidaySerializer(holidays, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_holiday(request):
    if not (request.user.groups.filter(name="Manager").exists()):
        return Response({"detail": "Not authorized."}, status=403)

    serializer = HolidaySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_holiday(request, hcode):
    if not (request.user.groups.filter(name="Admin").exists()):
        return Response({"detail": "Not authorized."}, status=403)

    holiday = Holiday.objects.filter(hcode=hcode).first()
    if not holiday:
        return Response({"detail": "Holiday not found."}, status=404)
    
    serializer = HolidaySerializer(holiday, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_holiday(request, hcode):
    if not (request.user.groups.filter(name="Admin").exists()):
        return Response({"detail": "Not authorized."}, status=403)

    holiday = Holiday.objects.filter(hcode=hcode).first()
    if not holiday:
        return Response({"detail": "Holiday not found."}, status=404)
    holiday.delete()
    return Response({"message": "Holiday deleted."}, status=204)


@api_view(['GET'])
def generate_report(request):
    # Required date range
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date') or start_date_str

    # Optional filters
    user_id = request.GET.get('user_id')
    outlet = request.GET.get('outlet')  # Assuming outlet is a field in Employee

    if not start_date_str:
        return Response({"detail": "start_date is required."}, status=400)

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        return Response({"detail": "Invalid date format. Use YYYY-MM-DD."}, status=400)

    # Filter employees
    employees = Employee.objects.all()
    if user_id:
        employees = employees.filter(id=user_id)
    if outlet:
        employees = employees.filter(outlets=outlet)

    report = []

    # Loop through each day and employee
    current_date = start_date
    while current_date <= end_date:
        for employee in employees:
            attendance = Attendance.objects.filter(employee=employee, date=current_date).first()
            leave = None if attendance else EmpLeave.objects.filter(
                employee=employee, leave_date=current_date, leave_status="Approved"
            ).first()
            holiday = Holiday.objects.filter(hdate=current_date).first()

            row = {
                "emp_id": employee.emp_id,
                "designation": employee.role.designation if hasattr(employee, 'role') else '',
                "id_no": employee.id_no,
                "name": employee.name,
                "date": current_date,
                "time_in": attendance.time_in if attendance else '',
                "time_out": attendance.time_out if attendance else '',
                "type": (
                    'WD' if attendance else
                    (leave.leave_type if leave else '')
                ),
                "type_name": (
                    "" if attendance else
                    (leave.leave_type if leave else '')
                ),
                "hcode": holiday.hcode if holiday else '',
                "htype": holiday.holiday_type if holiday else '',
                "hname": holiday.holiday_name if holiday else '',
                "agency": employee.agency
            }

            report.append(row)
        current_date += timedelta(days=1)

    return Response(report)

