from odoo import models, api, fields
from odoo.exceptions import ValidationError
import logging
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    journal_idd = fields.Boolean(string="Use for Bulk Advance Payments")


