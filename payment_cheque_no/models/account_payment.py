from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    cheque_no = fields.Char(string="Cheque Number")


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    cheque_no = fields.Char(string="Cheque Number")

    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)
        payment_vals['cheque_no'] = self.cheque_no
        active_id = self.env.context.get('active_id')
        logger.info("AAAAAAAAAAAAAAAAAAAAAAAAAAADDDDDDD")
        logger.info(active_id)
        if self.cheque_no and active_id:
            bill = self.env['account.move'].browse(active_id)
            logger.info(bill)

            if bill.exists():
                bill.ref = self.cheque_no
                bill.cheque_no = self.cheque_no

        return payment_vals


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    cheque_no = fields.Char(string="Cheque Number")

    def action_post(self):
        res = super().action_post()
        for payment in self:
            if payment.cheque_no and payment.move_id:
                payment.move_id.cheque_no = payment.cheque_no

            if payment.cheque_no and payment.reconciled_invoice_ids:
                for inv in payment.reconciled_invoice_ids:
                    inv.cheque_no = payment.cheque_no
        return res

    # @api.model
    # def create(self, vals):
    #     res = super().create(vals)
    #     if res.cheque_no and res.move_id:
    #         res.move_id.cheque_no = res.cheque_no
    #
    #     if res.cheque_no and res.reconciled_invoice_ids:
    #         for inv in res.reconciled_invoice_ids:
    #             inv.cheque_no = res.cheque_no
    #
    #     return res
    #
    # def write(self, vals):
    #     res = super().write(vals)
    #     for rec in self:
    #         if vals.get('cheque_no') and rec.move_id:
    #             rec.move_id.cheque_no = vals['cheque_no']
    #         if vals.get('cheque_no') and rec.reconciled_invoice_ids:
    #             for inv in rec.reconciled_invoice_ids:
    #                 inv.cheque_no = vals['cheque_no']
    #     return res

    @api.constrains('cheque_no')
    def _check_duplicate_cheque_no(self):
        for rec in self:
            if rec.cheque_no:
                existing = self.env['account.payment'].search([
                    ('cheque_no', '=', rec.cheque_no),
                    ('id', '!=', rec.id)
                ])
                if existing:
                    raise ValidationError(
                        f"The cheque number '{rec.cheque_no}' already exists in another payment."
                    )
