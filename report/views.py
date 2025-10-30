from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection

class EmployeeReportAPIView(APIView):
    """
    Returns a comprehensive report for a single employee, with optional date filters.
    """

    def get(self, request, employee_id, format=None):
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        query = """
        WITH emp_outlets AS (
            SELECT
                e.employee_id,
                STRING_AGG(o.name, ', ') AS outlet_names,
                ARRAY_AGG(o.id) AS outlet_ids
            FROM main_employee e
            LEFT JOIN main_employee_outlets eo ON e.employee_id = eo.employee_id
            LEFT JOIN main_outlet o ON eo.outlet_id = o.id
            GROUP BY e.employee_id
        ),
        daily_attendance AS (
            SELECT
                employee_id,
                DATE(check_in_time) AS work_date,
                MIN(check_in_time) AS check_in_time,
                MAX(check_out_time) AS check_out_time,
                ROUND(EXTRACT(EPOCH FROM (MAX(check_out_time) - MIN(check_in_time))) / 3600, 2) AS worked_hours,
                MAX(status) AS attendance_status,
                JSON_AGG(verification_notes) AS verification_notes
            FROM main_attendance
            GROUP BY employee_id, DATE(check_in_time)
        ),
        approved_leaves AS (
            SELECT
                l.employee_id,
                l.leave_date,
                l.leave_refno,
                l.remarks AS leave_remarks,
                lt.id AS leave_type_id,
                lt.att_type,
                lt.att_type_name
            FROM main_empleave l
            LEFT JOIN leave_type lt ON l.leave_type_id = lt.id
            WHERE l.status = 'approved'
        )
        SELECT
            e.employee_id,
            e.user_id,
            e.fullname,
            u.first_name AS user_first_name,
            e.inactive_date,
            eo.outlet_names,
            eo.outlet_ids,
            da.work_date,
            da.check_in_time,
            da.check_out_time,
            da.worked_hours,
            da.attendance_status,
            da.verification_notes,
            al.leave_refno,
            al.leave_date,
            al.leave_remarks,
            al.leave_type_id,
            al.att_type,
            al.att_type_name
        FROM main_employee e
        LEFT JOIN auth_user u ON e.user_id = u.id
        LEFT JOIN emp_outlets eo ON e.employee_id = eo.employee_id
        LEFT JOIN daily_attendance da ON e.employee_id = da.employee_id
        LEFT JOIN approved_leaves al

            ON e.employee_id = al.employee_id
           AND da.work_date = al.leave_date
        WHERE e.employee_id = %s
        """
        
        params = [employee_id]

        if start_date:
            query += " AND COALESCE(da.work_date, al.leave_date) >= %s"
            params.append(start_date)

        if end_date:
            query += " AND COALESCE(da.work_date, al.leave_date) <= %s"
            params.append(end_date)

        query += " ORDER BY da.work_date DESC NULLS LAST;"

        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                columns = [col[0] for col in cursor.description]
                data = [dict(zip(columns, row)) for row in cursor.fetchall()]

            if not data:
                return Response(
                    {"detail": "No report data found for this employee."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
