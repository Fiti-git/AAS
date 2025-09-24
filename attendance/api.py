from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from main.models import Attendance, Employee, LeaveType, EmpLeave, Holiday
from django.utils import timezone
from main.serializers import EmpLeaveSerializer, HolidaySerializer, AttendanceSerializer,EmpLeaveCreateSerializer
from django.db.models import Q
from datetime import datetime, timedelta, date
from rest_framework import status
from main.utils import verify_location
import logging
from rest_framework.views import APIView
from .face_recognition import compare_faces
from django.conf import settings
from dateutil import parser



logger = logging.getLogger(__name__)


# POST /attendance/punch-in
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def punch_in(request):
    try:
        employee = request.user.employee
        data = request.data

        if not all(field in data for field in ['check_in_lat', 'check_in_long']):
            return Response({"error": "Missing required location fields"}, status=status.HTTP_400_BAD_REQUEST)
        
        if 'photo_check_in' not in request.FILES:
            return Response({"error": "Photo is required for punch-in"}, status=status.HTTP_400_BAD_REQUEST)

        open_attendance = Attendance.objects.filter(
            employee=employee,
            check_out_time__isnull=True
        ).last()

        if open_attendance:
            return Response({"error": "You must punch out from your previous session before punching in again"}, status=400)
            

        check_in_lat = float(data.get('check_in_lat'))
        check_in_long = float(data.get('check_in_long'))
        photo_file = request.FILES.get('photo_check_in')

        if not verify_location(employee, check_in_lat, check_in_long):
            return Response(
                {"error": "You're not at an allowed location for punch-in"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        verified_status = 'Pending'
        response_message = "Punch-in recorded successfully!"

        if not employee.reference_photo:
            employee.reference_photo = photo_file
            employee.punchin_selfie = photo_file
            employee.save()
            
            verified_status = 'Pending'
            response_message = "Punch-in recorded. Your photo has been submitted for verification."

        elif employee.reference_photo:
            # CORRECTED: Use the new field name
            employee.punchin_selfie = photo_file
            employee.save()
            
            try:
                employee.reference_photo.open('rb')
                employee.punchin_selfie.open('rb')
                source_bytes = employee.reference_photo.read()
                target_bytes = employee.punchin_selfie.read()
                employee.reference_photo.close()
                employee.punchin_selfie.close()
                
                result = compare_faces(
                    source_bytes=source_bytes,
                    target_bytes=target_bytes,
                    aws_access_key=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_key=settings.AWS_SECRET_ACCESS_KEY,
                    aws_region=settings.AWS_REKOGNITION_REGION
                )

                if result.get('FaceMatches'):
                    verified_status = 'Verified'
                else:
                    return Response({"error": "Face recognition failed. Please try again."}, status=status.HTTP_401_UNAUTHORIZED)
            
            except Exception as e:
                logger.error(f"Face comparison error for employee {employee.employee_id}: {str(e)}")
                return Response({"error": "Could not process image. Ensure your face is clearly visible."}, status=status.HTTP_400_BAD_REQUEST)

        attendance = Attendance.objects.create(
            employee=employee,
            date=timezone.now().date(),
            check_in_time=timezone.now(),
            check_in_lat=check_in_lat,
            check_in_long=check_in_long,
            punchin_verification=verified_status
        )


        return Response({
            "message": response_message,
            "data": AttendanceSerializer(attendance).data,
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Punch-in error: {str(e)}", exc_info=True)
        return Response({"error": "An unexpected error occurred during punch-in"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def punch_out(request):
    try:
        employee = request.user.employee
        data = request.data

        if not all(field in data for field in ['check_out_lat', 'check_out_long']):
            return Response({"error": "Missing required location fields"}, status=status.HTTP_400_BAD_REQUEST)
        
        if 'photo_check_out' not in request.FILES:
            return Response({"error": "Photo is required for punch-out"}, status=status.HTTP_400_BAD_REQUEST)

        attendance = Attendance.objects.filter(
            employee=employee,
            check_out_time__isnull=True
        ).last()

        if not attendance:
            return Response({"error": "No active punch-in session found"}, status=400)
            
        # CORRECTED: More robust check. Do not create a reference photo on punch-out.
        if not employee.reference_photo:
            employee.reference_photo = photo_file
            employee.save()
            # return Response({"error": "Cannot punch out because your face is not enrolled."}, status=status.HTTP_400_BAD_REQUEST)

        check_out_lat = float(data.get('check_out_lat'))
        check_out_long = float(data.get('check_out_long'))
        photo_file = request.FILES.get('photo_check_out')

        if not verify_location(employee, check_out_lat, check_out_long):
            return Response(
                {"error": "You're not at an allowed location for punch-out"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # CORRECTED: Use the new field name
        employee.punchout_selfie = photo_file
        employee.save()
        
        try:
            employee.reference_photo.open('rb')
            employee.punchout_selfie.open('rb')
            source_bytes = employee.reference_photo.read()
            target_bytes = employee.punchout_selfie.read()
            employee.reference_photo.close()
            employee.punchout_selfie.close()
            
            result = compare_faces(
                source_bytes=source_bytes,
                target_bytes=target_bytes,
                aws_access_key=settings.AWS_ACCESS_KEY_ID,
                aws_secret_key=settings.AWS_SECRET_ACCESS_KEY,
                aws_region=settings.AWS_REKOGNITION_REGION
            )

            if not result.get('FaceMatches'):
                return Response({"error": "Face recognition failed. Please try again."}, status=status.HTTP_401_UNAUTHORIZED)
        
        except Exception as e:
            logger.error(f"Face comparison error during punch-out for employee {employee.employee_id}: {str(e)}")
            return Response({"error": "Could not process image. Ensure your face is clearly visible."}, status=status.HTTP_400_BAD_REQUEST)

        attendance.check_out_time = timezone.now()
        attendance.check_out_lat = check_out_lat
        attendance.check_out_long = check_out_long
        attendance.punchout_verification = "Verified" 
        attendance.save()

        return Response({
            "message": "Punch-out recorded successfully!",
            "data": AttendanceSerializer(attendance).data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Punch-out error: {str(e)}", exc_info=True)
        return Response({"error": "An error occurred during punch-out"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_attendance(request):
    """
    Update check-in and/or check-out times of an attendance record.
    Recalculate worked hours, status, OT hours, and add verification notes.
    """
    data = request.data
    attendance_id = data.get('attendance_id')
    new_check_in = data.get('check_in_time')
    new_check_out = data.get('check_out_time')

    if not attendance_id:
        return Response({"error": "attendance_id is required."},
                        status=status.HTTP_400_BAD_REQUEST)
    
    try:
        attendance = Attendance.objects.get(attendance_id=attendance_id)
    except Attendance.DoesNotExist:
        return Response({"error": "Attendance record not found."},
                        status=status.HTTP_404_NOT_FOUND)
    
    notes = attendance.verification_notes or {}

    # Update check-in time if provided
    if new_check_in:
        try:
            check_in_dt = parser.parse(new_check_in)
            attendance.check_in_time = check_in_dt
            # Update JSON note for check-in
            notes['checkin_update'] = {
                "updated_by": request.user.username,
                "check_in_time": str(attendance.check_in_time),
                "updated_at": timezone.now().isoformat()
            }
            attendance.punchin_verification = 'Verified'
        except Exception as e:
            return Response({"error": f"Invalid check_in_time format: {str(e)}"},
                            status=status.HTTP_400_BAD_REQUEST)

    # Update check-out time if provided
    if new_check_out:
        try:
            check_out_dt = parser.parse(new_check_out)
            attendance.check_out_time = check_out_dt
            # Update JSON note for check-out
            notes['checkout_update'] = {
                "updated_by": request.user.username,
                "check_out_time": str(attendance.check_out_time),
                "updated_at": timezone.now().isoformat()
            }
            attendance.punchout_verification = 'Verified'
        except Exception as e:
            return Response({"error": f"Invalid check_out_time format: {str(e)}"},
                            status=status.HTTP_400_BAD_REQUEST)
    
    # Recalculate worked hours, OT hours, and status if both times exist
    if attendance.check_in_time and attendance.check_out_time:
        delta = attendance.check_out_time - attendance.check_in_time
        attendance.worked_hours = round(delta.total_seconds() / 3600, 2)
        if attendance.worked_hours < 4:
            attendance.status = 'Half Day'
        elif attendance.worked_hours > 8:
            attendance.ot_hours = attendance.worked_hours - 8
            attendance.status = 'Present'
        else:
            attendance.ot_hours = 0
            attendance.status = 'Present'

    attendance.verification_notes = notes
    attendance.save()

    return Response({
        "message": "Attendance updated successfully",
        "attendance_id": attendance.attendance_id,
        "worked_hours": attendance.worked_hours,
        "ot_hours": attendance.ot_hours,
        "status": attendance.status,
        "verification_notes": attendance.verification_notes
    })


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

@api_view(['GET'])
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
            'id': leave_type.id,
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


class VerifyAttendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        
        # --- Permission Check: Ensure user is a Manager or Admin ---
        if not (user.is_staff or user.groups.filter(name="Manager").exists()):
            return Response(
                {"error": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # --- Input Validation ---
        attendance_id = request.data.get('attendance_id')
        verification_type = request.data.get('verification_type') # Expected: 'punchin' or 'punchout'
        new_status = request.data.get('status') # Expected: 'Verified' or 'Rejected'
        notes = request.data.get('notes', '') # Optional notes

        if not all([attendance_id, verification_type, new_status]):
            return Response(
                {"error": "attendance_id, verification_type, and status are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if verification_type not in ['punchin', 'punchout']:
            return Response({"error": "verification_type must be 'punchin' or 'punchout'."}, status=status.HTTP_400_BAD_REQUEST)
            
        if new_status not in ['Verified', 'Rejected']:
            return Response({"error": "status must be 'Verified' or 'Rejected'."}, status=status.HTTP_400_BAD_REQUEST)
            
        # --- Database Update ---
        try:
            attendance = Attendance.objects.select_related('employee').get(attendance_id=attendance_id)
            
            # Security Check: Can this manager see this employee?
            if user.groups.filter(name="Manager").exists():
                manager_outlets = user.employee.outlets.all()
                if not attendance.employee.outlets.filter(id__in=manager_outlets.values_list('id', flat=True)).exists():
                    return Response({"error": "You are not authorized to verify this employee's attendance."}, status=status.HTTP_403_FORBIDDEN)

            # Update the correct field
            if verification_type == 'punchin':
                attendance.punchin_verification = new_status
            else: # 'punchout'
                attendance.punchout_verification = new_status
            
            if notes:
                attendance.verification_notes = notes
                
            attendance.save()
            
            # Return the updated record
            serializer = AttendanceSerializer(attendance)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Attendance.DoesNotExist:
            return Response({"error": "Attendance record not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_leave(request):
    serializer = EmpLeaveCreateSerializer(data=request.data)
    
    if serializer.is_valid():
        employee = serializer.validated_data['employee']
        leave_date = serializer.validated_data['leave_date']

        # Check for existing leave with status 'pending' or 'approved' for the same employee on leave_date
        existing = EmpLeave.objects.filter(
            employee=employee,
            leave_date=leave_date,
            status__in=['pending', 'approved']
        ).exists()

        if existing:
            return Response({
                "success": False, 
                "error": "A leave with status 'pending' or 'approved' already exists for this employee on the selected date."
            }, status=400)

        # Save leave
        leave = serializer.save(
            status='pending',
            action_user=request.user,
            action_date=None
        )
        return Response({
            "success": True,
            "leave_refno": leave.leave_refno
        })

    else:
        return Response({"success": False, "errors": serializer.errors}, status=400)