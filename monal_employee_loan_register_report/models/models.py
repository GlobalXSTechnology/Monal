from odoo import models, fields, api
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import calendar



class MonalLoanRegisterReport(models.TransientModel):
    _name = 'monal.loan.register.report'
    _description = "Loan Register Report Wizard"

    period = fields.Selection(selection=lambda self: self._get_month_selection(), string='Period', required=True)
    mode_type = fields.Selection([
        ('employee', 'Employee Wise'),
        ('department', 'Department Wise'),
        ('company', 'Company Wise'),
    ], string="Mode Type", default='company', required=True)

    from_date = fields.Date(
        'From Date',
        required=True
    )
    to_date = fields.Date(
        "To Date",
        required=True
    )
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=lambda self: self.env.company,
        domain=lambda self: [('id', '=', self.env.company.id)],
    )
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
            self.from_date = f'{year}-{month:02d}-01'
            last_day = calendar.monthrange(year, month)[1]
            self.to_date = f'{year}-{month:02d}-{last_day}'

    @api.onchange('mode_type')
    def _onchange_mode_type(self):
        if self.mode_type == 'employee':
            self.department_ids = False
            self.company_id = self.env.company
        elif self.mode_type == 'department':
            self.employee_ids = False
            self.company_id = self.env.company
        elif self.mode_type == 'company':
            self.employee_ids = False
            self.department_ids = False

    def print_report_loan(self):
        domain = [
            ('date_from', '>=', self.from_date),
            ('date_to', '<=', self.to_date),
            ('state', 'in', ['done', 'paid', 'verify']),
        ]

        if self.mode_type == 'company' and self.company_id:
            domain += [('company_id', '=', self.company_id.id)]

        if self.mode_type == 'department' and self.department_ids:
            domain += [('employee_id.department_id', 'in', self.department_ids.ids)]

        if self.mode_type == 'employee' and self.employee_ids:
            domain += [('employee_id', 'in', self.employee_ids.ids)]

        payslips = self.env['hr.payslip'].search(domain)
        all_datas = []

        for slip in payslips:
            loan_lines = slip.line_ids.filtered(
                lambda l: any(keyword in (l.code or '') for keyword in
                              ['LOAN/SAL', 'LOAN/SAL333', 'LOAN/EDU', 'LOAN/MED', 'COMPANY/LOAN', 'VEH/LOAN'])
            )
            for line in loan_lines:
                loan_rec = self.env['hr.advance.salary'].search([('name', '=', line.name)], limit=1)

                loan_type_display = ''
                code = line.code or ''
                rec_type = loan_rec.loan_type if loan_rec else ''

                if code in ['LOAN/SAL', 'LOAN/SAL333']:
                    loan_type_display = 'Salary Loan'
                elif 'LOAN/EDU' in code and rec_type == 'educational':
                    loan_type_display = 'Education Loan'
                elif 'LOAN/MED' in code and rec_type == 'medical':
                    loan_type_display = 'Medical Loan'
                elif 'COMPANY/LOAN' in code:
                    loan_type_display = 'Company Loan'
                elif 'VEH/LOAN' in code:
                    loan_type_display = 'Vehicle Loan'
                else:
                    continue

                data_dict = {
                    'emp_code': slip.employee_id.barcode or '',
                    'emp_name': slip.employee_id.name or '',
                    'father_name': slip.employee_id.x_studio_father_name or '',
                    'department': slip.employee_id.department_id.name or '',
                    'designation': slip.employee_id.job_id.name or '',
                    'joining_date': slip.contract_id.date_start or '',
                    'loan_type': loan_type_display,
                    'doc_no': slip.number or slip.name,
                    'effect_date': loan_rec.request_date if loan_rec else '',
                    'req_loan': loan_rec.request_amount if loan_rec else line.total,
                    'req_installments': loan_rec.duration_month if loan_rec else '',
                    'app_loan': loan_rec.amount_to_pay if loan_rec else '',
                    'app_installments': loan_rec.duration_month if loan_rec else '',
                    'guarantor_1_name': loan_rec.first_referral.name if loan_rec else '',
                    'guarantor_1_dept': loan_rec.first_referral.department_id.name if loan_rec and loan_rec.first_referral.department_id else '',
                    'guarantor_2_name': loan_rec.second_referral.name if loan_rec else '',
                    'guarantor_2_dept': loan_rec.second_referral.department_id.name if loan_rec and loan_rec.second_referral.department_id else '',
                    'rev_no': '--',
                    'period_type': '---',
                    'amount': line.total or line.total,
                    'from_date': loan_rec.payment_start_date if loan_rec else slip.date_from,
                    'to_date': loan_rec.payment_end_date if loan_rec else slip.date_to,
                }
                all_datas.append(data_dict)

        data = {
            'all_datas': all_datas,
            'mode_type': self.mode_type,
            'from_date': self.from_date,
            'to_date': self.to_date,
            'company_name': self.company_id.name if self.company_id else '',
        }
        return self.env.ref('monal_employee_loan_register_report.report_loan_register_employee').report_action([],
                                                                                                               data=data)
