from odoo import models, fields, api


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    last_purchase_price = fields.Float(
        string="Last Purchase Price",
        readonly=False,
        compute='_compute_product_id_last_price',
        help="The last price at which this product was purchased."
    )

    @api.depends('product_id')
    def _compute_product_id_last_price(self):
        for line in self:
            if line.product_id:
                last_po_line = self.env['purchase.order.line'].search([
                    ('product_id', '=', line.product_id.id),
                    ('order_id.state', 'in', ['purchase', 'done']),  # Only confirmed or done POs
                ], order="create_date desc", limit=1)

                line.last_purchase_price = last_po_line.price_unit if last_po_line else 0.0
