from odoo import models, fields, api

class ProductBrand(models.Model):
    _name = 'product.brand'
    _rec_name = 'brand_name'

    brand_name = fields.Char(string="Brand Name")
    product_name = fields.Many2one('product.product',string="Product Name")


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    brand_id = fields.Many2one('product.brand', string="Brand", domain="[('product_name', '=', product_id)]")

    @api.onchange('product_id')
    def _onchange_product_id_set_brand(self):
        if self.product_id:
            brand = self.env['product.brand'].search([('product_name', '=', self.product_id.id)], limit=1)
            self.brand_id = brand.id
        else:
            self.brand_id = False