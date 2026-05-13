from odoo import models, fields

class TransferConsumptionReport(models.Model):
    _inherit = 'transfer.consumption'

    def get_total_demand(self):
        return sum(line.demand for line in self.line_ids)

    def get_total_transferred(self):
        return sum(line.quantity for line in self.line_ids)