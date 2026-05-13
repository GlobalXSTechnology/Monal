# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CostField(models.Model):
    _inherit = 'stock.quant'


    pro_cost = fields.Float(related='product_id.standard_price', string='Cost')
    valuation_on_qty = fields.Float(compute='calculate_valuation_based_on_qty', string='Valuation Based On Counted Qty')

    @api.depends('pro_cost', 'inventory_quantity')
    def calculate_valuation_based_on_qty(self):
        for rec in self:
            rec.valuation_on_qty = rec.pro_cost * rec.inventory_quantity
