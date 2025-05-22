# serializers.py
from rest_framework import serializers
from .models import Outlet, EmpLeave, Holiday, Attendance, Employee, Agency, Holiday , LeaveType

class AttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.fullname', read_only=True)

    class Meta:
        model = Attendance
        fields = [
            'attendance_id',
            'employee',
            'employee_name',
            'date',
            'check_in_time',
            'check_in_lat',
            'check_in_long',
            'photo_check_in',
            'check_out_time',
            'check_out_lat',
            'check_out_long',
            'photo_check_out',
            'worked_hours',
            'ot_hours',
            'status',
            'verified',
            'verification_notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['attendance_id', 'worked_hours', 'ot_hours', 'status', 'verified', 'created_at', 'updated_at']


class OutletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Outlet
        fields = '__all__'

class EmpLeaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmpLeave
        fields = '__all__'

class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = '__all__'

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'

class AgencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Agency
        fields = '__all__'

class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = '__all__'
        read_only_fields = ('id',)

class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = '__all__'
        read_only_fields = ('id',)