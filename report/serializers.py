from rest_framework import serializers
from main.models import EmpLeave, LeaveType, Outlet, Employee


class EmpLeaveSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='employee.user.username', read_only=True)
    first_name = serializers.CharField(source='employee.user.first_name', read_only=True)
    employee_id = serializers.IntegerField(source='employee.employee_id', read_only=True)

    att_type = serializers.CharField(source='leave_type.att_type', read_only=True)
    att_type_name = serializers.CharField(source='leave_type.att_type_name', read_only=True)

    class Meta:
        model = EmpLeave
        fields = [
            'leave_refno',
            'employee_id',
            'username',
            'first_name',
            'att_type',
            'att_type_name',
            'leave_date',
            'add_date',
            'action_date',
            'remarks',
            'status',
        ]


class LeaveCreateSerializer(serializers.Serializer):
    outlet_id = serializers.IntegerField()
    employee_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
    leave_dates = serializers.ListField(
        child=serializers.DateField(),
        allow_empty=False
    )
    leave_type_id = serializers.IntegerField()
    remarks = serializers.CharField(required=False, allow_blank=True)

    def validate_outlet_id(self, value):
        if not Outlet.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid outlet id")
        return value

    def validate_leave_type_id(self, value):
        if not LeaveType.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid leave type id")
        return value

    def validate_employee_ids(self, value):
        if not Employee.objects.filter(employee_id__in=value).exists():
            raise serializers.ValidationError("One or more invalid employee ids")
        return value
