# from odoo import models, fields, api
#
# class EmployeeBatch(models.Model):
#     _name = 'employee.batch'
#     _description = 'Employees Master'
#
#     name = fields.Char( string='Employee Name',required=True)
#     badge_id = fields.Char(string='Badge ID')
#     company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
#     contract_id = fields.Many2one('hr.contract', string="Contract")
#
#     @api.model
#     def populate_employee_master(self):
#         hr_employees = self.env['hr.employee'].search([])
#         for emp in hr_employees:
#             existing = self.search([('name', '=', emp.name)])
#             if not existing:
#                 self.create({
#                     'name': emp.name,
#                     'badge_id': getattr(emp, 'barcode', ''),  # hr.employee me badge_id ya barcode
#                 })


from odoo import models, fields, api
from datetime import date


class EmployeeBatch(models.Model):
    _name = 'employee.batch'
    _description = 'Employees Master'

    name = fields.Char(string='Employee Name', required=True)
    badge_id = fields.Char(string='Badge ID')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    contract_id = fields.Many2one('hr.contract', string="Contract")
    has_active_contract = fields.Boolean(
        string='Has Active Contract',
        compute='_compute_has_active_contract',
        store=True,
        default=True
    )
    employee_id = fields.Many2one('hr.employee', string="Employee")

    @api.depends('employee_id.active','contract_id', 'contract_id.state', 'contract_id.date_end')
    def _compute_has_active_contract(self):
        today = date.today()
        for record in self:
            if not record.employee_id or not record.employee_id.active:
                record.has_active_contract = False
            elif record.contract_id:
                # Check if contract is running and not expired
                record.has_active_contract = (
                        record.contract_id.state == 'open' and
                        (not record.contract_id.date_end or record.contract_id.date_end >= today)
                )
            else:
                # If no contract linked, consider as inactive
                record.has_active_contract = False

    @api.model
    def populate_employee_master(self):
        hr_employees = self.env['hr.employee'].search([])
        for emp in hr_employees:
            existing = self.search([('name', '=', emp.name)])
            if not existing:
                # Get active contract
                active_contract = self.env['hr.contract'].search([
                    ('employee_id', '=', emp.id),
                    ('state', '=', 'open')
                ], limit=1)

                self.create({
                    'name': emp.name,
                    'badge_id': getattr(emp, 'barcode', ''),
                    'contract_id': active_contract.id if active_contract else False,
                })