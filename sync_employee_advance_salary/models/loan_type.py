from odoo import models, fields, api
from datetime import datetime


class LoanType(models.Model):
    _name = 'loan.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Loan Type"

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')