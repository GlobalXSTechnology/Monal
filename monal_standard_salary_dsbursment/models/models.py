from odoo import models, fields, api
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import calendar


class MonalStandardSalaryDis(models.TransientModel):
    _name = 'monal.standard.salary.disbursment'
    _description = "Standard Salary Sheet (Disbursment) Wizard"

    period = fields.Selection(
        selection=lambda self: self._get_month_selection(),
        string='Period',
        required=True,
    )
    date_to = fields.Date(string='Date To', required=True, store=True)
    date_from = fields.Date(string='Date From', required=True, store=True)
    department_ids = fields.Many2many('hr.department', string="Department")
    employee_ids = fields.Many2many('hr.employee', string="Employee")
    company = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.company)

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
            ('struct_id.name', 'not ilike', 'Allowance'),
            ('company_id', '=', self.company.id),  # Add company filter

        ]

        if self.department_ids:
            domain += [('employee_id.department_id', 'in', self.department_ids.ids)]
        # if self.company:
        #     domain.append(('company_id', '=', self.company.id))

        if self.employee_ids:
            domain += [('employee_id', 'in', self.employee_ids.ids)]

        payslips = self.env['hr.payslip'].search(domain)
        # depts = self.department_ids or self.env['hr.department'].search([], order="name asc")
        # result = []
        # for dept in depts:
        #     dept_slips = payslips.filtered(lambda s: s.employee_id.department_id == dept)
        #     if not dept_slips:
        #         continue
        #     dept_slips = sorted(dept_slips, key=lambda s: s.employee_id.name)
        #     emp_list = []
        #     for slip in dept_slips:
        #         net_line = slip.line_ids.filtered(lambda l: l.code == 'NET')
        #         net_salary = net_line.total if net_line else 0
        #         emp_list.append({
        #             'emp_code': slip.employee_id.barcode or '',
        #             'emp_name': slip.employee_id.name,
        #             'designation': slip.employee_id.job_id.name or '',
        #             'net_salary': net_salary,
        #         })
        #     result.append({
        #         'department': dept.name,
        #         'employees': emp_list,
        #     })
        dept_domain = [('company_id', '=', self.company.id)]
        if self.department_ids:
            dept_domain = [('id', 'in', self.department_ids.ids)]
        depts = self.department_ids or self.env['hr.department'].search(dept_domain, order="name asc")

        # First, create a flat list of all records with department info
        all_records = []
        for dept in depts:
            dept_slips = payslips.filtered(lambda s: s.employee_id.department_id == dept)
            if not dept_slips:
                continue

            for slip in dept_slips:
                net_line = slip.line_ids.filtered(lambda l: l.code == 'NET')
                net_salary = net_line.total if net_line else 0

                # Get wage from contract for sorting
                wage = slip.contract_id.wage or 0

                all_records.append({
                    'emp_code': slip.employee_id.barcode or '',
                    'emp_name': slip.employee_id.name,
                    'designation': slip.employee_id.job_id.name or '',
                    'net_salary': net_salary,
                    'department': dept.name,
                    'department_obj': dept,
                    '_wage': wage,
                })

        # Now apply the same sorting logic as your reference
        # Group by department
        from collections import defaultdict
        dept_dict = defaultdict(list)
        for rec in all_records:
            dept_name = rec['department'] or 'ZZZ'
            dept_dict[dept_name].append(rec)

        result = []
        # Sort departments alphabetically
        for dept_name in sorted(dept_dict.keys()):
            employees = dept_dict[dept_name]

            # Sort employees by wage in descending order (highest first)
            employees.sort(key=lambda x: x.get('_wage', 0), reverse=True)

            # Add sequence number after sorting
            for seq, emp_data in enumerate(employees, 1):
                emp_data['sr_no'] = seq

            result.append({
                'department': dept_name,
                'employees': employees,
            })
        year, month = map(int, self.period.split('-'))
        period_label = f"{calendar.month_name[month]} {year}"
        # period_name = datetime.strptime(self.period, '%Y-%m').strftime('%b %Y')
        data = {
            'period_name': period_label,
            'company_name': self.company.name,
            'departments': result,
        }
        return self.env.ref('monal_standard_salary_dsbursment.report_salary_disbursment_employee').report_action([],
                                                                                                                 data=data)
