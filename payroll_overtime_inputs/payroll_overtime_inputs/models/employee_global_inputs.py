from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)


class EmployeeGlobalInputs(models.Model):
    _name = 'employee.global.input'
    _rec_name = 'employee_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Employee Global Input'

    employee_id = fields.Many2one('hr.employee', 'Employee', store=True, tracking=True)
    date_to = fields.Date(string='Date To', tracking=True)
    date_from = fields.Date(string='Date From', tracking=True)
    apply_by = fields.Selection([
        ('batch', "Batch"),
        ('dpt', "Department"),
        ('comp', "Company"),
        ('emp', "Employees"),
        ('group_department', "Group By Department"),
    ], string="Apply Inputs By", default='batch', tracking=True)

    global_input_id = fields.Many2one('global.input', 'Batch', tracking=True)
    batch_id = fields.Many2one('hr.payslip.run', 'Batch', tracking=True)
    department_id = fields.Many2one('hr.department', 'Department', tracking=True)
    department_group = fields.Many2one('department.group', string='Department Group')
    company_id = fields.Many2one('res.company', 'Company', store=True,
                                 tracking=True)

    input_line_ids = fields.One2many(
        'employee.global.input.line', 'input_id', string='Payslip Inputs', store=True,
        readonly=False)


class EmployeeGlobalInputLine(models.Model):
    _name = 'employee.global.input.line'

    name = fields.Char(string="Description")
    input_id = fields.Many2one('employee.global.input', string='Global Input', ondelete='cascade', index=True)
    input_type_id = fields.Many2one('hr.payslip.input.type', string='Type', required=True)
    sequence = fields.Integer(required=True, index=True, default=10)
    amount = fields.Float(string="Amount")
    employee_id = fields.Many2one('hr.employee', string="Employee")
