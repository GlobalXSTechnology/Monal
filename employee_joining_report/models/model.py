from odoo import models, fields, api
from datetime import date


class EmployeeJoiningReport(models.Model):
    _name = 'employee.joining.report'

    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=lambda self: self.env.company.id,
        readonly=True
    )
    department_ids = fields.Many2many('hr.department', string="Departments")
    employee_ids = fields.Many2many('hr.employee', string="Employees")
    select_type = fields.Selection([('company', 'Company'), ('department', 'Department'), ('employee', 'Employee'), ],
                                   string="Select Type", required=True)

    def action_print_report(self):
        self.ensure_one()

        domain = []

        if self.select_type == 'company' and self.company_id:
            domain.append(('company_id', '=', self.company_id.id))

        elif self.select_type == 'department' and self.department_ids:
            domain.append(('department_id', 'in', self.department_ids.ids))

        elif self.select_type == 'employee' and self.employee_ids:
            return self.env.ref(
                'employee_joining_report.action_employee_form_report'
            ).report_action(self.employee_ids.ids)

        employees = self.env['hr.employee'].search(domain)

        return self.env.ref('employee_joining_report.action_employee_form_report').report_action(employees.ids)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    age_full = fields.Char(string='Age (Y-M-D)', compute='_compute_age_full', store=False)

    @api.depends('birthday')
    def _compute_age_full(self):
        for rec in self:
            if rec.birthday:
                today = date.today()
                bday = rec.birthday
                # Calculate difference
                years = today.year - bday.year
                months = today.month - bday.month
                days = today.day - bday.day

                if days < 0:
                    months -= 1
                    # Days in previous month
                    from calendar import monthrange
                    days += monthrange(today.year if today.month > 1 else today.year - 1,
                                       today.month - 1 if today.month > 1 else 12)[1]

                if months < 0:
                    years -= 1
                    months += 12

                rec.age_full = f"{years} Y - {months} M - {days} D"
            else:
                rec.age_full = ""

    def _get_contract_start_date(self):
        self.ensure_one()

        contract = self.env['hr.contract'].search([
            ('employee_id', '=', self.id),
            ('state', 'in', ['draft'])
        ], order='date_start desc', limit=1)

        # If no draft contract found → fallback to current contract
        if not contract:
            contract = self.contract_id

        # Return formatted date or empty string
        if contract and contract.date_start:
            return contract.date_start
        # .strftime('%d-%m-%Y')

        return ''

    def _get_display_contract(self):
        self.ensure_one()

        # 1. Try draft contract
        contract = self.env['hr.contract'].search([
            ('employee_id', '=', self.id),
            ('state', '=', 'draft')
        ], order='date_start desc', limit=1)

        # 2. Fallback to current contract
        if not contract:
            contract = self.contract_id

        return contract


class EmployeeJoiningReport(models.Model):
    _inherit = 'hr.employee'

    def get_first_referral_info(self):
        if not self.x_studio_referral_1:
            return {}

        badge = self.x_studio_referral_1.badge_id

        employee = self.env['hr.employee'].search(
            [('barcode', '=', badge)],
            limit=1
        )

        return {
            'name': employee.name,
            'identification_id': employee.identification_id,
            'dept': employee.department_id.name,
            'job': employee.job_id.name,
            'address': employee.private_street,
            'phone': employee.work_phone,
        }

    def get_second_referral_info(self):
        if not self.x_studio_referral_2:
            return {}

        badge = self.x_studio_referral_2.badge_id

        employee = self.env['hr.employee'].search(
            [('barcode', '=', badge)],
            limit=1
        )

        return {
            'name': employee.name,
            'identification_id': employee.identification_id,
            'dept': employee.department_id.name,
            'job': employee.job_id.name,
            'address': employee.private_street,
            'phone': employee.work_phone,
        }
