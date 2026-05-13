from odoo import fields, models, api, _

class TransferConsumption(models.Model):
    _inherit = 'transfer.consumption'


    custom_analytic_distribution = fields.Json(inverse="_inverse_analytic_distribution", )

    def _inverse_analytic_distribution(self):
        pass