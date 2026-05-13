from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class HRDepartment(models.Model):
    _inherit = 'hr.department'

    opening_count = fields.Integer(string="Opening Count", tracking=True)
    head_count_employee = fields.Integer(string="Total Head Count",
                                         tracking=True)
    opening_budget = fields.Monetary(string='Opening Budget', tracking=True)
    budget = fields.Monetary(string='Total Budget',
                             tracking=True)
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id.id,
        required=True)

    opening_count_check = fields.Boolean(string="Count")
    opening_budget_check = fields.Boolean(string="budget")
    total_wage = fields.Monetary(
        string="Total Wage Bill",
        compute='_compute_total_employee_wages',
        store=True,
        currency_field='currency_id',
        tracking=True,
    )

    @api.constrains('opening_count')
    def _compute_head_count_employee(self):
        for rec in self:
            rec.opening_count_check = True
            rec.head_count_employee = rec.opening_count

    @api.constrains('opening_budget')
    def _compute_budget(self):
        for rec in self:
            rec.opening_budget_check = True
            rec.budget = rec.opening_budget

    @api.depends('member_ids', 'member_ids.contract_id.wage')
    def _compute_total_employee_wages(self):
        for department in self:
            total = 0.0
            for employee in department.member_ids:
                if employee.contract_id and employee.contract_id.state in ['draft','open']:
                    total += employee.contract_id.wage
            department.total_wage = total