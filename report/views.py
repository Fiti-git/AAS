# reports/views_optimized.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from datetime import datetime, date, timedelta

MAX_RANGE_DAYS = 366  # protect against huge ranges


def parse_dates_or_default(start_date_str, end_date_str):
    today = date.today()
    if start_date_str and end_date_str:
        try:
            sd = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            ed = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD.")
    else:
        sd = date(today.year, today.month, 1)
        if today.month == 12:
            ed = date(today.year, 12, 31)
        else:
            ed = date(today.year, today.month + 1, 1) - timedelta(days=1)
    if (ed - sd).days > MAX_RANGE_DAYS:
        raise ValueError(f"Date range too large. Max {MAX_RANGE_DAYS} days allowed.")
    return sd, ed


def run_sql(query, params=None):
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        cols = [c[0] for c in cursor.description] if cursor.description else []
        rows = [dict(zip(cols, r)) for r in cursor.fetchall()] if cols else []
    return rows


# ------------------------------
# 1) DashboardOverviewAPIView
# ------------------------------
class DashboardOverviewAPIView(APIView):
    """
    Overview for ALL outlets
    """
    def get(self, request):
        try:
            query = """
            WITH emp_summary AS (
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
              SELECT COUNT(DISTINCT a.employee_id) AS present_emp
              FROM public.main_attendance a
              WHERE a.date = CURRENT_DATE
                AND (LOWER(a.status) IN ('present','late') OR a.status = '1')
            ),
            leave_today AS (
              SELECT COUNT(DISTINCT l.employee_id) AS on_leave
              FROM public.main_empleave l
              WHERE l.leave_date = CURRENT_DATE
                AND LOWER(l.status) = 'approved'
            ),
            pending_leaves AS (
              SELECT COUNT(*) AS pending_leave_req
              FROM public.main_empleave
              WHERE LOWER(status) = 'pending'
            )
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
            rows = run_sql(query)
            data = rows[0] if rows else {}
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            print("DashboardOverviewAPIView error:", e)
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------------------------------------
# 2) LeavePresenceTrendAPIView (last N days)
# ------------------------------------------------
class LeavePresenceTrendAPIView(APIView):
    """
    Trend for last N days (default 7). Query param: ?days=7 (max 30)
    """
    def get(self, request):
        try:
            days = int(request.query_params.get("days", 7))
            if days < 1 or days > 30:
                return Response({"detail": "days must be between 1 and 30"}, status=status.HTTP_400_BAD_REQUEST)

            # We will use INTERVAL placeholders - pass days as string to avoid SQL injection via formatting
            query = """
            WITH active_emp AS (
              SELECT employee_id FROM public.main_employee WHERE is_active = TRUE
            ),
            dates AS (
              SELECT generate_series(CURRENT_DATE - INTERVAL '%s days'::interval + INTERVAL '1 day', CURRENT_DATE, INTERVAL '1 day')::date AS date
            ),
            present_summary AS (
              SELECT a.date::date AS date, COUNT(DISTINCT a.employee_id) AS present_count
              FROM public.main_attendance a
              INNER JOIN active_emp e ON e.employee_id = a.employee_id
              WHERE a.date BETWEEN CURRENT_DATE - INTERVAL '%s days'::interval + INTERVAL '1 day' AND CURRENT_DATE
                AND (LOWER(a.status) IN ('present','late') OR a.status = '1')
              GROUP BY a.date::date
            ),
            leave_summary AS (
              SELECT l.leave_date::date AS date, COUNT(DISTINCT l.employee_id) AS leave_count
              FROM public.main_empleave l
              INNER JOIN active_emp e ON e.employee_id = l.employee_id
              WHERE l.leave_date BETWEEN CURRENT_DATE - INTERVAL '%s days'::interval + INTERVAL '1 day' AND CURRENT_DATE
                AND LOWER(l.status) = 'approved'
              GROUP BY l.leave_date::date
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
            params = [days, days, days]
            rows = run_sql(query, params)
            return Response(rows, status=status.HTTP_200_OK)
        except Exception as e:
            print("LeavePresenceTrendAPIView error:", e)
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------------------------------------
# 3) OutletSummaryAPIView (today)
# ------------------------------------------------
class OutletSummaryAPIView(APIView):
    """
    Summary per outlet for TODAY.
    """
    def get(self, request):
        try:
            query = """
            WITH
            emp_outlet AS (
              SELECT eo.outlet_id, e.employee_id
              FROM public.main_employee_outlets eo
              INNER JOIN public.main_employee e ON e.employee_id = eo.employee_id
              WHERE e.is_active = TRUE
            ),
            present AS (
              SELECT DISTINCT a.employee_id
              FROM public.main_attendance a
              WHERE a.date = CURRENT_DATE
                AND (LOWER(a.status) IN ('present','late') OR a.status = '1')
            ),
            on_leave AS (
              SELECT DISTINCT l.employee_id
              FROM public.main_empleave l
              WHERE l.leave_date = CURRENT_DATE
                AND LOWER(l.status) = 'approved'
            )
            SELECT
              o.id AS outlet_id,
              o.name,
              COUNT(DISTINCT eo.employee_id) AS totalemp,
              COUNT(DISTINCT eo.employee_id) FILTER (WHERE eo.employee_id IN (SELECT employee_id FROM present)) AS presentemp,
              COUNT(DISTINCT eo.employee_id) FILTER (WHERE eo.employee_id IN (SELECT employee_id FROM on_leave)) AS onleave,
              COUNT(DISTINCT eo.employee_id)
                - COUNT(DISTINCT eo.employee_id) FILTER (WHERE eo.employee_id IN (SELECT employee_id FROM present))
                - COUNT(DISTINCT eo.employee_id) FILTER (WHERE eo.employee_id IN (SELECT employee_id FROM on_leave))
                AS absentemp
            FROM emp_outlet eo
            INNER JOIN public.main_outlet o ON o.id = eo.outlet_id
            GROUP BY o.id, o.name
            ORDER BY o.id;
            """
            rows = run_sql(query)
            return Response(rows, status=status.HTTP_200_OK)
        except Exception as e:
            print("OutletSummaryAPIView error:", e)
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------------------------------------
# 4) EmployeeAttendanceSummaryAPIView (current month)
# ------------------------------------------------
class EmployeeAttendanceSummaryAPIView(APIView):
    """
    Summary per active employee for current month.
    """
    def get(self, request):
        try:
            query = """
            WITH
            emp_outlet AS (
              SELECT e.employee_id,
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
              SELECT a.employee_id, COUNT(DISTINCT a.date) AS present_days
              FROM public.main_attendance a
              WHERE a.date >= date_trunc('month', CURRENT_DATE)
                AND a.date <= CURRENT_DATE
                AND (LOWER(a.status) IN ('present','late') OR a.status = '1')
              GROUP BY a.employee_id
            ),
            leave_days AS (
              SELECT l.employee_id, COUNT(DISTINCT l.leave_date) AS leave_days
              FROM public.main_empleave l
              WHERE l.leave_date >= date_trunc('month', CURRENT_DATE)
                AND l.leave_date <= CURRENT_DATE
                AND LOWER(l.status) = 'approved'
              GROUP BY l.employee_id
            ),
            working_days AS (SELECT COUNT(*) AS total_days FROM date_range)
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
            ORDER BY eo.outlet_name, eo.fullname;
            """
            rows = run_sql(query)
            return Response(rows, status=status.HTTP_200_OK)
        except Exception as e:
            print("EmployeeAttendanceSummaryAPIView error:", e)
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------------------------------------
# 5) Outlet-filtered endpoints (By outlet_id param or query param)
# ------------------------------------------------
class DashboardOverviewByOutletAPIView(APIView):
    """
    Dashboard overview filtered by outlet_id.
    Accepts outlet_id as path param or ?outlet_id=<id> as query param.
    """
    def get(self, request, outlet_id=None):
        try:
            # allow both path param and query param
            if outlet_id is None:
                outlet_id = request.query_params.get('outlet_id', None)

            # treat 'all' or empty as None
            if outlet_id in ('all', '', None):
                # fallback to global overview
                return DashboardOverviewAPIView().get(request)

            query = """
            WITH filtered_employees AS (
              SELECT e.employee_id, e.is_active
              FROM public.main_employee e
              INNER JOIN public.main_employee_outlets eo ON eo.employee_id = e.employee_id
              WHERE eo.outlet_id = %s
            ),
            emp_summary AS (
              SELECT
                COUNT(fe.employee_id) AS total_emp,
                COUNT(fe.employee_id) FILTER (WHERE fe.is_active = TRUE) AS active_emp,
                COUNT(fe.employee_id) FILTER (WHERE fe.is_active = FALSE) AS inactive_emp
              FROM filtered_employees fe
            ),
            attendance_summary AS (
              SELECT COUNT(DISTINCT a.employee_id) AS present_emp
              FROM public.main_attendance a
              INNER JOIN filtered_employees fe ON fe.employee_id = a.employee_id
              WHERE a.date = CURRENT_DATE
                AND (LOWER(a.status) IN ('present','late') OR a.status = '1')
            ),
            leave_today AS (
              SELECT COUNT(DISTINCT l.employee_id) AS on_leave
              FROM public.main_empleave l
              INNER JOIN filtered_employees fe ON fe.employee_id = l.employee_id
              WHERE l.leave_date = CURRENT_DATE
                AND LOWER(l.status) = 'approved'
            ),
            pending_leaves AS (
              SELECT COUNT(*) AS pending_leave_req
              FROM public.main_empleave l
              INNER JOIN filtered_employees fe ON fe.employee_id = l.employee_id
              WHERE LOWER(l.status) = 'pending'
            ),
            outlet_summary AS (SELECT 1 AS outlet_count) -- since single outlet selected
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
            rows = run_sql(query, [int(outlet_id)])
            data = rows[0] if rows else {}
            data['filter_outlet_id'] = int(outlet_id)
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            print("DashboardOverviewByOutletAPIView error:", e)
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LeavePresenceTrendByOutletAPIView(APIView):
    """
    Leave/presence trend for outlet. Use ?days=7 and ?outlet_id=ID or path param.
    """
    def get(self, request, outlet_id=None):
        try:
            days = int(request.query_params.get("days", 7))
            if days < 1 or days > 30:
                return Response({"detail": "days must be between 1 and 30"}, status=status.HTTP_400_BAD_REQUEST)

            if outlet_id is None:
                outlet_id = request.query_params.get('outlet_id', None)

            if outlet_id in ('all', '', None):
                return LeavePresenceTrendAPIView().get(request)

            query = """
            WITH active_emp AS (
              SELECT DISTINCT e.employee_id
              FROM public.main_employee e
              INNER JOIN public.main_employee_outlets eo ON eo.employee_id = e.employee_id
              WHERE e.is_active = TRUE AND eo.outlet_id = %s
            ),
            dates AS (
              SELECT generate_series(CURRENT_DATE - INTERVAL '%s days'::interval + INTERVAL '1 day', CURRENT_DATE, INTERVAL '1 day')::date AS date
            ),
            present_summary AS (
              SELECT a.date::date AS date, COUNT(DISTINCT a.employee_id) AS present_count
              FROM public.main_attendance a
              INNER JOIN active_emp e ON e.employee_id = a.employee_id
              WHERE a.date BETWEEN CURRENT_DATE - INTERVAL '%s days'::interval + INTERVAL '1 day' AND CURRENT_DATE
                AND (LOWER(a.status) IN ('present','late') OR a.status = '1')
              GROUP BY a.date::date
            ),
            leave_summary AS (
              SELECT l.leave_date::date AS date, COUNT(DISTINCT l.employee_id) AS leave_count
              FROM public.main_empleave l
              INNER JOIN active_emp e ON e.employee_id = l.employee_id
              WHERE l.leave_date BETWEEN CURRENT_DATE - INTERVAL '%s days'::interval + INTERVAL '1 day' AND CURRENT_DATE
                AND LOWER(l.status) = 'approved'
              GROUP BY l.leave_date::date
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
            params = [int(outlet_id), days, days, days]
            rows = run_sql(query, params)
            return Response(rows, status=status.HTTP_200_OK)
        except Exception as e:
            print("LeavePresenceTrendByOutletAPIView error:", e)
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeeAttendanceSummaryByOutletAPIView(APIView):
    """
    Employee attendance summary for a specific outlet (current month).
    Accepts ?outlet_id or path param.
    """
    def get(self, request, outlet_id=None):
        try:
            if outlet_id is None:
                outlet_id = request.query_params.get('outlet_id', None)

            if outlet_id in ('all', '', None):
                return EmployeeAttendanceSummaryAPIView().get(request)

            query = """
            WITH
            emp_outlet AS (
              SELECT e.employee_id,
                     u.first_name AS fullname,
                     u.username AS empcode,
                     o.name AS outlet_name
              FROM public.main_employee e
              LEFT JOIN public.auth_user u ON u.id = e.user_id
              LEFT JOIN public.main_employee_outlets eo ON eo.employee_id = e.employee_id
              LEFT JOIN public.main_outlet o ON o.id = eo.outlet_id
              WHERE e.is_active = TRUE AND eo.outlet_id = %s
            ),
            date_range AS (
              SELECT generate_series(date_trunc('month', CURRENT_DATE)::date, CURRENT_DATE, '1 day'::interval) AS day
            ),
            present_days AS (
              SELECT a.employee_id, COUNT(DISTINCT a.date) AS present_days
              FROM public.main_attendance a
              INNER JOIN emp_outlet eo ON eo.employee_id = a.employee_id
              WHERE a.date >= date_trunc('month', CURRENT_DATE)
                AND a.date <= CURRENT_DATE
                AND (LOWER(a.status) IN ('present','late') OR a.status = '1')
              GROUP BY a.employee_id
            ),
            leave_days AS (
              SELECT l.employee_id, COUNT(DISTINCT l.leave_date) AS leave_days
              FROM public.main_empleave l
              INNER JOIN emp_outlet eo ON eo.employee_id = l.employee_id
              WHERE l.leave_date >= date_trunc('month', CURRENT_DATE)
                AND l.leave_date <= CURRENT_DATE
                AND LOWER(l.status) = 'approved'
              GROUP BY l.employee_id
            ),
            working_days AS (SELECT COUNT(*) AS total_days FROM date_range)
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
            ORDER BY eo.outlet_name, eo.fullname;
            """
            rows = run_sql(query, [int(outlet_id)])
            return Response(rows, status=status.HTTP_200_OK)
        except Exception as e:
            print("EmployeeAttendanceSummaryByOutletAPIView error:", e)
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------------------------------------
# 6) Employee report (full-range) and employee details
# ------------------------------------------------
class EmployeeReportAPIView(APIView):
    """
    Full-range employee report. Query params: start_date, end_date (YYYY-MM-DD)
    """
    def get(self, request, employee_id, format=None):
        try:
            start_date_str = request.query_params.get("start_date")
            end_date_str = request.query_params.get("end_date")
            start_date, end_date = parse_dates_or_default(start_date_str, end_date_str)

            query = """
            WITH emp_outlets AS (
                SELECT
                    e.employee_id,
                    STRING_AGG(o.name, ', ') AS outlet_names,
                    ARRAY_AGG(o.id) AS outlet_ids,
                    e.user_id,
                    e.fullname,
                    e.inactive_date
                FROM public.main_employee e
                LEFT JOIN public.main_employee_outlets eo ON e.employee_id = eo.employee_id
                LEFT JOIN public.main_outlet o ON eo.outlet_id = o.id
                WHERE e.employee_id = %s
                GROUP BY e.employee_id, e.user_id, e.fullname, e.inactive_date
            ),
            dates AS (
                SELECT generate_series(%s::date, %s::date, interval '1 day')::date AS day
            ),
            attendance AS (
                SELECT
                    a.employee_id,
                    a.date AS work_date,
                    MIN(a.check_in_time) AS check_in_time,
                    MAX(a.check_out_time) AS check_out_time,
                    ROUND(EXTRACT(EPOCH FROM (MAX(a.check_out_time) - MIN(a.check_in_time))) / 3600, 2) AS worked_hours,
                    MAX(a.status) AS attendance_status,
                    JSON_AGG(a.verification_notes) FILTER (WHERE a.verification_notes IS NOT NULL) AS verification_notes
                FROM public.main_attendance a
                WHERE a.date BETWEEN %s AND %s
                  AND a.employee_id = %s
                GROUP BY a.employee_id, a.date
            ),
            leaves AS (
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
                WHERE LOWER(l.status) = 'approved'
                  AND l.leave_date BETWEEN %s AND %s
                  AND l.employee_id = %s
            )
            SELECT
                eo.employee_id,
                eo.user_id,
                eo.fullname,
                u.first_name AS user_first_name,
                eo.inactive_date,
                eo.outlet_names,
                eo.outlet_ids,
                d.day AS work_date,
                a.check_in_time,
                a.check_out_time,
                a.worked_hours,
                a.attendance_status,
                a.verification_notes,
                lv.leave_refno,
                lv.leave_date,
                lv.leave_remarks,
                lv.leave_type_id,
                lv.att_type,
                lv.att_type_name
            FROM emp_outlets eo
            CROSS JOIN dates d
            LEFT JOIN attendance a ON a.employee_id = eo.employee_id AND d.day = a.work_date
            LEFT JOIN leaves lv ON lv.employee_id = eo.employee_id AND d.day = lv.leave_date
            LEFT JOIN auth_user u ON eo.user_id = u.id
            ORDER BY d.day DESC;
            """

            params = [
                employee_id,  # emp_outlets
                start_date, end_date,  # dates
                start_date, end_date, employee_id,  # attendance
                start_date, end_date, employee_id,  # leaves
            ]

            rows = run_sql(query, params)
            if not rows:
                emp_q = "SELECT employee_id, user_id, fullname, inactive_date FROM public.main_employee WHERE employee_id = %s"
                emp_rows = run_sql(emp_q, [employee_id])
                if not emp_rows:
                    return Response({"detail": "No employee found"}, status=status.HTTP_404_NOT_FOUND)
                employee_details = emp_rows[0]
                return Response({"employee_details": employee_details, "daily_report": []}, status=status.HTTP_200_OK)

            first = rows[0]
            employee_details = {
                "employee_id": first.get("employee_id"),
                "user_id": first.get("user_id"),
                "user_first_name": first.get("user_first_name"),
                "fullname": first.get("fullname"),
                "inactive_date": first.get("inactive_date"),
                "outlet_names": first.get("outlet_names"),
                "outlet_ids": first.get("outlet_ids"),
            }

            daily_report = []
            import json
            for r in rows:
                vnotes = r.get("verification_notes") or []
                if isinstance(vnotes, str):
                    try:
                        vnotes = json.loads(vnotes)
                    except Exception:
                        vnotes = [vnotes]
                entry = {
                    "work_date": r.get("work_date"),
                    "check_in_time": r.get("check_in_time"),
                    "check_out_time": r.get("check_out_time"),
                    "worked_hours": r.get("worked_hours"),
                    "attendance_status": r.get("attendance_status"),
                    "verification_notes": vnotes,
                    "leave_refno": r.get("leave_refno"),
                    "leave_remarks": r.get("leave_remarks"),
                    "leave_type_id": r.get("leave_type_id"),
                    "att_type": r.get("att_type"),
                    "att_type_name": r.get("att_type_name"),
                }
                if not entry["attendance_status"] and not entry["leave_refno"]:
                    entry["attendance_status"] = "Blank Day"
                daily_report.append(entry)

            return Response({"employee_details": employee_details, "daily_report": daily_report}, status=status.HTTP_200_OK)
        except ValueError as ve:
            return Response({"detail": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print("EmployeeReportAPIView error:", e)
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeeDetailsByUserAPIView(APIView):
    """
    Returns employee details for given user_id.
    """
    def get(self, request, user_id, format=None):
        try:
            query = """
            WITH emp_outlets AS (
                SELECT
                    e.employee_id,
                    STRING_AGG(o.name, ', ') AS outlet_names,
                    ARRAY_AGG(o.id) AS outlet_ids
                FROM public.main_employee e
                LEFT JOIN public.main_employee_outlets eo ON e.employee_id = eo.employee_id
                LEFT JOIN public.main_outlet o ON eo.outlet_id = o.id
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
            FROM public.main_employee e
            LEFT JOIN public.auth_user u ON e.user_id = u.id
            LEFT JOIN emp_outlets eo ON e.employee_id = eo.employee_id
            WHERE e.user_id = %s
            """
            rows = run_sql(query, [user_id])
            if not rows:
                return Response({"detail": "No employee data found for the given user."}, status=status.HTTP_404_NOT_FOUND)
            first = rows[0]
            employee_details = {
                "employee_id": first.get("employee_id"),
                "user_id": first.get("user_id"),
                "user_first_name": first.get("user_first_name"),
                "fullname": first.get("fullname"),
                "inactive_date": first.get("inactive_date"),
                "outlet_names": first.get("outlet_names"),
                "outlet_ids": first.get("outlet_ids"),
            }
            return Response(employee_details, status=status.HTTP_200_OK)
        except Exception as e:
            print("EmployeeDetailsByUserAPIView error:", e)
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
