from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from datetime import datetime, date, timedelta


class EmployeeReportAPIView(APIView):
    """
    Returns a comprehensive employee report structured into:
    1. Employee details
    2. Daily report covering attendance, leave, and blank days
    """

    def get(self, request, employee_id, format=None):
        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")

        # 🗓️ Parse or default to current month
        today = date.today()
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        else:
            start_date = date(today.year, today.month, 1)
            if today.month == 12:
                end_date = date(today.year, 12, 31)
            else:
                end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)

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
          AND COALESCE(da.work_date, al.leave_date) >= %s
          AND COALESCE(da.work_date, al.leave_date) <= %s
        ORDER BY da.work_date DESC NULLS LAST;
        """

        params = [employee_id, start_date, end_date]

        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                columns = [col[0] for col in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

            if not rows:
                return Response(
                    {"detail": "No report data found for this employee."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # ✅ Extract employee details (same for all rows)
            first_row = rows[0]
            employee_details = {
                "employee_id": first_row["employee_id"],
                "user_id": first_row["user_id"],
                "user_first_name": first_row["user_first_name"],
                "fullname": first_row["fullname"],
                "inactive_date": first_row["inactive_date"],
                "outlet_names": first_row["outlet_names"],
                "outlet_ids": first_row["outlet_ids"],
            }

            # ✅ Prepare attendance and leave data
            attendance = []
            leaves = []
            for row in rows:
                if row["work_date"]:
                    attendance.append({
                        "work_date": row["work_date"],
                        "check_in_time": row["check_in_time"],
                        "check_out_time": row["check_out_time"],
                        "worked_hours": row["worked_hours"],
                        "attendance_status": row["attendance_status"],
                        "verification_notes": row["verification_notes"] or []
                    })

                if row["leave_date"]:
                    leaves.append({
                        "leave_date": row["leave_date"],
                        "leave_refno": row["leave_refno"],
                        "leave_remarks": row["leave_remarks"],
                        "leave_type_id": row["leave_type_id"],
                        "att_type": row["att_type"],
                        "att_type_name": row["att_type_name"]
                    })

            # ✅ Convert to lookup dicts for faster merge
            attendance_dict = {a["work_date"]: a for a in attendance}
            leave_dict = {l["leave_date"]: l for l in leaves}

            # ✅ Generate all dates in the range
            all_dates = []
            current = start_date
            while current <= end_date:
                all_dates.append(current)
                current += timedelta(days=1)

            # ✅ Combine into full daily report
            daily_report = []
            for d in all_dates:
                record = {
                    "work_date": d,
                    "check_in_time": None,
                    "check_out_time": None,
                    "worked_hours": None,
                    "attendance_status": None,
                    "verification_notes": [],
                    "leave_refno": None,
                    "leave_remarks": None,
                    "leave_type_id": None,
                    "att_type": None,
                    "att_type_name": None,
                }

                if d in attendance_dict:
                    record.update(attendance_dict[d])
                if d in leave_dict:
                    record.update(leave_dict[d])

                daily_report.append(record)

            response_data = {
                "employee_details": employee_details,
                "daily_report": daily_report,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EmployeeDetailsByUserAPIView(APIView):
    """
    Returns employee details based on the provided user_id.
    """

    def get(self, request, user_id, format=None):
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
        )
        SELECT
            e.employee_id,
            e.user_id,
            e.fullname,
            u.first_name AS user_first_name,
            e.inactive_date,
            eo.outlet_names,
            eo.outlet_ids
        FROM main_employee e
        LEFT JOIN auth_user u ON e.user_id = u.id
        LEFT JOIN emp_outlets eo ON e.employee_id = eo.employee_id
        WHERE e.user_id = %s
        """

        params = [user_id]

        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                columns = [col[0] for col in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

            if not rows:
                return Response(
                    {"detail": "No employee data found for the given user."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # ✅ Extract employee details (same for all rows)
            first_row = rows[0]
            employee_details = {
                "employee_id": first_row["employee_id"],
                "user_id": first_row["user_id"],
                "user_first_name": first_row["user_first_name"],
                "fullname": first_row["fullname"],
                "inactive_date": first_row["inactive_date"],
                "outlet_names": first_row["outlet_names"],
                "outlet_ids": first_row["outlet_ids"],
            }

            return Response(employee_details, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class EmployeeDetailsByUserAPIView(APIView):
    """
    API endpoint to get:
        - Manager info (employee_id, user_id)
        - All employees grouped by outlet that belong to the same outlets
    """

    def get(self, request, user_id, format=None):
        # Step 1: Get manager details + their outlet IDs
        manager_query = """
        WITH emp_outlets AS (
            SELECT
                e.employee_id,
                ARRAY_AGG(o.id) AS outlet_ids
            FROM main_employee e
            LEFT JOIN main_employee_outlets eo ON e.employee_id = eo.employee_id
            LEFT JOIN main_outlet o ON eo.outlet_id = o.id
            GROUP BY e.employee_id
        )
        SELECT
            e.employee_id,
            e.user_id,
            eo.outlet_ids
        FROM main_employee e
        LEFT JOIN emp_outlets eo ON e.employee_id = eo.employee_id
        WHERE e.user_id = %s
        """

        try:
            with connection.cursor() as cursor:
                cursor.execute(manager_query, [user_id])
                row = cursor.fetchone()

            if not row:
                return Response(
                    {"detail": "No employee found for the given user ID."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            manager_employee_id, manager_user_id, outlet_ids = row

            # Step 2: If manager has outlets, get all employees in those outlets
            employees_by_outlet = {}
            if outlet_ids:
                employees_query = """
                WITH outlet_ids AS (
                    SELECT UNNEST(%s::int[]) AS outlet_id
                )
                SELECT
                    e.employee_id,
                    e.user_id,
                    u.first_name AS user_first_name,
                    e.fullname,
                    o.id AS outlet_id,
                    o.name AS outlet_name
                FROM main_employee e
                LEFT JOIN auth_user u ON e.user_id = u.id
                LEFT JOIN main_employee_outlets eo ON e.employee_id = eo.employee_id
                LEFT JOIN main_outlet o ON eo.outlet_id = o.id
                WHERE o.id IN (SELECT outlet_id FROM outlet_ids)
                ORDER BY o.id, e.fullname;
                """

                with connection.cursor() as cursor:
                    cursor.execute(employees_query, [outlet_ids])
                    cols = [col[0] for col in cursor.description]
                    employees = [dict(zip(cols, row)) for row in cursor.fetchall()]

                # Group employees by outlet
                for emp in employees:
                    outlet_id = emp["outlet_id"]
                    outlet_name = emp["outlet_name"]
                    if outlet_id not in employees_by_outlet:
                        employees_by_outlet[outlet_id] = {
                            "outlet_name": outlet_name,
                            "employees": [],
                        }
                    employees_by_outlet[outlet_id]["employees"].append({
                        "employee_id": emp["employee_id"],
                        "fullname": emp["fullname"],
                        "user_first_name": emp["user_first_name"],
                        "user_id": emp["user_id"],
                    })

            # Step 3: Build the response
            response_data = {
                "manager": {
                    "employee_id": manager_employee_id,
                    "user_id": manager_user_id,
                },
                "employees_by_outlet": employees_by_outlet,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)