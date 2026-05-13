from odoo import models, fields, api
from num2words import num2words

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    amount_words = fields.Char(string="Amount in Words", compute="_compute_amount_words")

    @api.depends('amount')
    def _compute_amount_words(self):
        for rec in self:
            rec.amount_words = self.amount_to_words(rec.amount)

    def amount_to_words(self, amount):
        if not amount:
            return ""
        whole = int(amount)
        words = num2words(whole, lang='en').capitalize()
        words += " Only"
        return words