from odoo import models, fields, api
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class AttendanceReportWizard(models.TransientModel):
    _name = 'attendance.report.wizard'
    _description = 'Monthly Attendance Report Wizard'

    date_from = fields.Date(
        'From Date',
        default=lambda self: fields.Date.to_string(date.today()),
        required=True
    )
    date_to = fields.Date(
        "To Date",
        required=True
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

    @api.onchange('date_from')
    def _onchange_date_from(self):
        if self.date_from:
            # Calculate last day of selected month
            first_day = self.date_from.replace(day=1)
            last_day = first_day + relativedelta(months=1, days=-1)
            self.date_to = last_day
    @api.onchange('select_employee')
    def _onchange_select_employee(self):
        if self.select_employee == 'company':
            self.department_id = False
            self.employee_ids = False
        elif self.select_employee == 'department':
            self.employee_ids = False
        elif self.select_employee == 'employee':
            self.department_id = False

    def action_print_report(self):
        self.ensure_one()
        data = {
            'date_from': self.date_from.strftime('%Y-%m-%d') if self.date_from else '',
            'date_to': self.date_to.strftime('%Y-%m-%d') if self.date_to else '',
            'select_employee': self.select_employee,
            'company_id': self.company_id.id,
            'company_name': self.company_id.name,
            'department_ids': self.department_id.ids if self.department_id else [],
            'employee_ids': self.employee_ids.ids if self.employee_ids else [],
            'doc_ids': self.ids,
        }

        return self.env.ref('monal_mis_leave_summary.action_report_mis_attendance').report_action(self, data=data)

    def get_total_days_in_month(self, from_date, to_date):
        delta = to_date - from_date
        return delta.days + 1

    def get_weekly_off_count(self, from_date, to_date):
        try:
            weekly_off_count = 0
            current_date = from_date

            while current_date <= to_date:
                if current_date.weekday() == 6:
                    weekly_off_count += 1
                current_date += timedelta(days=1)

            return weekly_off_count
        except Exception as e:
            _logger.error(f"Error calculating weekly off count: {e}")
            return 0

    def get_attendance_data(self, employee, from_date, to_date):
        try:
            total_days = (to_date - from_date).days + 1
            total_sundays = self.get_weekly_off_count(from_date, to_date)

            is_zero_shift = employee.resource_calendar_id.x_studio_is_zero if employee.resource_calendar_id else False

            present_count = 0
            absent_count = 0
            paid_leave_count = 0
            unpaid_leave_count = 0
            check_out_miss_count = 0
            off_count = 0

            temp_records = []
            current_date = from_date

            while current_date <= to_date:
                day_status = self._get_day_status(employee, current_date, is_zero_shift)
                temp_records.append({
                    'date': current_date,
                    'status': day_status
                })
                current_date += timedelta(days=1)

            offs_to_mark = total_sundays
            offs_marked = 0

            for record in temp_records:
                if (record['status'] == 'absent' or record[
                    'status'] == 'check_out_miss') and offs_marked < offs_to_mark:
                    record['status'] = 'off'
                    offs_marked += 1

            for record in temp_records:
                status = record['status']

                if status == "present":
                    present_count += 1
                elif status == "paid_leave":
                    paid_leave_count += 1
                elif status == "unpaid_leave":
                    unpaid_leave_count += 1
                elif status == "check_out_miss":
                    check_out_miss_count += 1
                elif status == "off":
                    off_count += 1
                elif status == "absent":
                    absent_count += 1

            sundays_converted = offs_marked

            total_present = present_count

            _logger.info(f"Attendance for {employee.name}: Present={total_present}, Absent={absent_count}, "
                         f"Off={off_count}, Paid Leaves={paid_leave_count}, Check Out Miss={check_out_miss_count}, "
                         f"Sundays Consumed={sundays_converted}")

            return {
                'present_days': total_present,
                'total_work_days': total_present + paid_leave_count,
                'absent_days': absent_count,
                'paid_leaves': paid_leave_count,
                'unpaid_leaves': unpaid_leave_count,
                'sundays_as_leaves': sundays_converted,
                'total_leave_days': paid_leave_count + unpaid_leave_count + sundays_converted,
                'total_month_days': total_days,
                'weekly_off': total_sundays,
                'off_days': off_count,
                'check_out_miss': check_out_miss_count,
            }

        except Exception as e:
            _logger.error(f"Error in get_attendance_data for {employee.name}: {e}")
            return self._get_default_attendance_data()

    def _get_day_status(self, employee, check_date, is_zero_shift):
        try:
            date_start = datetime.combine(check_date, datetime.min.time())
            date_end = datetime.combine(check_date, datetime.max.time())

            attendance = self.env["hr.attendance"].search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', date_start),
                ('check_in', '<=', date_end),
            ], limit=1, order='check_in desc')

            if attendance:
                work_hours = float(attendance.worked_hours or 0.0)

                if attendance.check_in and attendance.check_out:
                    if is_zero_shift or work_hours >= 6.0:
                        return "present"
                    else:
                        return "absent"
                elif attendance.check_in and not attendance.check_out:
                    return "check_out_miss"
                else:
                    return "absent"

            leaves = self.env["hr.leave"].search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),
                ('request_date_from', '<=', check_date),
                ('request_date_to', '>=', check_date),
            ])

            if leaves:
                is_unpaid = any(leave.holiday_status_id.unpaid for leave in leaves)
                return "unpaid_leave" if is_unpaid else "paid_leave"

            return "absent"

        except Exception as e:
            _logger.error(f"Error in _get_day_status for {employee.name} on {check_date}: {e}")
            return "absent"

    def _get_default_attendance_data(self):
        return {
            'present_days': 0,
            'total_work_days': 0,
            'absent_days': 0,
            'paid_leaves': 0,
            'unpaid_leaves': 0,
            'sundays_as_leaves': 0,
            'total_leave_days': 0,
            'total_month_days': 0,
            'weekly_off': 0,
        }

    def get_leave_balance_data(self, employee, from_date, to_date):
        try:
            x_studio_residence_type = self._get_x_studio_residence_type(employee)

            entitled_leaves = self.get_weekly_off_count(from_date, to_date)
            encash_leaves_data_1 = self.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),
                ('leave_encashed_check', '=', True),
                ('holiday_status_id.name', '=', 'Weekly Off'),
                ('request_date_from', '>=', from_date),
                ('request_date_to', '<=', to_date),
            ])

            encash_leaves_1 = sum(encash_leave.number_of_days for encash_leave in encash_leaves_data_1)

            opening_balance = self._get_opening_balance_from_allocation(employee, from_date, to_date) - encash_leaves_1
            if opening_balance < 0:
                opening_balance = 0

            weekly_off_leaves = self.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),
                ('leave_encashed_check', '=', False),
                ('holiday_status_id.name', '=', 'Weekly Off'),
                ('request_date_from', '>=', from_date),
                ('request_date_to', '<=', to_date),
            ])

            actual_leaves_taken = sum(leave.number_of_days for leave in weekly_off_leaves)

            attendance_data = self.get_attendance_data(employee, from_date, to_date)
            sundays_consumed = attendance_data.get('sundays_as_leaves', 0)

            month_key = from_date.strftime('%Y-%m')
            encash_leaves_data = self.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),
                ('leave_encashed_check', '=', True),
                ('holiday_status_id.name', '=', 'Weekly Off'),
                ('month', '=', month_key),
            ])

            encash_leaves = sum(encash_leave.number_of_days for encash_leave in encash_leaves_data)
            next_month_first = (from_date + relativedelta(months=1)).replace(day=1)
            next_month_last = (next_month_first + relativedelta(months=1)) - relativedelta(days=1)
            nex_month_weekly_leaves_data = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'refuse'),
                ('holiday_status_id.name', '=', 'Weekly Off'),
                ('date_from', '>=', next_month_first),
                ('date_to', '<=', next_month_last),
            ])

            nex_month_weekly = sum(next_leave.number_of_days for next_leave in nex_month_weekly_leaves_data)

            # availed_leaves = sundays_consumed + actual_leaves_taken
            workable = (attendance_data.get('total_month_days', 0)) - (entitled_leaves)
            if attendance_data.get('present_days', 0) <= workable:
                consumed_sunday = entitled_leaves
            else:
                consumed_sunday = attendance_data.get('total_month_days', 0) - attendance_data.get('present_days', 0)

            availed_leaves =  actual_leaves_taken + consumed_sunday

            current_balance = ((opening_balance + entitled_leaves) - (availed_leaves + encash_leaves)) - nex_month_weekly
            if current_balance < 0:
                current_balance = 0

            _logger.info(current_balance)
            _logger.info('current_balance')
            _logger.info('current_balance')
            _logger.info('current_balance')

            balance_after = 0
            waved_leaves = 0

            if x_studio_residence_type == 'local':
                if current_balance > 2:
                    balance_after = 2
                    waved_leaves = current_balance - 2
                else:
                    balance_after = max(current_balance, 0)
                    waved_leaves = 0

            elif x_studio_residence_type == 'outsider':
                max_outside_balance = 5
                if current_balance > max_outside_balance:
                    balance_after = max_outside_balance
                    waved_leaves = current_balance - max_outside_balance
                else:
                    balance_after = max(current_balance, 0)
                    waved_leaves = 0

            elif x_studio_residence_type == 'northern':
                if current_balance > 20:
                    balance_after = 20
                    waved_leaves = current_balance - 20
                else:
                    balance_after = max(current_balance, 0)
                    waved_leaves = 0
            else:
                balance_after = max(current_balance, 0)
                waved_leaves = 0

            _logger.info(f"Leave Balance for {employee.name} ({x_studio_residence_type}): Opening={opening_balance}, "
                         f"Entitled={entitled_leaves}, Sundays Consumed={sundays_consumed}, "
                         f"Actual Leaves={actual_leaves_taken}, Total Availed={availed_leaves}, "
                         f"Balance={current_balance}, Balance After={balance_after}, Waved={waved_leaves}")

            return {
                'opening': opening_balance,
                'entitled': entitled_leaves,
                'availed': availed_leaves,
                'encash': encash_leaves,
                'balance': current_balance,
                'waved': waved_leaves,
                'balance_after': balance_after,
            }

        except Exception as e:
            _logger.error(f"Error getting leave balance for {employee.name}: {e}")
            return {
                'opening': 0,
                'entitled': 0,
                'availed': 0,
                'encash': 0,
                'balance': 0,
                'waved': 0,
                'balance_after': 0,
            }

    def _get_x_studio_residence_type(self, employee):
        try:
            # if hasattr(employee, 'x_studio_residence_type') and employee.x_studio_residence_type:
            #     return employee.x_studio_residence_type.lower()

            if employee.emp_type:
                if employee.emp_type == 'local':
                    return 'local'
                elif employee.emp_type == 'northern':
                    return 'northern'
                else:
                    return 'outsider'

            # return 'local'

        except Exception as e:
            _logger.error(f"Error getting residence type for {employee.name}: {e}")
            return 'local'
    # def _get_opening_balance_from_allocation(self, employee, current_from_date):
    #     try:
    #         # Subtract 1 month from current_from_date
    #         previous_month_date = current_from_date - relativedelta(months=1)
    #         month_key = previous_month_date.strftime('%Y-%m')
    #
    #         allocations = self.env['hr.leave.allocation'].search([
    #             ('employee_id', '=', employee.id),
    #             ('holiday_status_id.name', '=', 'Weekly Off'),
    #             ('state', '=', 'validate'),
    #             ('month', '=', month_key),
    #         ])
    #
    #         if allocations:
    #             return sum(allocations.mapped('number_of_days'))
    #
    #         return 0
    #
    #     except Exception as e:
    #         _logger.error(f"Error getting opening balance from allocation for {employee.name}: {e}")
    #         return 0

    def _get_opening_balance_from_allocation(self, employee, from_date, to_date):
        try:
            allocations = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', employee.id),
                ('holiday_status_id.name', '=', 'Weekly Off'),
                ('state', '=', 'validate'),
                ('date_from', '>=', from_date),
                ('date_to', '<=', to_date),
            ])

            if allocations:
                return sum(allocations.mapped('number_of_days'))

            return 0

        except Exception as e:
            _logger.error(f"Error getting opening balance from allocation for {employee.name}: {e}")
            return 0

    # def _get_opening_balance_from_allocation(self, employee, current_from_date):
    #     try:
    #         allocation = self.env['hr.leave.allocation'].search([
    #             ('employee_id', '=', employee.id),
    #             ('holiday_status_id.name', '=', 'Weekly Off'),
    #             ('state', '=', 'validate'),
    #         ], limit=1, order='date_from desc')

    #         if allocation:

    #             previous_leaves = self.env['hr.leave'].search([
    #                 ('employee_id', '=', employee.id),
    #                 ('state', '=', 'validate'),
    #                 ('holiday_status_id.name', '=', 'Weekly Off'),
    #                 ('request_date_to', '<', current_from_date),
    #             ])

    #             leaves_taken_before = sum(leave.number_of_days for leave in previous_leaves)

    #             if allocation.date_from:
    #                 allocation_start = allocation.date_from
    #                 period_before_end = current_from_date - timedelta(days=1)

    #                 if allocation_start < current_from_date:
    #                     sundays_before = self.get_weekly_off_count(allocation_start, period_before_end)
    #                     opening = allocation.number_of_days + sundays_before - leaves_taken_before
    #                     return max(opening, 0)

    #             return allocation.number_of_days

    #         return 0

    #     except Exception as e:
    #         _logger.error(f"Error getting opening balance from allocation for {employee.name}: {e}")
    #         return 0


class ReportMonthlyAttendance(models.AbstractModel):
    _name = 'report.monal_mis_leave_summary.report_monthly_attendance'
    _description = 'Monthly Attendance Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data:
            data = {}

        wizard = False
        if docids:
            wizard = self.env['attendance.report.wizard'].browse(docids[0])
        elif data.get('doc_ids'):
            wizard = self.env['attendance.report.wizard'].browse(data['doc_ids'][0])

        company_id = data.get('company_id', self.env.company.id)
        company = self.env['res.company'].browse(company_id)

        date_from = data.get('date_from', '')
        date_to = data.get('date_to', '')

        if date_from and isinstance(date_from, str):
            try:
                date_from_formatted = datetime.strptime(date_from, '%Y-%m-%d').strftime('%d/%m/%Y')
            except:
                date_from_formatted = str(date_from)
        else:
            date_from_formatted = date_from

        if date_to and isinstance(date_to, str):
            try:
                date_to_formatted = datetime.strptime(date_to, '%Y-%m-%d').strftime('%d/%m/%Y')
            except:
                date_to_formatted = str(date_to)
        else:
            date_to_formatted = date_to

        if not wizard:
            wizard = self.env['attendance.report.wizard'].new({
                'select_employee': data.get('select_employee', 'employee'),
                'company_id': company_id,
                'date_from': data.get('date_from'),
                'date_to': data.get('date_to'),
            })

        return {
            'doc_ids': docids,
            'doc_model': 'attendance.report.wizard',
            'data': data,
            'docs': wizard,
            'company': company,
            'company_name': company.name,
            'date_from_formatted': date_from_formatted,
            'date_to_formatted': date_to_formatted,
            'get_departments': self._get_departments,
            'get_employees_data': self._get_employees_data,
        }

    def _get_departments(self, data):
        try:
            select_employee = data.get('select_employee', 'employee')
            company_id = data.get('company_id', self.env.company.id)
            department_ids = data.get('department_ids', [])
            employee_ids = data.get('employee_ids', [])
            date_from_str = data.get('date_from')
            date_to_str = data.get('date_to')

            if not date_from_str or not date_to_str:
                return []

            from_date = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            to_date = datetime.strptime(date_to_str, '%Y-%m-%d').date()

            attendance_records = self.env['hr.attendance'].search_read([
                ('check_in', '>=', from_date),
                ('check_in', '<=', to_date)
            ], ['employee_id'])
            employee_ids_with_attendance = list({
                rec['employee_id'][0]
                for rec in attendance_records if rec.get('employee_id')
            })

            if not employee_ids_with_attendance:
                return []

            domain = []
            if select_employee == 'company':
                domain.append(('company_id', '=', company_id))
            elif select_employee == 'department' and department_ids:
                domain.append(('id', 'in', department_ids))
            elif select_employee == 'department' and not department_ids:
                domain.append(('company_id', '=', company_id))
            elif select_employee == 'employee' and employee_ids:
                employees = self.env['hr.employee'].browse(employee_ids)
                dept_ids = employees.mapped('department_id.id')
                domain.append(('id', 'in', dept_ids))
            elif select_employee == 'employee' and not employee_ids:
                domain.append(('company_id', '=', company_id))
            else:
                domain.append(('company_id', '=', company_id))

            departments = self.env['hr.department'].search(domain)

            valid_departments = []
            for dept in departments:
                has_data = self.env['hr.employee'].search_count([
                    ('id', 'in', employee_ids_with_attendance),
                    ('department_id', '=', dept.id)
                ])
                if has_data:
                    valid_departments.append(dept)

            return valid_departments

        except Exception as e:
            _logger.error(f"Error in _get_departments: {e}")
            return []

    def _get_employees_data(self, dept, data):
        try:
            select_employee = data.get('select_employee', 'employee')
            employee_ids = data.get('employee_ids', [])
            date_from_str = data.get('date_from')
            date_to_str = data.get('date_to')

            from_date = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            to_date = datetime.strptime(date_to_str, '%Y-%m-%d').date()

            attendance_emps = self.env['hr.attendance'].search_read([
                ('check_in', '>=', from_date),
                ('check_in', '<=', to_date)
            ], ['employee_id'])
            employee_ids_with_attendance = list({
                rec['employee_id'][0]
                for rec in attendance_emps if rec.get('employee_id')
            })

            if not employee_ids_with_attendance:
                return []

            employees_domain = [('department_id', '=', dept.id), ('id', 'in', employee_ids_with_attendance)]

            if select_employee == 'employee' and employee_ids:
                employees_domain.append(('id', 'in', employee_ids))

            employees = self.env['hr.employee'].search(employees_domain)
            if not employees:
                return []

            wizard = self.env['attendance.report.wizard'].new({
                'date_from': from_date,
                'date_to': to_date,
            })

            result = []
            seq = 1
            for emp in employees:
                try:
                    attendance_data = wizard.get_attendance_data(emp, from_date, to_date)
                    leave_balance_data = wizard.get_leave_balance_data(emp, from_date, to_date)

                    emp_code = emp.barcode or ''
                    designation = emp.job_id.name if emp.job_id else ''
                    join_date = emp.create_date.strftime('%Y-%m-%d') if emp.create_date else ''
                    location = getattr(emp, 'work_location', '') or getattr(emp.work_location_id, 'name', '') or ''
                    residence_type = getattr(emp, 'emp_type', '') or ''

                    result.append({
                        'sr_no': seq,
                        'emp_code': emp_code,
                        'name': emp.name or '',
                        'designation': designation,
                        'join_date': join_date,
                        'location': location,
                        'residence_type': residence_type,
                        'opening': leave_balance_data.get('opening', 0),
                        'total_days': attendance_data.get('total_month_days', 0),
                        'present': attendance_data.get('present_days', 0),
                        'entitled': leave_balance_data.get('entitled', 0),
                        'availed': leave_balance_data.get('availed', 0),
                        'encash': leave_balance_data.get('encash', 0),
                        'balance': leave_balance_data.get('balance', 0),
                        'waved': leave_balance_data.get('waved', 0),
                        'balance_after': leave_balance_data.get('balance_after', 0),
                    })
                    seq += 1
                except Exception as emp_error:
                    _logger.error(f"Error processing employee {emp.id}: {emp_error}")
                    continue

            return result

        except Exception as e:
            _logger.error(f"Error in _get_employees_data: {e}")
            return []
