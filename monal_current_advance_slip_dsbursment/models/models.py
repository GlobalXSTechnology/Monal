from odoo import models, fields, api
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import calendar



class MonalOtherAllowanceDis(models.TransientModel):
    _name = 'monal.current.advance.slip.disbursment'
    _description = "Other Allowances (Disbursment) Wizard"

    period = fields.Selection(selection=lambda self: self._get_month_selection(), string='Period', required=True)
    advance_type = fields.Selection([('bank', 'Bank'), ('cash', 'Cash'), ('final_bank_salary', 'Final Bank Salary')],
                                    string='Type', default=False)
    date_to = fields.Date(string='Date To', required=True, store=True)
    date_from = fields.Date(string='Date From', required=True, store=True)
    department_ids = fields.Many2many('hr.department', string="Department")
    employee_ids = fields.Many2many('hr.employee', string="Employee")

    def _get_month_selection(self):
        months = [
            ('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
            ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'),
            ('09', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
        ]
        month_selection = []
        for year in range(2025, 2035):
            for code, name in months:
                month_selection.append((f'{year}-{code}', f'{name} {year}'))
        return month_selection

    @api.onchange('period')
    def _onchange_month(self):
        if self.period:
            year, month = map(int, self.period.split('-'))
            self.date_from = f'{year}-{month:02d}-01'
            last_day = calendar.monthrange(year, month)[1]
            self.date_to = f'{year}-{month:02d}-{last_day}'

    def print_report_imp(self):
        from_date = self.date_from
        to_date = self.date_to

        domain = [
            ('request_date', '>=', from_date),
            ('request_date', '<=', to_date),
            ('state', 'in', ['done', 'paid', 'gm_finance']),
            ('payment', '=', 'fully'),
        ]

        if self.department_ids:
            domain.append(('employee_id.department_id', 'in', self.department_ids.ids))

        if self.advance_type:
            domain.append(('advance_type', '=', self.advance_type))

        if self.employee_ids:
            domain.append(('employee_id', 'in', self.employee_ids.ids))

        advance_sal = self.env['hr.advance.salary'].search(domain)

        depts = self.department_ids or self.env['hr.department'].search([], order="name asc")

        result = []
        for dept in depts:
            dept_records = advance_sal.filtered(lambda s: s.employee_id.department_id == dept)
            if not dept_records:
                continue

            sorted_records = sorted(dept_records, key=lambda s: s.employee_id.name)
            emp_list = []

            for slip in sorted_records:
                employee = slip.employee_id

                attendances = self.env['hr.attendance'].search([
                    ('employee_id', '=', employee.id),
                    ('attend_check_in', '>=', from_date),
                    ('attend_check_in', '<=', to_date),
                ])
                if employee.resource_calendar_id.x_studio_is_zero:
                    attendance_dates = {a.attend_check_in for a in attendances if a.attend_check_in and a.check_out}
                else:
                    attendance_dates = {a.attend_check_in for a in attendances if a.attend_check_in and a.worked_hours >= 6 and a.check_out}
                # attendance_dates = {a.check_in.date() for a in attendances if a.check_in}
                
                attendance_days = len(attendance_dates)

                total_sundays = [
                    from_date + relativedelta(days=i)
                    for i in range((to_date - from_date).days + 1)
                    if (from_date + relativedelta(days=i)).weekday() == 6
                ]

                sundays_attended = [d for d in total_sundays if d in attendance_dates]
                sundays_not_attended = len(total_sundays) - len(sundays_attended)

                # salary_days = attendance_days + sundays_not_attended
                salary_days = attendance_days
                contract = employee.contract_id
                wage = contract.wage if contract else 0.0

                # total_month_days = (to_date - from_date).days + 1
                total_month_days = len([
                    from_date + relativedelta(days=i)
                    for i in range((to_date - from_date).days + 1)
                    if (from_date + relativedelta(days=i)).weekday() != 6
                ])

                salary_till_date = 0.0
                if wage > 0 and total_month_days > 0:
                    salary_till_date = (wage / total_month_days) * salary_days
                emp_list.append({
                    'emp_code': employee.barcode or '',
                    'emp_name': employee.name,
                    'designation': employee.job_id.name or '',
                    'salary_days': salary_days,
                    'requested_amount': slip.request_amount,
                    'advance_amount': slip.amount_to_pay,
                    'request_date': slip.request_date or '',
                    'salary_till_date': round(salary_till_date, 2),
                })

            result.append({
                'department': dept.name,
                'employees': emp_list,
            })

        year, month = map(int, self.period.split('-'))
        period_label = f"{calendar.month_name[month]} {year}"

        data = {
            'period_name': period_label,
            'departments': result,
        }
        return self.env.ref(
            'monal_current_advance_slip_dsbursment.report_current_advance_slip_employee').report_action([],
                                                                                                        data=data)
