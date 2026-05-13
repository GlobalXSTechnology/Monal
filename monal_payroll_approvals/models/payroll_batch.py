from odoo import models, api, fields
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, date
import logging
from dateutil.relativedelta import relativedelta

import calendar

_logger = logging.getLogger(__name__)


class HRPayslipRun(models.Model):
    _inherit= 'hr.payslip.run'

    state = fields.Selection([
        ('draft', 'New'),
        ('verify', 'Confirmed'),
        ('hr', 'HR'),
        ('audit', 'Audit'),
        ('close', 'Done'),
        ('paid', 'Paid'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft',tracking=True, store=True, compute='_compute_state_change')

    def action_hr_approval(self):
        self.state = 'hr'

    def action_audit_approval(self):
        self.state = 'audit'


class HrContract(models.Model):
    _inherit = 'hr.contract'

    structure_type_id = fields.Many2one(
        tracking=True
    )