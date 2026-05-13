from odoo import models, fields, api
import pytz
import statistics
from datetime import datetime, timedelta, time
import logging

_logger = logging.getLogger(__name__)


class MonalAttendanceDeptGrid(models.TransientModel):
    _name = 'monal.attendance.dept.grid'
    _description = "Department Grid Attendance Report"

    select_employee = fields.Selection(
        [('department', 'Department'), ('company', 'Company')],
        string="Report Type",
        default='company',
        required=True
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        domain=lambda self: [('id', '=', self.env.company.id)],
    )

    department_id = fields.Many2many(
        'hr.department',
        string="Departments",
        domain=lambda self: [('company_id', '=', self.env.company.id)]
    )

    from_date = fields.Date(required=True)
    to_date = fields.Date(required=True)
    status_filter = fields.Selection(
        [
            ('all', 'All'),
            ('present', 'Present'),
            ('absent', 'Absent'),
            ('leave', 'Leave'),
            ('check_in_miss', 'Check In Miss'),
            ('check_out_miss', 'Check Out Miss'),
            ('off', 'Off'),
        ],
        string='Status Filter',
        default='all'
    )

    def convert_hours_to_time(self, hours_float):
        if not hours_float:
            return "00:00"
        hours = int(hours_float)
        minutes = int(round((hours_float - hours) * 60))
        return f"{hours:02d}:{minutes:02d}"

    def get_attendance_data_same(self, employees):
        datas = []
        tz = pytz.timezone('Asia/Karachi')

        total_checkins = []
        total_checkouts = []
        total_work_hours = []
        total_presents = total_leaves = total_offs = total_absents = 0
        total_check_in_miss = total_check_out_miss = 0

        if not employees:
            return [], {}

        for emp in employees:
            temp_records = []
            date_range = [self.from_date + timedelta(days=x)
                          for x in range((self.to_date - self.from_date).days + 1)]

            is_zero_shift = emp.resource_calendar_id.x_studio_is_zero if emp.resource_calendar_id else False

            contract = self.env['hr.contract'].search([
                ('employee_id', '=', emp.id),
                ('state', 'in', ['draft', 'open', 'close']),
            ], order='date_start desc', limit=1)

            contract_start = contract.date_start if contract else self.from_date
            contract_end = contract.date_end if contract and contract.date_end else self.to_date

            effective_start = max(self.from_date, contract_start)
            effective_end = min(self.to_date, contract_end)
            effective_range = [effective_start + timedelta(days=x)
                               for x in range((effective_end - effective_start).days + 1)]

            total_sundays = sum(1 for d in effective_range if d.strftime("%A") == "Sunday")

            for rec_date in date_range:
                day_name = rec_date.strftime("%A")

                record_data = {
                    'date': rec_date,
                    'day_name': day_name,
                    'check_in': "--:--",
                    'check_out': "--:--",
                    'work_hours': 0.0,
                    'net_hours': 0.0,
                    'status': 'Absent',
                    'break': 'N/A',
                    'remarks': '',
                    'm_number': '',
                    'mode': '',
                    'source': '',
                }

                if (contract_start and rec_date < contract_start) or (contract_end and rec_date > contract_end):
                    record_data['status'] = "N"
                    record_data['remarks'] = "Out of Contract"
                    temp_records.append(record_data)
                    continue

                day_start = datetime.combine(rec_date, time.min)
                day_end = datetime.combine(rec_date, time.max)

                attendance = self.env['hr.attendance'].search([
                    ('employee_id', '=', emp.id),
                    ('check_in', '>=', day_start),
                    ('check_in', '<=', day_end),
                ])

                adjustment = self.env["attendance.adjustment"].search([
                    ('name', '=', emp.id),
                    ('att_date', '=', rec_date),
                    ('state', '=', 'done'),
                ], limit=1)

                leaves = self.env["hr.leave"].search([
                    ('employee_id', '=', emp.id),
                    ('state', '=', 'validate'),
                    ('request_date_from', '<=', rec_date),
                    ('request_date_to', '>=', rec_date),
                    ('leave_encashed_check', '!=', True),
                ])

                check_in_dt = check_out_dt = None
                work_hours = net_work_hours = 0.0
                break_status = ""
                remarks = ""
                m_number = mode = source = ""
                attendance_hours = total_break_hours = 0.0

                if adjustment:
                    check_in_dt = adjustment.emp_check_in.astimezone(tz)
                    check_out_dt = adjustment.emp_check_out.astimezone(tz)
                    work_hours = adjustment.worked_hours
                    mode = "A"
                    break_logs = self.env['sa.biometric.att'].search([
                        ('emp_code', '=', emp.barcode),
                        ('punch_type', '=', 1),
                        ('punch_time', '>=', adjustment.emp_check_in),
                        ('punch_time', '<=', adjustment.emp_check_out),
                    ], order='punch_time asc')
                    for i in range(0, len(break_logs) - 1, 2):
                        break_in = break_logs[i].punch_time.astimezone(tz)
                        break_out = break_logs[i + 1].punch_time.astimezone(tz)
                        total_break_hours += (break_out - break_in).total_seconds() / 3600.0

                elif attendance:
                    first_att = attendance[0]
                    check_in_dt = first_att.check_in.astimezone(tz) if first_att.check_in else None
                    check_out_dt = first_att.check_out.astimezone(tz) if first_att.check_out else None
                    attendance_hours = sum(att.worked_hours for att in attendance)
                    work_hours = attendance_hours
                    mode = "F" if any(att.device_code and str(att.device_code) != '0' for att in attendance) else "M"
                    source = "machine" if mode == "F" else "manual"
                    m_number = first_att.checkin_device_id.id if getattr(first_att, 'checkin_device_id', False) else ""
                    break_logs = self.env['sa.biometric.att'].search([
                        ('emp_code', '=', emp.barcode),
                        ('punch_type', '=', 1),
                        ('punch_time', '>=', rec_date),
                        ('punch_time', '<', rec_date + timedelta(days=1)),
                    ], order='punch_time asc')
                    for i in range(0, len(break_logs) - 1, 2):
                        break_in = break_logs[i].punch_time.astimezone(tz)
                        break_out = break_logs[i + 1].punch_time.astimezone(tz)
                        total_break_hours += (break_out - break_in).total_seconds() / 3600.0

                net_work_hours = work_hours - total_break_hours if work_hours else 0.0
                break_status = 'B' if total_break_hours > 0 else 'N/A'

                if leaves:
                    unpaid_leave = any(leave.holiday_status_id.name.lower().find("unpaid") != -1 for leave in leaves)
                    if unpaid_leave:
                        status = "LW"
                    else:
                        status = "PL"
                    leave_names = ", ".join([leave.holiday_status_id.name for leave in leaves])
                    remarks = leave_names
                elif work_hours >= 6 or (is_zero_shift and check_out_dt):
                    status = "Present"
                elif adjustment:
                    status = "Present"
                else:
                    status = "Absent"
                    if work_hours > 0:
                        remarks = f"Worked only {work_hours:.2f} hours (less than 6)"
                record_data.update({
                    'check_in': check_in_dt.strftime("%d-%m-%Y %I:%M:%S %p") if check_in_dt else "--:--",
                    'check_out': check_out_dt.strftime("%d-%m-%Y %I:%M:%S %p") if check_out_dt else "--:--",
                    'work_hours': work_hours,
                    'net_hours': net_work_hours,
                    'status': status,
                    'break': break_status,
                    'remarks': remarks,
                    'm_number': m_number,
                    'mode': mode,
                    'source': source,
                })

                temp_records.append(record_data)

            offs_marked = 0
            for record in temp_records:
                if record['status'] == 'Absent' and offs_marked < total_sundays:
                    record['status'] = 'Off'
                    record['remarks'] = "Weekly Off"
                    offs_marked += 1

            datas.extend(temp_records)

        return datas

    def get_employee_grid_data(self, employee):
        datas = self.get_attendance_data_same([employee])
        grid = {}
        counts = {'P': 0, 'A': 0, 'L': 0, 'O': 0}

        total_hours = 0
        present_days = 0

        for rec in datas:
            day = rec['date'].day
            status = rec['status']
            work_hours = rec.get('work_hours', 0)

            total_hours += work_hours

            if status == "Present":
                code = "P"
                counts['P'] += 1
                present_days += 1

            elif status in ["Leave", "PL"]:
                code = "PL"
                counts['PL'] = counts.get('PL', 0) + 1

            elif status in ["Unpaid", "LW"]:
                code = "LW"
                counts['LW'] = counts.get('LW', 0) + 1

            elif status == "Off":
                code = "O"
                counts['O'] += 1

            elif status == "N":
                code = "N"
                counts['N'] = counts.get('N', 0) + 1

            else:
                code = "A"
                counts['A'] += 1

            grid[str(day)] = code

        avg_hours = total_hours / present_days if present_days else 0

        total_work_hours = self.convert_hours_to_time(total_hours)
        avg_time = self.convert_hours_to_time(avg_hours)

        _logger.info(f"{employee.name} grid: {grid}, counts: {counts}")

        return grid, counts, total_work_hours, avg_time

    def print_dept_grid_report(self):
        if self.select_employee == 'company':
            employees = self.env['hr.employee'].search([
                ('company_id', '=', self.company_id.id)
            ])
        else:
            employees = self.env['hr.employee'].search([
                ('department_id', 'in', self.department_id.ids),
                ('company_id', '=', self.company_id.id)
            ])
        _logger.info(f"Employees fetched: {[emp.name for emp in employees]}")

        data = {
            'from_date': self.from_date,
            'to_date': self.to_date,
            'company_name': self.company_id.name,
            'departments': {},
        }

        for emp in employees:
            grid, counts, total_work_hours, avg_time = self.get_employee_grid_data(emp)
            if self.status_filter == 'present' and counts.get('P', 0) == 0:
                continue
            if self.status_filter == 'absent' and counts.get('A', 0) == 0:
                continue
            if self.status_filter == 'leave' and counts.get('L', 0) == 0:
                continue
            if self.status_filter == 'off' and counts.get('O', 0) == 0:
                continue

            dept_name = emp.department_id.name or "No Department"
            if dept_name not in data['departments']:
                data['departments'][dept_name] = []

            data['departments'][dept_name].append({
                'barcode': emp.barcode,
                'name': emp.name,
                'cnic': emp.identification_id,
                'doj': emp.first_contract_date.strftime('%d-%m-%Y') if emp.first_contract_date else '',
                'designation': emp.job_id.name if emp.job_id else '',
                'grid': grid,
                'counts': counts,
                'total_work_hours': total_work_hours,
                'avg_time': avg_time,
            })



        return self.env.ref(
            'monal_attendance_dept_grid_report.action_attendance_dept_grid_report'
        ).report_action(self, data=data)


class ReportAttendanceDeptGrid(models.AbstractModel):
    _name = 'report.monal_attendance_dept_grid_report.attendance_template'
    _description = 'Attendance Dept Grid Report'

    def _get_report_values(self, docids, data=None):
        data = data or {}
        from_date = data.get('from_date')
        to_date = data.get('to_date')

        if isinstance(from_date, str):
            from_date = datetime.strptime(from_date, "%Y-%m-%d").date()
        if isinstance(to_date, str):
            to_date = datetime.strptime(to_date, "%Y-%m-%d").date()

        date_list = []
        if from_date and to_date:
            current = from_date
            while current <= to_date:
                date_list.append(current)
                current += timedelta(days=1)

        return {
            'docs': self.env['monal.attendance.dept.grid'].browse(docids),
            'report_data': data,
            'date_list': date_list,
        }
