from odoo import models, api
from odoo.exceptions import UserError


class TransferConsumptionLine(models.Model):
    _inherit = 'transfer.consumption.line'

    def unlink(self):
        for rec in self:
            if rec.transfer_id and rec.transfer_id.approval_stage != 'draft':
                raise UserError("Unable to delete this line ! Only 'Draft' stage deletion is allowed .")

        return super(TransferConsumptionLine, self).unlink()
