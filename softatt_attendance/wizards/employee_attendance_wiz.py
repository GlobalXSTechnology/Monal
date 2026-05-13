from datetime import datetime, timedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import xlsxwriter
import base64
from io import BytesIO
from odoo.tools import date_utils
import logging

_logger = logging.getLogger(__name__)


class SaEmployeeReportWiz(models.TransientModel):
    _name = 'sa.employee.report.wizard'
    _description = 'Employee Report Wizard'

    filter_type = fields.Selection([
        ('employee', 'Employee'),
        ('department', 'Department'),
        ('company', 'Company'),
    ], string="Report Type", default='employee', required=True)

    date_from = fields.Date(string="From", default=lambda self: fields.Date.today(), required=True)
    date_to = fields.Date(string="To", default=lambda self: fields.Date.today(), required=True)

    employee_ids = fields.Many2many('hr.employee', string="Employees")
    department_ids = fields.Many2many('hr.department', string="Departments")
    company_id = fields.Many2one('res.company', string="Company")

    datas = fields.Binary('File', readonly=True)
    checkout_miss = fields.Boolean(string="Checkout Missing Only")

    def _get_dates(self, s, e):
        date_range = [[
            s + timedelta(days=x),
            date_utils._softatt_localize(s + timedelta(days=x), self.env.user.tz).date()
        ] for x in range((e - s).days + 1)]
        return date_range

    def _get_employees(self):
        """Return employee recordset based on filter type."""

        if self.filter_type == 'employee':
            if not self.employee_ids:
                raise ValidationError("Please select at least one employee.")
            return self.employee_ids

        if self.filter_type == 'department':
            if not self.department_ids:
                raise ValidationError("Please select at least one department.")
            employees = self.env['hr.employee'].search([
                ('department_id', 'in', self.department_ids.ids)
            ])
            if not employees:
                raise ValidationError("No employees found in selected department(s).")
            return employees

        if self.filter_type == 'company':
            if not self.company_id:
                raise ValidationError("Please select a company.")
            employees = self.env['hr.employee'].search([
                ('company_id', '=', self.company_id.id)
            ])
            if not employees:
                raise ValidationError("No employees found in selected company.")
            return employees

        return self.env['hr.employee']

    def action_export_to_excel(self):
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)

        bold = workbook.add_format({'bold': True})

        report = self.env['report.softatt_attendance.employee_report']
        s, e = date_utils._softatt_get_span_dates(self.date_from, self.date_to, self.env.user.tz)

        employees = self._get_employees()

        for employee in employees:
            worksheet = workbook.add_worksheet(employee.name[:30])

            headers = ['Employee', 'Title', 'Shift', 'Date', 'Day of the Week',
                       'Check In', 'Check Out', 'Worked Hours', 'Late Minutes', 'Overtime']
            worksheet.write_row(0, 0, headers, bold)

            row = 1

            employee_name = employee.name
            job_title = employee.job_title or '-'
            shift = employee.resource_calendar_id.name or '-'

            lines = report._lines(employee.id, {
                'form': {
                    'date_from': s,
                    'date_to': e,
                    '_from': str(self.date_from),
                    '_to': str(self.date_to),
                    'checkout_miss': self.checkout_miss,
                }
            })

            for date_str, data in lines.items():
                worksheet.write(row, 0, employee_name)
                worksheet.write(row, 1, job_title)
                worksheet.write(row, 2, shift)
                worksheet.write(row, 3, date_str)
                worksheet.write(row, 4, report._dayofweek(date_str))

                if data and data.get('employee_id'):
                    worksheet.write(row, 5, data.get('check_in') or '-')
                    worksheet.write(row, 6, data.get('check_out') or '-')
                    worksheet.write_number(row, 7, data.get('worked_hours') or 0.0)
                    worksheet.write_number(row, 8, data.get('late_minutes') or 0)
                    worksheet.write_number(row, 9, data.get('overtime') or 0.0)
                else:
                    worksheet.merge_range(row, 5, row, 9, report._absence_str(employee.id, date_str))

                row += 1

        workbook.close()

        out = base64.encodebytes(fp.getvalue())
        self.write({'datas': out})
        fp.close()

        filename = 'Attendance_Report.xlsx'
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': f'web/content/?model={self._name}&id={self.id}&field=datas&download=true&filename={filename}',
        }

    def action_confirm(self):
        s, e = date_utils._softatt_get_span_dates(self.date_from, self.date_to, self.env.user.tz)

        employees = self._get_employees()

        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                "date_from": s,
                "date_to": e,
                "_from": self.date_from,
                "_to": self.date_to,
                "dates": self._get_dates(s, e),
                # "employee_ids": employees.read(['name', 'job_title', 'resource_calendar_id']),
                "employee_ids": employees.read(['name', 'job_title', 'resource_calendar_id', 'barcode', 'department_id']),
                "checkout_miss": self.checkout_miss,
                "filter_type": self.filter_type,
                "department_ids": self.department_ids.ids,
                "company_id": self.company_id,
            },
        }
        return self.env.ref('softatt_attendance.action_employee_report').report_action(self, data=data)


class SaEmpoyeeReport(models.AbstractModel):
    _name = 'report.softatt_attendance.employee_report'
    _description = 'Employee Report'

    def _lines(self, employee_id, data):
        date_from = data['form']['date_from']
        date_to = data['form']['date_to']

        checkout_miss = data['form'].get('checkout_miss', False)

        employee_ids = [employee_id]
        user_tz = self.env.user.tz or 'UTC'

        query = """
            SELECT
                a.employee_id,
                date_trunc('day', a.check_in AT TIME ZONE 'UTC' AT TIME ZONE %s)::date AS att_date,

                TO_CHAR(MIN(a.check_in AT TIME ZONE 'UTC' AT TIME ZONE %s), 'YYYY-MM-DD') || ' | ' ||
                TO_CHAR(MIN(a.check_in AT TIME ZONE 'UTC' AT TIME ZONE %s), 'HH24:MI:SS') AS check_in,

                TO_CHAR(MAX(a.check_out AT TIME ZONE 'UTC' AT TIME ZONE %s), 'YYYY-MM-DD') || ' | ' ||
                TO_CHAR(MAX(a.check_out AT TIME ZONE 'UTC' AT TIME ZONE %s), 'HH24:MI:SS') AS check_out,

                COALESCE(SUM(a.worked_hours), 0) AS total_worked_hours,
                COALESCE(SUM(a.late_minutes), 0) AS total_late_minutes,
                COALESCE(SUM(a.overtime_hours), 0) AS total_overtime_hours

            FROM hr_attendance a
            WHERE a.check_in::date BETWEEN %s AND %s
              AND a.employee_id IN %s
        """

        if checkout_miss:
            query += " AND a.check_in IS NOT NULL AND a.check_out IS NULL "

        query += """
            GROUP BY
                a.employee_id,
                date_trunc('day', a.check_in AT TIME ZONE 'UTC' AT TIME ZONE %s)::date

            ORDER BY att_date;
        """

        self.env.cr.execute(query, (
            user_tz, user_tz, user_tz, user_tz, user_tz,
            date_from, date_to, tuple(employee_ids),
            user_tz
        ))

        attendance_data = self.env.cr.fetchall()

        # if checkout_miss True => show only missing checkout dates
        if checkout_miss:
            final_report = {}
        else:
            _from = datetime.strptime(str(data['form']['_from']), '%Y-%m-%d').date()
            _to = datetime.strptime(str(data['form']['_to']), '%Y-%m-%d').date()
            final_report = {str(_from + timedelta(days=i)): {} for i in range((_to - _from).days + 1)}

        for row in attendance_data:
            employee_id, att_date, check_in, check_out, worked_hours, late_minutes, overtime = row

            final_report[str(att_date)] = {
                'employee_id': employee_id,
                'date': att_date,
                'check_in': check_in,
                'check_out': check_out,
                'worked_hours': worked_hours or 0,
                'late_minutes': late_minutes or 0,
                'overtime': overtime or 0
            }

        return final_report

    def _dayofweek(self, date):
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        return date_obj.strftime('%A')

    def _employee_image(self, employee_id):
        employee = self.env['hr.employee'].browse(employee_id)
        return employee.image_1920

    def _absence_str(self, employee_id, _date):
        employee = self.env['hr.employee'].browse(employee_id)
        calendar = employee.resource_calendar_id

        if not calendar:
            return 'No schedule defined'

        date = datetime.strptime(_date, '%Y-%m-%d')
        weekday = date.weekday()

        is_working_day = any(
            work_day.dayofweek == str(weekday)
            for work_day in calendar.attendance_ids
        )

        if date.date() == datetime.now().date():
            return 'Off Day' if not is_working_day else 'Absent'

        return 'Absent' if is_working_day else 'Off Day'

    def _get_report_values(self, docids, data=None):
        return {
            'data': data,
            'doc_ids': docids,
            'doc_model': 'hr.employee',
            'lines': self._lines,
            "date_from": data['form']['date_from'],
            "date_to": data['form']['date_to'],
            "_from": data['form']['_from'],
            "_to": data['form']['_to'],
            "employee_ids": data['form']['employee_ids'],
            "tz": self.env.user.tz,
            "localize": date_utils._softatt_localize,
            "dayofweek": self._dayofweek,
            "absence_str": self._absence_str,
            "employee_image": self._employee_image,
            "checkout_miss": data['form'].get('checkout_miss'),
            "filter_type": data['form'].get('filter_type'),
            "department_ids": data['form'].get('department_ids'),
            "company_id": data['form'].get('company_id'),
        }


# from datetime import datetime, timedelta
# from odoo import models, fields, api
# from odoo.exceptions import ValidationError
# import xlsxwriter
# import base64
# from io import BytesIO
# from odoo.tools import date_utils
#
# import logging
# _logger = logging.getLogger(__name__)
#
#
#
# class SaEmployeeReportWiz(models.TransientModel):
#     _name = 'sa.employee.report.wizard'
#     _description = 'Employee Report Wizard'
#
#     date_from       = fields.Date(string="From",default=lambda self: fields.Date.today(), required=True)
#     date_to         = fields.Date(string="To",default=lambda self: fields.Date.today(), required=True)
#     employee_ids    = fields.Many2many('hr.employee')
#     datas           = fields.Binary('File', readonly=True)
#     checkout_miss = fields.Boolean(string="Checkout Missing Only")
#
#
#     def _get_dates(self, s, e):
#         date_range = [[s + timedelta(days=x),
#                        date_utils._softatt_localize(s + timedelta(days=x), self.env.user.tz).date()] for x in range((e - s).days + 1)]
#         return date_range
#
#     def action_export_to_excel(self):
#         fp = BytesIO()
#         workbook = xlsxwriter.Workbook(fp)
#
#         date_format = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss'})  # DateTime format
#         bold = workbook.add_format({'bold': True})
#
#         report = self.env['report.softatt_attendance.employee_report']
#         s, e = date_utils._softatt_get_span_dates(self.date_from, self.date_to, self.env.user.tz)
#
#         for employee in self.employee_ids:
#             # Create a worksheet for each employee
#             worksheet = workbook.add_worksheet(employee.name[:30])  # Limiting worksheet name to 30 characters
#
#             # Headers
#             headers = ['Employee', 'Title', 'Shift', 'Date', 'Day of the Week', 'Check In', 'Check Out', 'Worked Hours', 'Late Minutes', 'Overtime']
#             worksheet.write_row(0, 0, headers, bold)
#
#             row = 1  # Start data rows below headers
#
#             employee_name = employee.name
#             job_title = employee.job_title or '-'
#             shift = employee.resource_calendar_id.name or '-'
#
#             # Fetch attendance lines for this employee
#             lines = report._lines(employee.id, {'form': {
#                 'date_from': s,
#                 'date_to': e,
#                 '_from': str(self.date_from),
#                 '_to': str(self.date_to),
#             }})
#
#             for date_str, data in lines.items():
#                 worksheet.write(row, 0, employee_name)
#                 worksheet.write(row, 1, job_title)
#                 worksheet.write(row, 2, shift)
#                 worksheet.write(row, 3, date_str, date_format)  # Date
#                 worksheet.write(row, 4, report._dayofweek(date_str))  # Day of the Week
#
#                 if data and data.get('employee_id'):
#                     worksheet.write(row, 5, data.get('check_in') or '-')
#                     worksheet.write(row, 6, data.get('check_out') or '-')
#                     worksheet.write_number(row, 7, data.get('worked_hours') or 0.0)
#                     worksheet.write_number(row, 8, data.get('late_minutes') or 0)
#                     worksheet.write_number(row, 9, data.get('overtime') or 0.0)
#                 else:
#                     worksheet.merge_range(row, 5, row, 9, report._absence_str(employee.id, date_str))
#                 # if data:
#                 #     # Check In and Check Out as DateTime format
#                 #     worksheet.write(row, 5, data.get('check_in', '-'), date_format)  # Check In
#                 #     worksheet.write(row, 6, data.get('check_out', '-'), date_format)  # Check Out
#                 #     worksheet.write_number(row, 7, data.get('worked_hours', 0.0))  # Worked Hours
#                 #     worksheet.write_number(row, 8, data.get('late_minutes', 0))  # Late Minutes
#                 #     worksheet.write_number(row, 9, data.get('overtime', 0.0))  # Overtime
#                 # else:
#                 #     worksheet.merge_range(row, 5, row, 9, report._absence_str(employee.id, date_str))
#
#                 row += 1
#
#         # Close the workbook
#         workbook.close()
#
#         # Get the file content
#         out = base64.encodebytes(fp.getvalue())
#         self.write({'datas': out})
#         fp.close()
#
#         # Return the file as a download link
#         filename = 'Attendance_Report.xlsx'
#         return {
#             'type': 'ir.actions.act_url',
#             'target': 'new',
#             'url': f'web/content/?model={self._name}&id={self.id}&field=datas&download=true&filename={filename}',
#         }
#
#
#     def action_confirm(self):
#         s, e = date_utils._softatt_get_span_dates(self.date_from, self.date_to, self.env.user.tz)
#         data = {
#             'ids': self.ids,
#             'model': self._name,
#             'form': {
#                 "date_from"         : s,
#                 "date_to"           : e,
#                 "_from"             : self.date_from,
#                 "_to"               : self.date_to,
#                 "dates"             : self._get_dates(s, e),
#                 "employee_ids"      : self.employee_ids.read(['name','job_title','resource_calendar_id']),
#                 "checkout_miss": self.checkout_miss,
#             },
#         }
#         return self.env.ref('softatt_attendance.action_employee_report').report_action(self, data=data)
#
#
#
#
#
#
#
# class SaEmpoyeeReport(models.AbstractModel):
#     _name = 'report.softatt_attendance.employee_report'
#     _description = 'Employee Report'
#
#
#     def _lines(self, employee_id, data):
#         date_from = data['form']['date_from']
#         date_to = data['form']['date_to']
#
#         employee_ids = [employee_id]
#         user_tz = self.env.user.tz or 'UTC'
#
#         # SQL query to fetch all dates between range and match attendance
#         # query = """
#         #         SELECT
#         #             a.employee_id,
#         #             date_trunc('day', a.check_in AT TIME ZONE 'UTC' AT TIME ZONE %s)::date AS date,
#         #             TO_CHAR(MIN(a.check_in AT TIME ZONE 'UTC' AT TIME ZONE %s), 'YYYY-MM-DD') || ' | ' ||
#         #             TO_CHAR(MIN(a.check_in AT TIME ZONE 'UTC' AT TIME ZONE %s), 'HH24:MI:SS') AS check_in,
#         #             TO_CHAR(MAX(a.check_out AT TIME ZONE 'UTC' AT TIME ZONE %s), 'YYYY-MM-DD') || ' | ' ||
#         #             TO_CHAR(MAX(a.check_out AT TIME ZONE 'UTC' AT TIME ZONE %s), 'HH24:MI:SS') AS check_out,
#         #             SUM(a.worked_hours) AS total_worked_hours,
#         #             SUM(a.late_minutes) AS total_late_minutes,
#         #             SUM(a.overtime_hours) AS total_overtime_hours
#         #         FROM hr_attendance a
#         #         WHERE a.check_in BETWEEN %s AND %s
#         #         AND a.employee_id IN %s
#         #         GROUP BY date, a.employee_id
#         #         ORDER BY date;
#         # """
#         query = """
#             SELECT
#                 a.employee_id,
#                 date_trunc('day', a.check_in AT TIME ZONE 'UTC' AT TIME ZONE %s)::date AS att_date,
#
#                 TO_CHAR(MIN(a.check_in AT TIME ZONE 'UTC' AT TIME ZONE %s), 'YYYY-MM-DD') || ' | ' ||
#                 TO_CHAR(MIN(a.check_in AT TIME ZONE 'UTC' AT TIME ZONE %s), 'HH24:MI:SS') AS check_in,
#
#                 TO_CHAR(MAX(a.check_out AT TIME ZONE 'UTC' AT TIME ZONE %s), 'YYYY-MM-DD') || ' | ' ||
#                 TO_CHAR(MAX(a.check_out AT TIME ZONE 'UTC' AT TIME ZONE %s), 'HH24:MI:SS') AS check_out,
#
#                 SUM(a.worked_hours) AS total_worked_hours,
#                 SUM(a.late_minutes) AS total_late_minutes,
#                 SUM(a.overtime_hours) AS total_overtime_hours
#
#             FROM hr_attendance a
#             WHERE a.check_in::date BETWEEN %s AND %s
#               AND a.employee_id IN %s
#
#             GROUP BY
#                 a.employee_id,
#                 date_trunc('day', a.check_in AT TIME ZONE 'UTC' AT TIME ZONE %s)::date
#
#             ORDER BY att_date;
#         """
#         # Use the tuple method to ensure correct SQL execution
#
#         self.env.cr.execute(query, (
#             user_tz, user_tz, user_tz, user_tz, user_tz,
#             date_from, date_to, tuple(employee_ids),
#             user_tz
#         ))
#         # self.env.cr.execute(query, (user_tz, user_tz, user_tz, user_tz, user_tz, date_from, date_to, tuple(employee_ids)))
#         attendance_data = self.env.cr.fetchall()
#         _from           = datetime.strptime(data['form']['_from'], '%Y-%m-%d').date()
#         _to             = datetime.strptime(data['form']['_to'], '%Y-%m-%d').date()
#
#         final_report       = {str(_from + timedelta(days=i)):{} for i in range((_to - _from).days + 1)}
#
#         # Collect attendance data
#         for row in attendance_data:
#             employee_id, date, check_in, check_out, worked_hours, late_minutes, overtime = row
#             final_report[str(date)].update({
#                 'employee_id'   : employee_id,
#                 'date'          : date,
#                 'check_in'      : check_in,
#                 'check_out'     : check_out,
#                 'worked_hours'  : worked_hours,
#                 'late_minutes'  : late_minutes,
#                 'overtime'      : overtime
#             })
#         return final_report
#
#     def _dayofweek(self, date):
#         # Convert the string to a datetime object
#         date_obj = datetime.strptime(date, '%Y-%m-%d')  # Assuming the date is in 'YYYY-MM-DD' format
#         return date_obj.strftime('%A')
#
#     def _employee_image(self, employee_id):
#         employee = self.env['hr.employee'].browse(employee_id)
#         return employee.image_1920
#
#
#
#
#     def _absence_str(self, employee_id, _date):
#         employee = self.env['hr.employee'].browse(employee_id)
#         calendar = employee.resource_calendar_id
#         if not calendar:
#             return 'No schedule defined'
#         date            = datetime.strptime(_date, '%Y-%m-%d')
#         weekday         = date.weekday()
#         is_working_day  = any(
#             work_day.dayofweek == str(weekday)
#             for work_day in calendar.attendance_ids
#         )
#         if date.date() == datetime.now().date():
#             return 'Off Day' if not is_working_day else 'Absent'
#         return 'Absent' if is_working_day else 'Off Day'
#
#     def _get_report_values(self, docids, data=None):
#         return {
#             'data': data,
#             'doc_ids': docids,
#             'doc_model': 'hr.employee',
#             'lines': self._lines,
#             "date_from": data['form']['date_from'],
#             "date_to": data['form']['date_to'],
#             "_from": data['form']['_from'],
#             "_to": data['form']['_to'],
#             "employee_ids": data['form']['employee_ids'],
#             "tz": self.env.user.tz,
#             "localize": date_utils._softatt_localize,
#             "dayofweek": self._dayofweek,
#             "absence_str": self._absence_str,
#             "employee_image": self._employee_image,
#         }
