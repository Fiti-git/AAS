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
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"detail": "Invalid date format. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            # Default to the first day of the current month
            start_date = date(today.year, today.month, 1)
            # Default to the last day of the current month
            if today.month == 12:
                end_date = date(today.year, 12, 31)
            else:
                end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)

        # The key change is here: the LEFT JOIN with approved_leaves should not be constrained
        # by da.work_date, as we want leave records even if there is no attendance record for that day.
        # The main JOIN is between the employee, daily_attendance, and approved_leaves.
        # We want records where EITHER attendance OR leave exists, constrained by the date range.

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
            FROM public.main_attendance
            WHERE DATE(check_in_time) BETWEEN %s AND %s
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
            FROM public.main_empleave l
            LEFT JOIN public.leave_type lt ON l.leave_type_id = lt.id
            WHERE l.status = 'approved'
            AND l.leave_date BETWEEN %s AND %s
        ),
        all_dates AS (
            SELECT work_date AS common_date, employee_id FROM daily_attendance
            UNION
            SELECT leave_date AS common_date, employee_id FROM approved_leaves
        )
        SELECT
            e.employee_id,
            e.user_id,
            e.fullname,
            u.first_name AS user_first_name,
            e.inactive_date,
            eo.outlet_names,
            eo.outlet_ids,
            ad.common_date AS work_date,
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
        FROM public.main_employee e
        LEFT JOIN auth_user u ON e.user_id = u.id
        LEFT JOIN emp_outlets eo ON e.employee_id = eo.employee_id
        INNER JOIN all_dates ad ON ad.employee_id = e.employee_id
        LEFT JOIN daily_attendance da ON e.employee_id = da.employee_id AND ad.common_date = da.work_date
        LEFT JOIN approved_leaves al ON e.employee_id = al.employee_id AND ad.common_date = al.leave_date
        WHERE e.employee_id = %s
        ORDER BY ad.common_date DESC;
        """

        params = [start_date, end_date, start_date, end_date, employee_id]

        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                columns = [col[0] for col in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

            if not rows:
                # Still check if employee details are available even if no daily data
                # but for simplicity keep the 404 for now
                return Response(
                    {"detail": "No report data found for this employee in the specified period."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # ✅ Extract employee details (same for all rows)
            # Use the first row where employee data is guaranteed from the main_employee table
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

            # ✅ Prepare attendance and leave data from all rows
            attendance = []
            leaves = []
            
            # Use the actual date from the row which could be da.work_date or al.leave_date
            # The FULL OUTER JOIN ensures we get a row for every day with *either* attendance or leave
            for row in rows:
                report_date = row.get("work_date") or row.get("leave_date")
                if not report_date:
                    continue # Skip if no date is found

                if row["work_date"]:
                    attendance.append({
                        "work_date": row["work_date"],
                        "check_in_time": row["check_in_time"],
                        "check_out_time": row["check_out_time"],
                        "worked_hours": row["worked_hours"],
                        "attendance_status": row["attendance_status"],
                        "verification_notes": row["verification_notes"] or [] # Correctly included
                    })

                if row["leave_date"]:
                    leaves.append({
                        "leave_date": row["leave_date"],
                        "leave_refno": row["leave_refno"],
                        "leave_remarks": row["leave_remarks"], # Correctly included
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

            # ✅ Combine into full daily report for *all* days
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
                    "leave_remarks": None, # Will be filled if leave_dict has data
                    "leave_type_id": None,
                    "att_type": None,
                    "att_type_name": None,
                }

                if d in attendance_dict:
                    record.update(attendance_dict[d])
                if d in leave_dict:
                    record.update(leave_dict[d])

                # Determine status for 'blank days'
                if not record["attendance_status"] and not record["leave_refno"]:
                     record["attendance_status"] = "Blank Day"

                daily_report.append(record)

            response_data = {
                "employee_details": employee_details,
                "daily_report": daily_report,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            # Better to log the full exception on the server side
            print(f"Database error: {e}")
            return Response({"error": "An internal server error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
class DashboardOverviewAPIView(APIView):
    def get(self, request):
        query = """
        WITH
        emp_summary AS (
          SELECT
            COUNT(*) AS total_emp,
            COUNT(*) FILTER (WHERE is_active = TRUE) AS active_emp,
            COUNT(*) FILTER (WHERE is_active = FALSE) AS inactive_emp
          FROM public.main_employee
        ),
        outlet_summary AS (
          SELECT COUNT(*) AS outlet_count FROM public.main_outlet
        ),
        attendance_summary AS (
          SELECT
            COUNT(DISTINCT employee_id) AS present_emp
          FROM public.main_attendance
          WHERE date = CURRENT_DATE
            AND (status ILIKE 'present' OR status = '1')
        ),
        leave_today AS (
          SELECT
            COUNT(DISTINCT employee_id) AS on_leave
          FROM public.main_empleave
          WHERE leave_date = CURRENT_DATE
            AND status ILIKE 'approved'
        ),
        pending_leaves AS (
          SELECT COUNT(*) AS pending_leave_req
          FROM public.main_empleave
          WHERE status ILIKE 'pending'
        )
        SELECT
          e.total_emp,
          e.active_emp,
          e.inactive_emp,
          o.outlet_count AS outlets,
          a.present_emp AS present,
          COALESCE(l.on_leave, 0) AS on_leave,
          (e.active_emp - COALESCE(a.present_emp, 0) - COALESCE(l.on_leave, 0)) AS absentee,
          p.pending_leave_req
        FROM emp_summary e
        CROSS JOIN outlet_summary o
        CROSS JOIN attendance_summary a
        CROSS JOIN leave_today l
        CROSS JOIN pending_leaves p;
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                columns = [col[0] for col in cursor.description]
                row = cursor.fetchone()
                data = dict(zip(columns, row))
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LeavePresenceTrendAPIView(APIView):
    def get(self, request):
        query = """
        WITH
        active_emp AS (
          SELECT employee_id FROM public.main_employee WHERE is_active = TRUE
        ),
        dates AS (
          SELECT generate_series(CURRENT_DATE - INTERVAL '6 days', CURRENT_DATE, INTERVAL '1 day')::date AS date
        ),
        present_summary AS (
          SELECT
            a.date::date AS date,
            COUNT(DISTINCT a.employee_id) AS present_count
          FROM public.main_attendance a
          INNER JOIN active_emp e ON e.employee_id = a.employee_id
          WHERE a.date BETWEEN CURRENT_DATE - INTERVAL '6 days' AND CURRENT_DATE
            AND (a.status ILIKE 'present' OR a.status = '1')
          GROUP BY a.date
        ),
        leave_summary AS (
          SELECT
            l.leave_date::date AS date,
            COUNT(DISTINCT l.employee_id) AS leave_count
          FROM public.main_empleave l
          INNER JOIN active_emp e ON e.employee_id = l.employee_id
          WHERE l.leave_date BETWEEN CURRENT_DATE - INTERVAL '6 days' AND CURRENT_DATE
            AND l.status ILIKE 'approved'
          GROUP BY l.leave_date
        ),
        total_emp AS (
          SELECT COUNT(*) AS active_count FROM active_emp
        )
        SELECT
          to_char(d.date, 'DD-Mon') AS date_label,
          COALESCE(l.leave_count, 0) AS leave,
          COALESCE(p.present_count, 0) AS present,
          (t.active_count - COALESCE(p.present_count, 0) - COALESCE(l.leave_count, 0)) AS not_marked
        FROM dates d
        CROSS JOIN total_emp t
        LEFT JOIN present_summary p ON d.date = p.date
        LEFT JOIN leave_summary l ON d.date = l.date
        ORDER BY d.date;
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                columns = [col[0] for col in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return Response(rows, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class OutletSummaryAPIView(APIView):
    def get(self, request):
        query = """
        WITH
        emp_outlet AS (
          SELECT
            eo.outlet_id,
            e.employee_id
          FROM public.main_employee_outlets eo
          INNER JOIN public.main_employee e ON e.employee_id = eo.employee_id
          WHERE e.is_active = TRUE
        ),
        present AS (
          SELECT DISTINCT a.employee_id
          FROM public.main_attendance a
          WHERE a.date = CURRENT_DATE
            AND (a.status ILIKE 'present' OR a.status = '1')
        ),
        on_leave AS (
          SELECT DISTINCT l.employee_id
          FROM public.main_empleave l
          WHERE l.leave_date = CURRENT_DATE
            AND l.status ILIKE 'approved'
        ),
        outlet_summary AS (
          SELECT
            o.id AS outlet_id,
            o.name,
            COUNT(DISTINCT eo.employee_id) AS totalEmp,
            COUNT(DISTINCT eo.employee_id) FILTER (WHERE eo.employee_id IN (SELECT employee_id FROM present)) AS presentEmp,
            COUNT(DISTINCT eo.employee_id) FILTER (WHERE eo.employee_id IN (SELECT employee_id FROM on_leave)) AS onLeave,
            COUNT(DISTINCT eo.employee_id)
              - COUNT(DISTINCT eo.employee_id) FILTER (WHERE eo.employee_id IN (SELECT employee_id FROM present))
              - COUNT(DISTINCT eo.employee_id) FILTER (WHERE eo.employee_id IN (SELECT employee_id FROM on_leave))
              AS absentEmp
          FROM emp_outlet eo
          INNER JOIN public.main_outlet o ON o.id = eo.outlet_id
          GROUP BY o.id, o.name
        )
        SELECT * FROM outlet_summary ORDER BY outlet_id;
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                columns = [col[0] for col in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return Response(rows, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EmployeeAttendanceSummaryAPIView(APIView):
    def get(self, request):
        query = """
        WITH
        emp_outlet AS (
          SELECT
            e.employee_id,
            u.first_name AS fullname,
            u.username AS empcode,
            o.name AS outlet_name
          FROM public.main_employee e
          LEFT JOIN public.auth_user u ON u.id = e.user_id
          LEFT JOIN public.main_employee_outlets eo ON eo.employee_id = e.employee_id
          LEFT JOIN public.main_outlet o ON o.id = eo.outlet_id
          WHERE e.is_active = TRUE
        ),
        date_range AS (
          SELECT generate_series(date_trunc('month', CURRENT_DATE)::date, CURRENT_DATE, '1 day'::interval) AS day
        ),
        present_days AS (
          SELECT
            a.employee_id,
            COUNT(DISTINCT a.date) AS present_days
          FROM public.main_attendance a
          WHERE a.date >= date_trunc('month', CURRENT_DATE)
            AND a.date <= CURRENT_DATE
            AND (a.status ILIKE 'present' OR a.status = '1')
          GROUP BY a.employee_id
        ),
        leave_days AS (
          SELECT
            l.employee_id,
            COUNT(DISTINCT l.leave_date) AS leave_days
          FROM public.main_empleave l
          WHERE l.leave_date >= date_trunc('month', CURRENT_DATE)
            AND l.leave_date <= CURRENT_DATE
            AND l.status ILIKE 'approved'
          GROUP BY l.employee_id
        ),
        working_days AS (
          SELECT COUNT(*) AS total_days FROM date_range
        ),
        employee_summary AS (
          SELECT
            eo.employee_id,
            eo.outlet_name,
            eo.fullname,
            eo.empcode,
            COALESCE(pd.present_days, 0) AS present_days,
            COALESCE(ld.leave_days, 0) AS leave_days,
            wd.total_days - COALESCE(pd.present_days, 0) - COALESCE(ld.leave_days, 0) AS absent_days
          FROM emp_outlet eo
          LEFT JOIN present_days pd ON pd.employee_id = eo.employee_id
          LEFT JOIN leave_days ld ON ld.employee_id = eo.employee_id
          CROSS JOIN working_days wd
          ORDER BY eo.outlet_name, eo.fullname
        )
        SELECT * FROM employee_summary;
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                columns = [col[0] for col in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return Response(rows, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DashboardOverviewByOutletAPIView(APIView):
    """
    Returns dashboard overview filtered by outlet_id.
    If outlet_id is not provided or is 'all', returns data for all outlets.
    """
    
    def get(self, request, outlet_id=None):
        # Get outlet_id from URL parameter or query parameter
        if outlet_id is None:
            outlet_id = request.query_params.get('outlet_id', 'all')
        
        # Convert 'all' or empty string to None for query logic
        if outlet_id == 'all' or outlet_id == '':
            outlet_id = None
        
        query = """
        WITH
        -- 1. Filter the base list of employees by outlet (if provided)
        filtered_employees AS (
            SELECT e.employee_id, e.is_active
            FROM public.main_employee e
            {outlet_join}
            {outlet_where}
        ),
        -- 2. Summarize employee counts for the filtered group
        emp_summary AS (
            SELECT
                COUNT(fe.employee_id) AS total_emp,
                COUNT(fe.employee_id) FILTER (WHERE fe.is_active = TRUE) AS active_emp,
                COUNT(fe.employee_id) FILTER (WHERE fe.is_active = FALSE) AS inactive_emp
            FROM filtered_employees fe
        ),
        -- 3. Outlet count (1 if specific outlet selected, otherwise all)
        outlet_summary AS (
            SELECT
                CASE 
                    WHEN %s IS NOT NULL THEN 1
                    ELSE COUNT(*)
                END AS outlet_count 
            FROM public.main_outlet
        ),
        -- 4. Today's presence count for the filtered active employees
        attendance_summary AS (
            SELECT
                COUNT(DISTINCT a.employee_id) AS present_emp
            FROM public.main_attendance a
            INNER JOIN filtered_employees fe ON fe.employee_id = a.employee_id AND fe.is_active = TRUE
            WHERE a.date = CURRENT_DATE
              AND (a.status ILIKE 'present' OR a.status = '1')
        ),
        -- 5. Today's approved leave count for the filtered active employees
        leave_today AS (
            SELECT
                COUNT(DISTINCT l.employee_id) AS on_leave
            FROM public.main_empleave l
            INNER JOIN filtered_employees fe ON fe.employee_id = l.employee_id AND fe.is_active = TRUE
            WHERE l.leave_date = CURRENT_DATE
              AND l.status ILIKE 'approved'
        ),
        -- 6. Pending leaves count for the filtered active employees
        pending_leaves AS (
            SELECT COUNT(*) AS pending_leave_req
            FROM public.main_empleave l
            INNER JOIN filtered_employees fe ON fe.employee_id = l.employee_id AND fe.is_active = TRUE
            WHERE l.status ILIKE 'pending'
        )
        -- 7. Final selection and Absentee calculation
        SELECT
            e.total_emp,
            e.active_emp,
            e.inactive_emp,
            o.outlet_count AS outlets,
            COALESCE(a.present_emp, 0) AS present,
            COALESCE(l.on_leave, 0) AS on_leave,
            (e.active_emp - COALESCE(a.present_emp, 0) - COALESCE(l.on_leave, 0)) AS absentee,
            p.pending_leave_req
        FROM emp_summary e
        CROSS JOIN outlet_summary o
        CROSS JOIN attendance_summary a
        CROSS JOIN leave_today l
        CROSS JOIN pending_leaves p;
        """
        
        # Dynamic query construction based on outlet_id
        if outlet_id:
            outlet_join = "INNER JOIN public.main_employee_outlets eo ON eo.employee_id = e.employee_id"
            outlet_where = "WHERE eo.outlet_id = %s"
            params = [outlet_id, outlet_id]
        else:
            outlet_join = ""
            outlet_where = ""
            params = [None]
        
        final_query = query.format(outlet_join=outlet_join, outlet_where=outlet_where)
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(final_query, params)
                columns = [col[0] for col in cursor.description]
                row = cursor.fetchone()
                data = dict(zip(columns, row))
            
            # Add outlet_id to response for clarity
            data['filter_outlet_id'] = outlet_id
            
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LeavePresenceTrendByOutletAPIView(APIView):
    """
    Returns 7-day leave/presence trend filtered by outlet_id.
    """
    
    def get(self, request, outlet_id=None):
        if outlet_id is None:
            outlet_id = request.query_params.get('outlet_id', 'all')
        
        if outlet_id == 'all' or outlet_id == '':
            outlet_id = None
        
        query = """
        WITH
        -- Filter active employees by outlet
        active_emp AS (
          SELECT DISTINCT e.employee_id 
          FROM public.main_employee e
          {outlet_join}
          WHERE e.is_active = TRUE
          {outlet_where}
        ),
        dates AS (
          SELECT generate_series(CURRENT_DATE - INTERVAL '6 days', CURRENT_DATE, INTERVAL '1 day')::date AS date
        ),
        present_summary AS (
          SELECT
            a.date::date AS date,
            COUNT(DISTINCT a.employee_id) AS present_count
          FROM public.main_attendance a
          INNER JOIN active_emp e ON e.employee_id = a.employee_id
          WHERE a.date BETWEEN CURRENT_DATE - INTERVAL '6 days' AND CURRENT_DATE
            AND (a.status ILIKE 'present' OR a.status = '1')
          GROUP BY a.date
        ),
        leave_summary AS (
          SELECT
            l.leave_date::date AS date,
            COUNT(DISTINCT l.employee_id) AS leave_count
          FROM public.main_empleave l
          INNER JOIN active_emp e ON e.employee_id = l.employee_id
          WHERE l.leave_date BETWEEN CURRENT_DATE - INTERVAL '6 days' AND CURRENT_DATE
            AND l.status ILIKE 'approved'
          GROUP BY l.leave_date
        ),
        total_emp AS (
          SELECT COUNT(*) AS active_count FROM active_emp
        )
        SELECT
          to_char(d.date, 'DD-Mon') AS date_label,
          COALESCE(l.leave_count, 0) AS leave,
          COALESCE(p.present_count, 0) AS present,
          (t.active_count - COALESCE(p.present_count, 0) - COALESCE(l.leave_count, 0)) AS not_marked
        FROM dates d
        CROSS JOIN total_emp t
        LEFT JOIN present_summary p ON d.date = p.date
        LEFT JOIN leave_summary l ON d.date = l.date
        ORDER BY d.date;
        """
        
        if outlet_id:
            outlet_join = "INNER JOIN public.main_employee_outlets eo ON eo.employee_id = e.employee_id"
            outlet_where = "AND eo.outlet_id = %s"
            params = [outlet_id]
        else:
            outlet_join = ""
            outlet_where = ""
            params = []
        
        final_query = query.format(outlet_join=outlet_join, outlet_where=outlet_where)
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(final_query, params)
                columns = [col[0] for col in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return Response(rows, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeeAttendanceSummaryByOutletAPIView(APIView):
    """
    Returns employee attendance summary for current month filtered by outlet_id.
    """
    
    def get(self, request, outlet_id=None):
        if outlet_id is None:
            outlet_id = request.query_params.get('outlet_id', 'all')
        
        if outlet_id == 'all' or outlet_id == '':
            outlet_id = None
        
        query = """
        WITH
        emp_outlet AS (
          SELECT
            e.employee_id,
            u.first_name AS fullname,
            u.username AS empcode,
            o.name AS outlet_name
          FROM public.main_employee e
          LEFT JOIN public.auth_user u ON u.id = e.user_id
          LEFT JOIN public.main_employee_outlets eo ON eo.employee_id = e.employee_id
          LEFT JOIN public.main_outlet o ON o.id = eo.outlet_id
          WHERE e.is_active = TRUE
          {outlet_where}
        ),
        date_range AS (
          SELECT generate_series(date_trunc('month', CURRENT_DATE)::date, CURRENT_DATE, '1 day'::interval) AS day
        ),
        present_days AS (
          SELECT
            a.employee_id,
            COUNT(DISTINCT a.date) AS present_days
          FROM public.main_attendance a
          INNER JOIN emp_outlet eo ON eo.employee_id = a.employee_id
          WHERE a.date >= date_trunc('month', CURRENT_DATE)
            AND a.date <= CURRENT_DATE
            AND (a.status ILIKE 'present' OR a.status = '1')
          GROUP BY a.employee_id
        ),
        leave_days AS (
          SELECT
            l.employee_id,
            COUNT(DISTINCT l.leave_date) AS leave_days
          FROM public.main_empleave l
          INNER JOIN emp_outlet eo ON eo.employee_id = l.employee_id
          WHERE l.leave_date >= date_trunc('month', CURRENT_DATE)
            AND l.leave_date <= CURRENT_DATE
            AND l.status ILIKE 'approved'
          GROUP BY l.employee_id
        ),
        working_days AS (
          SELECT COUNT(*) AS total_days FROM date_range
        ),
        employee_summary AS (
          SELECT
            eo.employee_id,
            eo.outlet_name,
            eo.fullname,
            eo.empcode,
            COALESCE(pd.present_days, 0) AS present_days,
            COALESCE(ld.leave_days, 0) AS leave_days,
            wd.total_days - COALESCE(pd.present_days, 0) - COALESCE(ld.leave_days, 0) AS absent_days
          FROM emp_outlet eo
          LEFT JOIN present_days pd ON pd.employee_id = eo.employee_id
          LEFT JOIN leave_days ld ON ld.employee_id = eo.employee_id
          CROSS JOIN working_days wd
          ORDER BY eo.outlet_name, eo.fullname
        )
        SELECT * FROM employee_summary;
        """
        
        if outlet_id:
            outlet_where = "AND eo.outlet_id = %s"
            params = [outlet_id]
        else:
            outlet_where = ""
            params = []
        
        final_query = query.format(outlet_where=outlet_where)
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(final_query, params)
                columns = [col[0] for col in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return Response(rows, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)