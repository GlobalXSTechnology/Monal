from odoo import models, fields, api
from datetime import date, datetime, timedelta, time
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
import pytz
import logging
import statistics

_logger = logging.getLogger(__name__)


class WorkEntry(models.Model):
    _inherit = 'hr.work.entry'

    def write(self, vals):
        if self.env.context.get('skip_work_entry_validation'):
            return super().write(vals)
        return super().write(vals)


class SABiomatricDevice(models.Model):
    _inherit = 'sa.biometric.device'

    machine_code = fields.Char(string="Machine Code", store=True)


class HRAttendance(models.Model):
    _inherit = 'hr.attendance'

    machine_code = fields.Char(string="Machine Code", compute="_compute_machine_code", store=False)

    @api.depends('device_code')
    def _compute_machine_code(self):
        for rec in self:
            if rec.device_code:
                machine = rec.env['sa.biometric.device'].browse(rec.device_code)
                rec.machine_code = machine.machine_code or False
            else:
                rec.machine_code = False

    def write(self, vals):
        if self.env.context.get('skip_work_entry_validation'):
            return super().write(vals)
        return super().write(vals)

    def _check_validated_work_entries(self):
        # ? Bypass validation when context flag is set
        if self.env.context.get('skip_work_entry_validation'):
            return
        return super()._check_validated_work_entries()


class MonalAttendanceReportEmp(models.TransientModel):
    _name = 'monal.attendance.report.employee'
    _description = "Attendance Report Wizard"

    show_time_filter = fields.Boolean(string="Enable Time Filter")
    archived_employee = fields.Boolean(string="Archive Employee", default=False)
    check_in_time = fields.Float(
        string="Check In Time",
        help="Filter for Check In"
    )
    check_out_time = fields.Float(
        string="Check Out Time",
        help="Filter for Check Out"
    )

    # Naya Attendance Source Filter
    source_filter = fields.Selection(
        [
            ('all', 'All'),
            ('machine', 'File Load Attendance'),
            ('manual', 'Manual Attendance'),
        ],
        string="Attendance Status",
        default='all',
        required=True
    )

    # Enhanced Status Filter
    status_filter = fields.Selection(
        [
            ('all', 'All'),
            ('present', 'Present'),
            ('absent', 'Absent'),
            ('leave', 'Leave'),
            # ('check_in_miss', 'Check In Miss'),
            ('check_out_miss', 'Check Out Miss'),
            ('off', 'Off'),
            ('Work_hours', 'Work Hours'),
        ],
        string="Status Filter",
        default='all',
        required=True
    )

    work_hours_filter = fields.Float(
        string="Work Hours",
        help="Filter for specific work hours (e.g., 1, 2, 3 hours)"
    )

    select_employee = fields.Selection(
        [
            ('employee', 'Employee'),
            ('department', 'Department'),
            ('company', 'Company'),
        ],
        string="Report Type",
        default='employee',
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

    employee_ids = fields.Many2many(
        'hr.employee',
        string="Employees",
        domain=lambda self: [('company_id', '=', self.env.company.id)]
    )
    from_date = fields.Date(
        'From Date',
        default=lambda self: fields.Date.to_string(date.today()),
        required=True
    )
    to_date = fields.Date(
        "To Date",
        default=lambda self: fields.Date.to_string(
            (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()
        ),
        required=True
    )

    @api.onchange('select_employee')
    def _onchange_select_employee(self):
        self.company_id = False
        self.department_id = False
        self.employee_ids = [(5, 0, 0)]

    def get_selected_employees(self):
        company = self.env.company
        today = fields.Date.today()

        # Base domain with company filter
        base_domain = [('company_id', '=', company.id)]

        if self.select_employee == 'employee' and self.employee_ids:
            employees = self.employee_ids.filtered(lambda e: e.company_id == company)

        elif self.select_employee == 'department' and self.department_id:
            employees = self.env['hr.employee'].search([
                ('department_id', 'in', self.department_id.ids),
                ('company_id', '=', company.id)
            ])
            if self.archived_employee:
                employees2 = self.env['hr.employee'].search([
                    ('department_id', 'in', self.department_id.ids),
                    ('company_id', '=', company.id), ('active', '=', False)
                ])
                employees = employees + employees2

        elif self.select_employee == 'company':
            employees = self.env['hr.employee'].search([
                ('company_id', '=', company.id)
            ])
            if self.archived_employee:
                employees2 = self.env['hr.employee'].search([
                    ('company_id', '=', company.id), ('active', '=', False)
                ])
                employees = employees + employees2

        else:
            employees = self.env['hr.employee'].browse([])
            if self.archived_employee:
                employees2 = self.env['hr.employee'].search([
                    ('active', '=', False)
                ])
                employees = employees + employees2

        # ✅ Filter employees with running contracts only
        filtered_employees = self.env['hr.employee']

        for employee in employees:
            # Get the most recent contract
            contract = self.env['hr.contract'].search([
                ('employee_id', '=', employee.id),
                ('state', 'in', ['draft', 'open', 'close']),

            ], order='date_start desc', limit=1)

            if contract:
                contract_start = contract.date_start
                contract_end = contract.date_end or today

                if contract_start <= self.to_date and contract_end >= self.from_date:
                    filtered_employees |= employee

        return filtered_employees

    def get_leave_allocations(self, employee):
        """Fetch leave allocations for employee - ALL leaves"""
        allocations = []

        # Get all leave types allocated to this employee
        leave_allocations = self.env['hr.leave.allocation'].search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'validate'),
        ])

        # Group by leave type to sum multiple allocations
        leave_type_dict = {}

        for allocation in leave_allocations:
            leave_type = allocation.holiday_status_id
            allocated_days = allocation.number_of_days

            if leave_type.id not in leave_type_dict:
                leave_type_dict[leave_type.id] = {
                    'leave_type': leave_type.name,
                    'allocated': 0,
                    'taken_in_period': 0,
                    'total_taken': 0,
                    'remaining': 0,
                }

            leave_type_dict[leave_type.id]['allocated'] += allocated_days

        # Calculate taken and remaining for each leave type
        for leave_type_id, leave_data in leave_type_dict.items():
            # Get taken leaves that OVERLAP with the report period
            taken_in_period = self.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('holiday_status_id', '=', leave_type_id),
                ('state', '=', 'validate'),
                ('request_date_from', '<=', self.to_date),
                ('request_date_to', '>=', self.from_date),
                ('leave_encashed_check', '!=', True),
            ])

            # Get TOTAL taken leaves (all time)
            total_taken = self.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('holiday_status_id', '=', leave_type_id),
                ('state', '=', 'validate'),
                ('leave_encashed_check', '!=', True),
            ])

            # Calculate actual days taken within the report period
            taken_in_period_days = 0
            for leave in taken_in_period:
                # Calculate the overlap between leave period and report period
                overlap_start = max(leave.request_date_from, self.from_date)
                overlap_end = min(leave.request_date_to, self.to_date)

                # Count days in the overlap
                if overlap_start <= overlap_end:
                    days_count = (overlap_end - overlap_start).days + 1
                    taken_in_period_days += days_count

            total_taken_days = sum(total_taken.mapped('number_of_days'))

            leave_data['taken_in_period'] = taken_in_period_days
            leave_data['total_taken'] = total_taken_days
            leave_data['remaining'] = leave_data['allocated'] - total_taken_days

            allocations.append(leave_data)

        # Sort by leave type name
        allocations = sorted(allocations, key=lambda x: x['leave_type'])

        return allocations

    def convert_hours_to_time(self, hours):
        """Convert decimal hours to HH:MM:SS format"""
        if not hours or hours <= 0:
            return ""

        total_seconds = int(hours * 3600)
        hours_int = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        return f"{hours_int:02d}:{minutes:02d}:{seconds:02d}"

    def get_attendance_data(self, employees):
        datas = []
        tz = pytz.timezone('Asia/Karachi')

        total_checkins = []
        total_checkouts = []
        total_work_hours = []
        total_presents = 0
        total_leaves = 0
        total_offs = 0
        total_absents = 0
        total_check_in_miss = 0
        total_check_out_miss = 0

        if not employees:
            return [], {
                'avg_check_in': "--:--",
                'avg_check_out': "--:--",
                'avg_hours': "",
                'total_work_hours': "",
                'total_present': 0,
                'total_leave': 0,
                'total_off': 0,
                'total_absent': 0,
                'total_check_in_miss': 0,
                'total_check_out_miss': 0,
            }

        for emp in employees:
            is_rec_leaves = False
            temp_records = []
            date_range = [self.from_date + timedelta(days=x)
                          for x in range((self.to_date - self.from_date).days + 1)]

            is_zero_shift = emp.resource_calendar_id.x_studio_is_zero if emp.resource_calendar_id else False

            # total_sundays = sum(1 for d in date_range if d.strftime("%A") == "Sunday")
            # _logger.info(f"Total Sundays in period for {emp.name}: {total_sundays}")
            contract = self.env['hr.contract'].search([
                ('employee_id', '=', emp.id),
                ('state', 'in', ['draft', 'open', 'close']),
            ], order='date_start desc', limit=1)

            contract_start = contract.date_start if contract else self.from_date
            contract_end = contract.date_end if contract and contract.date_end else self.to_date

            # Effective range (intersection of report range and contract range)
            effective_start = max(self.from_date, contract_start)
            effective_end = min(self.to_date, contract_end)

            effective_range = [
                effective_start + timedelta(days=x)
                for x in range((effective_end - effective_start).days + 1)
            ]

            total_sundays = sum(1 for d in effective_range if d.strftime("%A") == "Sunday")

            for rec_date in date_range:
                day_name = rec_date.strftime("%A")

                contract = self.env['hr.contract'].search([
                    ('employee_id', '=', emp.id),
                    ('state', 'in', ['draft', 'open', 'close']),
                ], order='date_start desc', limit=1)
                contract_start = contract.date_start if contract else None
                contract_end = contract.date_end if contract else None

                if (contract_start and rec_date < contract_start) or (contract_end and rec_date > contract_end):
                    temp_records.append({
                        'date': rec_date,
                        'day_name': day_name,
                        'check_in': "--:--",
                        'check_out': "--:--",
                        'work_hours': 0.0,
                        'net_hours': 0.0,
                        'status': 'N/A',
                        'break': 'N/A',
                        'remarks': '',
                        'm_number': '',
                        'mode': '',
                        'source': '',
                    })
                    continue

                check_in = "--:--"
                check_out = "--:--"
                work_hours = 0.0
                net_work_hours = 0.0
                status = "Absent"
                break_status = ""
                remarks = ""
                m_number = ""
                mode = ""
                source = ""
                adjustment = self.env["attendance.adjustment"].search([
                    ('name', '=', emp.id),
                    ('att_date', '=', rec_date),
                    ('state', '=', 'done'),
                ], limit=1)

                if adjustment:
                    _logger.info(f"Found adjustment for {emp.name} on {rec_date}: {adjustment.notes}")
                    if adjustment.notes:
                        remarks = adjustment.notes

                day_start = datetime.combine(rec_date, time.min)
                day_end = datetime.combine(rec_date, time.max)

                day_start = datetime.combine(rec_date, time.min)
                day_end = datetime.combine(rec_date, time.max)

                attendance = self.env['hr.attendance'].search([
                    ('employee_id', '=', emp.id),
                    ('attend_check_in', '=', rec_date),
                    # ('check_in', '<=', day_end),
                ])

                _logger.info(f"{day_end}---------{day_start}")

                # attendance = self.env["hr.attendance"].search([
                #     ('employee_id', '=', emp.id),
                # ('check_in', '<=', day_end),
                # ('check_out', '>=', day_start),
                # ])
                #

                # _logger.info('attendanceeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee')
                # _logger.info('attendanceeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee')
                # _logger.info('attendanceeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee')
                # _logger.info(attendance)

                leaves = self.env["hr.leave"].search([
                    ('employee_id', '=', emp.id),
                    ('state', '=', 'validate'),
                    ('request_date_from', '<=', rec_date),
                    ('request_date_to', '>=', rec_date),
                    ('leave_encashed_check', '!=', True),
                ])

                if attendance:
                    # device_code = getattr(attendance, 'device_code', 0)
                    device_codes = attendance.mapped('device_code')
                    if any(str(code) != '0' and code for code in device_codes):
                        source = "machine"
                    else:
                        source = "manual"

                    if adjustment:
                        mode = "A"
                    elif source == "machine":
                        mode = "F"
                    else:
                        mode = "M"

                    # mode = "A" if adjustment else "F" if source == "machine" else "M"

                    # if device_code and str(device_code) != '0':
                    # source = "machine"
                    # mode = "A" if adjustment else "F"
                    # else:
                    #     source = "manual"
                    #     mode = "M"

                    attendance_hours = 0.0
                    total_break_hours = 0.0
                    tz = pytz.timezone('Asia/Karachi')
                    check_in_dt = None
                    check_out_dt = None

                    for att in attendance:
                        m_number = att.machine_code
                        att2 = self.env['hr.attendance'].search([
                            ('employee_id', '=', emp.id),
                            ('attend_check_in', '=', att.attend_check_in),

                        ])
                        if len(att2) > 1 and 5 == 9:
                            for u in att2:
                                if u.check_out:
                                    att = u
                        if att.attend_check_in:
                            is_rec_leaves = self.env["hr.leave"].search([
                                ('employee_id', '=', emp.id),
                                ('state', '=', 'validate'),
                                ('request_date_from', '<=', att.attend_check_in),
                                ('request_date_to', '>=', att.attend_check_in),
                                ('leave_encashed_check', '!=', True),
                            ])
                        else:
                            is_rec_leaves = self.env["hr.leave"].search([
                                ('employee_id', '=', emp.id),
                                ('state', '=', 'validate'),
                                ('request_date_from', '<=', att.check_in.date()),
                                ('request_date_to', '>=', att.check_in.date()),
                                ('leave_encashed_check', '!=', True),
                            ])
                            # if not att.check_in or not att.check_out:
                        if not att.check_in:
                            continue

                        check_in_dt = att.check_in.astimezone(tz)
                        check_out_dt = att.check_out.astimezone(tz) if att.check_out else False
                        # att_hours = (att.check_out - att.check_in).total_seconds() / 3600.0
                        # attendance_hours += att.worked_hours
                        attendance_hours = att.worked_hours

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
                    if adjustment:
                        check_in_dt = adjustment.emp_check_in.astimezone(tz)
                        check_out_dt = adjustment.emp_check_out.astimezone(tz)
                        attendance_hours = adjustment.worked_hours
                        break_logs = self.env['sa.biometric.att'].search([
                            ('emp_code', '=', emp.barcode),
                            ('punch_type', '=', 1),
                            ('punch_time', '>=', adjustment.emp_check_in),
                            ('punch_time', '<=', adjustment.emp_check_out),
                        ], order='punch_time asc')
                        total_break_hours = 0.0
                        for i in range(0, len(break_logs) - 1, 2):
                            break_in = break_logs[i].punch_time.astimezone(tz)
                            break_out = break_logs[i + 1].punch_time.astimezone(tz)
                            total_break_hours += (break_out - break_in).total_seconds() / 3600.0

                    net_work_hours = attendance_hours - total_break_hours if attendance_hours else 0.0
                    break_status = 'B' if total_break_hours > 0 else 'N/A'

                    check_in = check_in_dt.strftime("%d-%m-%Y %I:%M:%S %p") if check_in_dt else "-"
                    check_in_hour = check_in_dt.hour + check_in_dt.minute / 60.0 if check_in_dt else 0

                    check_out = check_out_dt.strftime("%d-%m-%Y %I:%M:%S %p") if check_out_dt else "-"
                    check_out_hour = check_out_dt.hour + check_out_dt.minute / 60.0 if check_out_dt else 0

                    work_hours = float(attendance_hours or 0.0)
                    # m_number = attendance[0].checkin_device_id.id if attendance and getattr(attendance[0],
                    #                                                                         'checkin_device_id',
                    #                                                                         False) else ""

                    if is_zero_shift:
                        if check_out_dt:
                            status = "Present"
                        else:
                            status = "Absent"

                    elif work_hours >= 6:
                        status = "Present"
                    elif is_rec_leaves:
                        status = "Unpaid"
                    else:
                        status = "Absent"
                        if remarks == "":
                            remarks = f"Worked only {work_hours:.2f} hours (less than 6 hours)"
                        else:
                            remarks += f" | Worked only {work_hours:.2f} hours (less than 6 hours)"

                    # if attendance.check_in and attendance.check_out:
                    #     status = "Present"
                    # elif attendance.check_in and not attendance.check_out:
                    #     status = "Check Out Miss"
                    # elif not attendance.check_in and attendance.check_out:
                    #     status = "Check In Miss"
                    # else:
                    #     status = "Absent"

                    # if not is_zero_shift and work_hours < 6.0 and status == "Present":
                    #     status = "Absent"
                    #     if remarks == "":
                    #         remarks = f"Worked only {work_hours:.2f} hours (less than 6 hours)"
                    #     else:
                    #         remarks += f" | Worked only {work_hours:.2f} hours (less than 6 hours)"

                    # Apply time filters

                    if status == "Present":
                        if check_in_dt:
                            total_checkins.append(check_in_dt)
                        if check_out_dt:
                            total_checkouts.append(check_out_dt)
                        total_work_hours.append(work_hours)
                        # total_presents += 1

                    if self.check_in_time and check_in_hour < self.check_in_time:
                        continue

                    if self.check_out_time and (not check_out_hour or check_out_hour > self.check_out_time):
                        continue



                elif leaves:
                    status = "Leave"
                    leave_names = ", ".join([leave.holiday_status_id.name for leave in leaves])
                    if remarks == "":
                        remarks = leave_names
                    else:
                        remarks += " | " + leave_names
                    # total_leaves += 1
                elif adjustment:
                    check_in_dt = adjustment.emp_check_in.astimezone(tz)
                    check_out_dt = adjustment.emp_check_out.astimezone(tz)
                    attendance_hours = adjustment.worked_hours
                    check_in = check_in_dt.strftime("%d-%m-%Y %I:%M:%S %p") if check_in_dt else "-"
                    check_out = check_out_dt.strftime("%d-%m-%Y %I:%M:%S %p") if check_out_dt else "-"
                    work_hours = float(attendance_hours or 0.0)
                    mode = "A"
                    if is_zero_shift:
                        if check_out_dt:
                            status = "Present"
                        else:
                            status = "Absent"
                    elif work_hours >= 6:
                        status = "Present"
                    elif is_rec_leaves:
                        status = "Unpaid"
                    else:
                        status = "Absent"
                    break_logs = self.env['sa.biometric.att'].search([
                        ('emp_code', '=', emp.barcode),
                        ('punch_type', '=', 1),
                        ('punch_time', '>=', adjustment.emp_check_in),
                        ('punch_time', '<=', adjustment.emp_check_out),
                    ], order='punch_time asc')
                    total_break_hours = 0.0
                    for i in range(0, len(break_logs) - 1, 2):
                        break_in = break_logs[i].punch_time.astimezone(tz)
                        break_out = break_logs[i + 1].punch_time.astimezone(tz)
                        total_break_hours += (break_out - break_in).total_seconds() / 3600.0

                    net_work_hours = attendance_hours - total_break_hours if attendance_hours else 0.0

                # ✅ Store temporary record
                temp_records.append({
                    'date': rec_date,
                    'day_name': day_name,
                    'check_in': check_in,
                    'check_out': check_out,
                    'work_hours': work_hours,
                    'net_hours': net_work_hours,
                    'status': status,
                    'break': break_status,
                    'remarks': remarks,
                    'm_number': m_number,
                    'mode': mode,
                    'source': source,
                })

            offs_to_mark = total_sundays
            offs_marked = 0

            for record in temp_records:
                # Mark first N absents as "Off" based on Sunday count
                if record['status'] == 'Absent' and offs_marked < offs_to_mark:

                    if record['work_hours'] >= 6:
                        record['status'] = 'Present'
                    else:
                        record['status'] = 'Off'

                    if record['remarks'] == "":
                        record['remarks'] = "Rest"
                    else:
                        record['remarks'] += " | Rest"
                    offs_marked += 1
            _logger.info(f"Marked {offs_marked} absents as Off for {emp.name} (out of {total_sundays} Sundays)")

            # ✅ Now create final records and count statuses
            for record in temp_records:
                final_record = {
                    'code': emp.barcode or '',
                    'name': emp.name or '',
                    'job_id': emp.job_id.name or '',
                    'department_id': emp.department_id.name or '',
                    'shift': emp.resource_calendar_id.name or '',
                    'date': record['date'].strftime("%d-%m-%Y"),
                    'grp_date': emp.contract_id.x_studio_group_joining_date.strftime(
                        "%d-%m-%Y") if emp.contract_id.x_studio_group_joining_date else '',
                    'day': record['day_name'],
                    'check_in': record['check_in'],
                    'check_out': record['check_out'],
                    'work_hours': self.convert_hours_to_time(record['work_hours']),
                    'net_hours': self.convert_hours_to_time(record['net_hours']),
                    'status': record['status'],
                    'remarks': record['remarks'],
                    'm_number': record['m_number'],
                    'mode': record['mode'],
                    'source': record['source'],
                    'break': record.get('break', 'N/A'),

                }

                # ✅ Count statuses for summary
                if record['status'] == 'Present':
                    total_presents += 1
                elif record['status'] == 'Off':
                    total_offs += 1
                elif record['status'] == 'Absent':
                    total_absents += 1
                elif record['status'] == 'Check In Miss':
                    total_check_in_miss += 1
                elif record['status'] == 'Check Out Miss':
                    total_check_out_miss += 1
                elif record['status'] in ['Leave', 'Unpaid']:
                    total_leaves += 1

                # ✅ Apply status filters
                should_include = True

                # Status filter apply karo
                if self.status_filter != 'all':
                    if self.status_filter == 'present' and final_record['status'] != 'Present':
                        should_include = False
                    elif self.status_filter == 'absent' and final_record['status'] != 'Absent':
                        should_include = False
                    elif self.status_filter == 'leave' and final_record['status'] != 'Leave':
                        should_include = False
                    elif self.status_filter == 'check_in_miss' and final_record['status'] != 'Check In Miss':
                        should_include = False
                    elif self.status_filter == 'check_out_miss' and final_record['status'] != 'Check Out Miss':
                        should_include = False
                    elif self.status_filter == 'off' and final_record['status'] != 'Off':
                        should_include = False
                    elif self.status_filter == 'Work_hours' and self.work_hours_filter:
                        # Filter by work hours
                        if not (record['work_hours'] >= self.work_hours_filter and
                                record['work_hours'] < self.work_hours_filter + 1):
                            should_include = False

                # Source filter apply karo
                if should_include and self.source_filter != 'all':
                    if self.source_filter == 'machine' and final_record['source'] != 'machine':
                        should_include = False
                    elif self.source_filter == 'manual' and final_record['source'] != 'manual':
                        should_include = False

                if should_include:
                    datas.append(final_record)

        def avg_time_from_datetimes(dt_list):
            if not dt_list:
                return None
            seconds = []
            for dt in dt_list:
                seconds.append(dt.hour * 3600 + dt.minute * 60 + dt.second)
            avg_seconds = int(sum(seconds) / len(seconds))
            avg_dt = (datetime(1970, 1, 1) + timedelta(seconds=avg_seconds))
            return avg_dt.strftime("%I:%M:%S %p")

        avg_check_in = avg_time_from_datetimes(total_checkins) if total_checkins else "--:--"
        avg_check_out = avg_time_from_datetimes(total_checkouts) if total_checkouts else "--:--"

        # avg_check_in = avg_time_from_datetimes(total_checkins) or "--:--"
        # avg_check_out = avg_time_from_datetimes(total_checkouts) or "--:--"
        avg_hours = self.convert_hours_to_time(
            statistics.mean(total_work_hours)) if total_work_hours else ""
        total_hours = self.convert_hours_to_time(sum(total_work_hours))

        summary = {
            'avg_check_in': avg_check_in,
            'avg_check_out': avg_check_out,
            'avg_hours': avg_hours,
            'total_work_hours': total_hours,
            'total_present': total_presents,
            'total_leave': total_leaves,
            'total_off': total_offs,
            'total_absent': total_absents,
            'total_check_in_miss': total_check_in_miss,
            'total_check_out_miss': total_check_out_miss,
        }

        return datas, summary

    def print_report_imp(self):
        employees = self.get_selected_employees()
        all_datas = []

        for employee in employees:
            datas, summary = self.get_attendance_data(employee)
            joining_date = employee.contract_id.date_start if employee.contract_id else False

            # Get wage from active contract
            wage = 0.0
            if employee.contract_id:
                wage = employee.contract_id.wage or 0.0

            # Get leave allocations
            leave_allocations = self.get_leave_allocations(employee)

            all_datas.append({
                'barcode': employee.barcode,
                'name': employee.name,
                'department_id': employee.department_id.name,
                'department_sequence': employee.department_id.id or 0,  # For sorting
                'job_id': employee.job_id.name,
                'joining_date': joining_date,
                'grp_date': employee.contract_id.x_studio_group_joining_date.strftime(
                    "%d-%m-%Y") if employee.contract_id.x_studio_group_joining_date else '',
                'wage': wage,  # Add wage for sorting
                'attendances': datas,
                'summary': summary,
                'leave_allocations': leave_allocations,
                'start_date': self.from_date.strftime('%#d-%b-%y'),
                'end_date': self.to_date.strftime('%#d-%b-%y'),
                'shift_name': employee.resource_calendar_id.name,
                'address': employee.address_id.name if employee.address_id else '',
                'doc_date': date.today().strftime('%d-%b-%Y'),
                'dob': employee.birthday,
                'father_name': employee.x_studio_father_name or '',
                'cnic': employee.identification_id,
            })

        # ✅ SORTING: First by Department, then by Wage (descending)
        all_datas = sorted(
            all_datas,
            key=lambda x: (
                x['department_id'] or '',  # Sort by department name
                -x['wage']  # Then by wage (descending - highest first)
            )
        )

        data = {'all_datas': all_datas}
        return self.env.ref('monal_employee_att_report.report_hr_attendance_employee').report_action([], data=data)
