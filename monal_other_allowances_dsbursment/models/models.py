from odoo import models, fields, api
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import calendar



class MonalOtherAllowanceDis(models.TransientModel):
    _name = 'monal.other.allowance.disbursment'
    _description = "Other Allowances (Disbursment) Wizard"

    period = fields.Selection(
        selection=lambda self: self._get_month_selection(),
        string='Period',
        required=True,
    )
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

    # def _get_period_selection(self):
    # 	today = fields.Date.today()
    # 	periods = []
    #
    # 	for i in range(12):
    # 		date = today - relativedelta(months=i)
    # 		period_name = date.strftime('%b %Y')
    # 		period_value = date.strftime('%Y-%m')
    # 		periods.append((period_value, period_name))
    #
    # 	return periods
    #
    # def _get_default_period(self):
    # 	return fields.Date.today().strftime('%Y-%m')
    #
    # def _get_period_dates(self, period_value):
    # 	year, month = map(int, period_value.split('-'))
    # 	from_date = datetime(year, month, 1).date()
    # 	to_date = from_date + relativedelta(months=1, days=-1)
    # 	return from_date, to_date

    def print_report_imp(self):
        from_date = self.date_from
        to_date = self.date_to
        domain = [
            ('date_from', '>=', from_date),
            ('date_to', '<=', to_date),
            ('state', 'in', ['done', 'paid', 'verify']),
            ('struct_id.name', 'ilike', 'Allowance Structure'),
        ]

        if self.department_ids:
            domain += [('employee_id.department_id', 'in', self.department_ids.ids)]

        if self.employee_ids:
            domain += [('employee_id', 'in', self.employee_ids.ids)]

        payslips = self.env['hr.payslip'].search(domain)
        depts = self.department_ids or self.env['hr.department'].search([], order="name asc")
        result = []
        for dept in depts:
            dept_slips = payslips.filtered(lambda s: s.employee_id.department_id == dept)
            if not dept_slips:
                continue
            dept_slips = sorted(dept_slips, key=lambda s: s.employee_id.name)
            emp_list = []
            for slip in dept_slips:
                total_allowances = 0
                # if slip.struct_id.name == 'Allowance Structure':
                allowance_lines = slip.line_ids.filtered(lambda l: l.total > 0)
                total_allowances = sum(allowance_lines.mapped('total'))

                employee = slip.employee_id

                attendances = self.env['hr.attendance'].search([
                    ('employee_id', '=', employee.id),
                    ('attend_check_in', '>=', slip.date_from),
                    ('attend_check_in', '<=', slip.date_to),
                    ('check_out','!=',False)
                ])
                attendance_dates = {a.check_in.date() for a in attendances if a.check_in}
                attendance_days = len(attendance_dates)
                total_sundays = [
                    slip.date_from + relativedelta(days=i)
                    for i in range((slip.date_to - slip.date_from).days + 1)
                    if (slip.date_from + relativedelta(days=i)).weekday() == 6
                ]
                # sundays_attended = [d for d in total_sundays if d in attendance_dates]
                # sundays_not_attended = len(total_sundays) - len(sundays_attended)
                total_days_in_month = calendar.monthrange(from_date.year, from_date.month)[1]
                all_days = [date(from_date.year, from_date.month, d) for d in range(1, total_days_in_month + 1)]
                sundays_not_attended = sum(1 for d in all_days if d.weekday() == 6)
                salary_days = attendance_days + sundays_not_attended

                emp_list.append({
                    'emp_code': employee.barcode or '',
                    'emp_name': employee.name,
                    'designation': employee.job_id.name or '',
                    'net_allowances': total_allowances,
                    'salary_days': salary_days,
                })
            result.append({
                'department': dept.name,
                'employees': emp_list,
            })
        year, month = map(int, self.period.split('-'))
        period_label = f"{calendar.month_name[month]} {year}"
        # period_name = datetime.strptime(self.period, '%Y-%m').strftime('%b %Y')
        data = {
            'period_name': period_label,
            'departments': result,
        }
        return self.env.ref('monal_other_allowances_dsbursment.report_other_allowance_employee').report_action([],
                                                                                                               data=data)
