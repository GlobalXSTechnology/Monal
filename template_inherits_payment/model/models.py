from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from num2words import num2words


class AccountPayment(models.Model):
    _inherit = 'account.payment'


    def get_invoices(self):
        return self.invoice_ids | self.reconciled_invoice_ids | self.reconciled_bill_ids


    def amount_to_words(self, amount):
        text_amount = ''
        if amount:
            # convert to words (without decimals)
            text_amount = num2words(int(amount), lang='en_IN')  # en_IN is good for money format
            # capitalize each word
            text_amount = ' '.join(word.capitalize() for word in text_amount.split())
            # add 'Only' at the end
            text_amount += " Only"
        return text_amount

