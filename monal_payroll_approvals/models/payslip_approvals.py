from odoo import models, api, fields
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, date
import logging
from dateutil.relativedelta import relativedelta

import calendar

_logger = logging.getLogger(__name__)


class HRPayslip(models.Model):
    _inherit= 'hr.payslip'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('verify', 'Waiting'),
        ('hr', 'HR'),
        ('audit', 'Audit'),
        ('done', 'Done'),
        ('paid', 'Paid'),
        ('cancel', 'Canceled')],
        string='Status', index=True, readonly=True, copy=False,
        default='draft', tracking=True,
        help="""* When the payslip is created the status is \'Draft\'
                    \n* If the payslip is under verification, the status is \'Waiting\'.
                    \n* If the payslip is confirmed then status is set to \'Done\'.
                    \n* When the user cancels a payslip, the status is \'Canceled\'.""")

    def payslip_hr_approval(self):
        self.state = 'hr'

    def payslip_audit_approval(self):
        self.state = 'audit'


