from django.db import models
from django.contrib.auth.models import User, Group
import uuid

# UserDevice Model (Missing Model)
class UserDevice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    uuid = models.CharField(max_length=255)  # Unique identifier for the device
    device_type = models.CharField(max_length=50)  # Device type: personal or company
    outlet = models.ForeignKey('Outlet', null=True, blank=True, on_delete=models.SET_NULL)  # If it’s a company device, link it to an outlet

    def __str__(self):
        return f"{self.user.username} - {self.device_type}"

# Employee Model
class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.AutoField(primary_key=True)
    fullname = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    profile_photo = models.URLField(null=True, blank=True)
    date_of_birth = models.DateField()
    outlets = models.ManyToManyField('Outlet', related_name='employees', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.fullname

# Attendance Model
class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Late', 'Late'),
        ('Half Day', 'Half Day'),
        ('Absent', 'Absent'),
        ('On Leave', 'On Leave'),
    ]
    
    VERIFICATION_CHOICES = [
        ('Pending', 'Pending'),
        ('Verified', 'Verified'),
        ('Rejected', 'Rejected'),
        ('Requires Review', 'Requires Review'),
    ]

    attendance_id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    check_in_time = models.DateTimeField()
    check_in_lat = models.FloatField()
    check_in_long = models.FloatField()
    photo_check_in = models.URLField(max_length=500, null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    check_out_lat = models.FloatField(null=True, blank=True)
    check_out_long = models.FloatField(null=True, blank=True)
    photo_check_out = models.URLField(max_length=500, null=True, blank=True)
    worked_hours = models.FloatField(null=True, blank=True)
    ot_hours = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Present')
    verified = models.CharField(max_length=20, choices=VERIFICATION_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verification_notes = models.TextField(null=True, blank=True)
    
    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date', 'employee']
        verbose_name_plural = 'Attendance Records'

    def __str__(self):
        return f"{self.employee.fullname} - {self.date} - {self.status}"
    
    def save(self, *args, **kwargs):
        if self.check_out_time and self.check_in_time:
            delta = self.check_out_time - self.check_in_time
            self.worked_hours = round(delta.total_seconds() / 3600, 2)
            
            if self.worked_hours < 4:
                self.status = 'Half Day'
            elif self.worked_hours > 8:
                self.ot_hours = self.worked_hours - 8
        super().save(*args, **kwargs)

# LeaveType Model
class LeaveType(models.Model):
    id = models.AutoField(primary_key=True)
    att_type = models.CharField(max_length=50, unique=True)
    att_type_name = models.CharField(max_length=255)
    active = models.BooleanField(default=True)
    att_type_group = models.CharField(max_length=100)
    att_type_per_day_hours = models.DecimalField(max_digits=5, decimal_places=2)
    pay_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    att_type_no_of_days_in_year = models.IntegerField()
    year_start_date = models.DateField()
    year_end_date = models.DateField()

    def __str__(self):
        return f"{self.att_type_name} ({self.att_type})"

    class Meta:
        db_table = 'leave_type'

# Holiday Model
class Holiday(models.Model):
    id = models.AutoField(primary_key=True)
    hcode = models.CharField(max_length=50)
    holiday_name = models.CharField(max_length=255)
    holiday_type = models.CharField(max_length=50)
    holiday_type_name = models.CharField(max_length=100)
    hdate = models.DateField()
    active = models.BooleanField(default=True)
    holiday_ot_pay_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    holiday_regular_pay_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.holiday_name} ({self.hcode})"

    class Meta:
        db_table = 'holiday'

# EmpLeave Model
class EmpLeave(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    leave_refno = models.AutoField(primary_key=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    leave_date = models.DateField()
    leave_type = models.ForeignKey(LeaveType, on_delete=models.SET_NULL, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    add_date = models.DateField(auto_now_add=True)
    action_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="leave_actioned_by")
    action_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Leave {self.leave_refno} - {self.employee.fullname}"

# Outlet Model
class Outlet(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    radius_meters = models.IntegerField()
    manager = models.ForeignKey(Employee, related_name="outlet_manager", on_delete=models.SET_NULL, null=True, blank=True)
    agency = models.ForeignKey('Agency', null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.SmallIntegerField(default=1)

    def __str__(self):
        return self.name

# Role Model
class Role(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE)
    designation = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.group.name

    class Meta:
        db_table = 'role'
