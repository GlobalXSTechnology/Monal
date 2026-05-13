from odoo import models, fields, api
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import calendar



class MonalFacilityRegisterReport(models.TransientModel):
    _name = 'monal.facility.register.report'
    _description = "Facility Register Report Wizard"

    period = fields.Selection(selection=lambda self: self._get_month_selection(), string='Period', required=True)
    mode_type = fields.Selection([
        ('employee', 'Employee Wise'),
        ('department', 'Department Wise'),
        ('company', 'Company Wise'),
    ], string="Mode Type", default='company', required=True)

    from_date = fields.Date(
        'From Date',
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

    def print_report_facility(self):
        domain = [
            ('distribution_date', '>=', self.from_date),
            ('distribution_date', '<=', self.to_date),
        ]

        if self.mode_type == 'company' and self.company_id:
            domain += [('company_id', '=', self.company_id.id)]

        if self.mode_type == 'department' and self.department_ids:
            domain += [('line_ids.department_id', 'in', self.department_ids.ids)]

        if self.mode_type == 'employee' and self.employee_ids:
            domain += [('line_ids.employee_id', 'in', self.employee_ids.ids)]

        # payslips = self.env['hr.payslip'].search(domain)
        #
        # if self.department_ids:
        # 	domain += [('line_ids.department_id', 'in', self.department_ids.ids)]
        # if self.employee_ids:
        # 	domain += [('line_ids.employee_id', 'in', self.employee_ids.ids)]
        # if self.company_id:
        # 	domain += [('company_id', '=', self.company_id.id)]

        # Fetch uniform distributions within range
        uniform_records = self.env['employee.uniform'].search(domain)
        all_datas = []

        for rec in uniform_records:
            for line in rec.line_ids:
                data_dict = {
                    'ref_no': rec.name,
                    'distribution_date': rec.distribution_date,
                    'company': rec.company_id.name or '',
                    'product': line.product_id.name or '',
                    'source_location': rec.source_location_id.display_name or '',
                    'destination_location': rec.destination_location_id.display_name or '',
                    'emp_code': line.employee_id.barcode or '',
                    'emp_name': line.employee_id.name or '',
                    'department': line.department_id.name or '',
                    'designation': line.job_id.name or '',
                    'sr': '----',
                    'method': line.check_filter or '',
                    'remarks': '----',
                    'quantity': line.quantity or 0.0,
                    'unit_price': line.price_unit or 0.0,
                    'total_price': line.total_price or 0.0,
                    'issued_before': line.total_issued_to_employee or 0.0,
                }
                # If line.check_fillter == 'return', show return-related info
                if line.check_filter == 'return':
                    data_dict.update({
                        'method_return': line.check_filter or '',
                        'return_date': rec.distribution_date or '',
                        'return_doc_no': rec.name,
                        'return_qty': line.quantity or 0.0,
                    })
                else:
                    data_dict.update({
                        'method_return': '----',
                        'return_date': '----',
                        'return_doc_no': '----',
                        'return_qty': '----',
                    })
                all_datas.append(data_dict)

        data = {'all_datas': all_datas}
        return self.env.ref('monal_employee_facility_register_report.report_facility_register_employee').report_action(
            [], data=data)
