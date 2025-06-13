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
    leave_type_id = serializers.IntegerField(source='leave_type.id', read_only=True)
    leave_type_name = serializers.CharField(source='leave_type.att_type_name', read_only=True)

    class Meta:
        model = EmpLeave
        fields = [
            'leave_refno',
            'leave_date',
            'remarks',
            'add_date',
            'action_date',
            'status',
            'employee',
            'leave_type_id',
            'leave_type_name',
            'action_user'
        ]


class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = '__all__'

class EmployeeSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)
    groups = serializers.SerializerMethodField()
    outlet = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Employee
        fields = [
            'employee_id',
            'fullname',
            'phone_number',
            'profile_photo',
            'date_of_birth',
            'outlet',
            'email',
            'first_name',
            'last_name',
            'is_active',
            'groups',
        ]

    def get_groups(self, obj):
        return [group.name for group in obj.user.groups.all()]

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