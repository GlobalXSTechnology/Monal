from odoo import models, api, fields
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, date
import logging
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class EmployeeLoanBudget(models.Model):
    _name = 'employee.loan.budget'
    _description = 'Employee Budget Configuration'
    _rec_name = 'name'

    name = fields.Char(
        string="Reference",
        required=True,
        readonly=True,
        default=lambda self: self._get_default_ref(),
        copy=False,
    )
    company_id = fields.Many2one(comodel_name="res.company",
                                 string="Company",
                                 required=True,
                                 index=True,
                                 default=lambda self: self.env.company)
    department_id = fields.Many2many(
        'hr.department',
        string='Department',
        required=True
    )
    budget = fields.Float(string='Budget', required=True)
    # budget2 = fields.Float(string='Secondary Budget')
    consumed_budget = fields.Float(
        string="Consumed Budget",
        default=0.0,
        readonly=True
    )
    remaining_budget = fields.Float(
        string="Remaining Budget",
        compute='_compute_remaining_budget',
        store=True
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('refuse', 'Refuse'),
    ], default="draft", track_visibility='always')

    @api.depends('budget', 'consumed_budget')
    def _compute_remaining_budget(self):
        for record in self:
            record.remaining_budget = record.budget - record.consumed_budget

    # @api.model
    # def create(self, vals):
    #     if vals.get('name', 'New') == 'New':
    #         vals['name'] = self.env['ir.sequence'].next_by_code('employee.loan.budget') or 'New'
    #     return super().create(vals)

    # @api.model
    # def create(self, vals):
    #     if vals.get('name', 'New') == 'New':
    #         seq = self.env['ir.sequence'].next_by_code('employee.loan.budget') or 'New'
    #         _logger.info("Generated Sequence: %s", seq)
    #         vals['name'] = seq
    #     return super().create(vals)
    @api.model
    def _get_default_ref(self):
        return self.env['ir.sequence'].next_by_code('employee.loan.budget') or 'New'

    def action_approve(self):
        self.state = 'approved'

    def action_refuse(self):
        self.state = 'refuse'
