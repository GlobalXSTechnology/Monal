# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    advance_salary_id = fields.Many2one('hr.advance.salary', string='Advance Payment')

    @api.model
    def default_get(self, fields):
        """
        Default Get From Advance salary Request.
        """
        rec = super(AccountPayment, self).default_get(fields)
        
        _logger.info('Context: %s', self.env.context)

        if self.env.context.get('advance_salary_id'):
            advance_salary = self.env['hr.advance.salary'].browse(self.env.context.get('advance_salary_id'))
            
            _logger.info('Advance Salary: %s', advance_salary)
            
            rec.update({
                'payment_type': 'outbound',
                'partner_id': advance_salary.employee_id.work_contact_id.id,
                'amount_exclusive_sales_tax': advance_salary.request_amount,
                'journal_id': self.env['account.journal'].search([('type', 'in', ['bank', 'cash'])], limit=1).id,
                'advance_salary_id': advance_salary.id,
            })

            _logger.info('Updated rec: %s', rec)
        else:
            _logger.info('No advance_salary_id in context')

        return rec

    def action_post(self):
        """
            Override method for Advance salary request paid time calculate advance salary
        """
        rec = super(AccountPayment, self).action_post()
        # if self.journal_id.type == 'bank':
            # sequence = self.env.ref('account_payment_field.account_payment_sequence')
            #if sequence and 'BNK' not in self.name:
            # self.name = sequence.next_by_id()
        if self.advance_salary_id:
            self.advance_salary_id.write({
                'paid_date': datetime.today(),
                'paid_by': self.env.uid,
                'state': 'paid',
                'payment_id': self.id,
                'paid_amount': self.amount,
            })
        return rec


class AccountAbstractPayment(models.Model):
    _inherit = 'account.payment'

    @api.onchange('currency_id')
    def _onchange_currency(self):
        self.amount = abs(self.amount)
