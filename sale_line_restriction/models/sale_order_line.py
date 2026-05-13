from odoo import models, api
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def unlink(self):
        for line in self:
            # Sale Order ki states: 'draft' (Quotation), 'sent' (Quotation Sent), 'sale' (Sales Order)
            # Boss ki requirement: Sirf 'draft' par delete ho, baaki par error aye
            if line.order_id and line.order_id.state != 'draft':
                raise UserError(
                    "You are unable to delete this line ! This Line  only delete on 'Quotation' stage.")

        # Agar state 'draft' hai to deletion proceed hogi
        return super(SaleOrderLine, self).unlink()