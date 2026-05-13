from odoo import models, fields, api
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import calendar

class MonalDeductionReportEmp(models.TransientModel):
    _name = 'monal.deduction.report.employee'
    _description = "Deduction Report Wizard"
    
    mode_type = fields.Selection([
        ('employee', 'Employee Wise'),
        ('department', 'Department Wise'),
        ('company', 'Company Wise'),
    ], string="Mode Type", default='company', required=True)
    
    # period = fields.Selection(
    #     selection='_get_period_selection',
    #     string='Period',
    #     required=True,
    #     default=lambda self: self._get_default_period()
    # )
    
    from_date = fields.Date(
        'From Date',
        required=True,
        store=False
    )
    to_date = fields.Date(
        "To Date",
        store=True,
        required=False
    )
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=lambda self: self.env.company,
        domain=lambda self: [('id', '=', self.env.company.id)],
    )
    department_ids = fields.Many2many('hr.department', string="Department")
    employee_ids = fields.Many2many('hr.employee', string="Employee")
    
    deduction_rule_ids = fields.Many2many(
        'hr.salary.rule',
        string="Deduction Type",
        domain="[('id', 'in', rule_domain_ids)]", relation="wiz_deduction_rule_rel",
    )
    rule_domain_ids = fields.Many2many(
        'hr.salary.rule',
        string="Rule Domain Helper", relation="wiz_deduction_rule_domain_rel",
    )
    
    section_ids = fields.Many2many(
        'department.section',
        string="Section",
    )
    period = fields.Selection(
        selection=lambda self: self._get_month_selection(),
        string="Period",
        required=True,
    )

    def _get_month_selection(self):
        period = [
            ('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
            ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'),
            ('09', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
        ]
        month_selection = []
        for year in range(2025, 2035):
            for code, name in period:
                month_selection.append((f'{year}-{code}', f'{name} {year}'))
        return month_selection

    @api.onchange('period')
    def _onchange_month(self):
        if self.period:
            year, month = map(int, self.period.split('-'))
            self.from_date = f'{year}-{month:02d}-01'
            last_day = calendar.monthrange(year, month)[1]
            self.to_date = f'{year}-{month:02d}-{last_day}'
    
    salary_structure_id = fields.Many2one(
        'hr.payroll.structure',
        string="Salary Structure",
        help="Filter deduction rules by selected salary structure"
    )
    
    
    # def _get_period_selection(self):
    #     today = fields.Date.today()
    #     periods = []
    #
    #     for i in range(12):
    #         date = today - relativedelta(months=i)
    #         period_name = date.strftime('%b %Y')
    #         period_value = date.strftime('%Y-%m')
    #         periods.append((period_value, period_name))
    #
    #     return periods
    
    
    def _get_default_period(self):
        return fields.Date.today().strftime('%Y-%m')
    
    
    def _get_period_dates(self, period_value):
        year, month = map(int, period_value.split('-'))
        from_date = datetime(year, month, 1).date()
        to_date = from_date + relativedelta(months=1, days=-1)
        return from_date, to_date
    
    
    @api.onchange('salary_structure_id')
    def _onchange_salary_structure_id(self):
        self.rule_domain_ids = False
        domain = [('category_id.code', '=', 'DED')]
        Rule = self.env['hr.salary.rule']
        if self.salary_structure_id:
            domain.append(('struct_id', '=', self.salary_structure_id.id))
            rules = Rule.search(domain)
        else:
            rules_all = Rule.search(domain)
            unique_rules = {}
            for rule in rules_all:
                if rule.name not in unique_rules:
                    unique_rules[rule.name] = rule
            rules = Rule.browse([r.id for r in unique_rules.values()])
        self.rule_domain_ids = rules
    
    
    # @api.onchange('salary_structure_id')
    # def _onchange_salary_structure_id(self):
    # 	self.rule_domain_ids = False
    #
    # 	domain = [('category_id.code', '=', 'DED')]
    # 	if self.salary_structure_id:
    # 		domain.append(('struct_id', '=', self.salary_structure_id.id))
    #
    # 	rules = self.env['hr.salary.rule'].search(domain)
    # 	self.rule_domain_ids = rules.ids
    #
    #
    #
    
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
    
    
    def print_report_imp(self):
        
        # Convert selected period to date_from & date_to
        from_date, to_date = self._get_period_dates(self.period)
        domain = [
            ('date_from', '>=', from_date),
            ('date_to', '<=', to_date),
            ('state', 'in', ['done', 'paid', 'verify']),
        ]
        
        if self.mode_type == 'company' and self.company_id:
            domain += [('company_id', '=', self.company_id.id)]
        
        if self.mode_type == 'department' and self.department_ids:
            domain += [('employee_id.department_id', 'in', self.department_ids.ids)]
        
        if self.mode_type == 'employee' and self.employee_ids:
            domain += [('employee_id', 'in', self.employee_ids.ids)]
        
        if self.section_ids:
            domain += [('employee_id.department_id.section_id', 'in', self.section_ids.ids)]
        
        if self.salary_structure_id:
            domain.append(('struct_id', '=', self.salary_structure_id.id))
        
        payslips = self.env['hr.payslip'].search(domain)
        
        # Sort Payslips:
        # 1. By Department name (A → Z)
        # 2. By Wage highest → lowest
        sorted_slips = sorted(payslips, key=lambda s: (
            s.employee_id.department_id.name or '',
            -(s.contract_id.wage if s.contract_id and s.contract_id.wage else 0)
        ))
        
        total_deductions = 0
        all_datas = []
        today_date = date.today()  # current date
        for slip in sorted_slips:
            deduction_lines = slip.line_ids.filtered(
                lambda l: l.category_id.code == 'DED' or l.total < 0
            )
            if self.deduction_rule_ids:
                deduction_lines = deduction_lines.filtered(
                    lambda l: l.salary_rule_id.id in self.deduction_rule_ids.ids
                )
            for line in deduction_lines:
                all_datas.append({
                    'emp_code': slip.employee_id.barcode or '',
                    'emp_name': slip.employee_id.name,
                    'father_name': slip.employee_id.x_studio_father_name,
                    'cnic': slip.employee_id.identification_id or '',
                    'dob': slip.employee_id.birthday,
                    'department': slip.employee_id.department_id.name or '',
                    'designation': slip.employee_id.job_id.name or '',
                    'joining_date': slip.contract_id.date_start if slip.contract_id else '',
                    'doc_no': slip.number or slip.name,
                    'doc_date': today_date.strftime('%Y-%m-%d'),
                    'sr_no': line.id,
                    'line_type': line.name,
                    'deduction_amount': line.total,
                    'remarks': '---',
                })
                total_deductions += line.total
        data = {'all_datas': all_datas,
                'total_deductions': total_deductions,
                }
        return self.env.ref('monal_employee_deduction_report.report_hr_deduction_employee').report_action([], data=data)
