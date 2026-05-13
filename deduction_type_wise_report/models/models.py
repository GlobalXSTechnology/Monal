from odoo import models, fields, api
from datetime import date
import calendar
from dateutil.relativedelta import relativedelta


class DeductionTypeWiseReport(models.TransientModel):
    _name = 'deduction.wise.report'

    structure_ids = fields.Many2many('hr.payroll.structure', string='Section')
    rule_ids = fields.Many2many('hr.salary.rule','deduction_rule_rel','wizard_id', 'rule_id', string='Line Type', domain="[('id', 'in', rule_domain_ids)]")
    period = fields.Selection(
        selection=lambda self: self._get_month_selection(),
        string='Period',
        required=True,
    )
    date_to = fields.Date(string='Date To', required=True, store=True)
    date_from = fields.Date(string='Date From', required=True, store=True)
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

    rule_domain_ids = fields.Many2many(
        'hr.salary.rule',
        'deduction_rule_domain_rel',
        'wizard_id',
        'rule_domain_id',
        string="Rule Domain Helper",
    )
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=lambda self: self.env.company, readonly=True
    )

    @api.onchange('structure_ids')
    def _onchange_salary_structure_id(self):
        if self.structure_ids:
            rules = self.structure_ids.mapped('rule_ids').filtered(lambda r: r.category_id.code == 'DED')
        else:
            rules = self.env['hr.salary.rule'].search([('category_id.code', '=', 'DED')])

        unique_rules = {}
        for r in rules:
            if r.code not in unique_rules:
                unique_rules[r.code] = r.id

        self.rule_domain_ids = list(unique_rules.values())

    @api.model
    def _get_last_12_months(self):
        months = []
        today = date.today()
        for i in range(12):
            month_date = today - relativedelta(months=i)
            label = month_date.strftime('%b %Y')
            value = month_date.strftime('%Y-%m')
            months.append((value, label))
        return months

    def print_deduction_type_wise_report(self):
        year, month = map(int, self.period.split('-'))
        # date_from = date(year, month, 1)
        # date_to = (date_from + relativedelta(months=1)) - relativedelta(days=1)
        date_from = self.date_from
        date_to = self.date_to

        domain = [
            ('slip_id.date_from', '>=', date_from),
            ('slip_id.date_to', '<=', date_to),
            ('slip_id.company_id', '=', self.company_id.id),
        ]

        if self.structure_ids:
            domain.append(('slip_id.struct_id', 'in', self.structure_ids.ids))

        if self.rule_ids:
            domain.append(('salary_rule_id', 'in', self.rule_ids.ids))

        payslip_lines = self.env['hr.payslip.line'].search(domain)

        result = {}
        for line in payslip_lines:
            structure = line.slip_id.struct_id
            rule = line.salary_rule_id
            if rule.category_id.code != 'DED':
                continue

            if structure not in result:
                result[structure] = {}

            if rule not in result[structure]:
                result[structure][rule] = 0

            result[structure][rule] += line.total

        structure_wise = []
        for struct, rules in result.items():
            filtered_rules = {rule: amount for rule, amount in rules.items() if amount != 0}
            if not filtered_rules:
                continue
            structure_wise.append({
                    'structure_name': struct.name,
                    'rules': [
                        {
                            'rule_name': rule.name,
                            'amount': amount
                        } for rule, amount in filtered_rules.items()
                    ]
                })
        year, month = map(int, self.period.split('-'))
        period_label = f"{calendar.month_name[month]} {year}"
        final_data = {
            'period_label': period_label,
            'company_name': self.company_id.name,
            'structure_wise': structure_wise
        }

        return self.env.ref('deduction_type_wise_report.action_deduction_type_wise_report').report_action(self, data=final_data)


