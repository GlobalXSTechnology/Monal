from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, date
import logging
from dateutil.relativedelta import relativedelta

from odoo.addons.stock.report.stock_traceability import autoIncrement

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'


    amount_2 = fields.Char(string="Amount", store=True, tracking=True)
    acc_no = fields.Char(string="Beneficiary Account #", store=True, tracking=True,compute='get_iojdihf')
    beneficiary_code = fields.Char(string="Beneficiary Code", store=True, tracking=True,compute='get_iojdihf')
    bank_name = fields.Char(string="Beneficiary Bank", store=True, tracking=True,compute='get_iojdihf')
    account_holder = fields.Many2one('res.partner',string="Beneficiary Name", store=True, tracking=True,compute='get_iojdihf')
    reference_1 = fields.Char(string="Reference 1", store=True, tracking=True)
    reference_2 = fields.Char(string="Reference 2", store=True, tracking=True)
    beneficiary_email = fields.Char(string="Beneficiary Email", store=True, tracking=True)
    beneficiary_mobile = fields.Char(string="Beneficiary Mobile", store=True, tracking=True)
    product_type_code = fields.Char(string="Product Type Code", store=True, tracking=True)

    @api.depends('work_contact_id')
    def get_iojdihf(self):
        for rec in self:
            _logger.info('0000000')
            _logger.info('0000000')
            _logger.info('0000000')
            _logger.info('0000000')
            _logger.info('0000000')
            _logger.info('0000000')
            _logger.info('0000000')
            _logger.info('0000000')
            _logger.info('0000000')
            _logger.info('0000000')
            _logger.info('0000000')
            _logger.info('0000000')
            _logger.info('0000000')
            _logger.info(rec.work_contact_id)
            rec.account_holder = rec.work_contact_id.id
            rec.acc_no = rec.work_contact_id.bank_ids.acc_number
            rec.bank_name = rec.work_contact_id.bank_ids.bank_id.name
            rec.beneficiary_code = rec.work_contact_id.bank_ids.bank_id.bic
            _logger.info(rec.work_contact_id.bank_ids)
            _logger.info(rec.work_contact_id.bank_ids.bank_id)
            _logger.info(rec.work_contact_id.bank_ids.bank_id.bic)
            _logger.info(rec.work_contact_id.bank_ids.bank_id.name)